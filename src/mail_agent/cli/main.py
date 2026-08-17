"""
Job Agent CLI

A conversational assistant that can (optionally) read/send mail on your
behalf, backed by a local or cloud LLM provider.
"""

from dotenv import load_dotenv

load_dotenv()

import asyncio
import os

import httpx
import ollama
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

import questionary

from mail_agent import MailAgent
from mail_agent.model import PROVIDERS
from mail_agent.utils import (
    is_ollama_running,
    check_user_authentication,
    authorize_google_mail,
    load_config,
    save_config,
)

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Manage and chat with your local mail agent.",
)
console = Console()

MAIL_TOOLS = ["send_mail", "read_mail"]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _print_message(message: str, *, title: str = "Info", style: str = "cyan") -> None:
    """Render a nicely styled panel for CLI feedback."""
    console.print(
        Panel.fit(
            message,
            title=f"[bold]{title}[/bold]",
            border_style=style,
            padding=(0, 2),
        )
    )


def _print_success(message: str) -> None:
    _print_message(message, title="Success", style="green")


def _print_warning(message: str) -> None:
    _print_message(message, title="Warning", style="yellow")


def _print_error(message: str) -> None:
    _print_message(message, title="Error", style="red")


def _list_ollama_models() -> list[dict]:
    """Return installed Ollama models, or exit if there are none / Ollama is down."""
    if not is_ollama_running():
        _print_error("Ollama isn't running. Start it and try again.")
        raise typer.Exit(code=1)

    models = ollama.list().get("models", [])
    if not models:
        _print_warning(
            "No models found. Pull one first, for example: "
            "[bold]ollama pull llama3[/bold]."
        )
        raise typer.Exit(code=1)

    return models


def _list_groq_models() -> list[str]:
    """Fetch available Groq models via their API."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        _print_error(
            "GROQ_API_KEY not set. Add it to your .env or export it in your shell."
        )
        raise typer.Exit(code=1)

    try:
        resp = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        models = resp.json().get("data", [])
        return sorted([m["id"] for m in models])
    except Exception as exc:
        _print_error(f"Failed to fetch Groq models: {exc}")
        raise typer.Exit(code=1) from exc


def _list_openrouter_models() -> list[str]:
    """Fetch available OpenRouter models via their API."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        _print_error(
            "OPENROUTER_API_KEY not set. Add it to your .env or export it in your shell."
        )
        raise typer.Exit(code=1)

    try:
        resp = httpx.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        # Filter to chat-capable models only
        chat_models = []
        for m in data:
            modality = m.get("architecture", {}).get("modality", "")
            if "text" in modality:
                chat_models.append(m["id"])
        return sorted(chat_models)
    except Exception as exc:
        _print_error(f"Failed to fetch OpenRouter models: {exc}")
        raise typer.Exit(code=1) from exc


def _render_model_table(models: list[str], provider: str) -> None:
    table = Table(title=f"Available {PROVIDERS[provider]['name']} Models")
    table.add_column("Model", style="cyan")

    for model in models:
        table.add_row(model)

    console.print(table)


def _choose_provider() -> str:
    """Let user pick a provider. Returns provider key (e.g. 'ollama', 'groq')."""
    choices = list(PROVIDERS.keys())
    display = [PROVIDERS[p]["name"] for p in choices]

    chosen = questionary.select(
        "Choose a model provider",
        choices=display,
    ).ask()

    # map display name back to key
    for key, info in PROVIDERS.items():
        if info["name"] == chosen:
            return key
    return choices[0]


def _check_api_key(provider: str) -> None:
    """Ensure the required API key env var is set for cloud providers."""
    info = PROVIDERS[provider]
    if not info["requires_api_key"]:
        return

    env_key = info["env_key"]
    if not os.getenv(env_key):
        _print_error(
            f"{env_key} not found in environment. "
            f"Get your key from the provider's console and add it to your .env file:\n\n"
            f"  {env_key}=your_key_here\n"
        )
        raise typer.Exit(code=1)


def _choose_model_for_provider(provider: str) -> str:
    """Fetch and let user pick a model for the given provider."""
    if provider == "ollama":
        models = _list_ollama_models()
        names = [m["model"] for m in models]
        _render_model_table(names, provider)
        return questionary.select("Choose a model", choices=names).ask()

    elif provider == "groq":
        with console.status("Fetching Groq models..."):
            models = _list_groq_models()
        _render_model_table(models, provider)
        return questionary.select("Choose a model", choices=models).ask()

    elif provider == "openrouter":
        with console.status("Fetching OpenRouter models..."):
            models = _list_openrouter_models()
        _render_model_table(models, provider)
        return questionary.select("Choose a model", choices=models).ask()

    else:
        _print_error(f"Unknown provider: {provider}")
        raise typer.Exit(code=1)


def _ensure_google_auth(config: dict) -> None:
    """Make sure Google mail auth is set up, asking the user if it isn't."""
    if check_user_authentication():
        config["mail_authorization"] = True
        _print_success("Google authentication is already configured.")
        return

    if not Confirm.ask("Authorize with Google to enable the Gmail tool?"):
        config["mail_authorization"] = False
        return

    try:
        authorize_google_mail()
    except Exception as exc:  # noqa: BLE001
        _print_error(f"Google authorization failed: {exc}")
        raise typer.Exit(code=1) from exc

    config["mail_authorization"] = True
    _print_success("Google mail authorization completed successfully.")


# --------------------------------------------------------------------------- #
# Chat
# --------------------------------------------------------------------------- #


async def _run_chat_loop() -> None:
    agent = MailAgent()
    with console.status("Starting agent..."):
        await agent.intialize()

    console.print(
        Panel.fit(
            "Type your message and press enter. Type [bold]exit[/bold] or "
            "[bold]quit[/bold] to leave.",
            title="[bold]Mail Agent[/bold]",
            border_style="blue",
        )
    )

    while True:
        try:
            user_input = Prompt.ask("[bold blue]You[/bold blue]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session ended.[/dim]")
            break

        if user_input.strip().lower() in {"exit", "quit"}:
            console.print("[dim]Goodbye![/dim]")
            break

        status = None
        assistent_started = False
        async for event in agent.stream(user_input=user_input):
            if event["type"] == "status":
                if status is None:
                    status = console.status(event["data"])
                    status.start()
                else:
                    status.update(event["data"])

            elif event["type"] == "token":
                if not assistent_started and event["data"] != "":
                    assistent_started = True
                    console.print("[bold green]Assistant[/bold green]: ", end="")

                if status:
                    status.stop()
                    status = None
                    console.print("[bold green]Assistant[/bold green]: ", end="")

                console.print(event["data"], end="")
        console.print()  # newline after the streamed reply


@app.command()
def start() -> None:
    """Start an interactive chat session."""
    config = load_config()

    if not config.get("user_mail"):
        _print_error(
            "Agent setup is incomplete. Run [bold]mail-agent setup[/bold] to configure your account first."
        )
        raise typer.Exit(code=1)

    provider = config.get("provider", "ollama")
    if provider == "ollama" and not is_ollama_running():
        _print_error("Ollama isn't running. Start it and try again.")
        raise typer.Exit(code=1)

    if provider != "ollama":
        _check_api_key(provider)

    asyncio.run(_run_chat_loop())


@app.command()
def tui() -> None:
    """Launch the modern chat TUI."""
    config = load_config()
    if not config.get("user_mail"):
        _print_error(
            "Agent setup is incomplete. Run [bold]mail-agent setup[/bold] to configure your account first."
        )
        raise typer.Exit(code=1)

    provider = config.get("provider", "ollama")
    if provider == "ollama" and not is_ollama_running():
        _print_error("Ollama isn't running. Start it and try again.")
        raise typer.Exit(code=1)

    if provider != "ollama":
        _check_api_key(provider)

    from mail_agent.tui.app import MailTUI

    MailTUI().run()


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #


@app.command()
def models() -> None:
    """List available models for the current (or all) provider(s)."""
    config = load_config()
    current_provider = config.get("provider", "ollama")

    provider_to_show = questionary.select(
        "List models for which provider?",
        choices=[PROVIDERS[current_provider]["name"] + " (current)"]
        + [info["name"] for key, info in PROVIDERS.items() if key != current_provider],
    ).ask()

    # resolve provider key
    chosen_key = current_provider
    suffix = " (current)"
    for key, info in PROVIDERS.items():
        display = info["name"] + (suffix if key == current_provider else "")
        if display == provider_to_show:
            chosen_key = key
            break

    if chosen_key == "ollama":
        model_list = _list_ollama_models()
        names = [m["model"] for m in model_list]
        _render_model_table(names, chosen_key)
    elif chosen_key == "groq":
        with console.status("Fetching Groq models..."):
            names = _list_groq_models()
        _render_model_table(names, chosen_key)
    elif chosen_key == "openrouter":
        with console.status("Fetching OpenRouter models..."):
            names = _list_openrouter_models()
        _render_model_table(names, chosen_key)


# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #


@app.command()
def setup() -> None:
    """Set up the agent: pick a provider & model, wire up Gmail, and choose tools."""
    config = load_config()

    # --- Provider ---
    console.rule("Provider")
    provider = _choose_provider()
    config["provider"] = provider
    _print_success(f"Using provider [bold]{PROVIDERS[provider]['name']}[/bold].")

    # --- API Key check for cloud providers ---
    if PROVIDERS[provider]["requires_api_key"]:
        _check_api_key(provider)

    # --- Model ---
    console.rule("Model")
    config["model"] = _choose_model_for_provider(provider)
    _print_success(f"Using model [bold]{config['model']}[/bold].")

    # --- Google Mail ---
    console.rule("Google Mail")
    user_mail = config.get("user_mail", "")
    if config.get("user_mail"):
        if Confirm.ask("You already setup a mail, Do you want to change it"):
            user_mail = Prompt.ask(
                "Type your Email address, we will use this as default sender mail"
            )
    else:
        user_mail = Prompt.ask(
            "Type your Email address, we will use this as default sender mail"
        )
    config["user_mail"] = user_mail
    _ensure_google_auth(config)

    # --- Tools ---
    console.rule("Tools")
    enabled_tools = config.get("enabled_tools", [])
    attachment_dir = config.get("attachment_dir", "")
    if MAIL_TOOLS not in enabled_tools and Confirm.ask("Enable the mail-sending tool?"):
        enabled_tools.extend(MAIL_TOOLS)
        enabled_tools = list(set(enabled_tools))  # remove duplicates
        config["enabled_tools"] = enabled_tools
        _print_success("Mail tool enabled.")

    if not attachment_dir:
        if Confirm.ask("Setup Attachment Directory?"):
            attachment_dir = Prompt.ask("Enter your attachment directory path")
            config["attachment_dir"] = attachment_dir
            _print_success("Attachment directory configured.")

    save_config(config)
    console.rule()
    _print_success("Setup complete. You can start the agent now.")


@app.command()
def mail_auth() -> None:
    """Authorize Gmail access if it isn't already set up."""
    config = load_config()
    _ensure_google_auth(config)
    save_config(config)


@app.command()
def enable_email(
    disable: bool = typer.Option(
        False, "--disable", help="Disable the mail tool instead."
    ),
) -> None:
    """Enable (or disable) the mail-sending tool."""
    config = load_config()
    enabled_tools = config.setdefault("enabled_tools", [])
    mail_tools = set(MAIL_TOOLS)
    enabled_tools = set(enabled_tools)

    if disable:
        enabled_mail_tools = enabled_tools.intersection(mail_tools)
        if enabled_mail_tools:
            for tool in enabled_mail_tools:
                enabled_tools.remove(tool)

            config["enabled_tools"] = list(enabled_tools)
            save_config(config)
            _print_warning("Mail tool disabled.")
        else:
            _print_warning("Mail tool was already disabled.")
        return

    if not mail_tools.difference(enabled_tools):
        _print_warning("Mail tool is already enabled.")
        return

    enabled_tools = list(enabled_tools)
    enabled_tools.extend(MAIL_TOOLS)
    enabled_tools = list(set(enabled_tools))

    config["enabled_tools"] = enabled_tools
    save_config(config)
    _print_success("Mail tool enabled.")


@app.command()
def clear_config():
    """Disable the mail tool instead."""
    config = {}
    save_config(config)
    _print_warning("Configuration cleared.")


if __name__ == "__main__":
    app()

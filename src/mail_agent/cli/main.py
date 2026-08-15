"""
Job Agent CLI

A conversational assistant that can (optionally) read/send mail on your
behalf, backed by a local Ollama model.
"""
from dotenv import load_dotenv
load_dotenv()

import asyncio
from typing import Optional

import ollama
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

import questionary

from mail_agent import MailAgent
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


def _render_model_table(models: list[dict]) -> None:
    table = Table(title="Installed Ollama Models")
    table.add_column("Model", style="cyan")
    table.add_column("Size (GB)", justify="right")

    for model in models:
        size_gb = model["size"] / (1024**3)
        table.add_row(model["model"], f"{size_gb:.2f}")

    console.print(table)
    


def _choose_model(models: list[dict]) -> str:
    _render_model_table(models)

    names = [m["model"] for m in models]

    return questionary.select(
        "Choose a model",
        choices=names,
    ).ask()


# def _choose_model(models: list[dict]) -> str:
#     _render_model_table(models)
#     names = [m["model"] for m in models]

#     selected = Prompt.ask("Choose a model", choices=names, show_choices=False)
#     return selected


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

        # console.print("[bold green]Assistant[/bold green]: ", end="")

        status = None
        assistent_started = False
        async for event in agent.stream(user_input=user_input):

            if event['type'] == "status": # Status reminders, "tool {name} Executing...."

                # For terminal spinner effect
                if status == None:
                    status = console.status(event["data"])
                    status.start()
                
                else:
                    status.update(event["data"])

                # console.print()
            elif event['type'] == "token":

                # a fix for assitent text coming and erased my spinner of tool executing status,
                #  so only asistent msg will show assisten msg not for tool spinner
                # when tool executing, first few token will "", so condition on ""
                if not assistent_started and event["data"] != "":
                    assistent_started = True
                    console.print("[bold green]Assistant[/bold green]: ", end="")
                
                # stop the spinner when ai start generating, means tool execution complete
                if status:
                    status.stop()
                    status = None
                    console.print("[bold green]Assistant[/bold green]: ", end="")
                    
                    
                console.print(event['data'], end="")
        console.print()  # newline after the streamed reply


@app.command()
def start() -> None:
    """Start an interactive chat session."""
    setup = load_config().get("user_mail")

    
    if not setup:
        _print_error(
            "Agent setup is incomplete. Run [bold]job-agent setup[/bold] to configure your account first."
        )
        raise typer.Exit(code=1)

    if not is_ollama_running():
        _print_error("Ollama isn't running. Start it and try again.")
        raise typer.Exit(code=1)
    
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

    if not is_ollama_running():
        _print_error("Ollama isn't running. Start it and try again.")
        raise typer.Exit(code=1)

    from mail_agent.tui.app import MailTUI

    MailTUI().run()


# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #

@app.command()
def setup() -> None:
    """Set up the agent: pick a model, wire up Gmail, and choose tools."""
    config = load_config()

    console.rule("Ollama")
    models = _list_ollama_models()
    config["model"] = _choose_model(models)
    _print_success(f"Using model [bold]{config['model']}[/bold].")

    console.rule("Google Mail")
    user_mail = config.get('user_mail', "")
    if config['user_mail']:
        if Confirm.ask("You already setup a mail, Do you want to change it"):
            user_mail = Prompt.ask("Type your Email address, we will use this as default sender mail")
    else:
        user_mail = Prompt.ask("Type your Email address, we will use this as default sender mail")
    config['user_mail'] = user_mail
    _ensure_google_auth(config)

    console.rule("Tools")
    enabled_tools = config.get("enabled_tools", [])
    attachment_dir = config.get("attachment_dir", "")
    if MAIL_TOOLS not in enabled_tools and Confirm.ask("Enable the mail-sending tool?"):
        enabled_tools.extend(MAIL_TOOLS)
        enabled_tools = list(set(enabled_tools)) # remove duplicates
        config['enabled_tools'] = enabled_tools
        _print_success("Mail tool enabled.")

    if not attachment_dir:
        if Confirm.ask("Setup Attachment Directory?"):
            attachment_dir = Prompt.ask('Enter your attachment directory path')
            config['attachment_dir'] = attachment_dir
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
    disable: bool = typer.Option(False, "--disable", help="Disable the mail tool instead."),
) -> None:
    """Enable (or disable) the mail-sending tool."""
    config = load_config()
    enabled_tools = config.setdefault("enabled_tools", [])
    mail_tools = set(MAIL_TOOLS)
    enabled_tools = set(enabled_tools)


    if disable:
        enabled_mail_tools = enabled_tools.intersection(mail_tools)
        # if any mail tools are inside enabled tools remove it
        if enabled_mail_tools:
            for tool in enabled_mail_tools:
                enabled_tools.remove(tool)
            
            config['enaled_tools'] = enabled_tools
            save_config(config)
            _print_warning("Mail tool disabled.")
        else:
            _print_warning("Mail tool was already disabled.")
        return

    # if there is no tools in mail tools that are not in enabled tools then skip
    if not mail_tools.difference(enabled_tools):
        _print_warning("Mail tool is already enabled.")
        return
    
    enabled_tools = list(enabled_tools)
    enabled_tools.extend(MAIL_TOOLS)

    # remove duplicates
    enabled_tools = list(set(enabled_tools))
    
    config['enabled_tools'] = enabled_tools
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
"""
Job Agent CLI

A conversational assistant that can (optionally) read/send mail on your
behalf, backed by a local Ollama model.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import ollama
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from job_agent import MailAgent
from job_agent.utils import (
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

MAIL_TOOLS = ["send_mail","read_mail"]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _list_ollama_models() -> list[dict]:
    """Return installed Ollama models, or exit if there are none / Ollama is down."""
    if not is_ollama_running():
        console.print("[red]✗[/red] Ollama isn't running. Start it and try again.")
        raise typer.Exit(code=1)

    models = ollama.list().get("models", [])
    if not models:
        console.print(
            "[yellow]No models found.[/yellow] Pull one first, e.g. "
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
    

import questionary

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
        console.print("[green]✓[/green] Google auth already configured.")
        return

    if not Confirm.ask("Authorize with Google to enable the Gmail tool?"):
        config["mail_authorization"] = False
        return

    try:
        authorize_google_mail()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]✗[/red] Google authorization failed: {exc}")
        raise typer.Exit(code=1) from exc

    config["mail_authorization"] = True
    console.print("[green]✓[/green] Google mail authorized.")


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
            title="Mail Agent",
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

        console.print("[bold green]Assistant[/bold green]: ", end="")
        async for chunk in agent.stream(user_input=user_input):
            console.print(chunk, end="")
        console.print()  # newline after the streamed reply


@app.command()
def start() -> None:
    """Start an interactive chat session."""
    asyncio.run(_run_chat_loop())


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
    console.print(f"[green]✓[/green] Using model [bold]{config['model']}[/bold]")

    console.rule("Google Mail")
    user_mail = Prompt.ask("Type your Email address, we will use this as default sender mail")
    config['user_mail'] = user_mail
    _ensure_google_auth(config)

    console.rule("Tools")
    enabled_tools = config.setdefault("enabled_tools", [])
    if MAIL_TOOLS not in enabled_tools and Confirm.ask("Enable the mail-sending tool?"):
        enabled_tools.extend(MAIL_TOOLS)
        console.print("[green]✓[/green] Mail tool enabled.")

    save_config(config)
    console.rule()
    console.print("[bold green]Setup complete.[/bold green]")


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
            console.print("[green]✓[/green] Mail tool disabled.")
        else:
            console.print("[yellow]Mail tool was already disabled.[/yellow]")
        return

    # if there is no tools in mail tools that are not in enabled tools then skip
    if not mail_tools.difference(enabled_tools):
        console.print("[yellow]Mail tool is already enabled.[/yellow]")
        return
    
    enabled_tools = list(enabled_tools)
    enabled_tools.extend(MAIL_TOOLS)

    # remove duplicates
    enabled_tools = list(set(enabled_tools))
    
    config['enabled_tools'] = enabled_tools
    save_config(config)
    console.print("[green]✓[/green] Mail tool enabled.")

@app.command()
def clear_config():
   """Disable the mail tool instead."""
   config = {}
   save_config(config)
   console.print("[green]✓[/green] Cleared the config.")

if __name__ == "__main__":
    app()
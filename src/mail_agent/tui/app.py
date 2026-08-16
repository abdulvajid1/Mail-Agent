"""
Mail Agent — a modern chat TUI.

A Textual application styled like a contemporary chat client (think Claude or
opencode): warm dark palette, message bubbles, streaming output with a blinking
cursor, live tool-execution chips, and a composer that submits on Enter.
"""

from __future__ import annotations

import re

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Footer, Markdown, Static, TextArea

from mail_agent import MailAgent
from mail_agent.utils import is_ollama_running, load_config

CURSOR = "▍"
BRAND_ICON = "✉"

SUGGESTIONS = [
    "Read and summarize my emails",
    "Send a follow-up to my boss",
    "Check my unread mail",
]

_MARKDOWN_RE = re.compile(
    r"(?:^|\n)(?:#{1,6}\s|>\s|```|\s*[-*+]\s|\s*\d+\.\s|\[[^\]]+\]\([^)]*\)|!\[|\s*\||~~|\*\*|__)"
)

WELCOME = (
    f"[#d97757]{BRAND_ICON} Mail Agent[/]\n\n"
    "[b]Your inbox, in conversation.[/]\n"
    "Ask me anything about your mail — read it, summarize it, or send replies."
)


class Spinner(Static):
    """A tiny braille spinner that switches to a checkmark when done."""

    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def on_mount(self) -> None:
        self._index = 0
        self.update(self.FRAMES[self._index])
        self._timer = self.set_interval(0.09, self._tick)

    def _tick(self) -> None:
        self._index = (self._index + 1) % len(self.FRAMES)
        self.update(self.FRAMES[self._index])

    def done(self) -> None:
        timer = getattr(self, "_timer", None)
        if timer is not None:
            timer.stop()
        self.set_classes("chip-icon done")
        self.update("✓")


class StatusChip(Horizontal):
    """A pill that reports a tool executing, e.g. ``send_mail``."""

    def __init__(self, text: str) -> None:
        super().__init__(classes="status-chip")
        self._label = text

    def compose(self) -> ComposeResult:
        self._icon = Spinner(classes="chip-icon")
        yield self._icon
        yield Static(self._label, classes="chip-text", markup=False)

    def set_done(self) -> None:
        self.set_classes("status-chip done")
        self._icon.done()


class MessageBubble(Vertical):
    """A single chat message rendered as a bubble row."""

    def __init__(
        self,
        role: str,
        content: str = "",
        *,
        streaming: bool = False,
    ) -> None:
        super().__init__(classes=f"message {role}")
        self.role = role
        self._content = content
        self._streaming = streaming
        self._buffer = content
        self._cursor_on = True
        self._finished = False
        self._chips: list[StatusChip] = []

    def compose(self) -> ComposeResult:
        with Horizontal(classes="row"):
            if self.role == "user":
                with Vertical(classes="body"):
                    yield Static(self._content, classes="bubble user-bubble", markup=False)
                yield Static("You", classes="avatar user-avatar", markup=False)
            else:
                yield Static("Assistent", classes="avatar agent-avatar", markup=False)
                with Vertical(classes="body"):
                    yield Static("Mail Agent", classes="meta agent-meta", markup=False)
                    self._stream = Static(classes="stream", markup=False)
                    yield self._stream

    def on_mount(self) -> None:
        if self.role == "assistant":
            self._render_stream()
            if self._streaming:
                self._cursor_timer = self.set_interval(0.5, self._toggle_cursor)

    def _toggle_cursor(self) -> None:
        self._cursor_on = not self._cursor_on
        self._render_stream()

    def _render_stream(self) -> None:
        if self.role != "assistant":
            return
        text = self._buffer
        if self._streaming and not self._finished:
            text = f"{text}{CURSOR}" if text and self._cursor_on else text or "Thinking…"
        self._stream.update(text)

    def append_token(self, token: str) -> None:
        if self.role != "assistant" or self._finished:
            return
        self._buffer += token
        self._render_stream()

    async def add_status(self, text: str) -> None:
        if self.role != "assistant":
            return
        chip = StatusChip(text)
        self._chips.append(chip)
        await self.mount(chip, before=self._stream)

    async def error(self, message: str) -> None:
        if self._finished:
            return
        self._finish_streaming()
        self._stream.set_classes("stream error")
        self._stream.update(f"Something went wrong: {message}")
        if self._chips:
            self._chips[-1].set_done()

    async def finish(self) -> None:
        if self._finished:
            return
        self._finish_streaming()
        for chip in self._chips:
            chip.set_done()
        if self.role != "assistant":
            return
        content = self._buffer.strip()
        if not content:
            self._stream.update("(no response)")
        elif _MARKDOWN_RE.search(content):
            await self._stream.remove()
            await self.mount(Markdown(content, classes="markdown"))
        else:
            self._stream.update(content)

    def _finish_streaming(self) -> None:
        self._finished = True
        timer = getattr(self, "_cursor_timer", None)
        if timer is not None:
            timer.stop()


class Composer(TextArea):
    """Chat input that submits on Enter and keeps the classic editing keys."""

    class Submitted(Message):
        def __init__(self, composer: Composer) -> None:
            super().__init__()
            self.composer = composer

    async def _on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            event.stop()
            event.prevent_default()
            self.post_message(self.Submitted(self))
            return
        await super()._on_key(event)


class MailTUI(App):
    """The chat interface for the Mail Agent."""

    TITLE = "Mail Agent"
    SUB_TITLE = "Your inbox, in conversation"
    CSS_PATH = "app.tcss"
    AUTO_FOCUS = "#composer"

    BINDINGS = [
        Binding("ctrl+l", "clear_chat", "Clear chat"),
        Binding("ctrl+n", "new_chat", "New chat"),
        Binding("ctrl+c", "help_quit", "Quit", priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.agent: MailAgent | None = None
        self.ready = False
        self.busy = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            with Horizontal(id="brand"):
                yield Static(BRAND_ICON, id="brand-icon", markup=False)
                yield Static("Mail Agent", id="brand-title", markup=False)
            yield Static("", id="topbar-gap", markup=False)
            yield Static("● connecting", id="conn-chip", classes="chip", markup=False)
            yield Static("", id="model-chip", classes="chip", markup=False)
            yield Static("", id="mail-chip", classes="chip", markup=False)

        with VerticalScroll(id="chat-scroll"):
            with Vertical(id="hero"):
                yield Static(WELCOME, id="welcome-box", classes="welcome")
                with Horizontal(id="suggestions"):
                    for text in SUGGESTIONS:
                        yield Button(text, classes="suggestion")

        with Horizontal(id="composer-wrap"):
            yield Composer(
                placeholder="Ask me to read or send an email…",
                id="composer",
            )
            yield Button("Send", id="send-btn")

        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._init_agent())

    async def _init_agent(self) -> None:
        conn = self.query_one("#conn-chip", Static)
        model_chip = self.query_one("#model-chip", Static)
        mail_chip = self.query_one("#mail-chip", Static)
        try:
            config = load_config()
            model = config.get("model")
            mail = config.get("user_mail")
            if model:
                model_chip.update(model)
                model_chip.display = True
            if mail:
                mail_chip.update("gmail")
                mail_chip.display = True

            if not model or not mail:
                conn.set_classes("chip warn")
                conn.update("● setup needed")
                self.notify(
                    "Run `mail-agent setup` first.",
                    title="Setup required",
                    severity="warning",
                )
                return
            if not is_ollama_running():
                conn.set_classes("chip err")
                conn.update("● ollama offline")
                self.notify(
                    "Start Ollama and try again.",
                    title="Ollama offline",
                    severity="error",
                )
                return

            agent = MailAgent()
            await agent.intialize()
            self.agent = agent
            self.ready = True
            conn.set_classes("chip ok")
            conn.update("● ready")
            self._set_input_enabled(True)
            self.query_one("#composer", Composer).focus()
        except Exception as exc:  # noqa: BLE001
            conn.set_classes("chip err")
            conn.update("● error")
            self.notify(str(exc), title="Agent failed to start", severity="error")

    async def on_composer_submitted(self, event: Composer.Submitted) -> None:
        event.stop()
        await self._send()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        button = event.button
        if button.id == "send-btn":
            await self._send()
        elif "suggestion" in button.classes:
            composer = self.query_one("#composer", Composer)
            composer.text = button.label.plain
            composer.focus()
            await self._send()

    async def _send(self) -> None:
        composer = self.query_one("#composer", Composer)
        text = composer.text.strip()
        if not text or not self.ready or self.busy:
            return
        self.busy = True
        self._set_input_enabled(False)
        composer.clear()

        hero = self.query_one("#hero")
        if hero.display:
            hero.display = False

        chat = self.query_one("#chat-scroll")
        user_msg = MessageBubble("user", text)
        agent_msg = MessageBubble("assistant", streaming=True)
        await chat.mount_all([user_msg, agent_msg])
        self._scroll_to_bottom(animate=False)
        self.run_worker(self._stream_chat(agent_msg, text))

    async def _stream_chat(self, message: MessageBubble, text: str) -> None:
        try:
            async for event in self.agent.stream(text):  # type: ignore[union-attr]
                if event["type"] == "status":
                    await message.add_status(event["data"])
                elif event["type"] == "token":
                    message.append_token(event["data"])
                if self._is_at_bottom():
                    self._scroll_to_bottom(animate=False)
        except Exception as exc:  # noqa: BLE001
            await message.error(str(exc))
        finally:
            await message.finish()
            if self._is_at_bottom():
                self._scroll_to_bottom(animate=False)
            self.busy = False
            self._set_input_enabled(True)
            self.query_one("#composer", Composer).focus()

    def _is_at_bottom(self) -> bool:
        chat = self.query_one("#chat-scroll")
        return chat.scroll_offset.y >= chat.max_scroll_y - 1

    def _scroll_to_bottom(self, animate: bool = True) -> None:
        self.query_one("#chat-scroll").scroll_end(animate=animate)

    def _set_input_enabled(self, enabled: bool) -> None:
        self.query_one("#composer", Composer).disabled = not enabled
        self.query_one("#send-btn", Button).disabled = not enabled

    def _reset_chat(self) -> None:
        if self.busy:
            self.notify("Agent is still responding.", severity="warning")
            return
        chat = self.query_one("#chat-scroll")
        chat.remove_children(".message")
        self.query_one("#hero").display = True
        self.query_one("#composer", Composer).focus()

    def action_clear_chat(self) -> None:
        self._reset_chat()

    def action_new_chat(self) -> None:
        self._reset_chat()


if __name__ == "__main__":
    MailTUI().run()

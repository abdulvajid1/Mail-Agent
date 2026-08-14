from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer
from textual.containers import Horizontal
from textual.widgets import Input, Static
class MailAgent(App):
    """
    The TUI for Mail Agent.
    """

    TITLE = "Mail Agent"
    CSS_PATH = "./app.tcss"

    def compose(self):
        yield Header(show_clock=True)
        with Horizontal(id="input_container"):
            yield Static(">", id="prompt_icon")
            yield Input(
                placeholder="Ask me any Mail related questions",
                id="prompt_input"
                )
        yield Footer()


if __name__ == "__main__":
    app = MailAgent()
    app.run()

# Mail Agent

An AI-powered command-line agent that connects to a local [Ollama](https://ollama.com) model and your Gmail account, letting you chat with an assistant that can read, manage, and send email on your behalf — right from your terminal.

## Features

- 🖥️ **Runs anywhere** — install with a single command, no manual Python setup required
- 🤖 **Local LLM powered** — pick from any model you already have pulled in Ollama (e.g. `llama3.1`, `qwen2.5-coder`, `nomic-embed-text`)
- 📧 **Gmail integration** — authorize once, then let the agent read and send mail through natural conversation
- ⚙️ **Simple CLI** — guided setup wizard, no config files to hand-edit

## Prerequisites

- [Ollama](https://ollama.com) installed and running locally, with at least one model pulled
  ```bash
  ollama pull llama3.1
  ```
- `git` (used by the installer to fetch the package)
- A Gmail account, if you want to enable the mail tool

You do **not** need Python installed beforehand — the installer handles that for you.

## Installation

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/abdulvajid1/Mail-Agent/master/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/abdulvajid1/Mail-Agent/master/install.ps1 | iex
```

After installation, **restart your terminal** (or open a new tab) so your shell picks up the `mail-agent` command.

<details>
<summary>What does the installer actually do?</summary>

1. Installs [`uv`](https://docs.astral.sh/uv/) (a fast Python package/tool manager) if it's not already on your system — this also transparently installs an isolated Python for you if needed
2. Uses `uv tool install` to build Mail Agent into its own isolated environment, so it won't conflict with anything else on your machine
3. Adds the `mail-agent` command to your shell's `PATH` via `uv tool update-shell`

Nothing is installed system-wide outside of `uv` itself and this one isolated tool environment.
</details>

## Usage

Run the setup wizard first — it walks you through picking a model and connecting Gmail:

```bash
mail-agent setup
```

Then start chatting with your agent:

```bash
mail-agent start
```

### All commands

| Command | Description |
|---|---|
| `mail-agent setup` | Pick a model, wire up Gmail, and choose tools |
| `mail-agent start` | Start an interactive chat session |
| `mail-agent mail-auth` | Authorize Gmail access if it isn't already set up |
| `mail-agent enable-email` | Enable (or disable) the mail-sending tool |
| `mail-agent clear-config` | Reset/disable the mail tool |
| `mail-agent --help` | Show all available commands |

## Web UI

A minimalist React frontend that talks to the agent through a FastAPI server
over Server-Sent Events (SSE). Tool executions are surfaced in real time as
status events while the assistant streams its reply.

**Start the API** (from the repo root, requires a configured `~/.agent/config.json` — run `mail-agent setup` first):

```bash
uv run python -m mail_agent.api
```

The API runs on `http://localhost:8000`:
- `GET /config` — agent/setup status, model, enabled tools, Ollama status
- `GET /chat?user_input=...` or `POST /chat` — SSE stream of `{type, data}` events (`status`, `token`, `done`, `error`)

**Start the frontend** (in a second terminal):

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` to the
FastAPI backend, so no CORS setup is needed locally.

## Updating

```bash
uv tool upgrade mail-agent
```

## Uninstall

Remove everything (the tool, its config, and your Gmail credentials) with one command:

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/abdulvajid1/Mail-Agent/master/uninstall.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/abdulvajid1/Mail-Agent/master/uninstall.ps1 | iex
```

This uninstalls the `mail-agent` tool, deletes `~/.agent/config.json`, your OAuth `token.json`, and — if you run it interactively — offers to remove `uv` too. The script asks before touching anything outside of mail-agent's own files.

## Development

Clone the repo and set up locally with `uv`:

```bash
git clone https://github.com/abdulvajid1/Mail-Agent.git
cd Mail-Agent
uv sync --group dev
```

Run linting:
```bash
uv run ruff check .
```

## Privacy & Credentials

Mail Agent authorizes Gmail access via OAuth on your own machine — your credentials and tokens stay local and are never bundled with or shared through this repository. Each user authorizes their own Google account during `mail-agent setup` or `mail-agent mail-auth`.

## License

See [LICENSE](LICENSE) for details.
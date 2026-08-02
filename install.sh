#!/usr/bin/env bash
set -euo pipefail

REPO="abdulvajid1/Mail-Agent"

echo "Installing mail-agent..."

# 1. Ensure curl or wget is available
if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
    echo "❌ Neither curl nor wget found. Please install one and re-run."
    exit 1
fi

# 2. Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    if command -v curl &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    else
        wget -qO- https://astral.sh/uv/install.sh | sh
    fi
    export PATH="$HOME/.local/bin:$PATH"
fi

# 3. Ensure git is available (needed for git+https installs)
if ! command -v git &> /dev/null; then
    echo "❌ git is required but was not found. Please install git and re-run."
    exit 1
fi

# 4. If already installed, do a full clean reinstall so we never serve stale code
if uv tool list 2>/dev/null | grep -q "^mail-agent"; then
    echo "Existing installation found — reinstalling with the latest version..."
    uv tool uninstall mail-agent
    uv cache clean
fi

# 5. Install fresh from GitHub
uv tool install "git+https://github.com/${REPO}.git"

# 6. Make sure the install dir is actually on PATH
uv tool update-shell

echo "✅ Installed! Restart your terminal, then run: mail-agent"
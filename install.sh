#!/usr/bin/env bash
set -euo pipefail

REPO="abdulvajid1/Mail-Agent"

echo "Installing job-agent..."

# 1. Ensure uv is installed
if ! command -v uv &> /dev/null; then
    if ! command -v curl &> /dev/null; then
        echo "❌ curl is required but not found. Please install curl first."
        exit 1
    fi
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Install your tool straight from GitHub (public repo)
uv tool install "git+https://github.com/${REPO}.git"

# 3. Make sure the install dir is actually on PATH
uv tool update-shell

echo "✅ Installed! Restart your terminal, then run: job-agent"
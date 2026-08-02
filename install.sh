#!/usr/bin/env bash
# Mail Agent installer for macOS / Linux / WSL.
# Usage:  curl -fsSL https://raw.githubusercontent.com/abdulvajid1/Mail-Agent/master/install.sh | bash
set -euo pipefail

REPO="abdulvajid1/Mail-Agent"
REF="${MAIL_AGENT_VERSION:-master}"   # pin a tag like "v0.1.0" via MAIL_AGENT_VERSION if you like

say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m==>\033[0m %s\n' "$*" >&2; exit 1; }

# --------------------------------------------------------------------------- #
# 1. Fetch tool
# --------------------------------------------------------------------------- #
if command -v curl >/dev/null 2>&1; then
    DOWNLOAD="curl -fsSL"
elif command -v wget >/dev/null 2>&1; then
    DOWNLOAD="wget -qO-"
else
    die "Neither curl nor wget found. Install one of them and re-run."
fi

# --------------------------------------------------------------------------- #
# 2. Ensure uv is installed
# --------------------------------------------------------------------------- #
if ! command -v uv >/dev/null 2>&1; then
    say "uv not found — installing the latest version..."
    $DOWNLOAD https://astral.sh/uv/install.sh | sh

    # The installer drops uv into one of these; make sure it is on PATH
    # for the rest of this script even if the user's shell hasn't reloaded.
    for dir in "$HOME/.local/bin" "$HOME/.cargo/bin"; do
        if [ -x "$dir/uv" ]; then
            export PATH="$dir:$PATH"
            break
        fi
    done

    command -v uv >/dev/null 2>&1 || die "uv was installed but could not be found on PATH. Restart your terminal and re-run."
else
    say "uv found: $(uv --version)"
fi

# --------------------------------------------------------------------------- #
# 3. Ensure git is available (needed to fetch the source from GitHub)
# --------------------------------------------------------------------------- #
command -v git >/dev/null 2>&1 || die "git is required. Install it (e.g. 'brew install git', 'apt install git', 'dnf install git') and re-run."

# --------------------------------------------------------------------------- #
# 4. Install (or reinstall) the tool, always fresh from GitHub
# --------------------------------------------------------------------------- #
say "Installing mail-agent from https://github.com/${REPO} (${REF})..."
uv tool install --force "git+https://github.com/${REPO}.git@${REF}"

# --------------------------------------------------------------------------- #
# 5. Refresh shell PATH so `mail-agent` resolves in a brand-new terminal
# --------------------------------------------------------------------------- #
uv tool update-shell >/dev/null 2>&1 || true

# --------------------------------------------------------------------------- #
# 6. Sanity check + next steps
# --------------------------------------------------------------------------- #
ok "mail-agent installed successfully."
echo ""
echo "  Next steps:"
echo "    1. Open a new terminal (or run:  source ~/.bashrc   # /  source ~/.zshrc)"
echo "    2. Configure once:               mail-agent setup"
echo "    3. Start chatting:               mail-agent start"
echo ""
echo "  Update later:                      uv tool upgrade mail-agent"
echo "  Uninstall:                         uv tool uninstall mail-agent"

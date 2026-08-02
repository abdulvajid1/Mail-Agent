#!/usr/bin/env bash
# Mail Agent uninstaller for macOS / Linux / WSL — removes the tool, config, and credentials.
# Usage:  curl -fsSL https://raw.githubusercontent.com/abdulvajid1/Mail-Agent/master/uninstall.sh | bash
set -euo pipefail

say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }

# --------------------------------------------------------------------------- #
# 1. Remove the mail-agent tool
# --------------------------------------------------------------------------- #
if command -v uv >/dev/null 2>&1 && uv tool list 2>/dev/null | grep -q "^mail-agent"; then
    say "Uninstalling mail-agent tool..."
    uv tool uninstall mail-agent
else
    # uv is gone or the tool isn't registered — remove the shim directly
    for bin in "$HOME/.local/bin/mail-agent" "$HOME/.cargo/bin/mail-agent"; do
        if [ -e "$bin" ]; then
            say "Removing $bin"
            rm -f "$bin"
        fi
    done
fi

# --------------------------------------------------------------------------- #
# 2. Remove config + credentials created by the app
# --------------------------------------------------------------------------- #
for path in \
    "$HOME/.agent" \
    "$HOME/token.json" \
    "$HOME/credentials.json" \
    "./token.json" \
    "./credentials.json"
do
    if [ -e "$path" ]; then
        say "Removing $path"
        rm -rf "$path"
    fi
done

# --------------------------------------------------------------------------- #
# 3. Optionally remove uv too (only the installer installs it automatically)
# --------------------------------------------------------------------------- #
if command -v uv >/dev/null 2>&1; then
    if [ -t 0 ]; then
        printf 'Remove uv as well? The installer may have installed it. [y/N] '
        read -r answer
        case "$answer" in
            y|Y|yes|Yes)
                say "Removing uv..."
                rm -f "$HOME/.local/bin/uv" "$HOME/.local/bin/uvx" \
                      "$HOME/.cargo/bin/uv" "$HOME/.cargo/bin/uvx"
                rm -rf "$HOME/.local/share/uv" "$HOME/.cache/uv"
                ;;
            *)
                ok "Keeping uv installed."
                ;;
        esac
    else
        ok "Keeping uv (run this script interactively if you also want it removed)."
    fi
fi

ok "Done — mail-agent has been removed."
echo ""
echo "  Final cleanup (optional):"
echo "    - Close and reopen your terminal."
echo "    - If uv added a PATH export to ~/.bashrc / ~/.zshrc and you removed uv,"
echo "      delete that line (e.g. 'export PATH=\"\$HOME/.local/bin:\$PATH\"')."
echo "    - If you ran 'mail-agent setup' from another folder, delete its token.json too."

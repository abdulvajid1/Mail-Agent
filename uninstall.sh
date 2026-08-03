#!/usr/bin/env bash
# Mail Agent uninstaller for macOS / Linux / WSL — removes the tool, config, and credentials.
# Usage:  curl -fsSL https://raw.githubusercontent.com/abdulvajid1/Mail-Agent/master/uninstall.sh | bash
set -euo pipefail

say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }

# --------------------------------------------------------------------------- #
# 1. Remove the mail-agent tool (only mail-agent, never other uv tools)
# --------------------------------------------------------------------------- #
if command -v uv >/dev/null 2>&1 && uv tool list 2>/dev/null | grep -q "^mail-agent"; then
    say "Uninstalling mail-agent tool..."
    uv tool uninstall mail-agent
else
    # uv is gone or the tool isn't registered — remove the shim + tool dir directly
    for bin in "$HOME/.local/bin/mail-agent" "$HOME/.cargo/bin/mail-agent"; do
        if [ -e "$bin" ]; then
            say "Removing $bin"
            rm -f "$bin"
        fi
    done
    for dir in \
        "$HOME/.local/share/uv/tools/mail-agent" \
        "$HOME/.cargo/uv/tools/mail-agent" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/uv/tools/mail-agent"
    do
        if [ -d "$dir" ]; then
            say "Removing $dir"
            rm -rf "$dir"
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
# 3. Optionally remove uv itself (binaries + cache only; other tools/projects
#    and uv-managed Pythons are left untouched)
# --------------------------------------------------------------------------- #
if command -v uv >/dev/null 2>&1; then
    if [ -t 0 ]; then
        printf 'Remove uv itself? This deletes the uv binaries and its download cache, '
        printf 'but leaves every other tool and project on your machine. [y/N] '
        read -r answer
        case "$answer" in
            y|Y|yes|Yes)
                say "Removing uv binaries and cache..."
                rm -f "$HOME/.local/bin/uv" "$HOME/.local/bin/uvx" \
                      "$HOME/.cargo/bin/uv" "$HOME/.cargo/bin/uvx"
                rm -rf "$HOME/.cache/uv" "${XDG_CACHE_HOME:-$HOME/.cache}/uv"
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

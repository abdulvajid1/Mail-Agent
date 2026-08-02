# Mail Agent installer for Windows.
# Usage:  irm https://raw.githubusercontent.com/abdulvajid1/Mail-Agent/master/install.ps1 | iex
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$Repo = "abdulvajid1/Mail-Agent"
$Ref = if ($env:MAIL_AGENT_VERSION) { $env:MAIL_AGENT_VERSION } else { "master" }

Write-Host "Installing mail-agent..." -ForegroundColor Cyan

# 1. Ensure uv is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..." -ForegroundColor Cyan
    powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $uvBin = "$env:USERPROFILE\.local\bin"
    if (Test-Path "$uvBin\uv.exe") {
        $env:PATH = "$uvBin;$env:PATH"
    }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "uv was installed but could not be found on PATH. Restart your terminal and re-run." -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "uv found: $((uv --version))" -ForegroundColor Cyan
}

# 2. Ensure git is available (needed to fetch the source from GitHub)
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "git is required. Install it from https://git-scm.com/download/win and re-run." -ForegroundColor Red
    exit 1
}

# 3. Install (or reinstall) the tool, always fresh from GitHub
Write-Host "Installing mail-agent from https://github.com/$Repo ($Ref)..." -ForegroundColor Cyan
uv tool install --force "git+https://github.com/$Repo.git@$Ref"

# 4. Refresh shell PATH so `mail-agent` resolves in a new terminal
uv tool update-shell | Out-Null

# 5. Sanity check + next steps
Write-Host "`nmail-agent installed successfully." -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:"
Write-Host "    1. Open a new terminal"
Write-Host "    2. Configure once:               mail-agent setup"
Write-Host "    3. Start chatting:               mail-agent start"
Write-Host ""
Write-Host "  Update later:                      uv tool upgrade mail-agent"
Write-Host "  Uninstall:                         uv tool uninstall mail-agent"

#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$Repo = "abdulvajid1/Mail-Agent"

Write-Host "Installing mail-agent..." -ForegroundColor Cyan

# 1. Ensure uv is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $uvBin = "$env:USERPROFILE\.local\bin"
    if (Test-Path $uvBin) {
        $env:PATH = "$uvBin;$env:PATH"
    }
}

# 2. Ensure git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ git is required but was not found. Install it from https://git-scm.com/download/win and re-run this script." -ForegroundColor Red
    exit 1
}

# 3. If already installed, do a full clean reinstall
$installed = uv tool list 2>$null | Select-String "^mail-agent"
if ($installed) {
    Write-Host "Existing installation found — reinstalling with the latest version..."
    uv tool uninstall mail-agent
    uv cache clean
}

# 4. Install fresh from GitHub
uv tool install "git+https://github.com/$Repo.git"

# 5. Make sure the install dir is actually on PATH
uv tool update-shell

Write-Host "✅ Installed! Close and reopen your terminal, then run: mail-agent" -ForegroundColor Green
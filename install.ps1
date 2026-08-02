#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$Repo = "https://github.com/abdulvajid1/Mail-Agent"

Write-Host "Installing job-agent..." -ForegroundColor Cyan

# 1. Ensure uv is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"

    # uv installs to this path by default on Windows
    $uvBin = "$env:USERPROFILE\.local\bin"
    if (Test-Path $uvBin) {
        $env:PATH = "$uvBin;$env:PATH"
    }
}

# 2. Ensure git exists (needed for git+https installs)
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ git is required but was not found. Install it from https://git-scm.com/download/win and re-run this script." -ForegroundColor Red
    exit 1
}

# 3. Install your tool straight from GitHub (public repo)
uv tool install "git+https://github.com/$Repo.git"

# 4. Make sure the install dir is actually on PATH
uv tool update-shell

Write-Host "✅ Installed! Close and reopen your terminal, then run: job-agent" -ForegroundColor Green
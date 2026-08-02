# Mail Agent uninstaller for Windows — removes the tool, config, and credentials.
# Usage:  irm https://raw.githubusercontent.com/abdulvajid1/Mail-Agent/master/uninstall.ps1 | iex
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

# 1. Remove the mail-agent tool
$installed = if (Get-Command uv -ErrorAction SilentlyContinue) { uv tool list 2>$null | Select-String "^mail-agent" } else { $null }
if ($installed) {
    Write-Host "Uninstalling mail-agent tool..." -ForegroundColor Cyan
    uv tool uninstall mail-agent
}
else {
    $shim = Join-Path $HOME ".local\bin\mail-agent.exe"
    if (Test-Path $shim) {
        Write-Host "Removing $shim" -ForegroundColor Cyan
        Remove-Item -Force $shim
    }
}

# 2. Remove config + credentials created by the app
$targets = @(
    (Join-Path $HOME ".agent"),
    (Join-Path $HOME "token.json"),
    (Join-Path $HOME "credentials.json"),
    (Join-Path (Get-Location) "token.json"),
    (Join-Path (Get-Location) "credentials.json")
)
foreach ($path in $targets) {
    if (Test-Path $path) {
        Write-Host "Removing $path" -ForegroundColor Cyan
        Remove-Item -Recurse -Force $path
    }
}

# 3. Optionally remove uv too
if (Get-Command uv -ErrorAction SilentlyContinue) {
    $ans = Read-Host "Remove uv as well? The installer may have installed it. (y/N)"
    if ($ans -match "^(y|yes)$") {
        Write-Host "Removing uv..." -ForegroundColor Cyan
        Remove-Item -Recurse -Force "$HOME\.local\bin\uv.exe", "$HOME\.local\bin\uvx.exe", "$env:APPDATA\uv", "$env:LOCALAPPDATA\uv" -ErrorAction SilentlyContinue
    }
    else {
        Write-Host "Keeping uv installed." -ForegroundColor Yellow
    }
}

Write-Host "`nDone - mail-agent has been removed." -ForegroundColor Green
Write-Host ""
Write-Host "  Final cleanup (optional):"
Write-Host "    - Close and reopen your terminal."
Write-Host "    - If you ran 'mail-agent setup' from another folder, delete its token.json too."

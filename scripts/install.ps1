# toktopus Windows One-Liner Installer
# Usage:
#   irm https://raw.githubusercontent.com/NadimHider/toktopus/main/scripts/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host ":: Installing toktopus (Universal AI Agent Monitor)..." -ForegroundColor Cyan
Write-Host ""

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python 3.9+ is required but was not found in PATH. Please install Python first."
}

Write-Host "[1/2] Installing dependencies and package via pip..." -ForegroundColor DarkCyan
python -m pip install --upgrade --quiet rich psutil
python -m pip install --upgrade --quiet git+https://github.com/NadimHider/toktopus.git

$wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
if (Test-Path $wingetLinks) {
    $shimContent = "@echo off`r`npython -m toktopus.cli %*`r`n"
    Set-Content -Path "$wingetLinks\toktopus.cmd" -Value $shimContent -Force
}

Write-Host ""
Write-Host "[OK] toktopus installed successfully!" -ForegroundColor Green
Write-Host "Run it anytime in your terminal with:" -ForegroundColor White
Write-Host "     toktopus" -ForegroundColor Cyan
Write-Host ""

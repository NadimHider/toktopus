# toktopus Windows One-Liner Installer
# Usage:
#   irm https://raw.githubusercontent.com/nadimhider/toktopus/main/scripts/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "🐙 Installing toktopus (Universal AI Agent Monitor)..." -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python 3.9+ is required but was not found in PATH. Please install Python first."
}

# 2. Install or upgrade via pip
Write-Host "📦 Installing toktopus package via pip..." -ForegroundColor DarkCyan
python -m pip install --upgrade --quiet rich psutil
python -m pip install --upgrade --quiet git+https://github.com/nadimhider/toktopus.git

# 3. Create helper shim in User PATH if needed
$wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
if (Test-Path $wingetLinks) {
    $shimContent = "@echo off`r`npython -m toktopus.cli %*`r`n"
    Set-Content -Path "$wingetLinks\toktopus.cmd" -Value $shimContent -Force
}

Write-Host ""
Write-Host "✨ toktopus installed successfully!" -ForegroundColor Green
Write-Host "🚀 Run it anytime in your terminal with:" -ForegroundColor White
Write-Host "     toktopus" -ForegroundColor Cyan
Write-Host ""

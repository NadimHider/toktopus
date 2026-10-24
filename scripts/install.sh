#!/usr/bin/env bash
# toktopus Linux and macOS One-Liner Installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/NadimHider/toktopus/main/scripts/install.sh | bash

set -e

echo ""
echo ":: Installing toktopus (Universal AI Agent Monitor)..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3.9+ is required but was not found. Please install Python 3."
    exit 1
fi

python3 -m pip install --user --upgrade rich psutil
python3 -m pip install --user --upgrade git+https://github.com/NadimHider/toktopus.git

echo ""
echo "[OK] toktopus installed successfully!"
echo "Run it anytime in your terminal with:"
echo "     toktopus"
echo ""

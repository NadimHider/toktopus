#!/usr/bin/env bash
# toktopus Linux & macOS One-Liner Installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/nadimhider/toktopus/main/scripts/install.sh | bash

set -e

echo ""
echo "🐙 Installing toktopus (Universal AI Agent Monitor)..."
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.9+ is required but was not found. Please install Python 3."
    exit 1
fi

# 2. Install dependencies & toktopus
python3 -m pip install --user --upgrade rich psutil
python3 -m pip install --user --upgrade git+https://github.com/nadimhider/toktopus.git

echo ""
echo "✨ toktopus installed successfully!"
echo "🚀 Run it anytime in your terminal with:"
echo "     toktopus"
echo ""

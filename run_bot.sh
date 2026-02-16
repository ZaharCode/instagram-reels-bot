#!/bin/bash

echo "========================================"
echo "    Instagram Reels Bot"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Install Python 3.7+ and try again."
    read -p "Press Enter to exit..."
    exit 1
fi

# Run launcher
python3 run_bot.py

read -p "Press Enter to exit..."
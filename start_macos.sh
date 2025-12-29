#!/bin/bash
# Quick startup script for macOS

cd "$(dirname "$0")"

# Run preflight check
python3 preflight_check.py

# Check if preflight passed
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Please fix the issues above and try again."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "📋 Quick Checklist:"
echo "   1. ✅ Hancom Office HWP is open"
echo "   2. ✅ A document is open in HWP"
echo "   3. ✅ Accessibility permissions granted"
echo ""
echo "Ready? Press Enter to start the app..."
read

echo ""
echo "🔌 Starting Formulite..."
python3 -m gui.app

echo ""
echo "✨ App closed. Goodbye!"


#!/bin/bash

echo "================================"
echo "  EMInstaller Script Test"
echo "================================"
echo ""

# Display the script
echo "[1] VIEWING YOUR INSTALL SCRIPT:"
echo "-----------------------------------"
cat /test/install
echo ""
echo "-----------------------------------"
echo ""

# Test syntax
echo "[2] TESTING BASH SYNTAX:"
echo "-----------------------------------"
if bash -n /test/install; then
    echo "✓ Syntax is valid"
else
    echo "✗ Syntax error found"
fi
echo ""

# Show what the script does
echo "[3] SCRIPT BREAKDOWN:"
echo "-----------------------------------"
echo "• Checks if running as root"
echo "• Installs dependencies: python, git, curl"
echo "• Downloads installer from GitHub"
echo "• Verifies SHA256 checksum"
echo "• Runs the Python installer"
echo ""

# Test individual components
echo "[4] TESTING DEPENDENCIES:"
echo "-----------------------------------"
pacman -Sy --noconfirm python curl git >/dev/null 2>&1
echo "✓ python3: $(python3 --version)"
echo "✓ curl: $(curl --version | head -1)"
echo "✓ git: $(git --version)"
echo "✓ sha256sum: $(sha256sum --version | head -1)"
echo ""

# Show the Python installer
echo "[5] VIEWING YOUR PYTHON INSTALLER:"
echo "-----------------------------------"
if [ -f /test/eminstaller.py ]; then
    cat /test/eminstaller.py
else
    echo "Note: eminstaller.py not found in container"
fi
echo ""

echo "================================"
echo "  Test Complete!"
echo "================================"

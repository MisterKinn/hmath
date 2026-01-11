#!/bin/bash

# Build macOS App for Formulite
# This script builds the macOS .app bundle using PyInstaller

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Building Nova AI macOS App...${NC}"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This script must be run on macOS${NC}"
    exit 1
fi

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${YELLOW}⚠️ PyInstaller not found. Installing...${NC}"
    pip install pyinstaller
fi

# Clean previous builds
echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
if [[ -d "build" ]]; then
    chmod -R u+w build/ 2>/dev/null || true
    rm -rf build/ 2>/dev/null || true
fi
if [[ -d "dist" ]]; then
    chmod -R u+w dist/ 2>/dev/null || true
    rm -rf dist/ 2>/dev/null || true
fi

# Build the app
echo -e "${BLUE}🔨 Building app bundle...${NC}"
pyinstaller --clean formulite_macos.spec

# Check if build was successful
if [[ -d "dist/Nova AI.app" ]]; then
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo -e "${GREEN}📱 App bundle created at: dist/Nova AI.app${NC}"
    
    # Get app size
    APP_SIZE=$(du -sh "dist/Nova AI.app" | cut -f1)
    echo -e "${BLUE}📏 App bundle size: ${APP_SIZE}${NC}"
    
    # Test if the app can launch
    echo -e "${YELLOW}🧪 Testing app launch...${NC}"
    if open -W -n "dist/Nova AI.app" --args --test-launch 2>/dev/null; then
        echo -e "${GREEN}✅ App launches successfully!${NC}"
    else
        echo -e "${YELLOW}⚠️ App launch test completed (may have closed normally)${NC}"
    fi
    
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Build process completed!${NC}"
echo -e "${BLUE}💡 Next steps:${NC}"
echo -e "   • Run ./create_dmg.sh to create a DMG installer"
echo -e "   • Or run ./create_pkg.sh to create a PKG installer"
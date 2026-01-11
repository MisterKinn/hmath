#!/bin/bash

# Complete macOS build and packaging script for Nova AI
# This script builds the app and creates both DMG and PKG installers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 Nova AI macOS Complete Build & Package Script${NC}"
echo -e "${CYAN}================================================${NC}"

# Function to print step headers
print_step() {
    echo -e "\n${CYAN}📋 Step $1: $2${NC}"
    echo -e "${CYAN}$(printf '%.0s-' {1..50})${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_step "1" "Checking Prerequisites"
    
    # Check if we're on macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}❌ This script must be run on macOS${NC}"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is required but not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ macOS detected${NC}"
    echo -e "${GREEN}✅ Python 3 available${NC}"
    
    # Check and install PyInstaller if needed
    if ! command -v pyinstaller &> /dev/null; then
        echo -e "${YELLOW}⚠️ PyInstaller not found. Installing...${NC}"
        pip3 install pyinstaller
    fi
    echo -e "${GREEN}✅ PyInstaller available${NC}"
    
    # Check for required Python packages
    echo -e "${BLUE}🔍 Checking Python dependencies...${NC}"
    python3 -c "import PySide6; print('✅ PySide6 available')" || {
        echo -e "${YELLOW}⚠️ Installing PySide6...${NC}"
        pip3 install PySide6
    }
}

# Function to build the app
build_app() {
    print_step "2" "Building macOS App Bundle"
    
    # Make build script executable
    chmod +x build_macos.sh
    
    # Run the build
    ./build_macos.sh
}

# Function to create installers
create_installers() {
    print_step "3" "Creating Installation Packages"
    
    # Make scripts executable
    chmod +x create_dmg.sh create_pkg.sh
    
    echo -e "${BLUE}📦 Creating DMG installer...${NC}"
    ./create_dmg.sh
    
    echo -e "\n${BLUE}📦 Creating PKG installer...${NC}"
    ./create_pkg.sh
}

# Function to show final results
show_results() {
    print_step "4" "Build Complete"
    
    echo -e "${GREEN}🎉 All builds completed successfully!${NC}\n"
    
    # Show what was created
    if [[ -d "dist/Formulite.app" ]]; then
        APP_SIZE=$(du -sh dist/Formulite.app | cut -f1)
        echo -e "${GREEN}📱 App Bundle: dist/Formulite.app (${APP_SIZE})${NC}"
    fi
    
    if [[ -f "Formulite.dmg" ]]; then
        DMG_SIZE=$(du -sh Formulite.dmg | cut -f1)
        echo -e "${GREEN}💿 DMG Installer: Formulite.dmg (${DMG_SIZE})${NC}"
    fi
    
    if [[ -f "Formulite-Installer.pkg" ]]; then
        PKG_SIZE=$(du -sh Formulite-Installer.pkg | cut -f1)
        echo -e "${GREEN}📦 PKG Installer: Formulite-Installer.pkg (${PKG_SIZE})${NC}"
    fi
    
    echo -e "\n${CYAN}💡 Distribution Options:${NC}"
    echo -e "   • ${YELLOW}DMG${NC}: Drag-and-drop installation (recommended for most users)"
    echo -e "   • ${YELLOW}PKG${NC}: Guided installer with license agreement"
    echo -e "   • ${YELLOW}App Bundle${NC}: Direct distribution (advanced users)"
    
    echo -e "\n${BLUE}🔍 Testing Your Build:${NC}"
    echo -e "   • Test the app: open dist/Formulite.app"
    echo -e "   • Test DMG: open Formulite.dmg"
    echo -e "   • Test PKG: open Formulite-Installer.pkg"
    
    echo -e "\n${GREEN}🚀 Ready for distribution!${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}⏰ Build started at: $(date)${NC}\n"
    
    check_prerequisites
    build_app
    create_installers
    show_results
    
    echo -e "\n${BLUE}⏰ Build completed at: $(date)${NC}"
    echo -e "${PURPLE}🎯 Total build time: $SECONDS seconds${NC}"
}

# Handle script interruption
trap 'echo -e "\n${RED}❌ Build interrupted!${NC}"; exit 1' INT TERM

# Run main function
main "$@"
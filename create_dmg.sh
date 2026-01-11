#!/bin/bash

# Create DMG installer for Nova AI
# This script creates a beautiful DMG file with the app bundle

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="Nova AI"
APP_BUNDLE="dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME}"
VOLUME_NAME="${APP_NAME} Installer"
DMG_BACKGROUND="dmg_background.png"
TEMP_DMG="temp_${DMG_NAME}.dmg"
FINAL_DMG="${DMG_NAME}.dmg"

echo -e "${BLUE}📦 Creating DMG installer for ${APP_NAME}...${NC}"

# Check if app bundle exists
if [[ ! -d "$APP_BUNDLE" ]]; then
    echo -e "${RED}❌ App bundle not found at ${APP_BUNDLE}${NC}"
    echo -e "${YELLOW}💡 Please run ./build_macos.sh first${NC}"
    exit 1
fi

# Clean up any existing DMG files
echo -e "${YELLOW}🧹 Cleaning up existing DMG files...${NC}"
rm -f "${TEMP_DMG}" "${FINAL_DMG}"

# Calculate required size (app size + 50MB buffer)
echo -e "${BLUE}📏 Calculating DMG size...${NC}"
APP_SIZE=$(du -sm "${APP_BUNDLE}" | cut -f1)
DMG_SIZE=$((APP_SIZE + 50))
echo -e "${BLUE}💾 DMG size will be: ${DMG_SIZE}MB${NC}"

# Create temporary DMG
echo -e "${BLUE}🔨 Creating temporary DMG...${NC}"
hdiutil create -srcfolder "${APP_BUNDLE}" -volname "${VOLUME_NAME}" -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" -format UDRW -size ${DMG_SIZE}m "${TEMP_DMG}"

# Mount the DMG
echo -e "${BLUE}📁 Mounting temporary DMG...${NC}"
MOUNT_DIR="/Volumes/${VOLUME_NAME}"
# Ensure mountpoint does not already exist as a leftover; remove if empty
if [[ -d "${MOUNT_DIR}" ]] && [[ -z "$(ls -A "${MOUNT_DIR}")" ]]; then
    rmdir "${MOUNT_DIR}" 2>/dev/null || true
fi
hdiutil attach -readwrite -noverify -noautoopen "${TEMP_DMG}" -mountpoint "${MOUNT_DIR}" >/dev/null
# Wait briefly for mount to appear
for i in {1..10}; do
    if [[ -d "${MOUNT_DIR}" ]]; then
        break
    fi
    sleep 0.2
done
if [[ ! -d "${MOUNT_DIR}" ]]; then
    echo -e "${RED}❌ Failed to mount temporary DMG at ${MOUNT_DIR}${NC}"
    exit 1
fi

echo -e "${BLUE}📂 Mounted at: ${MOUNT_DIR}${NC}"

# Create Applications symlink
echo -e "${BLUE}🔗 Creating Applications symlink...${NC}"
ln -sf /Applications "${MOUNT_DIR}/Applications"

# Create a simple background if one doesn't exist
if [[ ! -f "${DMG_BACKGROUND}" ]]; then
    echo -e "${YELLOW}🎨 Creating simple background...${NC}"
    # Create a simple background using built-in tools
    cat > create_bg.py << 'EOF'
from PIL import Image, ImageDraw, ImageFont
import sys

# Create a 600x400 image with gradient background
img = Image.new('RGB', (600, 400), color='#f0f0f0')
draw = ImageDraw.Draw(img)

# Add a subtle gradient effect
for y in range(400):
    color_val = int(240 - (y * 20 / 400))
    color = (color_val, color_val, color_val)
    draw.line([(0, y), (600, y)], fill=color)

# Add text instructions
try:
    # Try to use a system font
    font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 24)
except:
    font = ImageFont.load_default()

text = "Drag Nova AI to Applications folder"
text_bbox = draw.textbbox((0, 0), text, font=font)
text_width = text_bbox[2] - text_bbox[0]
text_x = (600 - text_width) // 2
draw.text((text_x, 320), text, fill='#333333', font=font)

img.save('dmg_background.png')
print("Background created successfully")
EOF

    python3 create_bg.py && rm create_bg.py
fi

# Copy background to DMG (if it exists)
if [[ -f "${DMG_BACKGROUND}" ]]; then
    echo -e "${BLUE}🎨 Adding background image...${NC}"
    mkdir -p "${MOUNT_DIR}/.background"
    cp "${DMG_BACKGROUND}" "${MOUNT_DIR}/.background/"
fi

# Set up DMG window appearance using AppleScript
echo -e "${BLUE}🎨 Setting up DMG appearance...${NC}"
cat > setup_dmg.applescript << EOF
tell application "Finder"
    tell disk "${VOLUME_NAME}"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {400, 100, 1000, 500}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 128
        if exists file ".background:${DMG_BACKGROUND}" then
            set background picture of viewOptions to file ".background:${DMG_BACKGROUND}"
        end if
        
        -- Position the app icon and Applications link
        set position of item "${APP_NAME}.app" of container window to {150, 200}
        set position of item "Applications" of container window to {450, 200}
        
        close
        open
        update without registering applications
        delay 2
    end tell
end tell
EOF

# Run the AppleScript to set up the DMG appearance
osascript setup_dmg.applescript
rm setup_dmg.applescript

# Set file permissions
echo -e "${BLUE}🔐 Setting permissions...${NC}"
chmod -Rf go-w "${MOUNT_DIR}"

# Sync and unmount
echo -e "${BLUE}💾 Finalizing DMG...${NC}"
sync
# Try to detach gracefully, retry a few times, then force if needed
for _ in 1 2 3 4 5; do
    if hdiutil detach "${MOUNT_DIR}"; then
        break
    fi
    echo -e "${YELLOW}⚠️ Detach failed, retrying...${NC}"
    sleep 0.5
done
if [[ -d "${MOUNT_DIR}" ]]; then
    echo -e "${YELLOW}⚠️ Detach still failed, forcing detach...${NC}"
    hdiutil detach -force "${MOUNT_DIR}" || true
    # As a last resort, find and force-detach any /dev/disk devices tied to this image
    echo -e "${YELLOW}⚠️ Looking up device nodes for the DMG to force detach...${NC}"
    devs=$(hdiutil info | awk -v m="${MOUNT_DIR}" 'BEGIN{found=0} $0 ~ m {found=1} found && /^\/dev/ {print $1}')
    for d in $devs; do
        echo -e "${YELLOW}⚠️ Forcing detach of ${d}${NC}"
        hdiutil detach -force "${d}" || true
    done
fi

# Convert to compressed read-only DMG
echo -e "${BLUE}🗜️ Compressing final DMG...${NC}"
hdiutil convert "${TEMP_DMG}" -format UDZO -imagekey zlib-level=9 -o "${FINAL_DMG}"

# Clean up temporary files
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -f "${TEMP_DMG}"
rm -f "${DMG_BACKGROUND}" 2>/dev/null || true  # Remove background if we created it

# Get final DMG size
if [[ -f "${FINAL_DMG}" ]]; then
    FINAL_SIZE=$(du -sh "${FINAL_DMG}" | cut -f1)
    echo -e "${GREEN}✅ DMG created successfully!${NC}"
    echo -e "${GREEN}📦 DMG file: ${FINAL_DMG}${NC}"
    echo -e "${GREEN}📏 Final size: ${FINAL_SIZE}${NC}"
    
    # Make DMG executable/openable
    chmod +x "${FINAL_DMG}" 2>/dev/null || true
    
    echo -e "${BLUE}💡 You can now distribute ${FINAL_DMG} to users${NC}"
else
    echo -e "${RED}❌ DMG creation failed!${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 DMG creation completed!${NC}"
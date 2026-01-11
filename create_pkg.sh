#!/bin/bash

# Create PKG installer for Nova AI
# This script creates a macOS package installer (.pkg file)

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
PKG_NAME="${APP_NAME}-Installer"
IDENTIFIER="com.novaai.app.pkg"
VERSION="1.0.0"

echo -e "${BLUE}📦 Creating PKG installer for ${APP_NAME}...${NC}"

# Check if app bundle exists
if [[ ! -d "$APP_BUNDLE" ]]; then
    echo -e "${RED}❌ App bundle not found at ${APP_BUNDLE}${NC}"
    echo -e "${YELLOW}💡 Please run ./build_macos.sh first${NC}"
    exit 1
fi

# Clean up any existing PKG files
echo -e "${YELLOW}🧹 Cleaning up existing PKG files...${NC}"
rm -f "${PKG_NAME}.pkg"
rm -rf pkg_build/

# Create package build directory
echo -e "${BLUE}📁 Setting up package structure...${NC}"
mkdir -p pkg_build/Applications

# Copy app bundle to package directory
echo -e "${BLUE}📱 Copying app bundle...${NC}"
cp -R "${APP_BUNDLE}" pkg_build/Applications/

# Create package info files
echo -e "${BLUE}📄 Creating package metadata...${NC}"

# Create Distribution file
cat > pkg_build/Distribution << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>${APP_NAME}</title>
    <organization>com.formulite</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="false" rootVolumeOnly="true" />
    
    <!-- Define documents displayed at various steps -->
    <welcome    file="welcome.html"    mime-type="text/html" />
    <license    file="license.html"    mime-type="text/html" />
    <conclusion file="conclusion.html" mime-type="text/html" />
    
    <!-- List all component packages -->
    <pkg-ref id="${IDENTIFIER}"/>
    
    <!-- List them again here. They can now be organized
         as a hierarchy if you want. -->
    <choices-outline>
        <line choice="default">
            <line choice="${IDENTIFIER}"/>
        </line>
    </choices-outline>
    
    <!-- Define each choice above -->
    <choice id="default"/>
    <choice id="${IDENTIFIER}" visible="false">
        <pkg-ref id="${IDENTIFIER}"/>
    </choice>
    
    <!-- Define each package (pkg-ref) -->
    <pkg-ref id="${IDENTIFIER}" version="${VERSION}" onConclusion="none">${PKG_NAME}.pkg</pkg-ref>
</installer-gui-script>
EOF

# Create welcome message
cat > pkg_build/welcome.html << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }
        h1 { color: #1d1d1f; font-size: 32px; font-weight: 600; margin-bottom: 8px; }
        p { color: #1d1d1f; font-size: 17px; line-height: 1.4; margin-bottom: 16px; }
    </style>
</head>
<body>
    <h1>Welcome to ${APP_NAME}</h1>
    <p>This installer will install ${APP_NAME} on your Mac.</p>
    <p>${APP_NAME} is a powerful formula editor and HWP integration tool that helps you create mathematical formulas with ease.</p>
    <p>Click Continue to begin the installation.</p>
</body>
</html>
EOF

# Create license file
cat > pkg_build/license.html << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>License</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }
        h1 { color: #1d1d1f; font-size: 24px; font-weight: 600; margin-bottom: 16px; }
        p { color: #1d1d1f; font-size: 15px; line-height: 1.4; margin-bottom: 12px; }
    </style>
</head>
<body>
    <h1>Software License Agreement</h1>
    <p>By installing and using ${APP_NAME}, you agree to the following terms:</p>
    <p>This software is provided "as is" without warranty of any kind, either express or implied.</p>
    <p>The copyright holder grants you permission to use this software for personal and commercial purposes.</p>
    <p>You may not redistribute, modify, or reverse engineer this software without explicit permission.</p>
</body>
</html>
EOF

# Create conclusion message  
cat > pkg_build/conclusion.html << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Installation Complete</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }
        h1 { color: #1d1d1f; font-size: 32px; font-weight: 600; margin-bottom: 8px; }
        p { color: #1d1d1f; font-size: 17px; line-height: 1.4; margin-bottom: 16px; }
        .highlight { background-color: #f5f5f7; padding: 12px; border-radius: 8px; margin: 16px 0; }
    </style>
</head>
<body>
    <h1>Installation Complete!</h1>
    <p>${APP_NAME} has been successfully installed.</p>
    <div class="highlight">
        <p><strong>What's next?</strong></p>
        <p>• Launch ${APP_NAME} from your Applications folder</p>
        <p>• Start creating beautiful mathematical formulas</p>
        <p>• Integrate seamlessly with HWP documents</p>
    </div>
    <p>Thank you for installing ${APP_NAME}!</p>
</body>
</html>
EOF

# Build the component package
echo -e "${BLUE}🔨 Building component package...${NC}"
pkgbuild --root pkg_build/Applications \
         --identifier "${IDENTIFIER}" \
         --version "${VERSION}" \
         --install-location "/Applications" \
         "${PKG_NAME}.pkg"

# Build the final installer package
echo -e "${BLUE}📦 Creating installer package...${NC}"
productbuild --distribution pkg_build/Distribution \
             --package-path . \
             --resources pkg_build \
             "${PKG_NAME}-Final.pkg"

# Clean up build directory
echo -e "${YELLOW}🧹 Cleaning up build files...${NC}"
rm -rf pkg_build/
rm -f "${PKG_NAME}.pkg"

# Rename final package
mv "${PKG_NAME}-Final.pkg" "${PKG_NAME}.pkg"

# Verify the package was created
if [[ -f "${PKG_NAME}.pkg" ]]; then
    PKG_SIZE=$(du -sh "${PKG_NAME}.pkg" | cut -f1)
    echo -e "${GREEN}✅ PKG installer created successfully!${NC}"
    echo -e "${GREEN}📦 Package file: ${PKG_NAME}.pkg${NC}"
    echo -e "${GREEN}📏 Package size: ${PKG_SIZE}${NC}"
    
    echo -e "${BLUE}💡 Installation Instructions:${NC}"
    echo -e "   • Double-click ${PKG_NAME}.pkg to install"
    echo -e "   • Follow the installer prompts"
    echo -e "   • ${APP_NAME} will be installed to /Applications/"
else
    echo -e "${RED}❌ PKG creation failed!${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 PKG creation completed!${NC}"
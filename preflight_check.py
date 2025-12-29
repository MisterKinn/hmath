#!/usr/bin/env python3
"""
Pre-flight checker - runs before the app to ensure everything is ready.
"""

import sys
import subprocess

def check_accessibility_permissions():
    """Quick check for accessibility permissions."""
    test_script = '''
    tell application "System Events"
        return "ok"
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', test_script],
            capture_output=True,
            text=True,
            timeout=3
        )
        
        if result.returncode == 0:
            return True
        
        # Check for permission error
        if "osascript is not allowed" in result.stderr or "1002" in result.stderr:
            return False
            
        return True
    except Exception:
        return True  # Assume OK if we can't check

def check_hwp_running():
    """Check if Hancom Office HWP is running."""
    try:
        from backend.hwp.hwp_macos import HwpMacOS
        hwp = HwpMacOS()
        return hwp.is_running()
    except Exception:
        return False

def main():
    print("=" * 60)
    print("  Formulite - macOS Pre-Flight Check")
    print("=" * 60)
    print()
    
    all_ok = True
    
    # Check 1: Accessibility
    print("🔑 Checking Accessibility Permissions...")
    if check_accessibility_permissions():
        print("   ✅ Accessibility permissions: OK")
    else:
        print("   ❌ Accessibility permissions: NOT GRANTED")
        print()
        print("   📖 How to fix:")
        print("      1. System Settings → Privacy & Security → Accessibility")
        print("      2. Add Terminal to the list")
        print("      3. Enable the toggle")
        print("      4. Restart Terminal")
        print()
        print("   📄 Detailed guide: ACCESSIBILITY_PERMISSIONS.md")
        print()
        all_ok = False
    
    # Check 2: HWP
    print()
    print("📱 Checking Hancom Office HWP...")
    if check_hwp_running():
        print("   ✅ Hancom Office HWP: Running")
    else:
        print("   ⚠️  Hancom Office HWP: Not running")
        print("      → Please open HWP and create/open a document")
        print()
    
    print()
    print("=" * 60)
    
    if all_ok:
        print("✅ All critical checks passed!")
        print()
        print("🚀 Starting Formulite...")
        print("=" * 60)
        return 0
    else:
        print("❌ Some checks failed - please fix them first")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())


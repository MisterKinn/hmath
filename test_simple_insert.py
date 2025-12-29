#!/usr/bin/env python3
"""
Simple test: Open editor, type formula, and try to insert it.
"""

import subprocess
import time

def run_applescript(script):
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("="*70)
    print("Simple Formula Insertion Test")
    print("="*70)
    
    app_name = "Hancom Office HWP"
    formula = "a over b"
    
    # Complete script: Open, type, and close
    script = f'''
    tell application "{app_name}"
        activate
    end tell
    
    delay 0.5
    
    tell application "System Events"
        tell process "{app_name}"
            -- Open formula editor
            click menu item "수식..." of menu "입력 " of menu bar 1
            delay 1.5
            
            -- Type formula in text field
            set formulaWindow to window "수식 편집기"
            repeat with elem in (UI elements of formulaWindow)
                if role of elem is "AXTextField" then
                    set focused of elem to true
                    delay 0.3
                    keystroke "{formula}"
                    delay 0.5
                    exit repeat
                end if
            end repeat
            
            -- Try Escape to close and insert
            key code 53
            delay 0.3
            
            return "DONE"
        end tell
    end tell
    '''
    
    print(f"Formula: {formula}")
    print("Opening editor, typing, and closing...")
    
    stdout, stderr, code = run_applescript(script)
    
    if code == 0:
        print(f"✅ Script executed: {stdout.strip()}")
        print()
        print("Check your document!")
        print("Did the formula appear? (a/b as a fraction)")
    else:
        print(f"❌ Error: {stderr}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())


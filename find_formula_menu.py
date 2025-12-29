#!/usr/bin/env python3
"""
Script to find the correct menu path for opening 수식 편집기 (Formula Editor).
"""

import subprocess

def test_menu_paths():
    app_name = "Hancom Office HWP"
    
    print("=" * 70)
    print("Finding 수식 편집기 (Formula Editor) Menu Path")
    print("=" * 70)
    print()
    print("Make sure Hancom Office HWP is open with a document!")
    print()
    input("Press Enter to continue...")
    print()
    
    menu_paths = [
        ("삽입 → 수식", 'click menu item "수식" of menu "삽입" of menu bar 1'),
        ("삽입 → 수식 편집기", 'click menu item "수식 편집기" of menu "삽입" of menu bar 1'),
        ("Insert → Equation", 'click menu item "Equation" of menu "Insert" of menu bar 1'),
        ("Insert → Formula Editor", 'click menu item "Formula Editor" of menu "Insert" of menu bar 1'),
    ]
    
    for name, menu_script in menu_paths:
        print(f"Testing: {name}")
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        delay 0.3
        
        tell application "System Events"
            tell process "{app_name}"
                try
                    {menu_script}
                    return "SUCCESS"
                on error errMsg
                    return "FAILED: " & errMsg
                end try
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "SUCCESS" in result.stdout:
                print(f"  ✅ {name} - SUCCESS!")
                print(f"  → This menu path works!")
                print()
                input("Press Enter to continue testing other paths...")
                print()
            else:
                print(f"  ❌ {name} - {result.stdout.strip()}")
                print()
        except Exception as e:
            print(f"  ❌ Error: {e}")
            print()
    
    print("=" * 70)
    print("Testing keyboard shortcuts...")
    print("=" * 70)
    print()
    
    shortcuts = [
        ("Option+Command+E", 'keystroke "e" using {option down, command down}'),
        ("Command+E", 'keystroke "e" using command down'),
        ("Command+Shift+E", 'keystroke "e" using {shift down, command down}'),
    ]
    
    for name, shortcut in shortcuts:
        print(f"Testing: {name}")
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        delay 0.3
        
        tell application "System Events"
            tell process "{app_name}"
                {shortcut}
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                print(f"  ✅ {name} executed (check if formula editor opened)")
                print()
                input("Press Enter to continue...")
                print()
            else:
                print(f"  ❌ {name} failed")
                print()
        except Exception as e:
            print(f"  ❌ {name} error: {e}")
            print()
    
    print("=" * 70)
    print("✨ Testing complete!")
    print("=" * 70)
    print()
    print("Please note which method successfully opened the formula editor.")
    print("This information will help improve the automation.")

if __name__ == "__main__":
    test_menu_paths()



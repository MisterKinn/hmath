#!/usr/bin/env python3
"""
Test script to find the correct way to open and use the 수식 편집기 (Formula Editor).
"""

import subprocess
import time

def test_formula_editor():
    print("=" * 70)
    print("Testing 한글 수식 편집기 (Formula Editor) Access")
    print("=" * 70)
    print()
    print("Make sure Hancom Office HWP is open with a document!")
    print()
    input("Press Enter when ready...")
    print()
    
    app_name = "Hancom Office HWP"
    
    # Test 1: Try menu path
    print("Test 1: Opening via menu (삽입 > 수식)")
    script1 = f'''
    tell application "{app_name}"
        activate
    end tell
    
    delay 0.5
    
    tell application "System Events"
        tell process "{app_name}"
            -- Try to access menu
            try
                click menu item "수식" of menu "삽입" of menu bar 1
            on error
                -- Try English menu
                try
                    click menu item "Equation" of menu "Insert" of menu bar 1
                on error e
                    return "Menu not found: " & e
                end try
            end try
        end tell
    end tell
    
    return "Menu clicked"
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script1],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Result: {result.stdout.strip()}")
        if result.returncode != 0:
            print(f"Error: {result.stderr.strip()}")
        else:
            print("✅ Menu method worked!")
            time.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print()
    
    # Test 2: Try keyboard shortcuts
    shortcuts = [
        ("⌘+Option+E", 'keystroke "e" using {option down, command down}'),
        ("⌘+E", 'keystroke "e" using command down'),
        ("⌘+Shift+E", 'keystroke "e" using {shift down, command down}'),
        ("⌘+Control+E", 'keystroke "e" using {control down, command down}'),
    ]
    
    for name, shortcut in shortcuts:
        print(f"Test: {name}")
        script2 = f'''
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
                ['osascript', '-e', script2],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                print(f"✅ {name} executed (check if editor opened)")
                time.sleep(2)
            else:
                print(f"❌ {name} failed: {result.stderr.strip()}")
        except Exception as e:
            print(f"❌ {name} error: {e}")
        print()
    
    print("=" * 70)
    print("Next steps:")
    print("1. Check which method opened the formula editor")
    print("2. Look at the formula editor's input bar syntax")
    print("3. Try typing a simple formula like 'a over b'")
    print("4. Note the keyboard shortcut or menu path that worked")
    print("=" * 70)

if __name__ == "__main__":
    test_formula_editor()



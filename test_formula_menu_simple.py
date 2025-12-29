#!/usr/bin/env python3
"""
Simple test to see if we can open the formula editor and what actually happens.
"""

import subprocess
import time

app_name = "Hancom Office HWP"

print("=" * 70)
print("Simple Formula Editor Test")
print("=" * 70)
print()
print("Make sure Hancom Office HWP is open with a document!")
print()
input("Press Enter to continue...")
print()

# Test 1: Try the menu click
print("Test 1: Clicking '삽입 → 수식' menu...")
script1 = f'''
tell application "{app_name}"
    activate
end tell

delay 0.5

tell application "System Events"
    tell process "{app_name}"
        try
            click menu item "수식" of menu "삽입" of menu bar 1
            return "Menu clicked successfully"
        on error err
            return "Error: " & err
        end try
    end tell
end tell
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
        print(f"Error output: {result.stderr.strip()}")
    print()
    print("Did the formula editor window open? (y/n)")
    response = input().strip().lower()
    if response == 'y':
        print("✅ Success! Menu path works.")
    else:
        print("❌ Menu path doesn't work. Trying alternatives...")
        print()
        
        # Try listing what's actually in the menu
        print("Listing actual menu items in '삽입' menu:")
        script2 = f'''
        tell application "{app_name}"
            activate
        end tell
        
        delay 0.3
        
        tell application "System Events"
            tell process "{app_name}"
                try
                    set items to name of every menu item of menu "삽입" of menu bar 1
                    return items
                on error
                    try
                        set items to name of every menu item of menu "Insert" of menu bar 1
                        return items
                    on error err
                        return "Error: " & err
                    end try
                end try
            end tell
        end tell
        '''
        
        result2 = subprocess.run(
            ['osascript', '-e', script2],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(result2.stdout.strip())
        print()
        print("Please find '수식' or 'Equation' in the list above and tell me the exact name.")
        
except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 70)
print("Test complete!")
print("=" * 70)



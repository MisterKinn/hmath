#!/usr/bin/env python3
"""
Debug script to find the actual menu structure and correct way to open 수식 편집기.
"""

import subprocess

def list_menu_items():
    app_name = "Hancom Office HWP"
    
    print("=" * 70)
    print("Debugging 수식 편집기 Menu")
    print("=" * 70)
    print()
    print("This will list all menu items to find the correct path.")
    print("Make sure Hancom Office HWP is open!")
    print()
    input("Press Enter to continue...")
    print()
    
    # List all menu bar items
    print("1. Listing all menu bar items:")
    script1 = f'''
    tell application "{app_name}"
        activate
    end tell
    
    delay 0.3
    
    tell application "System Events"
        tell process "{app_name}"
            set menuBarItems to name of every menu of menu bar 1
            return menuBarItems
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
        print(result.stdout)
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
    
    # List items in "삽입" menu
    print("2. Listing items in '삽입' (Insert) menu:")
    script2 = f'''
    tell application "{app_name}"
        activate
    end tell
    
    delay 0.3
    
    tell application "System Events"
        tell process "{app_name}"
            try
                set insertMenu to menu "삽입" of menu bar 1
                set menuItems to name of every menu item of insertMenu
                return menuItems
            on error
                try
                    set insertMenu to menu "Insert" of menu bar 1
                    set menuItems to name of every menu item of insertMenu
                    return menuItems
                on error err
                    return "Error: " & err
                end try
            end try
        end tell
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script2],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(result.stdout)
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
    
    # Try to find any menu item containing "수식"
    print("3. Searching for menu items containing '수식' or 'Equation':")
    script3 = f'''
    tell application "{app_name}"
        activate
    end tell
    
    delay 0.3
    
    tell application "System Events"
        tell process "{app_name}"
            set foundItems to {{}}
            try
                repeat with m in menus of menu bar 1
                    try
                        set menuName to name of m
                        repeat with item in menu items of m
                            try
                                set itemName to name of item
                                if itemName contains "수식" or itemName contains "Equation" or itemName contains "formula" or itemName contains "수식 편집기" then
                                    set end of foundItems to menuName & " → " & itemName
                                end if
                            end try
                        end repeat
                    end try
                end repeat
            end try
            return foundItems
        end tell
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script3],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout.strip():
            print(result.stdout)
        else:
            print("No menu items found containing '수식' or 'Equation'")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
    
    print("=" * 70)
    print("Next steps:")
    print("1. Check the menu items listed above")
    print("2. Find the correct menu path for 수식 편집기")
    print("3. Update the code with the correct path")
    print("=" * 70)

if __name__ == "__main__":
    list_menu_items()



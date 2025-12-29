#!/usr/bin/env python3
"""
Advanced menu structure inspection for Hancom Office HWP.
"""

import subprocess
import sys

def run_applescript(script):
    """Run AppleScript and return output."""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("=" * 70)
    print("한글 앱 UI 요소 상세 분석")
    print("=" * 70)
    print()
    
    app_name = "Hancom Office HWP"
    
    # Method 1: Get entire UI element structure
    print("1. 전체 UI 구조 확인...")
    print("-" * 70)
    
    script = f'''
    tell application "{app_name}"
        activate
    end tell
    
    delay 0.5
    
    tell application "System Events"
        tell process "{app_name}"
            try
                -- Get menu bar
                set menuBarExists to exists menu bar 1
                return "Menu bar exists: " & menuBarExists
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(f"결과: {stdout.strip()}")
    print()
    
    # Method 2: Try to get menu titles with different approach
    print("2. 메뉴 타이틀 가져오기 (다른 방법)...")
    print("-" * 70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                set menuCount to count of menus of menu bar 1
                set menuInfo to "Total menus: " & menuCount & return
                
                repeat with i from 1 to menuCount
                    try
                        set menuTitle to name of menu i of menu bar 1
                        set menuInfo to menuInfo & "Menu " & i & ": " & menuTitle & return
                    on error
                        set menuInfo to menuInfo & "Menu " & i & ": (unable to read)" & return
                    end try
                end repeat
                
                return menuInfo
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(stdout.strip())
    print()
    
    # Method 3: Try UI elements approach
    print("3. UI 요소로 메뉴 찾기...")
    print("-" * 70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                -- Get all UI elements of menu bar
                set allElements to every UI element of menu bar 1
                set elementInfo to ""
                
                repeat with elem in allElements
                    try
                        set elemRole to role of elem
                        set elemTitle to title of elem
                        set elemInfo to elemInfo & elemRole & ": " & elemTitle & return
                    on error
                        set elemInfo to elemInfo & "Unable to read element" & return
                    end try
                end repeat
                
                return elemInfo
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(stdout.strip())
    print()
    
    # Method 4: Try to click based on position
    print("4. 위치 기반으로 메뉴 항목 찾기...")
    print("-" * 70)
    
    # Common menu positions (from image: 도구 is visible)
    menu_positions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    for pos in menu_positions:
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                try
                    set menuTitle to name of menu {pos} of menu bar 1
                    return "Menu {pos}: " & menuTitle
                on error
                    return "Menu {pos}: (none)"
                end try
            end tell
        end tell
        '''
        
        stdout, stderr, code = run_applescript(script)
        result = stdout.strip()
        if "(none)" not in result:
            print(f"  {result}")
    
    print()
    
    # Method 5: Look for specific UI element with "입력" or similar
    print("5. '입력' 텍스트가 있는 UI 요소 찾기...")
    print("-" * 70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                set foundElements to {{}}
                
                -- Check each menu
                repeat with i from 1 to 15
                    try
                        set menuObj to menu i of menu bar 1
                        set menuName to name of menuObj
                        
                        if menuName contains "입력" or menuName contains "삽입" or menuName contains "Input" or menuName contains "Insert" then
                            set end of foundElements to "Found at position " & i & ": " & menuName
                        end if
                    end try
                end repeat
                
                if (count of foundElements) > 0 then
                    return foundElements
                else
                    return {{"Not found"}}
                end if
            on error errMsg
                return {{"ERROR: " & errMsg}}
            end try
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(stdout.strip())
    print()
    
    print("=" * 70)
    print("분석 완료")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


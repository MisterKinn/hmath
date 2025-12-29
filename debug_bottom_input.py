#!/usr/bin/env python3
"""
Find and write to the bottom black input area (the actual formula input)
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
    print("하단 검은색 입력 영역 찾기 (실제 수식 입력)")
    print("="*70)
    print()
    
    app_name = "Hancom Office HWP"
    
    # Open editor
    print("수식 편집기 열기...")
    script = f'''
    tell application "{app_name}"
        activate
    end tell
    delay 0.5
    tell application "System Events"
        tell process "{app_name}"
            click menu item "수식..." of menu "입력 " of menu bar 1
        end tell
    end tell
    '''
    run_applescript(script)
    time.sleep(2)
    print("✅ 열림")
    print()
    
    # Find scroll area and its children
    print("스크롤 영역 (AXScrollArea) 내부 탐색...")
    print("-"*70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            set formulaWindow to window "수식 편집기"
            set scrollInfo to ""
            
            -- Find scroll area (Element 15)
            repeat with elem in (UI elements of formulaWindow)
                if role of elem is "AXScrollArea" then
                    set scrollInfo to scrollInfo & "Found AXScrollArea!" & return
                    set scrollInfo to scrollInfo & "Children count: " & (count of UI elements of elem) & return & return
                    
                    -- List all children
                    repeat with i from 1 to (count of UI elements of elem)
                        set child to UI element i of elem
                        set childRole to role of child
                        set childDesc to description of child
                        
                        set scrollInfo to scrollInfo & "Child " & i & ":" & return
                        set scrollInfo to scrollInfo & "  Role: " & childRole & return
                        set scrollInfo to scrollInfo & "  Desc: " & childDesc & return
                        
                        try
                            set childValue to value of child
                            set scrollInfo to scrollInfo & "  Value: " & childValue & return
                        end try
                        
                        set scrollInfo to scrollInfo & return
                    end repeat
                    
                    exit repeat
                end if
            end repeat
            
            return scrollInfo
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(stdout.strip())
    print()
    
    # Try to type in the scroll area
    print("="*70)
    print("스크롤 영역에 직접 입력 시도")
    print("="*70)
    print()
    
    test_text = "Hello from bottom input"
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            set formulaWindow to window "수식 편집기"
            
            -- Find and focus on scroll area
            repeat with elem in (UI elements of formulaWindow)
                if role of elem is "AXScrollArea" then
                    set focused of elem to true
                    delay 0.3
                    
                    -- Type text
                    keystroke "{test_text}"
                    delay 0.5
                    
                    return "SUCCESS: Typed in scroll area"
                end if
            end repeat
            
            return "ERROR: Scroll area not found"
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(f"결과: {stdout.strip()}")
    print()
    
    print("="*70)
    print("수식 편집기 창의 하단 검은색 영역을 확인하세요!")
    print(f"'{test_text}'가 입력되었나요?")
    print("="*70)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())


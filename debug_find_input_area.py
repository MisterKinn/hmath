#!/usr/bin/env python3
"""
Find the correct input area in formula editor
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
    print("수식 편집기의 모든 입력 가능한 요소 찾기")
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
    
    # Find all editable elements
    print("모든 편집 가능한 UI 요소 찾기...")
    print("-"*70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            set formulaWindow to window "수식 편집기"
            set editableElements to ""
            
            repeat with i from 1 to (count of UI elements of formulaWindow)
                set elem to UI element i of formulaWindow
                set elemRole to role of elem
                set elemDesc to description of elem
                
                -- Check if element is editable/focusable
                if elemRole contains "Text" or elemRole contains "Field" or elemRole contains "Area" then
                    set editableElements to editableElements & "Element " & i & ":" & return
                    set editableElements to editableElements & "  Role: " & elemRole & return
                    set editableElements to editableElements & "  Desc: " & elemDesc & return
                    
                    try
                        set elemValue to value of elem
                        set editableElements to editableElements & "  Value: " & elemValue & return
                    end try
                    
                    try
                        set canFocus to focused of elem
                        set editableElements to editableElements & "  Can focus: true" & return
                    end try
                    
                    set editableElements to editableElements & return
                end if
            end repeat
            
            return editableElements
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(stdout.strip())
    print()
    
    # Try to type in different elements
    print("="*70)
    print("다른 방법: 단축키로 입력 영역 접근")
    print("="*70)
    print()
    
    test_text = "Hello World"
    
    # Method 1: Just keystroke (current focus)
    print("Method 1: 현재 포커스된 곳에 바로 타이핑")
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            keystroke "{test_text}"
            delay 0.5
            return "Typed directly"
        end tell
    end tell
    '''
    stdout, stderr, code = run_applescript(script)
    print(f"  결과: {stdout.strip()}")
    time.sleep(1)
    
    # Method 2: Tab to input area
    print()
    print("Method 2: Tab 키로 입력 영역 이동")
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            key code 48  -- Tab
            delay 0.3
            keystroke "Test with Tab"
            delay 0.5
            return "Typed after Tab"
        end tell
    end tell
    '''
    stdout, stderr, code = run_applescript(script)
    print(f"  결과: {stdout.strip()}")
    
    print()
    print("="*70)
    print("수식 편집기 창을 확인하세요!")
    print("어디에 텍스트가 입력되었나요?")
    print("="*70)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())


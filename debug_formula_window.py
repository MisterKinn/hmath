#!/usr/bin/env python3
"""
Inspect formula editor window UI elements.
"""

import subprocess
import time

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
    print("수식 편집기 UI 요소 분석")
    print("=" * 70)
    print()
    
    app_name = "Hancom Office HWP"
    
    # Step 1: Open formula editor
    print("Step 1: 수식 편집기 열기...")
    script = f'''
    tell application "{app_name}"
        activate
    end tell
    delay 0.3
    tell application "System Events"
        tell process "{app_name}"
            click menu item "수식..." of menu "입력 " of menu bar 1
        end tell
    end tell
    '''
    run_applescript(script)
    print("✅ 수식 편집기 열림")
    time.sleep(1.5)
    print()
    
    # Step 2: Get window info
    print("Step 2: 수식 편집기 창 정보...")
    print("-" * 70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                set formulaWindow to window "수식 편집기"
                set windowInfo to "Window found: " & (exists formulaWindow) & return
                
                -- Get all UI elements
                set elementCount to count of UI elements of formulaWindow
                set windowInfo to windowInfo & "Total UI elements: " & elementCount & return
                
                return windowInfo
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(stdout.strip())
    print()
    
    # Step 3: Get all buttons
    print("Step 3: 버튼 찾기...")
    print("-" * 70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                set formulaWindow to window "수식 편집기"
                set buttonList to {{}}
                
                repeat with elem in (UI elements of formulaWindow)
                    try
                        if role of elem is "AXButton" then
                            set buttonTitle to title of elem
                            if buttonTitle is not "" then
                                set end of buttonList to buttonTitle
                            end if
                        end if
                    end try
                end repeat
                
                if (count of buttonList) > 0 then
                    return buttonList
                else
                    return {{"No buttons with titles found"}}
                end if
            on error errMsg
                return {{"ERROR: " & errMsg}}
            end try
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(f"버튼들: {stdout.strip()}")
    print()
    
    # Step 4: Get all text fields
    print("Step 4: 텍스트 입력 필드 찾기...")
    print("-" * 70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                set formulaWindow to window "수식 편집기"
                set textFieldInfo to ""
                
                repeat with elem in (UI elements of formulaWindow)
                    try
                        set elemRole to role of elem
                        if elemRole contains "Text" or elemRole contains "Field" then
                            set textFieldInfo to textFieldInfo & elemRole & return
                        end if
                    end try
                end repeat
                
                if textFieldInfo is "" then
                    return "No text fields found"
                else
                    return textFieldInfo
                end if
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(stdout.strip())
    print()
    
    # Step 5: Try to click insert button
    print("Step 5: '넣기' 또는 '삽입' 버튼 클릭 시도...")
    print("-" * 70)
    
    button_names = ["넣기", "삽입", "Insert", "OK", "확인"]
    
    for button_name in button_names:
        print(f"  시도: '{button_name}' 버튼")
        
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                try
                    set formulaWindow to window "수식 편집기"
                    click button "{button_name}" of formulaWindow
                    return "SUCCESS"
                on error errMsg
                    return "FAILED"
                end try
            end tell
        end tell
        '''
        
        stdout, stderr, code = run_applescript(script)
        
        if "SUCCESS" in stdout:
            print(f"    ✅ '{button_name}' 버튼 발견 및 클릭!")
            break
        else:
            print(f"    ❌ 버튼 없음")
    
    print()
    print("=" * 70)
    print("분석 완료")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())


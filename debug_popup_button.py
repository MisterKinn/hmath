#!/usr/bin/env python3
"""
Test clicking the "넣기" button in the popup dialog
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
    print("팝업 '넣기' 버튼 클릭 테스트")
    print("="*70)
    print()
    
    app_name = "Hancom Office HWP"
    
    # Open editor and type
    print("수식 편집기 열고 텍스트 입력...")
    script = f'''
    tell application "{app_name}"
        activate
    end tell
    delay 0.5
    tell application "System Events"
        tell process "{app_name}"
            -- Open editor
            click menu item "수식..." of menu "입력 " of menu bar 1
            delay 1.5
            
            -- Type in bottom area
            set formulaWindow to window "수식 편집기"
            repeat with elem in (UI elements of formulaWindow)
                if role of elem is "AXScrollArea" then
                    set focused of elem to true
                    delay 0.3
                    keystroke "test formula"
                    delay 0.5
                    exit repeat
                end if
            end repeat
        end tell
    end tell
    '''
    run_applescript(script)
    print("✅ 텍스트 입력 완료")
    print()
    
    # Try to close with Escape to trigger popup
    print("Escape 키를 눌러 팝업 트리거...")
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            key code 53  -- Escape
            delay 1.0
        end tell
    end tell
    '''
    run_applescript(script)
    print("✅ Escape 눌림, 팝업 확인 중...")
    time.sleep(1)
    print()
    
    # Find and click "넣기" button
    print("'넣기' 버튼 찾기 및 클릭...")
    print("-"*70)
    
    # Try different approaches
    approaches = [
        ("Method 1: sheet의 default button", '''
            tell application "System Events"
                tell process "{app_name}"
                    try
                        click button "넣기" of sheet 1 of window "수식 편집기"
                        return "SUCCESS: Clicked 넣기 in sheet"
                    on error errMsg
                        return "FAILED: " & errMsg
                    end try
                end tell
            end tell
        '''),
        ("Method 2: window의 button", '''
            tell application "System Events"
                tell process "{app_name}"
                    try
                        click button "넣기" of window 1
                        return "SUCCESS: Clicked 넣기 in window"
                    on error errMsg
                        return "FAILED: " & errMsg
                    end try
                end tell
            end tell
        '''),
        ("Method 3: Return key (default button)", '''
            tell application "System Events"
                tell process "{app_name}"
                    keystroke return
                    return "SUCCESS: Pressed Return"
                end tell
            end tell
        '''),
    ]
    
    for method_name, script_template in approaches:
        print(f"시도: {method_name}")
        script = script_template.format(app_name=app_name)
        stdout, stderr, code = run_applescript(script)
        print(f"  결과: {stdout.strip()}")
        
        if "SUCCESS" in stdout:
            print(f"  ✅ 성공!")
            break
        time.sleep(0.5)
    
    print()
    print("="*70)
    print("문서를 확인하세요!")
    print("수식이 삽입되었나요?")
    print("="*70)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())


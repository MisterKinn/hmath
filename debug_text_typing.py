#!/usr/bin/env python3
"""
Debug: Check if text is actually being typed
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
    print("텍스트 입력 디버깅")
    print("="*70)
    print()
    
    app_name = "Hancom Office HWP"
    test_text = "Hello World 123"
    
    print(f"입력할 텍스트: '{test_text}'")
    print()
    
    # Complete script
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
            
            -- Type in text field
            set formulaWindow to window "수식 편집기"
            
            set textTyped to false
            repeat with elem in (UI elements of formulaWindow)
                if role of elem is "AXTextField" then
                    -- Focus on text field
                    set focused of elem to true
                    delay 0.5
                    
                    -- Clear any existing content first
                    keystroke "a" using command down
                    delay 0.1
                    key code 51  -- Delete
                    delay 0.3
                    
                    -- Type the text
                    keystroke "{test_text}"
                    delay 1.0
                    
                    -- Check what's in the field
                    set fieldValue to value of elem
                    set textTyped to true
                    
                    return "Typed: {test_text}, Field value: " & fieldValue
                end if
            end repeat
            
            if not textTyped then
                return "ERROR: No text field found"
            end if
        end tell
    end tell
    '''
    
    print("실행 중...")
    stdout, stderr, code = run_applescript(script)
    
    if code == 0:
        print(f"✅ 결과: {stdout.strip()}")
        print()
        print("수식 편집기 창을 직접 확인하세요!")
        print(f"텍스트 필드에 '{test_text}'가 보이나요?")
    else:
        print(f"❌ 에러: {stderr}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())


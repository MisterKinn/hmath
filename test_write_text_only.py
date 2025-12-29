#!/usr/bin/env python3
"""
Test: Just write text in formula editor window
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
    print("수식 편집기에 텍스트 작성 테스트")
    print("="*70)
    print()
    
    app_name = "Hancom Office HWP"
    formula_text = "a over b"
    
    print(f"작성할 텍스트: {formula_text}")
    print()
    print("Step 1: 수식 편집기 열기...")
    
    # Open editor
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
    
    stdout, stderr, code = run_applescript(script)
    if code == 0:
        print("✅ 수식 편집기 열림")
    else:
        print(f"❌ 실패: {stderr}")
        return 1
    
    time.sleep(1.5)
    
    print()
    print("Step 2: 텍스트 필드에 포커스하고 타이핑...")
    print(f"입력할 내용: '{formula_text}'")
    
    # Type in text field
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            set formulaWindow to window "수식 편집기"
            
            -- Find text field
            set textFieldFound to false
            repeat with elem in (UI elements of formulaWindow)
                if role of elem is "AXTextField" then
                    set textFieldFound to true
                    
                    -- Focus on it
                    set focused of elem to true
                    delay 0.3
                    
                    -- Type the formula
                    keystroke "{formula_text}"
                    delay 0.5
                    
                    return "SUCCESS: Typed '" & "{formula_text}" & "' in text field"
                end if
            end repeat
            
            if not textFieldFound then
                return "ERROR: No text field found"
            end if
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(f"결과: {stdout.strip()}")
    
    if code != 0:
        print(f"❌ 에러: {stderr}")
        return 1
    
    print()
    print("="*70)
    print("✅ 완료!")
    print("="*70)
    print()
    print("수식 편집기 창을 확인하세요.")
    print(f"텍스트 필드에 '{formula_text}'가 입력되어 있어야 합니다.")
    print()
    print("⚠️  창은 열린 상태로 유지됩니다 (Escape를 누르지 않음)")
    print("직접 확인한 후 수동으로 닫거나 Escape를 누르세요.")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())


#!/usr/bin/env python3
"""
Test: Type plain text (not formula syntax) in formula editor window
"""

import subprocess
import time

def run_applescript(script):
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def test_text(text):
    """Test typing plain text in formula editor"""
    print(f"\n{'='*70}")
    print(f"입력할 텍스트: '{text}'")
    print('='*70)
    
    app_name = "Hancom Office HWP"
    
    # Complete script: Open editor and type text
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
            
            -- Type text in text field
            set formulaWindow to window "수식 편집기"
            repeat with elem in (UI elements of formulaWindow)
                if role of elem is "AXTextField" then
                    set focused of elem to true
                    delay 0.3
                    keystroke "{text}"
                    delay 0.5
                    exit repeat
                end if
            end repeat
            
            return "Typed: {text}"
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    
    if code == 0:
        print(f"✅ {stdout.strip()}")
        print()
        print("수식 편집기 창을 확인하세요!")
        print(f"텍스트 필드에 '{text}'가 입력되어 있어야 합니다.")
        print()
        input("확인했으면 Enter를 눌러 창을 닫고 다음 테스트로...")
        
        # Close window with Escape
        close_script = f'''
        tell application "System Events"
            tell process "{app_name}"
                key code 53
            end tell
        end tell
        '''
        run_applescript(close_script)
        time.sleep(0.5)
        
    else:
        print(f"❌ 실패: {stderr}")

def main():
    print("="*70)
    print("수식 편집기에 일반 텍스트 입력 테스트")
    print("="*70)
    print()
    print("여러 종류의 텍스트를 입력해봅니다:")
    print("- 일반 텍스트")
    print("- 수식 문법")
    print("- 한글 텍스트")
    print()
    
    # Test different types of text
    test_cases = [
        "Hello World",           # Plain English text
        "a over b",              # Formula syntax
        "x^2 + y^2",            # Formula with superscript
        "안녕하세요",              # Korean text
        "Test 123",              # Mixed text and numbers
        "alpha + beta",          # Greek letter names
    ]
    
    for text in test_cases:
        test_text(text)
    
    print("\n" + "="*70)
    print("✅ 모든 테스트 완료!")
    print("="*70)

if __name__ == "__main__":
    import sys
    sys.exit(main())


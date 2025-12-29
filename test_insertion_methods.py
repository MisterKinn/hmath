#!/usr/bin/env python3
"""
Test different methods to insert formula from editor.
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

def test_method(method_name, formula, close_method):
    """Test a specific method of inserting formula."""
    print(f"\n{'='*70}")
    print(f"Testing: {method_name}")
    print(f"Formula: {formula}")
    print(f"Close method: {close_method}")
    print('='*70)
    
    app_name = "Hancom Office HWP"
    
    # Step 1: Open formula editor
    print("1. Opening formula editor...")
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
    time.sleep(1.5)
    print("   ✅ Opened")
    
    # Step 2: Type formula
    print("2. Typing formula...")
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            set formulaWindow to window "수식 편집기"
            repeat with elem in (UI elements of formulaWindow)
                if role of elem is "AXTextField" then
                    set focused of elem to true
                    delay 0.2
                    keystroke "{formula}"
                    delay 0.3
                    exit repeat
                end if
            end repeat
        end tell
    end tell
    '''
    stdout, stderr, code = run_applescript(script)
    print(f"   ✅ Typed: {formula}")
    
    # Step 3: Close and insert
    print(f"3. Closing with: {close_method}")
    
    if close_method == "Escape":
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                key code 53  -- Escape
            end tell
        end tell
        '''
    elif close_method == "Command+W":
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                keystroke "w" using command down
            end tell
        end tell
        '''
    elif close_method == "Command+Return":
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                keystroke return using command down
            end tell
        end tell
        '''
    elif close_method == "Click Close Button":
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                set formulaWindow to window "수식 편집기"
                click button 1 of formulaWindow  -- Close button
            end tell
        end tell
        '''
    
    stdout, stderr, code = run_applescript(script)
    time.sleep(0.5)
    print(f"   ✅ Executed: {close_method}")
    
    print("\n   📝 Check your document to see if the formula was inserted!")
    input("   Press Enter to continue to next test...")

def main():
    print("=" * 70)
    print("수식 삽입 방법 테스트")
    print("=" * 70)
    print()
    print("여러 가지 방법으로 수식을 삽입해봅니다.")
    print("각 테스트 후 문서를 확인하고 Enter를 눌러주세요.")
    print()
    input("Press Enter to start...")
    
    # Test different methods
    methods = [
        ("Method 1: Escape key", "a over b", "Escape"),
        ("Method 2: Command+W", "x^2", "Command+W"),
        ("Method 3: Command+Return", "int x dx", "Command+Return"),
        ("Method 4: Click Close Button", "sum from 1 to n", "Click Close Button"),
    ]
    
    for method_name, formula, close_method in methods:
        test_method(method_name, formula, close_method)
    
    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)
    print("\n어떤 방법이 작동했는지 알려주세요!")

if __name__ == "__main__":
    import sys
    sys.exit(main())


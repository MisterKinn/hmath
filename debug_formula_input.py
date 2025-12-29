#!/usr/bin/env python3
"""
Debug script to test formula editor input step by step.
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
    print("수식 편집기 입력 디버그")
    print("=" * 70)
    print()
    
    app_name = "Hancom Office HWP"
    
    # Step 1: Open formula editor
    print("Step 1: 수식 편집기 열기...")
    print("-" * 70)
    
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
    
    return "Formula editor opened"
    '''
    
    stdout, stderr, code = run_applescript(script)
    if code == 0:
        print(f"✅ {stdout.strip()}")
    else:
        print(f"❌ 실패: {stderr}")
        return 1
    
    print("⏰ 수식 편집기가 열릴 때까지 대기 중...")
    time.sleep(1.5)  # Wait for window to open
    print()
    
    # Step 2: Check window
    print("Step 2: 수식 편집기 창 확인...")
    print("-" * 70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                set windowList to {{}}
                repeat with w in windows
                    set windowTitle to title of w
                    set end of windowList to windowTitle
                end repeat
                return windowList
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(f"열린 창들: {stdout.strip()}")
    print()
    
    # Step 3: Type formula using clipboard
    print("Step 3: 수식 입력 (clipboard 사용)...")
    print("-" * 70)
    
    formula = "a over b"
    print(f"입력할 수식: {formula}")
    
    # Copy to clipboard
    subprocess.run(['pbcopy'], input=formula.encode('utf-8'), check=True)
    print("✅ 클립보드에 복사됨")
    
    # Paste into formula editor
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            -- Paste formula
            keystroke "v" using command down
            delay 0.3
        end tell
    end tell
    
    return "Pasted"
    '''
    
    stdout, stderr, code = run_applescript(script)
    if code == 0:
        print(f"✅ {stdout.strip()}")
    else:
        print(f"❌ 실패: {stderr}")
    
    print("⏰ 수식이 입력될 때까지 대기 중...")
    time.sleep(0.5)
    print()
    
    # Step 4: Press Enter to insert
    print("Step 4: Enter 키를 눌러 수식 삽입...")
    print("-" * 70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            key code 36  -- Enter key
        end tell
    end tell
    
    return "Enter pressed"
    '''
    
    stdout, stderr, code = run_applescript(script)
    if code == 0:
        print(f"✅ {stdout.strip()}")
    else:
        print(f"❌ 실패: {stderr}")
    
    print()
    print("=" * 70)
    print("🎉 완료!")
    print("=" * 70)
    print()
    print("한글 문서에서 수식이 삽입되었는지 확인하세요.")
    print("만약 수식이 보이지 않으면:")
    print("1. 수식 편집기 창에 텍스트가 입력되었는지")
    print("2. Enter 키가 제대로 눌렸는지")
    print("3. 수식 편집기가 어떤 버튼을 눌러야 하는지 확인")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())


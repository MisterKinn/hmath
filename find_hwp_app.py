#!/usr/bin/env python3
"""
Find the actual running 한글 app process name.
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
    print("실행 중인 모든 앱 찾기")
    print("=" * 70)
    print()
    
    # Get all running apps
    script = '''
    tell application "System Events"
        set appList to name of every process whose background only is false
        return appList
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    
    if code != 0:
        print(f"❌ 에러: {stderr}")
        print()
        print("Accessibility 권한이 필요합니다:")
        print("System Settings → Privacy & Security → Accessibility → Terminal 추가")
        return 1
    
    print("실행 중인 앱들:")
    print("-" * 70)
    apps = stdout.strip().split(", ")
    
    hancom_apps = []
    
    for i, app in enumerate(apps, 1):
        print(f"{i}. {app}")
        
        # Look for anything related to Hancom, 한글, HWP, Hangul
        app_lower = app.lower()
        if any(keyword in app_lower for keyword in ['hancom', 'hwp', 'hangul', '한글']):
            hancom_apps.append(app)
            print(f"   ⭐ 한글 관련 앱일 수 있음!")
    
    print()
    print("=" * 70)
    
    if hancom_apps:
        print(f"✅ 발견된 한글 관련 앱: {hancom_apps}")
        print()
        print("이 앱 이름들을 사용해보세요:")
        for app in hancom_apps:
            print(f'  - "{app}"')
    else:
        print("❌ 한글 관련 앱을 찾을 수 없습니다.")
        print()
        print("다음을 확인해주세요:")
        print("1. 한글(Hancom Office HWP) 앱이 실행 중인가요?")
        print("2. 위 목록에서 한글 앱으로 보이는 것이 있나요?")
        print()
        print("한글 앱을 실행한 후 다시 시도해주세요.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


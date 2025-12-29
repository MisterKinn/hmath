#!/usr/bin/env python3
"""
Debug script to inspect the actual menu structure of 한글 app.
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
    print("한글 앱 메뉴 구조 디버깅")
    print("=" * 70)
    print()
    print("⚠️  한글(Hancom Office HWP) 앱이 실행 중이어야 합니다!")
    print()
    
    # Try different app names
    app_names = [
        "Hancom Office HWP",
        "Hancom Office Hangul",
        "한글",
        "Hangul",
        "HWP"
    ]
    
    detected_app = None
    
    print("1. 앱 이름 찾기...")
    print("-" * 70)
    
    for app_name in app_names:
        script = f'''
        tell application "System Events"
            return (name of processes) contains "{app_name}"
        end tell
        '''
        stdout, stderr, code = run_applescript(script)
        
        if code == 0 and stdout.strip().lower() == "true":
            print(f"✅ 발견: {app_name}")
            detected_app = app_name
            break
        else:
            print(f"❌ 없음: {app_name}")
    
    print()
    
    if not detected_app:
        print("❌ 한글 앱을 찾을 수 없습니다. 앱이 실행 중인지 확인해주세요.")
        return 1
    
    print(f"✅ 사용할 앱 이름: {detected_app}")
    print()
    
    # Get all menu bar items
    print("2. 메뉴 바 항목 확인...")
    print("-" * 70)
    
    script = f'''
    tell application "System Events"
        tell process "{detected_app}"
            set menuNames to {{}}
            try
                repeat with m in (menus of menu bar 1)
                    set end of menuNames to title of m
                end repeat
            end try
            return menuNames
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    
    if code == 0:
        print(f"메뉴 목록: {stdout.strip()}")
    else:
        print(f"❌ 에러: {stderr}")
        print()
        print("Accessibility 권한이 필요합니다:")
        print("System Settings → Privacy & Security → Accessibility → Terminal 추가")
        return 1
    
    print()
    
    # Check specific menus
    menu_names_to_check = ["입력", "삽입", "Input", "Insert"]
    
    print("3. '입력/삽입' 메뉴의 항목 확인...")
    print("-" * 70)
    
    for menu_name in menu_names_to_check:
        print(f"\n📋 메뉴: '{menu_name}'")
        
        script = f'''
        tell application "System Events"
            tell process "{detected_app}"
                try
                    set menuItems to {{}}
                    repeat with item in (menu items of menu "{menu_name}" of menu bar 1)
                        try
                            set itemTitle to title of item
                            if itemTitle is not "" then
                                set end of menuItems to itemTitle
                            end if
                        end try
                    end repeat
                    return menuItems
                on error errMsg
                    return "ERROR: " & errMsg
                end try
            end tell
        end tell
        '''
        
        stdout, stderr, code = run_applescript(script)
        
        if code == 0 and not stdout.startswith("ERROR:"):
            print(f"  항목들: {stdout.strip()}")
            
            # Check for 수식 specifically
            if "수식" in stdout:
                print(f"  ✅ '수식' 항목 발견!")
        else:
            print(f"  ❌ 메뉴 '{menu_name}' 없음 또는 에러: {stdout.strip()}")
    
    print()
    print("=" * 70)
    print("4. '수식' 메뉴 항목의 정확한 이름 찾기...")
    print("-" * 70)
    
    # Try to find the exact name of the equation menu item
    for menu_name in ["입력", "삽입", "Input", "Insert"]:
        script = f'''
        tell application "System Events"
            tell process "{detected_app}"
                try
                    set foundItems to {{}}
                    repeat with item in (menu items of menu "{menu_name}" of menu bar 1)
                        try
                            set itemTitle to title of item
                            if itemTitle contains "수식" or itemTitle contains "Equation" or itemTitle contains "Formula" then
                                set end of foundItems to itemTitle
                            end if
                        end try
                    end repeat
                    return foundItems
                on error
                    return {{}}
                end try
            end tell
        end tell
        '''
        
        stdout, stderr, code = run_applescript(script)
        
        if code == 0 and stdout.strip() != "{}" and stdout.strip() != "":
            print(f"\n✅ 메뉴 '{menu_name}'에서 발견:")
            print(f"   {stdout.strip()}")
    
    print()
    print("=" * 70)
    print("5. 메뉴 항목 클릭 테스트...")
    print("-" * 70)
    print()
    print("실제로 메뉴를 클릭해봅니다. 한글 앱을 확인하세요!")
    print()
    
    # Try to click the menu
    test_combinations = [
        ("입력", "수식..."),
        ("입력", "수식"),
        ("삽입", "수식..."),
        ("삽입", "수식"),
        ("Input", "Equation..."),
        ("Input", "Equation"),
        ("Insert", "Equation..."),
        ("Insert", "Equation"),
    ]
    
    for menu_name, item_name in test_combinations:
        print(f"시도: {menu_name} → {item_name}")
        
        script = f'''
        tell application "{detected_app}"
            activate
        end tell
        
        delay 0.3
        
        tell application "System Events"
            tell process "{detected_app}"
                try
                    click menu item "{item_name}" of menu "{menu_name}" of menu bar 1
                    return "SUCCESS"
                on error errMsg
                    return "FAILED: " & errMsg
                end try
            end tell
        end tell
        '''
        
        stdout, stderr, code = run_applescript(script)
        
        if "SUCCESS" in stdout:
            print(f"  ✅ 성공! 이 조합이 작동합니다: {menu_name} → {item_name}")
            print()
            print("=" * 70)
            print("🎉 성공! 위의 메뉴 경로를 사용하세요.")
            print("=" * 70)
            return 0
        else:
            print(f"  ❌ 실패: {stdout.strip()}")
        
        print()
    
    print("=" * 70)
    print("❌ 모든 시도 실패")
    print("=" * 70)
    print()
    print("다음을 확인해주세요:")
    print("1. 한글 앱이 실행 중인지")
    print("2. 문서가 열려 있는지")
    print("3. Accessibility 권한이 있는지")
    print("4. 위의 메뉴 구조를 보고 정확한 메뉴 이름을 확인")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())


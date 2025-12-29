#!/usr/bin/env python3
"""
Check menu items under '입력' menu.
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
    print("'입력' 메뉴의 하위 항목 확인")
    print("=" * 70)
    print()
    
    app_name = "Hancom Office HWP"
    
    # Try different variations of menu name
    menu_variations = [
        "입력",
        "입력 ",  # with trailing space
        "입력  ",  # with double space
    ]
    
    for menu_name in menu_variations:
        print(f"시도: '{menu_name}' (길이: {len(menu_name)})")
        print("-" * 70)
        
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                try
                    set menuItems to {{}}
                    set itemCount to count of menu items of menu "{menu_name}" of menu bar 1
                    
                    set menuItems to menuItems & "Total items: " & itemCount & return
                    
                    repeat with i from 1 to itemCount
                        try
                            set itemTitle to title of menu item i of menu "{menu_name}" of menu bar 1
                            set menuItems to menuItems & "Item " & i & ": [" & itemTitle & "]" & return
                        on error errMsg
                            set menuItems to menuItems & "Item " & i & ": ERROR - " & errMsg & return
                        end try
                    end repeat
                    
                    return menuItems
                on error errMsg
                    return "ERROR accessing menu: " & errMsg
                end try
            end tell
        end tell
        '''
        
        stdout, stderr, code = run_applescript(script)
        print(stdout.strip())
        print()
        
        if code == 0 and "Total items:" in stdout:
            # Found the right menu name! Now try to click 수식
            print("✅ 메뉴를 찾았습니다! 이제 '수식' 항목 클릭 시도...")
            print()
            
            # Try to find and click equation menu item
            formula_variations = [
                "수식...",
                "수식",
                "수식 ",
                "Equation...",
                "Equation",
            ]
            
            for formula_name in formula_variations:
                print(f"  시도: '{formula_name}'")
                
                script = f'''
                tell application "{app_name}"
                    activate
                end tell
                
                delay 0.3
                
                tell application "System Events"
                    tell process "{app_name}"
                        try
                            click menu item "{formula_name}" of menu "{menu_name}" of menu bar 1
                            return "SUCCESS"
                        on error errMsg
                            return "FAILED: " & errMsg
                        end try
                    end tell
                end tell
                '''
                
                stdout, stderr, code = run_applescript(script)
                
                if "SUCCESS" in stdout:
                    print(f"    ✅ 성공!")
                    print()
                    print("=" * 70)
                    print(f"🎉 작동하는 조합 발견!")
                    print(f"   메뉴: '{menu_name}'")
                    print(f"   항목: '{formula_name}'")
                    print("=" * 70)
                    return 0
                else:
                    print(f"    ❌ 실패: {stdout.strip()[:100]}")
            
            print()
            break
    
    print("=" * 70)
    print("❌ '수식' 메뉴 항목을 찾지 못했습니다")
    print("=" * 70)
    print("위의 항목 목록에서 수식 관련 항목을 확인해주세요.")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())


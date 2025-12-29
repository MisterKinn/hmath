#!/usr/bin/env python3
"""
Deep dive into formula editor window structure.
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
            timeout=15
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("=" * 70)
    print("수식 편집기 상세 구조 분석")
    print("=" * 70)
    print()
    
    app_name = "Hancom Office HWP"
    
    # Open formula editor
    print("수식 편집기 열기...")
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
    time.sleep(2)
    print("✅ 열림")
    print()
    
    # Get detailed structure
    print("전체 UI 구조 분석...")
    print("-" * 70)
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                set formulaWindow to window "수식 편집기"
                set uiInfo to ""
                
                repeat with i from 1 to (count of UI elements of formulaWindow)
                    try
                        set elem to UI element i of formulaWindow
                        set elemRole to role of elem
                        set elemDesc to description of elem
                        set elemTitle to ""
                        try
                            set elemTitle to title of elem
                        end try
                        set elemValue to ""
                        try
                            set elemValue to value of elem
                        end try
                        
                        set uiInfo to uiInfo & "Element " & i & ":" & return
                        set uiInfo to uiInfo & "  Role: " & elemRole & return
                        set uiInfo to uiInfo & "  Desc: " & elemDesc & return
                        set uiInfo to uiInfo & "  Title: " & elemTitle & return
                        set uiInfo to uiInfo & "  Value: " & elemValue & return
                        set uiInfo to uiInfo & return
                    end try
                end repeat
                
                return uiInfo
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(stdout.strip())
    print()
    
    # Try to focus on text field and type
    print("텍스트 필드에 포커스하고 입력 시도...")
    print("-" * 70)
    
    formula = "a over b"
    
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                set formulaWindow to window "수식 편집기"
                
                -- Try to find and focus text field
                repeat with elem in (UI elements of formulaWindow)
                    if role of elem is "AXTextField" then
                        set focused of elem to true
                        delay 0.2
                        
                        -- Type the formula
                        keystroke "{formula}"
                        delay 0.3
                        
                        return "SUCCESS: Typed in text field"
                    end if
                end repeat
                
                return "FAILED: No text field found"
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
    end tell
    '''
    
    stdout, stderr, code = run_applescript(script)
    print(stdout.strip())
    print()
    
    # Try pressing keyboard shortcuts
    print("키보드 단축키 시도...")
    print("-" * 70)
    
    shortcuts = [
        ("Command+Return", "return", "command down"),
        ("Return", "return", ""),
        ("Command+I", "i", "command down"),
        ("Escape then Return", "escape", ""),
    ]
    
    for name, key, mods in shortcuts:
        print(f"  시도: {name}")
        
        if mods:
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    keystroke {key} using {{{mods}}}
                end tell
            end tell
            '''
        else:
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    key code 53  -- Escape
                    delay 0.2
                    key code 36  -- Return
                end tell
            end tell
            '''
        
        stdout, stderr, code = run_applescript(script)
        time.sleep(0.3)
    
    print()
    print("=" * 70)
    print("완료 - 문서에서 수식이 삽입되었는지 확인하세요")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())


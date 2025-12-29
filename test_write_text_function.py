#!/usr/bin/env python3
"""
Test writing plain text in formula editor using the new function.
"""

import sys
from backend.hwp.hwp_controller import HwpController, HwpControllerError

def main():
    print("=" * 70)
    print("수식 편집기에 일반 텍스트 작성 테스트")
    print("=" * 70)
    print()
    
    try:
        # Initialize controller
        print("📱 Connecting to 한글...")
        hwp = HwpController()
        hwp.connect()
        print("✅ Connected successfully!")
        print()
        
        # Test 1: Write text without closing (window stays open)
        print("Test 1: 텍스트 작성 (창 열어두기)")
        print("-" * 70)
        text1 = "Hello World"
        print(f"입력할 텍스트: '{text1}'")
        print(f"close_window=False (창이 열린 상태로 유지)")
        print()
        
        try:
            hwp.write_in_formula_editor(text1, close_window=False)
            print("✅ 텍스트가 작성되었습니다!")
            print()
            print("⚠️  수식 편집기 창을 확인하세요!")
            print(f"   텍스트 필드에 '{text1}'가 입력되어 있어야 합니다.")
            print("   창은 열린 상태로 유지됩니다.")
            print()
            input("   확인했으면 Enter를 눌러 수동으로 창을 닫으세요 (Escape)...")
            
        except HwpControllerError as exc:
            print(f"❌ 실패: {exc}")
            return 1
        
        print()
        
        # Test 2: Write text and close (insert into document)
        print("Test 2: 수식 문법으로 텍스트 작성 후 자동 삽입")
        print("-" * 70)
        text2 = "a over b"
        print(f"입력할 텍스트: '{text2}'")
        print(f"close_window=True (자동으로 삽입)")
        print()
        
        try:
            hwp.write_in_formula_editor(text2, close_window=True)
            print("✅ 텍스트가 작성되고 문서에 삽입되었습니다!")
            print()
            print("🎉 문서에서 분수 'a/b'를 확인하세요!")
            print()
            
        except HwpControllerError as exc:
            print(f"❌ 실패: {exc}")
            return 1
        
        # Test 3: Plain text (not formula syntax)
        print("Test 3: 일반 텍스트 작성 후 자동 삽입")
        print("-" * 70)
        text3 = "This is plain text, not formula"
        print(f"입력할 텍스트: '{text3}'")
        print(f"close_window=True (자동으로 삽입)")
        print()
        
        try:
            hwp.write_in_formula_editor(text3, close_window=True)
            print("✅ 텍스트가 작성되고 문서에 삽입되었습니다!")
            print()
            print("📝 문서에서 텍스트를 확인하세요!")
            print()
            
        except HwpControllerError as exc:
            print(f"❌ 실패: {exc}")
            return 1
        
        print("=" * 70)
        print("✅ 모든 테스트 통과!")
        print("=" * 70)
        print()
        print("AI가 이제 수식 편집기에 텍스트를 작성할 수 있습니다!")
        print()
        print("사용법:")
        print("  hwp.write_in_formula_editor('텍스트', close_window=False)  # 창 열어두기")
        print("  hwp.write_in_formula_editor('텍스트', close_window=True)   # 자동 삽입")
        print()
        
        return 0
        
    except HwpControllerError as exc:
        print(f"❌ Error: {exc}")
        return 1
    except Exception as exc:
        print(f"❌ Unexpected error: {exc}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())


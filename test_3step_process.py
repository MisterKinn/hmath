#!/usr/bin/env python3
"""
Test the 3-step process:
1. Generate formula
2. Open formula editor window
3. Write formula in the window
"""

import sys
import time
from backend.hwp.hwp_controller import HwpController, HwpControllerError

def main():
    print("=" * 70)
    print("3단계 프로세스 테스트")
    print("=" * 70)
    print()
    
    try:
        # Connect
        print("한글에 연결 중...")
        hwp = HwpController()
        hwp.connect()
        print("✅ 연결 성공!")
        print()
        
        # Test 1: Manual 3-step process
        print("=" * 70)
        print("Test 1: 수동 3단계 프로세스")
        print("=" * 70)
        print()
        
        # Step 1: Generate formula
        formula = "a over b"
        print(f"Step 1: 수식 생성")
        print(f"  Generated formula: '{formula}'")
        print()
        
        # Step 2: Open formula editor window
        print(f"Step 2: 수식 편집기 창 열기 (IMPORTANT!)")
        hwp.open_formula_editor()
        print(f"  ✅ 수식 편집기 창이 열렸습니다!")
        print()
        
        # Wait for window to be ready
        time.sleep(1.5)
        
        # Step 3: Write formula in the window
        print(f"Step 3: 열린 창에 수식 작성")
        print(f"  Writing: '{formula}'")
        hwp.type_in_open_formula_editor(formula, close_window=True)
        print(f"  ✅ 수식이 작성되고 삽입되었습니다!")
        print()
        
        time.sleep(1)
        
        # Test 2: Automatic 3-step process (all in one)
        print("=" * 70)
        print("Test 2: 자동 3단계 프로세스 (all-in-one)")
        print("=" * 70)
        print()
        
        formula2 = "x^2 + y^2"
        print(f"Formula: '{formula2}'")
        print()
        print("실행 중:")
        print("  1. 수식 생성")
        print("  2. 수식 편집기 창 열기")
        print("  3. 수식 작성 및 삽입")
        print()
        
        hwp.write_in_formula_editor(formula2, close_window=True)
        print("✅ 완료!")
        print()
        
        # Test 3: Write without closing (for manual editing)
        print("=" * 70)
        print("Test 3: 수식 작성 (창 열어두기)")
        print("=" * 70)
        print()
        
        formula3 = "sum from i=1 to n"
        print(f"Formula: '{formula3}'")
        print()
        
        hwp.write_in_formula_editor(formula3, close_window=False)
        print("✅ 수식 편집기에 작성 완료!")
        print("   창이 열린 상태로 유지됩니다.")
        print("   수동으로 수정 가능합니다.")
        print()
        
        print("=" * 70)
        print("✅ 모든 테스트 성공!")
        print("=" * 70)
        print()
        print("프로세스:")
        print("  1. 수식 생성 ✅")
        print("  2. 수식 편집기 창 열기 ✅")
        print("  3. 열린 창에 수식 작성 ✅")
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


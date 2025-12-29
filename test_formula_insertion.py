#!/usr/bin/env python3
"""
Test script to verify formula insertion in the formula editor window.
"""

import sys
import time
from backend.hwp.hwp_controller import HwpController, HwpControllerError

def main():
    print("=" * 70)
    print("수식 편집기에 수식 자동 입력 테스트")
    print("=" * 70)
    print()
    
    try:
        # Initialize controller
        print("📱 Connecting to 한글...")
        hwp = HwpController()
        hwp.connect()
        print("✅ Connected successfully!")
        print()
        
        # Test: Insert equation via editor
        print("Test: 수식 편집기를 통한 수식 자동 삽입")
        print("Formula: a over b (분수)")
        print()
        
        try:
            hwp.insert_equation_via_editor("a over b")
            print("✅ 수식이 삽입되었습니다!")
            print()
            print("🎉 문서에서 분수 'a/b'를 확인하세요!")
            print()
            
        except HwpControllerError as exc:
            print(f"❌ 수식 삽입 실패: {exc}")
            return 1
        
        # Wait a bit and try another formula
        time.sleep(1)
        
        print("Test 2: 더 복잡한 수식")
        print("Formula: x^2 + y^2 (제곱)")
        print()
        
        try:
            hwp.insert_equation_via_editor("x^2 + y^2")
            print("✅ 수식이 삽입되었습니다!")
            print()
            
        except HwpControllerError as exc:
            print(f"❌ 수식 삽입 실패: {exc}")
            return 1
        
        print("=" * 70)
        print("✅ 모든 테스트 통과!")
        print("=" * 70)
        
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


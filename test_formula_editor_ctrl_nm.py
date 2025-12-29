#!/usr/bin/env python3
"""
Test script for opening 수식 입력 (Formula Input) window using Ctrl+N+M.
"""

from backend.hwp.hwp_controller import HwpController

def main():
    print("=" * 70)
    print("Testing 수식 입력 (Formula Input) Window")
    print("=" * 70)
    print()
    print("This will:")
    print("1. Open Hancom Office HWP")
    print("2. Press Ctrl+N+M to open formula input window")
    print("3. Type a formula and insert it")
    print()
    print("Make sure Hancom Office HWP is open with a document!")
    print()
    input("Press Enter to continue...")
    print()
    
    try:
        hwp = HwpController()
        hwp.connect()
        print("✅ Connected to HWP")
        print()
        
        # Test 1: Just open the editor
        print("Test 1: Opening formula input window (Ctrl+N+M)...")
        try:
            hwp.open_formula_editor()
            print("✅ Formula input window should be open now!")
            print("   (You can manually type a formula and press Enter)")
            print()
            input("Press Enter after you've tested manually...")
        except Exception as e:
            print(f"❌ Failed: {e}")
            print()
        
        # Test 2: Insert formula automatically
        print("Test 2: Inserting formula automatically...")
        test_formula = "a over b"
        print(f"   Formula: {test_formula}")
        try:
            hwp.insert_equation_via_editor(test_formula)
            print("✅ Formula inserted!")
            print("   Check your HWP document - you should see a fraction a/b")
        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
        print()
        
        # Test 3: More complex formula
        print("Test 3: Inserting complex formula...")
        test_formula2 = "x^2 + y^2"
        print(f"   Formula: {test_formula2}")
        try:
            hwp.insert_equation_via_editor(test_formula2)
            print("✅ Complex formula inserted!")
        except Exception as e:
            print(f"❌ Failed: {e}")
        print()
        
        print("=" * 70)
        print("✨ All tests completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Make sure:")
        print("1. Hancom Office HWP is running")
        print("2. A document is open")
        print("3. Accessibility permissions are granted")

if __name__ == "__main__":
    main()



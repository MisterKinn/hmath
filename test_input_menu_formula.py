#!/usr/bin/env python3
"""
Test script to verify that AI can open formula editor via 입력 → 수식 menu.
"""

import sys
import time
from backend.hwp.hwp_controller import HwpController, HwpControllerError

def main():
    print("=" * 70)
    print("Testing Formula Editor Opening via 입력 → 수식 Menu")
    print("=" * 70)
    print()
    print("⚠️  Make sure:")
    print("1. Hancom Office HWP is open")
    print("2. A document is open")
    print("3. Accessibility permissions are granted")
    print()
    input("Press Enter when ready...")
    print()
    
    try:
        # Initialize controller
        print("📱 Connecting to 한글...")
        hwp = HwpController()
        hwp.connect()
        print("✅ Connected successfully!")
        print()
        
        # Test 1: Open formula editor
        print("Test 1: Opening formula editor window")
        print("Trying menu path: 입력 → 수식")
        print()
        
        try:
            hwp.open_formula_editor()
            print("✅ Formula editor opened successfully!")
            print()
            print("🎉 The formula editor window should now be open!")
            print("You can manually enter a formula and click the insert button.")
            print()
            
        except HwpControllerError as exc:
            print(f"❌ Failed to open formula editor: {exc}")
            return 1
        
        # Wait for user to see the result
        input("Press Enter to continue to next test...")
        print()
        
        # Test 2: Auto-insert equation via editor
        print("Test 2: Auto-inserting equation via formula editor")
        print("Formula: a over b (fraction)")
        print()
        
        try:
            hwp.insert_equation_via_editor("a over b")
            print("✅ Equation inserted successfully!")
            print()
            print("🎉 The fraction 'a/b' should now be in your document!")
            print()
            
        except HwpControllerError as exc:
            print(f"❌ Failed to insert equation: {exc}")
            return 1
        
        # Final success message
        print("=" * 70)
        print("✅ All tests passed!")
        print("=" * 70)
        print()
        print("Summary:")
        print("1. ✅ Formula editor can be opened via 입력 → 수식")
        print("2. ✅ Equations can be auto-inserted via the editor")
        print()
        print("The AI can now open the formula window using:")
        print("  hwp.open_formula_editor()")
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


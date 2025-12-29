#!/usr/bin/env python3
"""
Test script to open 수식 편집기 (Formula Editor) window automatically.
"""

from backend.hwp.hwp_controller import HwpController

def main():
    print("=" * 70)
    print("Testing 수식 편집기 (Formula Editor) Auto-Open")
    print("=" * 70)
    print()
    print("This will:")
    print("1. Connect to Hancom Office HWP")
    print("2. Press Ctrl+N+M to open formula editor window")
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
        
        print("Opening formula editor window (Ctrl+N+M)...")
        try:
            hwp.open_formula_editor()
            print("✅ Formula editor window should be open now!")
            print()
            print("You can now:")
            print("  - Type formulas manually in the editor")
            print("  - Use the toolbar to insert symbols")
            print("  - Press Enter or click '넣기' to insert the formula")
            print()
            input("Press Enter when done testing...")
        except Exception as e:
            print(f"❌ Failed to open formula editor: {e}")
            import traceback
            traceback.print_exc()
        
        print()
        print("=" * 70)
        print("✨ Test completed!")
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




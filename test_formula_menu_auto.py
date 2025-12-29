#!/usr/bin/env python3
"""
Non-interactive test to verify formula editor menu opening.
"""

import sys
import logging
from backend.hwp.hwp_controller import HwpController, HwpControllerError

# Enable logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    print("Testing Formula Editor Opening (Non-interactive)")
    print("=" * 70)
    
    try:
        # Initialize controller
        print("Connecting to 한글...")
        hwp = HwpController()
        hwp.connect()
        print("✅ Connected successfully!")
        print()
        
        # Test: Open formula editor
        print("Opening formula editor via 입력 → 수식... menu")
        hwp.open_formula_editor()
        print("✅ Formula editor opened successfully!")
        print()
        print("🎉 Success! The formula editor window should now be open.")
        print()
        print("The AI can now open the 수식 window by clicking:")
        print("  입력 → 수식... button")
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


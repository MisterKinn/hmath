#!/usr/bin/env python3
"""
Test script for special character and formula insertion on macOS.
Run this with Hancom Office HWP open.
"""

from backend.hwp.hwp_controller import HwpController

def main():
    print("=" * 60)
    print("Testing Special Character Insertion")
    print("=" * 60)
    print()
    print("Make sure Hancom Office HWP is open with a document!")
    print()
    
    try:
        hwp = HwpController()
        hwp.connect()
        print("✅ Connected to HWP")
        print()
        
        tests = [
            ("Simple formula", "x² + y² = z²"),
            ("LaTeX notation", r"\int_{0}^{\infty} e^{-x} dx = 1"),
            ("Unicode symbols", "∫ f(x)dx + ∑ᵢ₌₁ⁿ xᵢ = α + β"),
            ("Quotes", 'The equation "E = mc²" is famous!'),
            ("Backslashes", r"C:\Users\path\to\file"),
            ("Braces", "f(x) = {a, b, c}"),
            ("Korean + Math", "이차방정식: ax² + bx + c = 0"),
            ("Mixed", "Hello 안녕 123 x² ∫ \"test\" \\backslash"),
        ]
        
        for i, (name, text) in enumerate(tests, 1):
            print(f"Test {i}: {name}")
            print(f"  Text: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            try:
                hwp.insert_text(text)
                hwp.insert_paragraph_break()
                print(f"  ✅ Success")
            except Exception as e:
                print(f"  ❌ Failed: {e}")
            
            print()
        
        print("=" * 60)
        print("✨ All tests completed!")
        print("Check your HWP document to see the results.")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Make sure:")
        print("1. Hancom Office HWP is running")
        print("2. A document is open")
        print("3. Accessibility permissions are granted")

if __name__ == "__main__":
    main()



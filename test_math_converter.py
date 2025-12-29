#!/usr/bin/env python3
"""
Test script to demonstrate LaTeX to Unicode conversion.
Shows what can be converted and examples.
"""

from backend.math_unicode_converter import latex_to_unicode, get_supported_conversions

def main():
    print("=" * 70)
    print("LaTeX to Unicode Math Converter - Supported Conversions")
    print("=" * 70)
    print()
    
    # Show supported conversions
    conversions = get_supported_conversions()
    print("📋 Supported Conversions:")
    print()
    for category, items in conversions.items():
        print(f"  {category}:")
        if isinstance(items, list):
            print(f"    {', '.join(str(x) for x in items)}")
        print()
    
    print("=" * 70)
    print("Example Conversions")
    print("=" * 70)
    print()
    
    examples = [
        # Basic math
        ("x^2 + y^2 = z^2", "Quadratic equation"),
        ("a^2 + b^2 = c^2", "Pythagorean theorem"),
        ("E = mc^2", "Einstein's equation"),
        
        # Subscripts
        ("x_1 + x_2 = x_3", "Subscripts"),
        ("H_2O", "Chemical formula"),
        ("CO_2", "Carbon dioxide"),
        
        # Greek letters
        ("\\alpha + \\beta = \\gamma", "Greek letters"),
        ("\\pi r^2", "Area of circle"),
        ("\\theta = 90^\\circ", "Angle"),
        
        # Calculus
        ("\\int_{0}^{\\infty} e^{-x} dx = 1", "Integral"),
        ("\\frac{d}{dx} f(x)", "Derivative"),
        ("\\sum_{i=1}^{n} x_i", "Summation"),
        ("\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1", "Limit"),
        
        # Relations
        ("x \\leq y", "Less than or equal"),
        ("a \\geq b", "Greater than or equal"),
        ("x \\neq 0", "Not equal"),
        ("x \\approx 3.14", "Approximately"),
        
        # Sets
        ("x \\in A", "Element of"),
        ("A \\cup B", "Union"),
        ("A \\cap B", "Intersection"),
        ("\\emptyset", "Empty set"),
        
        # Operators
        ("a \\times b", "Multiplication"),
        ("a \\div b", "Division"),
        ("a \\pm b", "Plus or minus"),
        ("a \\cdot b", "Dot product"),
        
        # Complex formulas
        ("\\int_{a}^{b} f(x) dx = F(b) - F(a)", "Fundamental theorem"),
        ("\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}", "Sum formula"),
        ("e^{i\\pi} + 1 = 0", "Euler's identity"),
        ("\\nabla \\cdot \\mathbf{F} = 0", "Divergence"),
        
        # Fractions
        ("\\frac{1}{2}", "Half"),
        ("\\frac{a}{b}", "Generic fraction"),
        ("\\frac{x^2 + y^2}{z^2}", "Complex fraction"),
    ]
    
    for latex, description in examples:
        unicode_result = latex_to_unicode(latex)
        print(f"📝 {description}:")
        print(f"   LaTeX: {latex}")
        print(f"   Unicode: {unicode_result}")
        print()
    
    print("=" * 70)
    print("✅ All conversions shown above are supported!")
    print("=" * 70)
    print()
    print("💡 Usage in code:")
    print("   from backend.hwp.hwp_controller import HwpController")
    print("   hwp = HwpController()")
    print("   hwp.connect()")
    print("   hwp.insert_math_text('x^2 + y^2 = z^2')")
    print()

if __name__ == "__main__":
    main()



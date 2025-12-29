#!/usr/bin/env python3
"""
Example formula code for 한글 수식 편집기 (Formula Editor).

These examples show different ways to insert formulas:
1. Using insert_math_text() - Unicode text (works now)
2. Using insert_equation_via_editor() - Real equation objects (needs testing)
"""

from backend.hwp.hwp_controller import HwpController

def example_basic_math():
    """Basic math formulas using Unicode."""
    print("=" * 70)
    print("Example 1: Basic Math (Unicode)")
    print("=" * 70)
    
    examples = [
        # Simple equations
        ("x^2 + y^2 = z^2", "Pythagorean theorem"),
        ("E = mc^2", "Einstein's equation"),
        ("a^2 + b^2 = c^2", "Pythagorean theorem (variables)"),
        
        # With subscripts
        ("H_2O", "Water molecule"),
        ("CO_2", "Carbon dioxide"),
        ("x_1 + x_2 = x_3", "Variables with subscripts"),
        
        # Mixed
        ("E_k = (1/2)mv^2", "Kinetic energy"),
        ("F = ma", "Newton's second law"),
    ]
    
    for latex, description in examples:
        print(f"\n{description}:")
        print(f"  Code: hwp.insert_math_text('{latex}')")
        print(f"  Result: Will display as Unicode math symbols")
        # Uncomment to actually insert:
        # hwp.insert_math_text(latex)
        # hwp.insert_paragraph_break()


def example_fractions():
    """Fraction examples."""
    print("\n" + "=" * 70)
    print("Example 2: Fractions")
    print("=" * 70)
    
    examples = [
        # Unicode fractions (works now)
        ("\\frac{1}{2}", "Half (Unicode: ½)"),
        ("\\frac{a}{b}", "Generic fraction (Unicode: a/b)"),
        ("\\frac{x^2 + y^2}{z^2}", "Complex fraction"),
        
        # Formula editor syntax (needs testing)
        ("a over b", "Simple fraction (Formula Editor)"),
        ("x^2 + y^2 over z^2", "Fraction with superscripts"),
        ("(a + b) over (c + d)", "Fraction with parentheses"),
    ]
    
    for formula, description in examples:
        print(f"\n{description}:")
        if "over" in formula:
            print(f"  Code: hwp.insert_equation_via_editor('{formula}')")
            print(f"  Note: Formula Editor syntax (needs testing)")
        else:
            print(f"  Code: hwp.insert_math_text('{formula}')")
            print(f"  Note: Unicode conversion")


def example_calculus():
    """Calculus formulas."""
    print("\n" + "=" * 70)
    print("Example 3: Calculus")
    print("=" * 70)
    
    examples = [
        # Integrals (Unicode)
        ("\\int_{0}^{\\infty} e^{-x} dx = 1", "Definite integral"),
        ("\\int f(x) dx", "Indefinite integral"),
        ("\\int_{a}^{b} f(x) dx", "Definite integral with limits"),
        
        # Integrals (Formula Editor)
        ("int from 0 to infinity e^-x dx", "Formula Editor syntax"),
        ("int from a to b f(x) dx", "Formula Editor with variables"),
        
        # Derivatives
        ("\\frac{d}{dx} f(x)", "Derivative"),
        ("\\frac{d^2}{dx^2} f(x)", "Second derivative"),
        
        # Sums
        ("\\sum_{i=1}^{n} i", "Summation"),
        ("\\sum_{i=1}^{n} x_i", "Sum with subscript"),
        ("sum from i=1 to n x_i", "Formula Editor sum"),
    ]
    
    for formula, description in examples:
        print(f"\n{description}:")
        if "from" in formula or "to" in formula:
            print(f"  Code: hwp.insert_equation_via_editor('{formula}')")
        else:
            print(f"  Code: hwp.insert_math_text('{formula}')")


def example_greek_letters():
    """Greek letter examples."""
    print("\n" + "=" * 70)
    print("Example 4: Greek Letters")
    print("=" * 70)
    
    examples = [
        ("\\alpha + \\beta = \\gamma", "Greek letters"),
        ("\\pi r^2", "Area of circle"),
        ("\\theta = 90^\\circ", "Angle"),
        ("\\lambda = \\frac{h}{p}", "De Broglie wavelength"),
        ("\\Delta x \\Delta p \\geq \\frac{\\hbar}{2}", "Heisenberg uncertainty"),
    ]
    
    for latex, description in examples:
        print(f"\n{description}:")
        print(f"  Code: hwp.insert_math_text('{latex}')")
        print(f"  Result: Converts to Unicode Greek letters")


def example_complex_formulas():
    """Complex multi-part formulas."""
    print("\n" + "=" * 70)
    print("Example 5: Complex Formulas")
    print("=" * 70)
    
    examples = [
        # Quadratic formula
        ("x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}", "Quadratic formula"),
        
        # Euler's identity
        ("e^{i\\pi} + 1 = 0", "Euler's identity"),
        
        # Sum formula
        ("\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}", "Sum of integers"),
        
        # Binomial theorem
        ("(a + b)^n = \\sum_{k=0}^{n} \\binom{n}{k} a^{n-k} b^k", "Binomial theorem"),
        
        # Fourier transform
        ("F(\\omega) = \\int_{-\\infty}^{\\infty} f(t) e^{-i\\omega t} dt", "Fourier transform"),
    ]
    
    for latex, description in examples:
        print(f"\n{description}:")
        print(f"  Code: hwp.insert_math_text('{latex}')")
        print(f"  Note: Complex formulas may need manual spacing adjustment")


def example_physics():
    """Physics formulas."""
    print("\n" + "=" * 70)
    print("Example 6: Physics Formulas")
    print("=" * 70)
    
    examples = [
        ("F = ma", "Newton's second law"),
        ("E = mc^2", "Mass-energy equivalence"),
        ("E = h\\nu", "Photon energy"),
        ("\\lambda = \\frac{h}{p}", "De Broglie wavelength"),
        ("\\Delta E = h\\nu", "Energy change"),
        ("v = v_0 + at", "Velocity with acceleration"),
        ("x = x_0 + v_0 t + \\frac{1}{2}at^2", "Position equation"),
        ("F = G\\frac{m_1 m_2}{r^2}", "Gravitational force"),
    ]
    
    for latex, description in examples:
        print(f"\n{description}:")
        print(f"  Code: hwp.insert_math_text('{latex}')")


def example_chemistry():
    """Chemistry formulas."""
    print("\n" + "=" * 70)
    print("Example 7: Chemistry Formulas")
    print("=" * 70)
    
    examples = [
        ("H_2O", "Water"),
        ("CO_2", "Carbon dioxide"),
        ("C_6H_{12}O_6", "Glucose"),
        ("CH_4", "Methane"),
        ("NH_3", "Ammonia"),
        ("H_2SO_4", "Sulfuric acid"),
        ("CaCO_3", "Calcium carbonate"),
    ]
    
    for latex, description in examples:
        print(f"\n{description}:")
        print(f"  Code: hwp.insert_math_text('{latex}')")


def example_ready_to_use():
    """Ready-to-use code snippets you can copy and paste."""
    print("\n" + "=" * 70)
    print("Ready-to-Use Code Snippets")
    print("=" * 70)
    print()
    print("Copy and paste these into your code:")
    print()
    
    snippets = [
        {
            "name": "Basic Setup",
            "code": '''
from backend.hwp.hwp_controller import HwpController

hwp = HwpController()
hwp.connect()
'''
        },
        {
            "name": "Insert Simple Formula",
            "code": '''
# Insert: x² + y² = z²
hwp.insert_math_text("x^2 + y^2 = z^2")
'''
        },
        {
            "name": "Insert Fraction",
            "code": '''
# Insert: ½
hwp.insert_math_text("\\frac{1}{2}")

# Or try formula editor (needs testing):
# hwp.insert_equation_via_editor("1 over 2")
'''
        },
        {
            "name": "Insert Integral",
            "code": '''
# Insert: ∫₀^∞ e⁻ˣ dx
hwp.insert_math_text("\\int_{0}^{\\infty} e^{-x} dx")
'''
        },
        {
            "name": "Insert Greek Letters",
            "code": '''
# Insert: α + β = γ
hwp.insert_math_text("\\alpha + \\beta = \\gamma")
'''
        },
        {
            "name": "Insert with Paragraph Break",
            "code": '''
hwp.insert_math_text("x^2 + y^2 = z^2")
hwp.insert_paragraph_break()
hwp.insert_text("This is regular text.")
'''
        },
        {
            "name": "Multiple Formulas",
            "code": '''
formulas = [
    "E = mc^2",
    "F = ma",
    "x^2 + y^2 = z^2",
]

for formula in formulas:
    hwp.insert_math_text(formula)
    hwp.insert_paragraph_break()
'''
        },
    ]
    
    for i, snippet in enumerate(snippets, 1):
        print(f"{i}. {snippet['name']}:")
        print(snippet['code'])
        print()


def main():
    """Show all examples."""
    print("\n" + "=" * 70)
    print("한글 수식 편집기 - Formula Code Examples")
    print("=" * 70)
    print()
    print("These examples show how to insert formulas into HWP documents.")
    print("Note: Make sure HWP is open before running these!")
    print()
    
    # Show examples (without actually inserting)
    example_basic_math()
    example_fractions()
    example_calculus()
    example_greek_letters()
    example_complex_formulas()
    example_physics()
    example_chemistry()
    example_ready_to_use()
    
    print("\n" + "=" * 70)
    print("💡 Tips:")
    print("=" * 70)
    print("1. Use insert_math_text() for Unicode text (works now)")
    print("2. Use insert_equation_via_editor() for real equations (needs testing)")
    print("3. Test formula editor syntax manually first")
    print("4. Complex formulas may need manual spacing")
    print("=" * 70)


if __name__ == "__main__":
    main()


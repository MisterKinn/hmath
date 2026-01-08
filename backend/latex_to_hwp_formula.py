"""
Converter from LaTeX to 한글 수식 편집기 (Formula Editor) syntax.

The 한글 formula editor uses a simple English-like syntax.
Examples:
- "a over b" for fractions
- "x^2" for superscripts
- "x_1" for subscripts
- "int from 0 to infinity" for integrals
"""

import re


def latex_to_hwp_formula(latex: str) -> str:
    """
    Convert LaTeX math notation to 한글 수식 편집기 syntax.
    
    Args:
        latex: LaTeX math notation
        
    Returns:
        Formula in 한글 수식 편집기 syntax
    """
    text = latex.strip()
    
    # Remove math delimiters
    text = re.sub(r'^\$|\$$', '', text)
    text = re.sub(r'^\\\[|\\\]$', '', text)
    text = re.sub(r'^\\\(|\\\)$', '', text)
    
    # Convert fractions: \frac{a}{b} → a over b
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1 over \2', text)
    
    # Convert superscripts: x^2 → x^2 (keep as is, editor handles it)
    # Or: x^{n+1} → x^(n+1)
    text = re.sub(r'\^\{([^}]+)\}', r'^(\1)', text)
    
    # Convert subscripts: x_1 → x_1 (keep as is)
    # Or: x_{i+1} → x_(i+1)
    text = re.sub(r'_\{(.+?)\}', r'_\1', text)
    
    # Convert integrals: \int_{a}^{b} → int from a to b
    def replace_integral(match):
        lower = match.group(1) if match.group(1) else ''
        upper = match.group(2) if match.group(2) else ''
        
        if lower and upper:
            return f"int from {lower} to {upper}"
        elif lower:
            return f"int from {lower}"
        elif upper:
            return f"int to {upper}"
        else:
            return "int"
    
    text = re.sub(r'\\int(?:_\{([^}]*)\})?(?:\^\{([^}]*)\})?', replace_integral, text)
    
    # Convert sums: \sum_{i=1}^{n} → sum from i=1 to n
    def replace_sum(match):
        lower = match.group(1) if match.group(1) else ''
        upper = match.group(2) if match.group(2) else ''
        
        if lower and upper:
            return f"sum from {lower} to {upper}"
        elif lower:
            return f"sum from {lower}"
        elif upper:
            return f"sum to {upper}"
        else:
            return "sum"
    
    text = re.sub(r'\\sum(?:_\{([^}]*)\})?(?:\^\{([^}]*)\})?', replace_sum, text)
    
    # Convert Greek letters (keep LaTeX names, editor may understand them)
    # Or convert to English: \alpha → alpha
    greek_map = {
        'alpha': 'alpha', 'beta': 'beta', 'gamma': 'gamma', 'delta': 'delta',
        'epsilon': 'epsilon', 'zeta': 'zeta', 'eta': 'eta', 'theta': 'theta',
        'iota': 'iota', 'kappa': 'kappa', 'lambda': 'lambda', 'mu': 'mu',
        'nu': 'nu', 'xi': 'xi', 'pi': 'pi', 'rho': 'rho', 'sigma': 'sigma',
        'tau': 'tau', 'upsilon': 'upsilon', 'phi': 'phi', 'chi': 'chi',
        'psi': 'psi', 'omega': 'omega',
    }
    
    for greek, english in greek_map.items():
        text = re.sub(r'\\' + greek + r'\b', english, text)
    
    # Convert common symbols
    symbol_map = {
        r'\\infty': 'infinity',
        r'\\cdot': '*',
        r'\\times': '×',
        r'\\div': '/',
        r'\\pm': '±',
        r'\\leq': '<=',
        r'\\geq': '>=',
        r'\\neq': '!=',
        r'\\approx': '≈',
    }
    
    for latex_sym, hwp_sym in symbol_map.items():
        text = text.replace(latex_sym, hwp_sym)
    
    # Clean up remaining backslashes
    text = re.sub(r'\\([a-zA-Z]+)', r'\1', text)
    
    return text


# Example conversions for testing
if __name__ == "__main__":
    examples = [
        (r"\frac{a}{b}", "a over b"),
        (r"x^2 + y^2", "x^2 + y^2"),
        (r"\int_{0}^{\infty} e^{-x} dx", "int from 0 to infinity e^-x dx"),
        (r"\sum_{i=1}^{n} x_i", "sum from i=1 to n x_i"),
        (r"\alpha + \beta", "alpha + beta"),
    ]
    
    print("LaTeX → 한글 수식 편집기 Conversion Examples:")
    print("=" * 60)
    for latex, expected in examples:
        result = latex_to_hwp_formula(latex)
        print(f"LaTeX: {latex}")
        print(f"  → {result}")
        print(f"  (Expected: {expected})")
        print()



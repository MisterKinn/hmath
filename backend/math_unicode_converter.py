"""
LaTeX to Unicode math symbol converter.
Converts LaTeX notation to Unicode characters that display correctly in text.
"""

import re
from typing import Dict

# Superscript mapping
SUPERSCRIPT_MAP: Dict[str, str] = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
    'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ',
    'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ', 'i': 'ⁱ', 'j': 'ʲ',
    'k': 'ᵏ', 'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ',
    'p': 'ᵖ', 'r': 'ʳ', 's': 'ˢ', 't': 'ᵗ', 'u': 'ᵘ',
    'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ',
}

# Subscript mapping
SUBSCRIPT_MAP: Dict[str, str] = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
    'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
    'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
    'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
    'v': 'ᵥ', 'x': 'ₓ',
}

# Greek letters (lowercase)
GREEK_LOWERCASE: Dict[str, str] = {
    'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ',
    'epsilon': 'ε', 'zeta': 'ζ', 'eta': 'η', 'theta': 'θ',
    'iota': 'ι', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ',
    'nu': 'ν', 'xi': 'ξ', 'omicron': 'ο', 'pi': 'π',
    'rho': 'ρ', 'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ',
    'phi': 'φ', 'chi': 'χ', 'psi': 'ψ', 'omega': 'ω',
}

# Greek letters (uppercase)
GREEK_UPPERCASE: Dict[str, str] = {
    'Alpha': 'Α', 'Beta': 'Β', 'Gamma': 'Γ', 'Delta': 'Δ',
    'Epsilon': 'Ε', 'Zeta': 'Ζ', 'Eta': 'Η', 'Theta': 'Θ',
    'Iota': 'Ι', 'Kappa': 'Κ', 'Lambda': 'Λ', 'Mu': 'Μ',
    'Nu': 'Ν', 'Xi': 'Ξ', 'Omicron': 'Ο', 'Pi': 'Π',
    'Rho': 'Ρ', 'Sigma': 'Σ', 'Tau': 'Τ', 'Upsilon': 'Υ',
    'Phi': 'Φ', 'Chi': 'Χ', 'Psi': 'Ψ', 'Omega': 'Ω',
}

# Math operators and symbols
MATH_SYMBOLS: Dict[str, str] = {
    # Operators
    '\\times': '×',
    '\\div': '÷',
    '\\pm': '±',
    '\\mp': '∓',
    '\\cdot': '·',
    '\\ast': '∗',
    '\\star': '⋆',
    
    # Relations
    '\\leq': '≤',
    '\\geq': '≥',
    '\\neq': '≠',
    '\\approx': '≈',
    '\\equiv': '≡',
    '\\sim': '∼',
    '\\propto': '∝',
    '\\ll': '≪',
    '\\gg': '≫',
    
    # Sets
    '\\in': '∈',
    '\\notin': '∉',
    '\\subset': '⊂',
    '\\supset': '⊃',
    '\\subseteq': '⊆',
    '\\supseteq': '⊇',
    '\\cup': '∪',
    '\\cap': '∩',
    '\\emptyset': '∅',
    
    # Arrows
    '\\rightarrow': '→',
    '\\leftarrow': '←',
    '\\Rightarrow': '⇒',
    '\\Leftarrow': '⇐',
    '\\leftrightarrow': '↔',
    '\\Leftrightarrow': '⇔',
    
    # Calculus
    '\\partial': '∂',
    '\\nabla': '∇',
    '\\infty': '∞',
    
    # Logic
    '\\land': '∧',
    '\\lor': '∨',
    '\\neg': '¬',
    '\\forall': '∀',
    '\\exists': '∃',
    
    # Other
    '\\sum': '∑',
    '\\prod': '∏',
    '\\int': '∫',
    '\\oint': '∮',
    '\\sqrt': '√',
    '\\angle': '∠',
    '\\triangle': '△',
    '\\parallel': '∥',
    '\\perp': '⊥',
    '\\therefore': '∴',
    '\\because': '∵',
}


def convert_superscript(text: str) -> str:
    """Convert ^{...} or ^x to superscript Unicode."""
    def replace_sup(match):
        content = match.group(1)
        if len(content) == 1:
            return SUPERSCRIPT_MAP.get(content, '^' + content)
        # Multiple characters - convert each
        return ''.join(SUPERSCRIPT_MAP.get(c, c) for c in content)
    
    # Handle ^{...} format
    text = re.sub(r'\^\{([^}]+)\}', replace_sup, text)
    # Handle ^x format (single char after ^)
    text = re.sub(r'\^([a-zA-Z0-9+\-=()])', lambda m: SUPERSCRIPT_MAP.get(m.group(1), '^' + m.group(1)), text)
    return text


def convert_subscript(text: str) -> str:
    """Convert _{...} or _x to subscript Unicode."""
    def replace_sub(match):
        content = match.group(1)
        if len(content) == 1:
            return SUBSCRIPT_MAP.get(content, '_' + content)
        # Multiple characters - convert each
        return ''.join(SUBSCRIPT_MAP.get(c, c) for c in content)
    
    # Handle _{...} format
    text = re.sub(r'\_\{([^}]+)\}', replace_sub, text)
    # Handle _x format (single char after _)
    text = re.sub(r'\_([a-zA-Z0-9+\-=()])', lambda m: SUBSCRIPT_MAP.get(m.group(1), '_' + m.group(1)), text)
    return text


def convert_greek(text: str) -> str:
    """Convert \\alpha, \\beta, etc. to Greek letters."""
    # Uppercase first
    for latex, unicode in GREEK_UPPERCASE.items():
        text = re.sub(r'\\' + latex + r'\b', unicode, text)
    # Lowercase
    for latex, unicode in GREEK_LOWERCASE.items():
        text = re.sub(r'\\' + latex + r'\b', unicode, text)
    return text


def convert_math_symbols(text: str) -> str:
    """Convert LaTeX math symbols to Unicode."""
    # Sort by length (longest first) to avoid partial matches
    sorted_symbols = sorted(MATH_SYMBOLS.items(), key=lambda x: -len(x[0]))
    for latex, unicode in sorted_symbols:
        text = text.replace(latex, unicode)
    return text


def convert_fractions(text: str) -> str:
    """Convert simple fractions like \\frac{a}{b} to Unicode fraction."""
    # Common fractions
    fraction_map = {
        r'\\frac\{1\}\{2\}': '½',
        r'\\frac\{1\}\{3\}': '⅓',
        r'\\frac\{2\}\{3\}': '⅔',
        r'\\frac\{1\}\{4\}': '¼',
        r'\\frac\{3\}\{4\}': '¾',
        r'\\frac\{1\}\{5\}': '⅕',
        r'\\frac\{2\}\{5\}': '⅖',
        r'\\frac\{3\}\{5\}': '⅗',
        r'\\frac\{4\}\{5\}': '⅘',
        r'\\frac\{1\}\{6\}': '⅙',
        r'\\frac\{5\}\{6\}': '⅚',
        r'\\frac\{1\}\{8\}': '⅛',
        r'\\frac\{3\}\{8\}': '⅜',
        r'\\frac\{5\}\{8\}': '⅝',
        r'\\frac\{7\}\{8\}': '⅞',
    }
    
    for latex, unicode in fraction_map.items():
        text = re.sub(latex, unicode, text)
    
    # Generic fraction: \frac{a}{b} → a/b (fallback)
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1/\2', text)
    
    return text


def convert_integrals(text: str) -> str:
    """Convert integral notation with limits."""
    # \int_{a}^{b} → ∫ₐᵇ
    def replace_integral(match):
        lower = match.group(1) if match.group(1) else ''
        upper = match.group(2) if match.group(2) else ''
        
        # Convert limits to sub/superscript
        lower_sub = ''.join(SUBSCRIPT_MAP.get(c, c) for c in lower)
        upper_sup = ''.join(SUPERSCRIPT_MAP.get(c, c) for c in upper)
        
        return '∫' + (lower_sub if lower_sub else '') + (upper_sup if upper_sup else '')
    
    text = re.sub(r'\\int(?:_\{([^}]*)\})?(?:\^\{([^}]*)\})?', replace_integral, text)
    return text


def convert_sums(text: str) -> str:
    """Convert sum notation with limits."""
    # \sum_{i=1}^{n} → ∑ᵢ₌₁ⁿ
    def replace_sum(match):
        lower = match.group(1) if match.group(1) else ''
        upper = match.group(2) if match.group(2) else ''
        
        # Convert limits
        lower_sub = ''.join(SUBSCRIPT_MAP.get(c, c) for c in lower)
        upper_sup = ''.join(SUPERSCRIPT_MAP.get(c, c) for c in upper)
        
        return '∑' + (lower_sub if lower_sub else '') + (upper_sup if upper_sup else '')
    
    text = re.sub(r'\\sum(?:_\{([^}]*)\})?(?:\^\{([^}]*)\})?', replace_sum, text)
    return text


def latex_to_unicode(latex_text: str) -> str:
    """
    Convert LaTeX math notation to Unicode characters.
    
    Supported conversions:
    - Superscripts: x^2 → x², x^{n+1} → xⁿ⁺¹
    - Subscripts: x_1 → x₁, x_{i+1} → xᵢ₊₁
    - Greek letters: \\alpha → α, \\Gamma → Γ
    - Math symbols: \\leq → ≤, \\infty → ∞, \\int → ∫
    - Fractions: \\frac{1}{2} → ½
    - Integrals: \\int_{0}^{\\infty} → ∫₀^∞
    - Sums: \\sum_{i=1}^{n} → ∑ᵢ₌₁ⁿ
    
    Args:
        latex_text: LaTeX math notation string
        
    Returns:
        Unicode string with math symbols
    """
    text = latex_text
    
    # Remove math delimiters if present
    text = re.sub(r'^\$|\$$', '', text)  # Remove $...$
    text = re.sub(r'^\\\[|\\\]$', '', text)  # Remove \[...\]
    text = re.sub(r'^\\\(|\\\)$', '', text)  # Remove \(...\)
    
    # Convert in order (some depend on others)
    text = convert_greek(text)
    text = convert_math_symbols(text)
    text = convert_fractions(text)
    text = convert_integrals(text)
    text = convert_sums(text)
    text = convert_subscript(text)
    text = convert_superscript(text)
    
    # Clean up any remaining backslashes (for unsupported commands)
    text = re.sub(r'\\([a-zA-Z]+)', r'\1', text)  # Remove backslash, keep command name
    
    return text


def get_supported_conversions() -> Dict[str, list]:
    """Return a dictionary of all supported conversions."""
    return {
        'Superscripts': list(SUPERSCRIPT_MAP.keys())[:10] + ['...'],
        'Subscripts': list(SUBSCRIPT_MAP.keys())[:10] + ['...'],
        'Greek Letters (lowercase)': list(GREEK_LOWERCASE.keys())[:10] + ['...'],
        'Greek Letters (uppercase)': list(GREEK_UPPERCASE.keys())[:10] + ['...'],
        'Math Operators': ['\\times', '\\div', '\\pm', '\\cdot', '\\ast'],
        'Relations': ['\\leq', '\\geq', '\\neq', '\\approx', '\\equiv'],
        'Sets': ['\\in', '\\notin', '\\subset', '\\cup', '\\cap'],
        'Arrows': ['\\rightarrow', '\\leftarrow', '\\Rightarrow', '\\Leftarrow'],
        'Calculus': ['\\partial', '\\nabla', '\\infty', '\\int', '\\sum'],
        'Logic': ['\\land', '\\lor', '\\neg', '\\forall', '\\exists'],
    }



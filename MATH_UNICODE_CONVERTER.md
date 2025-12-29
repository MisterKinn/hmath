# 📐 LaTeX to Unicode Math Converter

## Overview

A converter that transforms LaTeX math notation into Unicode characters that display correctly as text. Perfect for macOS where native equation insertion isn't available.

## ✅ What Can Be Converted

### 1. Superscripts
**Format:** `x^2` or `x^{n+1}`

**Examples:**
- `x^2` → `x²`
- `E = mc^2` → `E = mc²`
- `x^{n+1}` → `xⁿ⁺¹`
- `a^2 + b^2 = c^2` → `a² + b² = c²`

**Supported characters:** 0-9, a-z, +, -, =, (, )

### 2. Subscripts
**Format:** `x_1` or `x_{i+1}`

**Examples:**
- `x_1` → `x₁`
- `H_2O` → `H₂O`
- `CO_2` → `CO₂`
- `x_{i+1}` → `xᵢ₊₁`

**Supported characters:** 0-9, a-z, +, -, =, (, )

### 3. Greek Letters
**Format:** `\alpha`, `\Gamma`

**Lowercase:**
- `\alpha` → `α`
- `\beta` → `β`
- `\gamma` → `γ`
- `\pi` → `π`
- `\theta` → `θ`
- `\lambda` → `λ`
- `\mu` → `μ`
- `\sigma` → `σ`
- `\phi` → `φ`
- `\omega` → `ω`
- ... (all 24 lowercase Greek letters)

**Uppercase:**
- `\Alpha` → `Α`
- `\Gamma` → `Γ`
- `\Delta` → `Δ`
- `\Theta` → `Θ`
- `\Lambda` → `Λ`
- `\Pi` → `Π`
- `\Sigma` → `Σ`
- `\Omega` → `Ω`
- ... (all 24 uppercase Greek letters)

### 4. Math Operators
- `\times` → `×`
- `\div` → `÷`
- `\pm` → `±`
- `\mp` → `∓`
- `\cdot` → `·`
- `\ast` → `∗`
- `\star` → `⋆`

### 5. Relations
- `\leq` → `≤`
- `\geq` → `≥`
- `\neq` → `≠`
- `\approx` → `≈`
- `\equiv` → `≡`
- `\sim` → `∼`
- `\propto` → `∝`
- `\ll` → `≪`
- `\gg` → `≫`

### 6. Sets
- `\in` → `∈`
- `\notin` → `∉`
- `\subset` → `⊂`
- `\supset` → `⊃`
- `\subseteq` → `⊆`
- `\supseteq` → `⊇`
- `\cup` → `∪`
- `\cap` → `∩`
- `\emptyset` → `∅`

### 7. Arrows
- `\rightarrow` → `→`
- `\leftarrow` → `←`
- `\Rightarrow` → `⇒`
- `\Leftarrow` → `⇐`
- `\leftrightarrow` → `↔`
- `\Leftrightarrow` → `⇔`

### 8. Calculus
- `\partial` → `∂`
- `\nabla` → `∇`
- `\infty` → `∞`
- `\int` → `∫`
- `\oint` → `∮`
- `\sum` → `∑`
- `\prod` → `∏`

**With limits:**
- `\int_{0}^{\infty}` → `∫₀^∞`
- `\sum_{i=1}^{n}` → `∑ᵢ₌₁ⁿ`

### 9. Logic
- `\land` → `∧`
- `\lor` → `∨`
- `\neg` → `¬`
- `\forall` → `∀`
- `\exists` → `∃`

### 10. Other Symbols
- `\sqrt` → `√`
- `\angle` → `∠`
- `\triangle` → `△`
- `\parallel` → `∥`
- `\perp` → `⊥`
- `\therefore` → `∴`
- `\because` → `∵`

### 11. Fractions
**Common fractions:**
- `\frac{1}{2}` → `½`
- `\frac{1}{3}` → `⅓`
- `\frac{2}{3}` → `⅔`
- `\frac{1}{4}` → `¼`
- `\frac{3}{4}` → `¾`
- `\frac{1}{5}` → `⅕`
- ... (up to ⅞)

**Generic fractions:**
- `\frac{a}{b}` → `a/b`
- `\frac{x^2 + y^2}{z^2}` → `x² + y²/z²`

## 📝 Complex Examples

### Quadratic Formula
```latex
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
```
**Converts to:**
```
x = -b ± √b² - 4ac/2a
```

### Integral
```latex
\int_{0}^{\infty} e^{-x} dx = 1
```
**Converts to:**
```
∫₀^∞ e⁻ˣ dx = 1
```

### Summation
```latex
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
```
**Converts to:**
```
∑ᵢ₌₁ⁿ i = n(n+1)/2
```

### Euler's Identity
```latex
e^{i\pi} + 1 = 0
```
**Converts to:**
```
eⁱᵖⁱ + 1 = 0
```

### Pythagorean Theorem
```latex
a^2 + b^2 = c^2
```
**Converts to:**
```
a² + b² = c²
```

## 🚀 Usage

### In Code
```python
from backend.hwp.hwp_controller import HwpController

hwp = HwpController()
hwp.connect()

# Insert math formula (automatically converts LaTeX to Unicode)
hwp.insert_math_text("x^2 + y^2 = z^2")
# Result: x² + y² = z² appears in HWP document
```

### Through AI
```
User: "이차방정식 x^2 + y^2 = z^2를 입력해줘"
AI: *uses insert_math_text()*
Result: x² + y² = z² appears in document
```

### Direct Conversion
```python
from backend.math_unicode_converter import latex_to_unicode

result = latex_to_unicode("x^2 + y^2 = z^2")
print(result)  # x² + y² = z²
```

## ⚠️ Limitations

### What Works
✅ Superscripts and subscripts
✅ Greek letters
✅ Math operators and symbols
✅ Common fractions
✅ Integrals and sums with limits
✅ Relations and set symbols

### What Doesn't Work (Yet)
❌ Complex fractions (converts to a/b format)
❌ Matrices
❌ Multi-line equations
❌ Aligned equations
❌ Some advanced LaTeX commands

### What's Different from Real Equations
- **Display:** Text-based Unicode, not rendered equation objects
- **Editing:** Can't click to edit like in Word equation editor
- **Formatting:** Limited formatting options
- **Spacing:** May need manual spacing adjustments

## 📊 Comparison

| Feature | LaTeX | Unicode | Rendered Equation |
|---------|-------|---------|-------------------|
| Display | Code | Text symbols | Visual equation |
| Editing | Text editor | Text editor | Click to edit |
| Formatting | Full | Limited | Full |
| Platform | All | All | Windows only |

## 🎯 Best Practices

### ✅ Do
- Use for simple to medium complexity formulas
- Use Unicode for quick math notation
- Combine with regular text

### ❌ Don't
- Use for very complex multi-line equations
- Expect perfect spacing (may need manual adjustment)
- Use for equations that need to be editable as objects

## 📚 Examples by Category

### Algebra
```python
hwp.insert_math_text("x^2 + 2x + 1 = 0")  # x² + 2x + 1 = 0
hwp.insert_math_text("(a + b)^2 = a^2 + 2ab + b^2")  # (a + b)² = a² + 2ab + b²
```

### Calculus
```python
hwp.insert_math_text("\\int_{0}^{\\infty} e^{-x} dx")  # ∫₀^∞ e⁻ˣ dx
hwp.insert_math_text("\\frac{d}{dx} f(x)")  # d/dx f(x)
```

### Physics
```python
hwp.insert_math_text("E = mc^2")  # E = mc²
hwp.insert_math_text("F = ma")  # F = ma
hwp.insert_math_text("\\lambda = \\frac{h}{p}")  # λ = h/p
```

### Chemistry
```python
hwp.insert_math_text("H_2O")  # H₂O
hwp.insert_math_text("CO_2")  # CO₂
hwp.insert_math_text("C_6H_{12}O_6")  # C₆H₁₂O₆
```

## 🔧 Technical Details

### Conversion Order
1. Greek letters (to avoid conflicts)
2. Math symbols
3. Fractions
4. Integrals and sums
5. Subscripts
6. Superscripts

### Character Encoding
- All output is UTF-8 Unicode
- Works with Korean, English, and math symbols
- Compatible with all modern text editors

### Performance
- Fast conversion (regex-based)
- Handles strings up to thousands of characters
- No external dependencies

## 📖 Full List of Supported Symbols

Run the test script to see all supported conversions:

```bash
python3 test_math_converter.py
```

This will show:
- All supported superscripts/subscripts
- All Greek letters
- All math operators
- All relations and set symbols
- Example conversions

---

**Status:** ✅ Complete and Working
**Platform:** macOS + Windows (as fallback)
**Method:** LaTeX → Unicode conversion



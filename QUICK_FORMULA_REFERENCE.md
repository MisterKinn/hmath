# 📐 Quick Formula Code Reference

## 🚀 Quick Start

```python
from backend.hwp.hwp_controller import HwpController

hwp = HwpController()
hwp.connect()

# Insert formula
hwp.insert_math_text("x^2 + y^2 = z^2")
```

## 📝 Most Common Formulas

### Basic Math
```python
# Pythagorean theorem
hwp.insert_math_text("x^2 + y^2 = z^2")

# Einstein's equation
hwp.insert_math_text("E = mc^2")

# Simple equation
hwp.insert_math_text("a + b = c")
```

### Fractions
```python
# Half
hwp.insert_math_text("\\frac{1}{2}")

# Generic fraction
hwp.insert_math_text("\\frac{a}{b}")

# Complex fraction
hwp.insert_math_text("\\frac{x^2 + y^2}{z^2}")
```

### Subscripts & Superscripts
```python
# Water molecule
hwp.insert_math_text("H_2O")

# Carbon dioxide
hwp.insert_math_text("CO_2")

# With both
hwp.insert_math_text("x_1^2 + x_2^2")
```

### Greek Letters
```python
# Basic Greek
hwp.insert_math_text("\\alpha + \\beta = \\gamma")

# Pi
hwp.insert_math_text("\\pi r^2")

# Theta
hwp.insert_math_text("\\theta = 90^\\circ")
```

### Calculus
```python
# Integral
hwp.insert_math_text("\\int_{0}^{\\infty} e^{-x} dx")

# Sum
hwp.insert_math_text("\\sum_{i=1}^{n} x_i")

# Derivative
hwp.insert_math_text("\\frac{d}{dx} f(x)")
```

### Physics
```python
# Newton's law
hwp.insert_math_text("F = ma")

# Kinetic energy
hwp.insert_math_text("E_k = \\frac{1}{2}mv^2")

# Wave equation
hwp.insert_math_text("\\lambda = \\frac{h}{p}")
```

### Chemistry
```python
# Water
hwp.insert_math_text("H_2O")

# Glucose
hwp.insert_math_text("C_6H_{12}O_6")

# Sulfuric acid
hwp.insert_math_text("H_2SO_4")
```

## 🎯 Complete Examples

### Example 1: Simple Math
```python
from backend.hwp.hwp_controller import HwpController

hwp = HwpController()
hwp.connect()

hwp.insert_math_text("x^2 + y^2 = z^2")
hwp.insert_paragraph_break()
hwp.insert_text("This is the Pythagorean theorem.")
```

### Example 2: Multiple Formulas
```python
formulas = [
    "E = mc^2",
    "F = ma",
    "x^2 + y^2 = z^2",
]

for formula in formulas:
    hwp.insert_math_text(formula)
    hwp.insert_paragraph_break()
```

### Example 3: Complex Formula
```python
# Quadratic formula
hwp.insert_math_text("x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}")
```

### Example 4: With Text
```python
hwp.insert_text("The equation is: ")
hwp.insert_math_text("E = mc^2")
hwp.insert_text(" which is famous!")
```

## 📚 LaTeX Syntax Reference

### Superscripts
- `x^2` → x²
- `x^{n+1}` → xⁿ⁺¹

### Subscripts
- `x_1` → x₁
- `x_{i+1}` → xᵢ₊₁

### Fractions
- `\frac{a}{b}` → a/b or ½ (if common fraction)

### Greek Letters
- `\alpha` → α
- `\beta` → β
- `\gamma` → γ
- `\pi` → π
- `\theta` → θ
- `\lambda` → λ
- `\Delta` → Δ
- `\Omega` → Ω

### Math Operators
- `\int` → ∫
- `\sum` → ∑
- `\prod` → ∏
- `\infty` → ∞
- `\leq` → ≤
- `\geq` → ≥
- `\neq` → ≠
- `\pm` → ±
- `\times` → ×
- `\div` → ÷

### Calculus
- `\int_{a}^{b}` → ∫ₐᵇ
- `\sum_{i=1}^{n}` → ∑ᵢ₌₁ⁿ
- `\frac{d}{dx}` → d/dx

## 💡 Tips

1. **Use double backslashes** in Python strings:
   ```python
   "\\frac{a}{b}"  # Correct
   "\frac{a}{b}"   # Wrong (single backslash)
   ```

2. **Or use raw strings:**
   ```python
   r"\frac{a}{b}"  # Also correct
   ```

3. **Combine with text:**
   ```python
   hwp.insert_text("The formula is: ")
   hwp.insert_math_text("x^2 + y^2 = z^2")
   ```

4. **Add line breaks:**
   ```python
   hwp.insert_math_text("x^2 + y^2 = z^2")
   hwp.insert_paragraph_break()
   ```

## 🔧 Formula Editor (Advanced)

For actual equation objects (not just text), try:

```python
# Formula Editor syntax (needs testing)
hwp.insert_equation_via_editor("a over b")
hwp.insert_equation_via_editor("int from 0 to infinity")
hwp.insert_equation_via_editor("sum from i=1 to n")
```

**Note:** Formula Editor syntax needs to be tested. See `FORMULA_EDITOR_MACOS.md` for details.

## 📖 More Examples

See `formula_examples.py` for comprehensive examples:
```bash
python3 formula_examples.py
```

---

**Quick Reference:** Copy and paste these examples into your code!



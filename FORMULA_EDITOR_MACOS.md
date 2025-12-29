# 📐 한글 수식 편집기 (Formula Editor) on macOS

## Overview

Hancom Office HWP on macOS includes a **수식 편집기 (Formula Editor)** that can create actual equation objects (not just text). This is much better than Unicode text!

## ✅ What This Means

**Before (Unicode text):**
- `x² + y² = z²` ← Just text, not a real equation

**After (Formula Editor):**
- Actual equation object that can be edited, formatted, and looks professional

## 🔍 Finding the Formula Editor

### Method 1: Menu
1. Open Hancom Office HWP
2. Click **삽입 (Insert)** menu
3. Click **수식 (Equation)** or **수식 편집기 (Formula Editor)**

### Method 2: Keyboard Shortcut
Common shortcuts (may vary):
- `⌘+Option+E`
- `⌘+E`
- `⌘+Shift+E`

**To find the exact shortcut:**
1. Open 한글
2. Go to **도구 (Tools)** → **사용자 설정 (Preferences)**
3. Look for **키보드 단축키 (Keyboard Shortcuts)**
4. Search for "수식" or "Equation"

## 📝 Formula Editor Syntax

The formula editor uses a simple English-like syntax. Examples:

### Fractions
```
a over b          → a/b (fraction)
```

### Superscripts
```
x^2               → x²
x^(n+1)           → xⁿ⁺¹
```

### Subscripts
```
x_1               → x₁
x_(i+1)           → xᵢ₊₁
```

### Integrals
```
int from 0 to infinity
int from a to b
int
```

### Summations
```
sum from i=1 to n
sum from 1 to 10
sum
```

### Greek Letters
```
alpha, beta, gamma, pi, theta, etc.
```

### Operators
```
infinity          → ∞
×, /, +, -, =, <, >, <=, >=
```

## 🚀 Usage in Code

### Basic Usage
```python
from backend.hwp.hwp_controller import HwpController

hwp = HwpController()
hwp.connect()

# Insert equation using formula editor
hwp.insert_equation_via_editor("a over b")
# Creates actual fraction equation object
```

### Examples
```python
# Fraction
hwp.insert_equation_via_editor("x^2 + y^2 over z^2")

# Integral
hwp.insert_equation_via_editor("int from 0 to infinity e^-x dx")

# Sum
hwp.insert_equation_via_editor("sum from i=1 to n x_i")

# Complex
hwp.insert_equation_via_editor("(a + b)^2 = a^2 + 2ab + b^2")
```

## 🔧 Testing

### Step 1: Find the Right Shortcut
```bash
python3 test_formula_editor.py
```

This will test different methods to open the editor. **Note which one works!**

### Step 2: Test Formula Syntax
1. Open formula editor manually
2. Type in the input bar: `a over b`
3. Press Enter
4. See if it creates a fraction

### Step 3: Test Automation
```python
from backend.hwp.hwp_controller import HwpController

hwp = HwpController()
hwp.connect()
hwp.insert_equation_via_editor("a over b")
```

## ⚠️ Current Status

### ✅ What's Implemented
- Method to open formula editor
- Method to type formula text
- LaTeX to 한글 formula syntax converter (basic)

### 🔧 What Needs Testing
- **Exact keyboard shortcut** to open editor
- **Exact menu path** (Korean vs English)
- **Formula syntax** - what the editor actually accepts
- **Input bar focus** - how to focus on the input field

### 📋 To Do
1. Run `test_formula_editor.py` to find the right shortcut
2. Test formula syntax in the editor manually
3. Update `insert_equation_via_editor()` with correct shortcut
4. Refine LaTeX converter based on actual syntax

## 🎯 Next Steps

### For You (User)
1. **Run the test script:**
   ```bash
   python3 test_formula_editor.py
   ```

2. **Note which method opens the editor:**
   - Menu path?
   - Keyboard shortcut?

3. **Test formula syntax:**
   - Open editor manually
   - Try: `a over b`
   - Try: `x^2 + y^2`
   - Try: `int from 0 to infinity`
   - See what works!

4. **Report back:**
   - What shortcut/menu works?
   - What formula syntax works?
   - Any errors?

### For Me (Developer)
Once you tell me:
- The correct shortcut/menu path
- The exact formula syntax

I'll update the code to:
- Use the correct method to open editor
- Convert LaTeX to the right syntax
- Make it work automatically!

## 📚 Formula Editor Features

Based on the screenshot, the editor has:

### Toolbar Categories
- **기호 (Symbol)** - Math symbols
- **장식 (Decoration)** - Decorations
- **연산 (Operation)** - Operations
- **논리 (Logic)** - Logic symbols
- **행렬 (Matrix)** - Matrices
- **일반수식 (General Formula)** - General formulas

### Input Bar
- Bottom of editor window
- Accepts text commands
- Shows: `a over b` (for fractions)

### Features
- Font selection (HancomEQN)
- Font size
- Color picker
- Zoom (200%)
- Script window option

## 💡 Tips

1. **Start Simple:** Test with `a over b` first
2. **Check Syntax:** Look at the input bar to see how formulas are represented
3. **Use Menu:** If keyboard shortcut doesn't work, use menu
4. **Document:** Note what works and what doesn't

## 🔗 Related Files

- `backend/hwp/hwp_macos.py` - `insert_equation_via_editor()` method
- `backend/hwp/hwp_controller.py` - Controller wrapper
- `backend/latex_to_hwp_formula.py` - LaTeX to 한글 syntax converter
- `test_formula_editor.py` - Test script to find correct method

---

**Status:** 🚧 In Development - Needs Testing
**Help Needed:** Find correct shortcut/menu and formula syntax!



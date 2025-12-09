# Design Recommendations for HMATH AI

## ✅ Changes Implemented

### 1. **Modern Clean Layout**
- Increased window size to 680x780 for better content visibility
- Centered all primary actions and title
- Larger, bolder title (48px) with proper spacing
- Added descriptive subtitle matching your reference design

### 2. **Action Buttons**
- Added "💡 How to use" button with helpful guide
- Added "</> Latex Code" button with equation examples
- Both buttons centered with consistent styling
- White background with subtle borders

### 3. **Improved Color Scheme**
- Changed from pure white (#ffffff) to soft gray (#fafafa) background
- Better contrast for readability
- Blue accent color (#4a90e2) instead of darker blue
- Softer borders (#e0e0e0) for modern look

### 4. **Enhanced Typography**
- Larger title font (48px, was 22px)
- Better font stack with SF Pro Display fallback
- Monospace font for code editor (Menlo/Monaco)
- Improved line-height and letter-spacing

### 5. **Better Visual Hierarchy**
- Header → Action Buttons → Editor → Log Panel
- More generous spacing (32px between sections)
- Larger padding around content (48px horizontal)

---

## 🎨 Additional Design Recommendations

### 1. **File Upload Feature** (Like Your Screenshot)
Add drag-and-drop or file picker for PDFs:
```python
# In _build_editor(), add before action buttons:
upload_area = QFrame()
upload_area.setObjectName("upload-area")
# Style with dashed border for drag-drop zone
```

**Benefits:**
- Matches the "Upload a PDF" concept from your screenshot
- Makes it easier to process documents
- More intuitive for end users

### 2. **Dark Mode Support**
Add theme toggle:
```python
def _toggle_dark_mode(self):
    if self.dark_mode:
        # Apply dark stylesheet
        self.setStyleSheet(DARK_THEME)
    else:
        self.setStyleSheet(LIGHT_THEME)
```

**Benefits:**
- Reduces eye strain for long sessions
- Modern apps offer this option
- Easy to implement with PySide6

### 3. **Status Indicators**
Add visual feedback:
- 🟢 Green dot when HWP is connected
- 🔴 Red dot when disconnected
- 🟡 Yellow during script execution

**Implementation:**
```python
self.status_indicator = QLabel("●")
self.status_indicator.setObjectName("status-connected")
# Add to header or sidebar
```

### 4. **Recent Scripts / Templates**
Add a dropdown or sidebar with:
- Recently run scripts
- Pre-made templates (Math equations, Tables, etc.)
- Quick access to common operations

**Benefits:**
- Saves time for repeated tasks
- Helps users discover features
- Improves productivity

### 5. **Syntax Highlighting**
Install and use `QScintilla` or `Pygments`:
```python
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

self.script_edit = QsciScintilla()
lexer = QsciLexerPython()
self.script_edit.setLexer(lexer)
```

**Benefits:**
- Much easier to read code
- Helps catch syntax errors
- Professional code editor feel

### 6. **Progress Bar**
Add for long-running operations:
```python
self.progress_bar = QProgressBar()
self.progress_bar.setObjectName("progress-bar")
# Show during PDF processing or batch operations
```

### 7. **Icon Set**
Use consistent icon library:
- **Recommended:** Material Design Icons or Feather Icons
- Replace emoji icons (💡, </>) with proper SVG icons
- Better cross-platform appearance

**Add to project:**
```bash
pip install qtawesome
```

```python
import qtawesome as qta
icon = qta.icon('fa5s.lightbulb')
self.howto_button.setIcon(icon)
```

### 8. **Keyboard Shortcuts**
Add power-user features:
```python
# In __init__:
run_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
run_shortcut.activated.connect(self._handle_run_clicked)

save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
save_shortcut.activated.connect(self._save_script)
```

**Common shortcuts:**
- `Ctrl+Enter` - Run script
- `Ctrl+S` - Save script
- `Ctrl+O` - Open script
- `Ctrl+/` - Comment/uncomment line

### 9. **Error Highlighting**
When script fails, highlight the error line:
```python
def _highlight_error_line(self, line_number: int):
    cursor = self.script_edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    cursor.movePosition(
        QTextCursor.MoveOperation.Down,
        QTextCursor.MoveMode.MoveAnchor,
        line_number - 1
    )
    # Highlight the line
```

### 10. **Export/Import Settings**
Allow users to:
- Export their favorite scripts
- Share templates with colleagues
- Import community scripts

### 11. **Tooltips Everywhere**
Add helpful tooltips to all UI elements:
```python
self.run_button.setToolTip("Execute the Python script (Ctrl+Enter)")
self.script_edit.setToolTip("Write Python code using HWP automation functions")
```

### 12. **Responsive Design**
Make window resizable with constraints:
```python
self.setMinimumSize(600, 700)
self.setMaximumSize(1200, 1400)
```

### 13. **Loading Animations**
Add spinner during processing:
```python
from PySide6.QtCore import QTimer

def _show_loading(self):
    self.loading_label = QLabel("⏳ Processing...")
    # Animate with QTimer
```

### 14. **Settings Panel**
Add a settings dialog:
- Font size preferences
- Default HWP connection options
- OCR language selection
- Tesseract/Poppler paths

### 15. **Console Output Styling**
Improve log panel:
- Color-code messages (info=blue, error=red, success=green)
- Add timestamps
- Make it collapsible

**Example:**
```python
def _append_log(self, text: str, level: str = "info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = {"info": "#4a90e2", "error": "#e74c3c", "success": "#27ae60"}[level]
    html = f'<span style="color: {color}">[{timestamp}] {text}</span>'
    self.log_output.append(html)
```

---

## 🎯 Priority Recommendations

**High Priority (Implement First):**
1. ✅ Modern clean design (Already done!)
2. File upload/drag-drop feature
3. Syntax highlighting for code editor
4. Status indicators for HWP connection
5. Keyboard shortcuts

**Medium Priority:**
6. Dark mode toggle
7. Recent scripts/templates
8. Better error highlighting
9. Loading animations
10. Icon set integration

**Low Priority (Nice to Have):**
11. Export/import settings
12. Advanced settings panel
13. Console output color coding
14. Progress bars for batch operations
15. Responsive window sizing

---

## 📐 Design Principles to Follow

1. **Consistency**: Use the same colors, fonts, spacing throughout
2. **Clarity**: Every element should have an obvious purpose
3. **Feedback**: Always show the user what's happening
4. **Simplicity**: Don't overwhelm with too many options at once
5. **Accessibility**: Ensure good contrast and readable text sizes

---

## 🎨 Recommended Color Palette

**Current Implementation:**
- Background: `#fafafa` (soft gray)
- Cards: `#ffffff` (white)
- Borders: `#e0e0e0` (light gray)
- Primary: `#4a90e2` (blue)
- Text: `#2c2c2c` (dark gray)
- Muted text: `#666` (medium gray)

**Suggested Additions:**
- Success: `#27ae60` (green)
- Warning: `#f39c12` (orange)
- Error: `#e74c3c` (red)
- Info: `#3498db` (light blue)

---

## 🚀 Next Steps

1. **Test the new design** - Run `python -m gui.app` to see changes
2. **Get user feedback** - Show to potential users
3. **Implement file upload** - Start with drag-drop for PDFs
4. **Add syntax highlighting** - Big UX improvement
5. **Create more templates** - Help users get started quickly

---

## 📝 Notes

The new design is inspired by modern web applications and your reference screenshot. It emphasizes:
- **Clarity over decoration**
- **Function over form** (but still looks great!)
- **User guidance** (How to use, LaTeX helper)
- **Professional appearance**

The design scales well and can accommodate future features without looking cluttered.

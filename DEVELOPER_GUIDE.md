# Developer Guide: Line-by-Line Explanation

This guide explains the project code in detail for Python beginners.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [GUI Module (`gui/main_window.py`)](#gui-module)
3. [Backend HWP Controller (`backend/hwp/hwp_controller.py`)](#backend-hwp-controller)
4. [Script Runner (`backend/hwp/script_runner.py`)](#script-runner)
5. [Equation Utilities (`backend/hwp/hwp_equation_utils.py`)](#equation-utilities)
6. [LaTeX Converter (`backend/equations/latex_to_hwpeqn.py`)](#latex-converter)
7. [OCR Module (`backend/ocr/pix2text_client.py`)](#ocr-module)
8. [Configuration (`backend/config.py`)](#configuration)
9. [How to Extend the Project](#how-to-extend)

---

## Project Overview

**What this app does:**
- Provides a GUI where users can write Python scripts
- Scripts automate Hancom Hangul (HWP) document editing
- Can insert text, equations (LaTeX), and images into HWP documents
- Can OCR PDFs and convert them to HWP format

**Architecture:**
```
User writes Python in GUI → Script Runner executes it → HWP Controller 
                                                          ↓
                                                   Hancom Hangul (Windows)
```

---

## GUI Module (`gui/main_window.py`)

### Imports Section (Lines 1-23)

```python
"""AMEX AI script console."""
```
**Docstring**: A brief description of what this file does (creates the console window).

```python
from __future__ import annotations
```
**Purpose**: Allows using class names as type hints before they're defined. Modern Python feature for better code completion.

```python
from pathlib import Path
```
**Purpose**: `Path` is a modern way to handle file paths. Better than old string-based paths.
**Example**: `Path("/home/user/file.txt")` instead of `"/home/user/file.txt"`

```python
from typing import Optional
```
**Purpose**: For type hints. `Optional[str]` means "either a string or None".
**Example**: `name: Optional[str] = None` means name can be a string or None.

```python
from PySide6.QtCore import Qt, Signal, QThread, QObject, QSize
```
**What is PySide6?**: Python bindings for Qt, a powerful GUI framework.
**Breakdown**:
- `Qt`: Contains constants (like `Qt.AlignCenter` for centering widgets)
- `Signal`: Used to communicate between objects (like events)
- `QThread`: For running tasks in background without freezing the UI
- `QObject`: Base class for all Qt objects
- `QSize`: Represents width/height dimensions

```python
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPixmap
```
**Purpose**: GUI visual elements
- `QColor`: Defines colors (RGB)
- `QFont`: Text font settings (size, family, weight)
- `QFontDatabase`: Manages available fonts, loads custom fonts
- `QIcon`: Application/window icons
- `QPainter`: Low-level drawing
- `QPixmap`: Image display

```python
from PySide6.QtWidgets import (
    QApplication,      # Main app instance
    QFrame,           # Container widget with borders
    QHBoxLayout,      # Horizontal layout (left-to-right)
    QLabel,           # Text display (non-editable)
    QMainWindow,      # Main window with menubar/statusbar support
    QMessageBox,      # Pop-up dialog boxes
    QPushButton,      # Clickable button
    QTextEdit,        # Multi-line text editor
    QToolButton,      # Button for toolbars
    QVBoxLayout,      # Vertical layout (top-to-bottom)
    QWidget,          # Base widget class
)
```

```python
from backend.hwp.hwp_controller import HwpController, HwpControllerError
```
**Purpose**: Imports our custom class that controls Hancom Hangul.

```python
from backend.hwp.script_runner import HwpScriptRunner
```
**Purpose**: Imports the class that executes user Python scripts safely.

### Constants (Lines 25-30)

```python
DEFAULT_SCRIPT = """
# 예시: 텍스트 + 수식을 한 번에 삽입
insert_text("AMEX AI가 자동으로 한글 문단을 입력합니다.\\r")
insert_text("Einstein 질량-에너지 등가식은 아래와 같습니다.\\r")
insert_hwpeqn("E = m c ^{2}", font_size_pt=12.0, eq_font_name="HYhwpEQ")
"""
```
**Purpose**: Default example script shown when the app starts.
**Note**: `\\r` is a carriage return (like pressing Enter in HWP).

### ScriptWorker Class (Lines 33-52)

```python
class ScriptWorker(QThread):
```
**What is a class?**: A blueprint for creating objects. Like a recipe.
**QThread**: Runs code in a separate thread (background) so UI doesn't freeze.

```python
    log_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()
```
**Signals**: Like event broadcasters. When something happens, they notify listeners.
- `log_signal`: Emits log messages (string)
- `error_signal`: Emits error messages (string)
- `finished_signal`: Emits when script finishes (no data)

```python
    def __init__(self, script: str, parent: QObject | None = None) -> None:
```
**`__init__`**: Constructor - runs when you create a new object.
**Parameters**:
- `self`: Reference to the object itself (automatic in Python)
- `script: str`: The Python code to run (must be a string)
- `parent: QObject | None`: Optional parent object (for Qt memory management)
- `-> None`: Function returns nothing

```python
        super().__init__(parent)
```
**Purpose**: Calls the parent class's constructor. Required for proper initialization.

```python
        self._script = script
```
**Purpose**: Stores the script in an instance variable (member variable).
**Naming**: `_script` with underscore means "private" by convention.

```python
    def run(self) -> None:  # type: ignore[override]
```
**Purpose**: The main function that runs when thread starts.
**`# type: ignore[override]`**: Tells type checker to ignore a warning.

```python
        try:
            controller = HwpController()
            controller.connect()
```
**Try-except block**: Handles errors gracefully.
**These lines**: Create HWP controller and connect to Hancom Hangul.

```python
            runner = HwpScriptRunner(controller)
            runner.run(self._script, self.log_signal.emit)
```
**Purpose**: Create script runner and execute the user's script.
**`self.log_signal.emit`**: Pass the log function so script can send messages to UI.

```python
            self.finished_signal.emit()
```
**Purpose**: Notify UI that script finished successfully.

```python
        except HwpControllerError as exc:
            self.error_signal.emit(f"HWP 연결 실패: {exc}")
```
**Purpose**: Catch HWP connection errors specifically.
**f-string**: `f"text {variable}"` embeds variables in strings.

```python
        except Exception as exc:
            self.error_signal.emit(str(exc))
```
**Purpose**: Catch any other errors and send to UI.

### MainWindow Class (Lines 55-298)

```python
class MainWindow(QMainWindow):
```
**Purpose**: The main application window.

```python
    def __init__(self) -> None:
        super().__init__()
```
**Purpose**: Constructor for the window.

```python
        self.setWindowTitle("AMEX AI • Script Runner")
        self.resize(520, 820)
```
**Purpose**: Set window title and size (width=520px, height=820px).

```python
        self._worker: Optional[ScriptWorker] = None
```
**Purpose**: Store reference to the background worker thread.
**Type hint**: Can be `ScriptWorker` or `None`.

```python
        self._build_ui()
        self._apply_styles()
```
**Purpose**: Call methods to create UI elements and apply CSS-like styling.

#### `_build_ui` Method (Lines 64-84)

```python
    def _build_ui(self) -> None:
        central = QWidget(self)
```
**Purpose**: Create the central widget (main container for all UI elements).

```python
        layout = QHBoxLayout(central)
```
**HBoxLayout**: Arranges children horizontally (left to right).

```python
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
```
**Purpose**: Remove padding and spacing (for edge-to-edge layout).

```python
        main_area = QWidget()
        main_area.setObjectName("main-area")
```
**setObjectName**: Assigns a name for CSS-like styling later.

```python
        main_column = QVBoxLayout(main_area)
```
**VBoxLayout**: Arranges children vertically (top to bottom).

```python
        main_column.setContentsMargins(32, 24, 24, 24)
```
**Purpose**: Set padding (left=32px, top=24px, right=24px, bottom=24px).

```python
        main_column.setSpacing(16)
```
**Purpose**: 16px gap between child widgets.

```python
        main_column.addWidget(self._build_header())
```
**Purpose**: Add header widget to the top.

```python
        main_column.addWidget(self._build_log_panel(), 1)
```
**Purpose**: Add log panel with stretch factor of 1 (takes available space).

```python
        main_column.addWidget(self._build_editor())
```
**Purpose**: Add script editor at the bottom.

```python
        layout.addWidget(main_area, 1)
        layout.addWidget(self._build_sidebar(), 0)
```
**Purpose**: Add main area (stretch factor 1) and sidebar (no stretch).

```python
        self.setCentralWidget(central)
```
**Purpose**: Set this widget as the main window's central widget.

#### `_build_header` Method (Lines 86-96)

```python
    def _build_header(self) -> QWidget:
        frame = QFrame()
        lyt = QVBoxLayout(frame)
        lyt.setSpacing(4)
```
**Purpose**: Create a container for the header with 4px spacing.

```python
        title = QLabel("AMEX AI")
        title.setObjectName("app-title")
```
**Purpose**: Create title label with name for styling.

```python
        lyt.addWidget(title, alignment=Qt.AlignCenter)
```
**Purpose**: Add title and center it horizontally.

```python
        return frame
```
**Purpose**: Return the completed header widget.

#### `_build_editor` Method (Lines 98-123)

```python
    def _build_editor(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("editor-card")
```
**Purpose**: Create card-style container for the code editor.

```python
        self.script_edit = QTextEdit()
        self.script_edit.setObjectName("script-editor")
```
**Purpose**: Create multi-line text editor for Python code.
**Note**: `self.script_edit` means it's accessible from other methods.

```python
        self.script_edit.setPlaceholderText("예) insert_text('안녕하세요')")
```
**Purpose**: Gray hint text shown when editor is empty.

```python
        self.script_edit.setPlainText(DEFAULT_SCRIPT.strip())
```
**Purpose**: Pre-fill with example script.
**`.strip()`**: Remove leading/trailing whitespace.

```python
        self.script_edit.setMinimumHeight(320)
```
**Purpose**: Editor must be at least 320px tall.

```python
        self.run_button = QPushButton("실행")
        self.run_button.setObjectName("primary-action")
        self.run_button.clicked.connect(self._handle_run_clicked)
```
**Purpose**: Create "Run" button.
**`.clicked.connect()`**: When button is clicked, call `_handle_run_clicked` method.

```python
        run_row = QHBoxLayout()
        run_row.setContentsMargins(0, 0, 0, 0)
        run_row.addStretch()
        run_row.addWidget(self.run_button)
```
**Purpose**: Create horizontal layout with button aligned to the right.
**`addStretch()`**: Adds flexible space (pushes button right).

#### `_build_sidebar` Method (Lines 125-141)

```python
        self.always_on_top_btn = QToolButton()
        self.always_on_top_btn.setObjectName("pin-button")
        self.always_on_top_btn.setCheckable(True)
```
**Purpose**: Create toggle button (can be checked/unchecked).

```python
        self.always_on_top_btn.setToolTip("항상 위에 고정")
```
**Purpose**: Tooltip shown when hovering over button.

```python
        self.always_on_top_btn.setAutoRaise(True)
```
**Purpose**: Button only shows border when hovered.

```python
        self._set_pin_glyph(False)
```
**Purpose**: Set the icon for the button (pin icon).

```python
        self.always_on_top_btn.toggled.connect(self._handle_pin_toggled)
```
**Purpose**: When button is toggled, call `_handle_pin_toggled` method.

#### `_build_log_panel` Method (Lines 143-158)

```python
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
```
**Purpose**: Create text area that users can't edit (read-only).

```python
        self.log_output.setMinimumHeight(220)
```
**Purpose**: At least 220px tall.

```python
        self.log_output.setPlaceholderText("스크립트 결과가 여기에 표시됩니다.")
```
**Purpose**: Placeholder text when empty.

#### `_apply_styles` Method (Lines 160-232)

```python
    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #ffffff;
                color: #1b1d29;
                ...
            }
            """
        )
```
**Purpose**: Apply CSS-like styling to all widgets.
**Syntax**: Similar to CSS - `selector { property: value; }`

**Key style rules**:
- `QWidget`: Default styles for all widgets
- `#object-name`: Styles for widgets with specific object names
- `QWidget#object-name`: Combines type and name selectors
- `border-radius: 18px`: Rounded corners
- `padding: 10px`: Inner spacing
- `background-color: #ffffff`: White background (hex color)

#### `_handle_run_clicked` Method (Lines 234-245)

```python
    def _handle_run_clicked(self) -> None:
```
**Purpose**: Called when user clicks "Run" button.

```python
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "진행 중", "이미 스크립트를 실행 중입니다.")
            return
```
**Purpose**: Prevent running multiple scripts at once.
**`QMessageBox.information`**: Shows info dialog.

```python
        script = self.script_edit.toPlainText()
```
**Purpose**: Get the text from the code editor.

```python
        self._worker = ScriptWorker(script, self)
```
**Purpose**: Create new background worker with the script.

```python
        self._worker.log_signal.connect(self._append_log)
        self._worker.error_signal.connect(self._handle_error)
        self._worker.finished_signal.connect(self._handle_finished)
```
**Purpose**: Connect worker's signals to our methods.
**How it works**: When worker emits signal → our method is called automatically.

```python
        self.run_button.setEnabled(False)
```
**Purpose**: Disable button while script runs (prevent double-click).

```python
        self._append_log("=== 실행 요청 ===")
        self._worker.start()
```
**Purpose**: Log start message and start the worker thread.

#### `_handle_error` Method (Lines 247-250)

```python
    def _handle_error(self, message: str) -> None:
        self._append_log(f"[오류] {message}")
        QMessageBox.critical(self, "실행 오류", message)
        self.run_button.setEnabled(True)
```
**Purpose**: Show error message in log and popup, re-enable button.

#### `_handle_finished` Method (Lines 252-254)

```python
    def _handle_finished(self) -> None:
        self._append_log("=== 실행 완료 ===")
        self.run_button.setEnabled(True)
```
**Purpose**: Log completion message and re-enable button.

#### `_toggle_always_on_top` Method (Lines 256-258)

```python
    def _toggle_always_on_top(self, checked: bool) -> None:
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()
```
**Purpose**: Make window stay on top of all other windows.
**`.show()`**: Required to apply window flag changes.

#### `_append_log` Method (Lines 260-261)

```python
    def _append_log(self, text: str) -> None:
        self.log_output.append(text)
```
**Purpose**: Add text to the log panel.

#### `_handle_pin_toggled` Method (Lines 263-265)

```python
    def _handle_pin_toggled(self, checked: bool) -> None:
        self._set_pin_glyph(checked)
        self._toggle_always_on_top(checked)
```
**Purpose**: Update pin icon and window always-on-top state.

#### `_set_pin_glyph` Method (Lines 267-273)

```python
    def _set_pin_glyph(self, active: bool) -> None:
        font_name = _ensure_material_icon_font()
        font = QFont(font_name)
        font.setPointSize(28)
        self.always_on_top_btn.setFont(font)
        glyph = "\ue25c" if active else "\ue25d"
        self.always_on_top_btn.setText(glyph)
```
**Purpose**: Set pin icon using Material Icons font.
**Ternary operator**: `value_if_true if condition else value_if_false`
**Unicode**: `\ue25c` is a special character code for pin icon.

### Standalone Functions (Lines 276-318)

```python
def run_app() -> None:
    app = QApplication.instance() or QApplication([])
```
**Purpose**: Get existing Qt app or create new one.
**`or` operator**: If left side is None/False, use right side.

```python
    _apply_app_font(app)
    window = MainWindow()
    window.show()
    app.exec()
```
**Purpose**: Apply custom font, create window, show it, start event loop.
**`app.exec()`**: Starts the application (blocks until window closes).

```python
def _apply_app_font(app: QApplication) -> None:
    font_db = QFontDatabase()
    if "Pretendard" not in font_db.families():
        font_path = (
            Path(__file__).resolve().parents[1] / "resources" / "fonts" / "PretendardVariable.ttf"
        )
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))
```
**Purpose**: Load custom "Pretendard" font if not already loaded.
**`Path(__file__)`**: Path to current Python file.
**`.resolve()`**: Get absolute path.
**`.parents[1]`**: Go up one directory.

```python
    base_font = QFont("Pretendard")
    if base_font.family() != "Pretendard":
        base_font = app.font()
        base_font.setFamily("Pretendard")
    base_font.setPointSize(11)
    app.setFont(base_font)
```
**Purpose**: Set "Pretendard" as default font (11pt size).

```python
def _ensure_material_icon_font() -> str:
    font_db = QFontDatabase()
    target_name = "Material Icons Round"
    if target_name in font_db.families():
        return target_name
```
**Purpose**: Check if Material Icons font is already loaded.

```python
    font_path = (
        Path(__file__).resolve().parents[1] / "resources" / "fonts" / "MaterialSymbolsRounded.ttf"
    )
    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return families[0]
```
**Purpose**: Load Material Icons font file and return its name.

```python
    return QApplication.instance().font().family()
```
**Purpose**: Fallback to default font if Material Icons not found.

---

## Backend HWP Controller (`backend/hwp/hwp_controller.py`)

### Purpose
Provides a safe, simple interface to control Hancom Hangul (HWP) via COM automation.

### Key Classes

#### HwpConnectionOptions (Lines 34-43)
```python
@dataclass(slots=True)
class HwpConnectionOptions:
    visible: bool = True
    new_instance: bool = False
    register_module: bool = True
```
**`@dataclass`**: Decorator that auto-generates `__init__`, `__repr__`, etc.
**`slots=True`**: Memory optimization (reduces memory per instance).
**Fields**:
- `visible`: Whether HWP window should be visible
- `new_instance`: Create new HWP process or attach to existing
- `register_module`: Auto-register COM security module

#### HwpController Class (Lines 46-189)

**Purpose**: Main class for HWP automation.

```python
def __init__(self, options: Optional[HwpConnectionOptions] = None) -> None:
    self._options = options or HwpConnectionOptions()
    self._hwp: Optional["pyhwpx.Hwp"] = None
```
**`options or HwpConnectionOptions()`**: Use provided options or create default.
**`Optional["pyhwpx.Hwp"]`**: Type hint with string to avoid import errors.

```python
def connect(self) -> None:
    if pyhwpx is None:
        raise HwpNotAvailableError(...)
```
**Purpose**: Connect to Hancom Hangul. Raises error if pyhwpx not available.

```python
    if self._hwp is not None:
        return
```
**Purpose**: Don't reconnect if already connected.

```python
    try:
        self._hwp = pyhwpx.Hwp(
            new=self._options.new_instance,
            visible=self._options.visible,
            register_module=self._options.register_module,
        )
```
**Purpose**: Create connection to HWP using pyhwpx library.

```python
def insert_text(self, text: str) -> None:
    if not text:
        return
    hwp = self._ensure_connected()
    normalized = text.replace("\n", "\r\n")
    hwp.insert_text(normalized)
```
**Purpose**: Insert text at cursor position.
**`.replace("\n", "\r\n")`**: Convert Unix newlines to Windows format.

```python
def insert_paragraph_break(self) -> None:
    hwp = self._ensure_connected()
    hwp.BreakPara()
```
**Purpose**: Insert paragraph break (like pressing Enter).

```python
def insert_equation(self, hwpeqn: str, *, font_size_pt: float = 18.0, ...) -> None:
```
**`*` after `hwpeqn`**: All parameters after must be specified by name (keyword-only).
**Purpose**: Insert mathematical equation in HwpEqn format.

---

## Script Runner (`backend/hwp/script_runner.py`)

### Purpose
Executes user-provided Python code safely with access to HWP automation functions.

### Key Components

```python
SAFE_BUILTINS: Dict[str, object] = {
    "range": range,
    "len": len,
    "min": min,
    ...
}
```
**Purpose**: Whitelist of allowed built-in functions.
**Security**: Prevents users from accessing dangerous functions like `open()`, `eval()`, etc.

```python
class HwpScriptRunner:
    def __init__(self, controller: HwpController) -> None:
        self._controller = controller
```
**Purpose**: Store reference to HWP controller.

```python
def run(self, script: str, log: LogFn | None = None) -> None:
    cleaned = textwrap.dedent(script or "").strip()
```
**`textwrap.dedent()`**: Remove common leading whitespace from all lines.
**Purpose**: Clean up indentation from user script.

```python
    hwp_obj = self._controller._ensure_connected()
```
**Purpose**: Get the actual pyhwpx.Hwp object.

```python
    def _insert_equation(expr: str, *, ..., assume_hwpeqn: bool = False) -> None:
        text = (expr or "").strip()
        if not text:
            return
        hwpeqn = text if assume_hwpeqn else latex_to_hwpeqn(text)
        self._controller.insert_equation(hwpeqn, ...)
```
**Purpose**: Helper function exposed to user scripts.
**Logic**: If `assume_hwpeqn=True`, use text as-is; otherwise convert from LaTeX.

```python
    env: Dict[str, object] = {
        "__builtins__": SAFE_BUILTINS,
        "hwp": hwp_obj,
        "controller": self._controller,
        "insert_text": self._controller.insert_text,
        ...
    }
```
**Purpose**: Create execution environment (namespace) for user script.
**Keys**: Function names available to user.
**Values**: Actual Python objects/functions.

```python
    try:
        exec(cleaned, env, {})
```
**`exec()`**: Execute Python code from string.
**Parameters**: `exec(code, globals, locals)`

---

## Equation Utilities (`backend/hwp/hwp_equation_utils.py`)

### Purpose
Low-level COM automation for inserting equations with precise formatting.

### Key Components

```python
@dataclass(slots=True)
class EquationOptions:
    font_size_pt: float = 18.0
    eq_font_name: str = "HancomEQN"
    treat_as_char: bool = True
    ensure_newline: bool = False
```
**Purpose**: Configuration for equation appearance.

```python
def insert_equation_control(hwp: Any, hwpeqn: str, *, options: EquationOptions | None = None) -> None:
```
**Purpose**: Insert equation using HWP's COM interface.

**Steps**:
1. Create equation with `EquationCreate` action
2. Set font and size via `EqEdit` parameters
3. Re-open with `EquationPropertyDialog` to set version and formatting
4. Close dialog with `Cancel` action
5. Move cursor right with `MoveRight` action

```python
def _point_to_hwp_unit(hwp: Any, point: float) -> float:
    if hasattr(hwp, "PointToHwpUnit"):
        return hwp.PointToHwpUnit(point)
    return point * 100.0
```
**Purpose**: Convert font size from points to HWP internal units.
**Fallback**: If method not available, use approximation (1pt ≈ 100 units).

---

## LaTeX Converter (`backend/equations/latex_to_hwpeqn.py`)

### Purpose
Convert LaTeX math notation to HwpEqn format using Node.js CLI.

```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]
NODE_CLI = PROJECT_ROOT / "node_eqn" / "hwp_eqn_cli.js"
```
**Purpose**: Find path to Node.js converter script.
**`.parents[2]`**: Go up 2 directories (from file to project root).

```python
def latex_to_hwpeqn(latex: str, timeout: float = 15.0) -> str:
    text = latex.strip()
    if not text:
        return ""
```
**Purpose**: Main conversion function.

```python
    cmd = ["node", str(NODE_CLI)]
    result = subprocess.run(
        cmd,
        input=text,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
```
**`subprocess.run()`**: Execute external program (Node.js).
**Parameters**:
- `cmd`: Command and arguments
- `input`: Data to send to stdin
- `capture_output=True`: Capture stdout/stderr
- `text=True`: Use strings (not bytes)
- `timeout`: Maximum seconds to wait
- `check=True`: Raise exception if exit code != 0

```python
    output = result.stdout.strip()
    if not output:
        logger.warning("Equation converter returned empty output.")
        return latex
    return output
```
**Purpose**: Return converted output or original LaTeX if empty.

```python
except FileNotFoundError as exc:
    logger.error("Node.js is not installed or not on PATH: %s", exc)
except subprocess.CalledProcessError as exc:
    logger.error("Equation converter failed (exit %s): %s", exc.returncode, exc.stderr.strip())
except subprocess.TimeoutExpired:
    logger.error("Equation converter timed out after %s seconds", timeout)
```
**Purpose**: Handle different error types gracefully.

---

## OCR Module (`backend/ocr/pix2text_client.py`)

### Purpose
Extract text, equations, and images from document images using OCR.

### Key Classes

```python
@dataclass(slots=True)
class Pix2TextOptions:
    use_pix2tex_for_equations: bool = OCR.use_pix2tex
    detect_images: bool = True
    lang: str = OCR.lang
    min_confidence: int = OCR.min_text_confidence
    min_image_area_ratio: float = OCR.min_image_area_ratio
```
**Purpose**: Configuration for OCR behavior.

```python
class Pix2TextClient:
    def extract_blocks(self, image_path: str, page_index: int) -> PageBlocks:
```
**Purpose**: Main method to OCR an image and return structured blocks.

**Process**:
1. Load image with PIL
2. Run pytesseract OCR
3. Group results by paragraph/line
4. Classify as text vs equation
5. Optionally detect image regions
6. Sort by y-coordinate (top to bottom)

```python
def _classify_line(self, text: str) -> BlockType:
    score = sum(1 for ch in text if ch in MATH_TOKENS)
    digit_ratio = sum(ch.isdigit() for ch in text) / max(len(text), 1)
    if score >= 2 or digit_ratio > 0.25:
        if len(text) > 20 or "\\" in text:
            return BlockType.DISPLAY_EQUATION
        return BlockType.INLINE_EQUATION
    return BlockType.TEXT
```
**Purpose**: Heuristic to guess if text is an equation.
**Logic**:
- Count math symbols (=, +, -, etc.)
- Calculate digit ratio
- If many math symbols or digits → equation
- Long equations → display equation
- Short → inline equation

```python
def _detect_image_blocks(self, image: Image.Image, data: Dict, page_index: int) -> List[Tuple[float, Block]]:
```
**Purpose**: Find non-text regions (likely images/figures).

**Process**:
1. Create mask of all text regions
2. Invert mask (get non-text areas)
3. Dilate to connect nearby regions
4. Find contours (shapes)
5. Filter by size
6. Crop and save as temporary files

---

## Configuration (`backend/config.py`)

### Purpose
Centralized configuration using environment variables.

```python
def _env_path(name: str) -> Optional[Path]:
    value = os.getenv(name)
    if value:
        return Path(value).expanduser()
    return None
```
**Purpose**: Read path from environment variable.
**`.expanduser()`**: Convert `~` to user's home directory.

```python
@dataclass(frozen=True)
class PdfConfig:
    dpi: int = int(os.getenv("INLINE_HWP_PDF_DPI", "300"))
    poppler_path: Optional[Path] = _env_path("POPPLER_PATH")
```
**`frozen=True`**: Make dataclass immutable (can't change values after creation).
**`os.getenv("KEY", "default")`**: Read environment variable with fallback.

```python
PDF = PdfConfig()
OCR = OcrConfig()
PATHS = PathsConfig()
```
**Purpose**: Create global configuration singletons.

---

## How to Extend

### Add a new GUI button

1. In `_build_editor()` method, add:
```python
self.new_button = QPushButton("New Action")
self.new_button.clicked.connect(self._handle_new_action)
```

2. Add handler method:
```python
def _handle_new_action(self) -> None:
    self._append_log("New action clicked!")
    # Your code here
```

### Add a new helper function for scripts

1. In `script_runner.py`, add to `env` dictionary:
```python
env: Dict[str, object] = {
    ...
    "my_helper": self._my_helper,
}
```

2. Define the helper:
```python
def _my_helper(self, text: str) -> None:
    # Do something with HWP
    self._controller.insert_text(f"Helper: {text}")
```

### Add a new OCR option

1. In `config.py`, add to `OcrConfig`:
```python
@dataclass(frozen=True)
class OcrConfig:
    ...
    my_option: bool = os.getenv("INLINE_HWP_MY_OPTION", "0") == "1"
```

2. Use in code:
```python
from backend.config import OCR

if OCR.my_option:
    # Do something different
```

### Add a new block type

1. In `backend/ocr/__init__.py`:
```python
class BlockType(str, Enum):
    ...
    TABLE = "table"
```

2. In `pix2text_client.py`, detect and create:
```python
block = Block(block_type=BlockType.TABLE, content=table_data)
```

3. In `process_document.py`, handle:
```python
elif block.block_type == BlockType.TABLE:
    _handle_table_block(block, hwp, log)
```

---

## Common Python Patterns Explained

### Type Hints
```python
def func(name: str) -> int:
    return len(name)
```
- `name: str` → parameter must be string
- `-> int` → function returns integer

### Dataclasses
```python
@dataclass
class Person:
    name: str
    age: int = 0

p = Person("Alice", 25)
print(p.name)  # Alice
```
Auto-generates `__init__`, `__repr__`, comparison methods.

### Context Managers
```python
with open("file.txt") as f:
    data = f.read()
# File automatically closed
```

### List Comprehensions
```python
squares = [x**2 for x in range(10)]
# Same as:
squares = []
for x in range(10):
    squares.append(x**2)
```

### F-strings
```python
name = "Alice"
age = 25
msg = f"Hello, {name}! You are {age} years old."
```

### Decorators
```python
@property
def name(self):
    return self._name

# Use as: obj.name (no parentheses)
```

### Lambda Functions
```python
add = lambda x, y: x + y
# Same as:
def add(x, y):
    return x + y
```

---

## Next Steps

1. **Run the app**: `python -m gui.app`
2. **Try the example script** in the GUI
3. **Modify** the example script
4. **Add your own helper** in `script_runner.py`
5. **Customize the UI** in `main_window.py`
6. **Read Qt documentation**: https://doc.qt.io/qtforpython/

Happy coding! 🚀

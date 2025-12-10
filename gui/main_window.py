"""AMEX AI script console."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QThread, QObject, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QGridLayout,
    QFileDialog,
)

from backend.hwp.hwp_controller import HwpController, HwpControllerError
from backend.hwp.script_runner import HwpScriptRunner
from backend.chatgpt_helper import ChatGPTHelper

def _load_dialog_css() -> str:
    """Load external CSS file for dialogs."""
    css_path = Path(__file__).parent / "styles" / "dialog_styles.css"
    if css_path.exists():
        return css_path.read_text(encoding='utf-8')
    return ""

def _load_theme(theme_name: str) -> str:
    """Load external QSS theme file."""
    qss_path = Path(__file__).parent / "styles" / f"{theme_name}_theme.qss"
    if qss_path.exists():
        return qss_path.read_text(encoding='utf-8')
    return ""

def _create_styled_dialog(parent, title: str, content: str, min_width: int = 500, min_height: int = 0) -> QMessageBox:
    """Create a styled dialog with enhanced OK button."""
    css = _load_dialog_css()
    full_html = f"<style>{css}</style>{content}"
    
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setTextFormat(Qt.TextFormat.RichText)
    msg.setText(full_html)
    msg.setIcon(QMessageBox.Icon.NoIcon)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    
    msg.setMinimumWidth(min_width)
    if min_height > 0:
        msg.setMinimumHeight(min_height)
    
    return msg

DEFAULT_SCRIPT = """
# 예시: 텍스트 + 수식을 한 번에 삽입
insert_text("AMEX AI가 자동으로 한글 문단을 입력합니다.\\r")
insert_text("Einstein 질량-에너지 등가식은 아래와 같습니다.\\r")
insert_hwpeqn("E = m c ^{2}", font_size_pt=12.0, eq_font_name="HYhwpEQ")
"""

# Template library
TEMPLATES = {
    "텍스트": {
        "icon": "📝",
        "code": 'insert_text("여기에 텍스트를 입력하세요.\\r")\ninsert_paragraph()'
    },
    "벡터": {
        "icon": "🎯",
        "code": 'insert_equation(r"\\vec{a} = \\begin{pmatrix} a_1 \\\\ a_2 \\\\ a_3 \\end{pmatrix}", font_size_pt=14.0)'
    },
    "행렬": {
        "icon": "▦",
        "code": 'insert_equation(r"A = \\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}", font_size_pt=14.0)'
    },
    "시그마": {
        "icon": "Σ",
        "code": 'insert_equation(r"\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}", font_size_pt=14.0)'
    },
    "미분": {
        "icon": "∆",
        "code": 'insert_equation(r"\\frac{d}{dx}f(x) = \\lim_{h \\to 0} \\frac{f(x+h)-f(x)}{h}", font_size_pt=13.0)'
    },
    "적분": {
        "icon": "∫",
        "code": 'insert_equation(r"\\int_{a}^{b} f(x) dx = F(b) - F(a)", font_size_pt=14.0)'
    }
}

# Themes are now loaded from external QSS files
# - gui/styles/light_theme.qss
# - gui/styles/dark_theme.qss


class ScriptWorker(QThread):
    log_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, script: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._script = script

    def run(self) -> None:  # type: ignore[override]
        try:
            controller = HwpController()
            controller.connect()
            runner = HwpScriptRunner(controller)
            runner.run(self._script, self.log_signal.emit)
            self.finished_signal.emit()
        except HwpControllerError as exc:
            self.error_signal.emit(f"HWP 연결 실패: {exc}")
        except Exception as exc:
            self.error_signal.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HMATH AI")
        self.resize(900, 900)
        self._worker: Optional[ScriptWorker] = None
        self.dark_mode = False
        self.chatgpt = ChatGPTHelper()
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main_area = QWidget()
        main_area.setObjectName("main-area")
        main_column = QVBoxLayout(main_area)
        main_column.setContentsMargins(0, 0, 0, 0)
        main_column.setSpacing(0)
        
        # Top content area (templates or chat)
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(40, 40, 40, 0)
        content_layout.setSpacing(20)
        
        content_layout.addWidget(self._build_header())
        content_layout.addWidget(self._build_help_buttons())
        content_layout.addWidget(self._build_templates(), 1)
        
        # Input area (fixed at bottom)
        input_area = QWidget()
        input_area.setObjectName("input-container")
        input_layout = QVBoxLayout(input_area)
        input_layout.setContentsMargins(40, 24, 40, 40)
        input_layout.setSpacing(20)
        
        # Script editor
        self.script_edit = QTextEdit()
        self.script_edit.setObjectName("script-editor")
        self.script_edit.setPlaceholderText("코드를 작성하거나 붙여넣으세요")
        self.script_edit.setPlainText(DEFAULT_SCRIPT.strip())
        self.script_edit.setMaximumHeight(220)
        self.script_edit.setMinimumHeight(160)
        
        input_layout.addWidget(self.script_edit)
        
        # Run button centered
        run_row = QHBoxLayout()
        run_row.setContentsMargins(0, 0, 0, 0)
        
        self.run_button = QPushButton("▶ Run")
        self.run_button.setObjectName("primary-action")
        self.run_button.setMaximumWidth(140)
        self.run_button.setMinimumHeight(44)
        self.run_button.clicked.connect(self._handle_run_clicked)
        
        run_row.addStretch()
        run_row.addWidget(self.run_button)
        run_row.addStretch()
        
        input_layout.addLayout(run_row)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setObjectName("log-output")
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(80)
        self.log_output.setMinimumHeight(60)
        self.log_output.setPlaceholderText("출력 결과가 이곳에 표시됩니다")
        input_layout.addWidget(self.log_output)

        main_column.addWidget(self.content_area, 1)
        main_column.addWidget(input_area, 0)

        layout.addWidget(main_area, 1)
        layout.addWidget(self._build_sidebar(), 0)
        self.setCentralWidget(central)

    def _build_header(self) -> QWidget:
        frame = QFrame()
        lyt = QVBoxLayout(frame)
        lyt.setSpacing(8)
        lyt.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("HMATH")
        title.setObjectName("app-title")
        
        subtitle = QLabel("최고의 한글 수식 자동화 에이전트")
        subtitle.setObjectName("app-subtitle")
        
        lyt.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        lyt.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        return frame

    def _build_help_buttons(self) -> QWidget:
        """Build horizontally aligned help buttons."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        layout.addStretch()
        
        self.howto_button = QPushButton("💡 How to use")
        self.howto_button.setObjectName("help-button")
        self.howto_button.setMaximumWidth(140)
        self.howto_button.setMinimumHeight(36)
        self.howto_button.clicked.connect(self._show_howto)
        layout.addWidget(self.howto_button)
        
        self.latex_button = QPushButton("</> LaTeX")
        self.latex_button.setObjectName("help-button")
        self.latex_button.setMaximumWidth(140)
        self.latex_button.setMinimumHeight(36)
        self.latex_button.clicked.connect(self._show_latex_helper)
        layout.addWidget(self.latex_button)
        
        self.ai_generate_button = QPushButton("🤖 AI Generate")
        self.ai_generate_button.setObjectName("help-button")
        self.ai_generate_button.setMaximumWidth(140)
        self.ai_generate_button.setMinimumHeight(36)
        self.ai_generate_button.clicked.connect(self._show_ai_generate_dialog)
        layout.addWidget(self.ai_generate_button)
        
        self.ai_optimize_button = QPushButton("✨ AI Optimize")
        self.ai_optimize_button.setObjectName("help-button")
        self.ai_optimize_button.setMaximumWidth(140)
        self.ai_optimize_button.setMinimumHeight(36)
        self.ai_optimize_button.clicked.connect(self._show_ai_optimize_dialog)
        layout.addWidget(self.ai_optimize_button)
        
        layout.addStretch()
        return container

    def _build_templates(self) -> QWidget:
        """Build template library cards - centered."""
        container = QWidget()
        container.setObjectName("templates-container")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Center the grid
        grid_container = QWidget()
        grid_layout = QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a horizontal layout for the grid
        h_grid = QHBoxLayout()
        h_grid.setContentsMargins(0, 0, 0, 0)
        h_grid.setSpacing(12)
        h_grid.addStretch()
        
        for name, template in TEMPLATES.items():
            btn = QPushButton(f"{template['icon']} {name}")
            btn.setObjectName("template-btn")
            btn.setMaximumWidth(140)
            btn.setMinimumHeight(44)
            btn.clicked.connect(lambda checked, code=template["code"]: self._load_template(code))
            h_grid.addWidget(btn)
        
        h_grid.addStretch()
        grid_layout.addLayout(h_grid)
        
        layout.addWidget(grid_container)
        layout.addStretch()
        
        return container

    def _load_template(self, code: str) -> None:
        """Load template code into editor."""
        self.script_edit.setPlainText(code)
        self.script_edit.setFocus()
        self._animate_focus(self.script_edit)

    def _animate_focus(self, widget: QWidget) -> None:
        """Pulse animation when template is loaded."""
        original_style = widget.styleSheet()
        widget.setStyleSheet(original_style + "\nborder-color: #10a37f !important;")
        timer = QTimer()
        
        def reset():
            widget.setStyleSheet(original_style)
            timer.stop()
        
        timer.timeout.connect(reset)
        timer.start(600)

    def _build_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("sidebar")
        lyt = QVBoxLayout(frame)
        lyt.setContentsMargins(12, 20, 12, 20)
        lyt.setSpacing(12)

        # Save script button
        self.save_btn = QToolButton()
        self.save_btn.setObjectName("pin-button")
        self.save_btn.setToolTip("스크립트 저장")
        self.save_btn.setAutoRaise(True)
        self.save_btn.setText("💾")
        font = self.save_btn.font()
        font.setPointSize(24)
        self.save_btn.setFont(font)
        self.save_btn.clicked.connect(self._save_script)

        # Load script button
        self.load_btn = QToolButton()
        self.load_btn.setObjectName("pin-button")
        self.load_btn.setToolTip("스크립트 불러오기")
        self.load_btn.setAutoRaise(True)
        self.load_btn.setText("📂")
        font = self.load_btn.font()
        font.setPointSize(24)
        self.load_btn.setFont(font)
        self.load_btn.clicked.connect(self._load_script)

        # Theme button
        self.theme_btn = QToolButton()
        self.theme_btn.setObjectName("pin-button")
        self.theme_btn.setCheckable(True)
        self.theme_btn.setToolTip("다크 모드")
        self.theme_btn.setAutoRaise(True)
        self._set_theme_glyph(False)
        self.theme_btn.toggled.connect(self._toggle_theme)

        # Settings button
        self.settings_btn = QToolButton()
        self.settings_btn.setObjectName("pin-button")
        self.settings_btn.setToolTip("설정")
        self.settings_btn.setAutoRaise(True)
        self._set_settings_glyph()
        self.settings_btn.clicked.connect(self._show_settings)

        lyt.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignTop)
        lyt.addWidget(self.load_btn, alignment=Qt.AlignmentFlag.AlignTop)
        lyt.addWidget(self.theme_btn, alignment=Qt.AlignmentFlag.AlignTop)
        lyt.addStretch()
        lyt.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        return frame

    def _apply_styles(self) -> None:
        theme = "light" if not self.dark_mode else "dark"
        stylesheet = _load_theme(theme)
        self.setStyleSheet(stylesheet)

    def _handle_run_clicked(self) -> None:
        if self._worker and self._worker.isRunning():
            self._show_info_dialog("진행 중", "이미 스크립트를 실행 중입니다.")
            return
        script = self.script_edit.toPlainText()
        self._worker = ScriptWorker(script, self)
        self._worker.log_signal.connect(self._append_log)
        self._worker.error_signal.connect(self._handle_error)
        self._worker.finished_signal.connect(self._handle_finished)
        self.run_button.setEnabled(False)
        self._append_log("=== 실행 요청 ===")
        self._worker.start()

    def _handle_error(self, message: str) -> None:
        self._append_log(f"[오류] {message}")
        self._show_error_dialog(message)
        self.run_button.setEnabled(True)

    def _save_script(self) -> None:
        """Save current script to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "스크립트 저장",
            "",
            "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            try:
                Path(file_path).write_text(self.script_edit.toPlainText(), encoding='utf-8')
                self._show_info_dialog("저장 완료", f"스크립트가 저장되었습니다:\n{file_path}")
            except Exception as e:
                self._show_error_dialog(f"파일 저장 실패:\n{str(e)}")

    def _load_script(self) -> None:
        """Load script from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "스크립트 불러오기",
            "",
            "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            try:
                content = Path(file_path).read_text(encoding='utf-8')
                self.script_edit.setPlainText(content)
                self._show_info_dialog("불러오기 완료", f"스크립트를 불러왔습니다:\n{file_path}")
            except Exception as e:
                self._show_error_dialog(f"파일 불러오기 실패:\n{str(e)}")

    def _show_help_menu(self) -> None:
        """Show help menu dialog."""
        content = """
<h2>📖 도움말</h2>

<div class="setting-section">
    <div class="setting-title">빠른 시작</div>
    <div class="step">
        <span class="step-num">1</span>
        <strong>How to use</strong> 버튼을 클릭하여 사용 방법을 확인하세요
    </div>
    <div class="step">
        <span class="step-num">2</span>
        <strong>LaTeX</strong> 버튼을 클릭하여 수식 가이드를 확인하세요
    </div>
    <div class="step">
        <span class="step-num">3</span>
        <strong>템플릿</strong>을 클릭하여 예제 코드를 사용하세요
    </div>
</div>

<div class="setting-section">
    <div class="setting-title">주요 기능</div>
    <div class="setting-item">
        <span class="setting-label">💾 스크립트 저장</span>
        <span class="setting-value">작성한 코드 저장</span>
    </div>
    <div class="setting-item">
        <span class="setting-label">📂 스크립트 불러오기</span>
        <span class="setting-value">저장된 코드 불러오기</span>
    </div>
    <div class="setting-item">
        <span class="setting-label">🌙 다크 모드</span>
        <span class="setting-value">테마 전환</span>
    </div>
    <div class="setting-item">
        <span class="setting-label">⚙️ 설정</span>
        <span class="setting-value">앱 정보 및 설정</span>
    </div>
</div>

<div class="info-box">
    <strong>문의사항:</strong> GitHub Issues를 통해 버그 리포트 및 기능 제안을 해주세요
</div>
"""
        msg = _create_styled_dialog(self, "도움말", content, 550)
        msg.exec()

    def _show_error_dialog(self, message: str) -> None:
        """Show elegant error dialog."""
        error_content = f"""
<div class="error-container">
    <span class="error-icon">⚠️</span>
    <span class="error-title">실행 오류가 발생했습니다</span>
    
    <div class="error-message">
        {message}
    </div>
    
    <div class="help-text">
        <strong>도움말:</strong> Windows에서 한글이 실행 중인지 확인하세요. 문서가 열려있고 커서가 입력 가능한 위치에 있어야 합니다.
    </div>
</div>
"""
        msg = _create_styled_dialog(self, "오류", error_content, 500)
        msg.exec()

    def _show_info_dialog(self, title: str, message: str) -> None:
        """Show elegant info dialog."""
        info_content = f"""
<div class="info-container">
    <span class="info-icon">ℹ️</span>
    <span class="info-title">{title}</span>
    
    <div class="info-message">
        {message}
    </div>
</div>
"""
        msg = _create_styled_dialog(self, title, info_content, 450)
        msg.exec()

    def _handle_finished(self) -> None:
        self._append_log("=== 실행 완료 ===")
        self.run_button.setEnabled(True)
        self._show_success_animation()

    def _show_success_animation(self) -> None:
        """Show success indicator animation."""
        success = QLabel("✓")
        success.setObjectName("success-indicator")
        success.setStyleSheet("color: #10b981; font-size: 28px;")
        
        # Show briefly in the log area
        self.log_output.append("✓ 스크립트가 성공적으로 완료되었습니다!")

    def _toggle_theme(self, checked: bool) -> None:
        """Toggle between light and dark theme."""
        self.dark_mode = checked
        self._set_theme_glyph(checked)
        theme = "dark" if checked else "light"
        stylesheet = _load_theme(theme)
        self.setStyleSheet(stylesheet)

    def _set_theme_glyph(self, active: bool) -> None:
        """Set theme toggle icon."""
        font_name = _ensure_material_icon_font()
        font = QFont(font_name)
        font.setPointSize(24)
        self.theme_btn.setFont(font)
        glyph = "☀️" if active else "🌙"
        self.theme_btn.setText(glyph)

    def _show_howto(self) -> None:
        """Show how to use dialog."""
        howto_content = """
<h2>🚀 HMATH AI 사용 가이드</h2>

<div class="step">
    <strong>1. 한글 실행</strong><br>
    Windows에서 한컴 한글(HWP)을 실행하세요
</div>

<div class="step">
    <strong>2. 커서 위치 지정</strong><br>
    문서를 열고 내용을 입력할 위치에 커서를 놓으세요
</div>

<div class="step">
    <strong>3. 코드 작성</strong><br>
    에디터에 파이썬 자동화 코드를 작성하거나 붙여넣으세요
</div>

<div class="step">
    <strong>4. 실행</strong><br>
    "Run" 버튼을 클릭하여 자동화를 시작하세요
</div>

<div class="functions">
    <h3>📚 텍스트 작성 함수</h3>
    
    <div class="func-item">
        <code>insert_text("텍스트\\r")</code><br>
        <small style="color: #666;">텍스트 삽입 (\\r은 줄바꿈)</small>
    </div>
    
    <div class="func-item">
        <code>insert_paragraph()</code><br>
        <small style="color: #666;">문단 나누기</small>
    </div>
    
    <div class="func-item">
        <code>insert_equation("LaTeX")</code><br>
        <small style="color: #666;">LaTeX 수식 삽입</small>
    </div>
    
    <div class="func-item">
        <code>insert_hwpeqn("HwpEqn")</code><br>
        <small style="color: #666;">HWP 수식 형식으로 삽입</small>
    </div>
    
    <div class="func-item">
        <code>insert_image("경로/이미지.png")</code><br>
        <small style="color: #666;">이미지 삽입</small>
    </div>
</div>

<div class="functions">
    <h3>✨ 주요 기능</h3>
    
    <div class="func-item">
        <span class="setting-label">💾 스크립트 저장</span><br>
        <small style="color: #666;">현재 에디터의 코드를 Python 파일로 저장</small>
    </div>
    
    <div class="func-item">
        <span class="setting-label">📂 스크립트 불러오기</span><br>
        <small style="color: #666;">저장된 코드 파일을 에디터에 불러오기</small>
    </div>
    
    <div class="func-item">
        <span class="setting-label">🌙 다크 모드</span><br>
        <small style="color: #666;">밝은 테마와 어두운 테마 전환</small>
    </div>
    
    <div class="func-item">
        <span class="setting-label">⚙️ 설정</span><br>
        <small style="color: #666;">앱 정보 및 단축키 확인</small>
    </div>
</div>

<div class="note">
    <strong>참고:</strong> Windows 환경과 한컴 한글이 설치되어 있어야 합니다
</div>
"""
        msg = _create_styled_dialog(self, "사용 방법", howto_content, 600)
        msg.exec()

    def _show_latex_helper(self) -> None:
        """Show LaTeX code examples."""
        latex_content = """
<h2>📐 LaTeX 수식 가이드</h2>

<div class="columns">
<div class="column">
    <div class="section">
        <div class="section-title">기본 수식</div>
        <code>x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}</code>
        <code>E = mc^2</code>
    </div>
    
    <div class="section">
        <div class="section-title">적분</div>
        <code>\\int_{0}^{\\infty} e^{-x^2} dx</code>
        <code>\\int x^n dx = \\frac{x^{n+1}}{n+1}</code>
    </div>
    
    <div class="section">
        <div class="section-title">합 & 곱</div>
        <code>\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}</code>
        <code>\\prod_{i=1}^{n} a_i</code>
    </div>
    
    <div class="section">
        <div class="section-title">분수 & 제곱근</div>
        <code>\\frac{a}{b}, \\sqrt{x}, \\sqrt[n]{x}</code>
    </div>
    
    <div class="section">
        <div class="section-title">미분 & 극한</div>
        <code>\\frac{df}{dx}, f'(x)</code>
        <code>\\lim_{x \\to \\infty} f(x)</code>
    </div>
</div>

<div class="column">
    <div class="section greek">
        <div class="section-title">그리스 문자 (소문자)</div>
        <code>\\alpha</code> <code>\\beta</code> <code>\\gamma</code> <code>\\delta</code>
        <code>\\epsilon</code> <code>\\theta</code> <code>\\lambda</code> <code>\\mu</code>
        <code>\\pi</code> <code>\\sigma</code> <code>\\phi</code> <code>\\omega</code>
    </div>
    
    <div class="section greek">
        <div class="section-title">그리스 문자 (대문자)</div>
        <code>\\Gamma</code> <code>\\Delta</code> <code>\\Theta</code> <code>\\Lambda</code>
        <code>\\Pi</code> <code>\\Sigma</code> <code>\\Phi</code> <code>\\Omega</code>
    </div>
    
    <div class="section greek">
        <div class="section-title">관계 & 집합</div>
        <code>\\leq</code> <code>\\geq</code> <code>\\neq</code> <code>\\approx</code>
        <code>\\in</code> <code>\\subset</code> <code>\\cap</code> <code>\\cup</code>
    </div>
    
    <div class="section greek">
        <div class="section-title">논리 & 기타</div>
        <code>\\exists</code> <code>\\forall</code> <code>\\Rightarrow</code>
        <code>\\infty</code> <code>\\partial</code> <code>\\nabla</code>
    </div>
</div>

<div class="column">
    <div class="section">
        <div class="section-title">행렬</div>
        <code>\\begin{bmatrix}<br>a & b \\\\<br>c & d<br>\\end{bmatrix}</code>
        <code>\\begin{pmatrix}<br>1 & 2 \\\\<br>3 & 4<br>\\end{pmatrix}</code>
    </div>
    
    <div class="section">
        <div class="section-title">괄호</div>
        <code>\\left( x \\right)</code>
        <code>\\left[ x \\right]</code>
        <code>\\left\\{ x \\right\\}</code>
    </div>
    
    <div class="section">
        <div class="section-title">분할 식</div>
        <code>f(x) = \\begin{cases}<br>x^2 & x \\geq 0 \\\\<br>-x & x < 0<br>\\end{cases}</code>
    </div>
    
    <div class="section">
        <div class="section-title">기타</div>
        <code>\\binom{n}{k}</code>
        <code>\\frac{\\partial f}{\\partial x}</code>
    </div>
</div>
</div>
"""
        msg = _create_styled_dialog(self, "LaTeX 수식 가이드", latex_content, 900, 600)
        msg.exec()
        msg.setMinimumHeight(600)
        msg.exec()

    def _append_log(self, text: str) -> None:
        self.log_output.append(text)

    def _set_settings_glyph(self) -> None:
        """Set settings icon."""
        self.settings_btn.setText("⚙️")
        font = self.settings_btn.font()
        font.setPointSize(24)
        self.settings_btn.setFont(font)

    def _show_settings(self) -> None:
        """Show settings dialog."""
        settings_content = """
<h2>⚙️ 설정</h2>

<div class="setting-section">
    <div class="setting-title">애플리케이션 정보</div>
    
    <div class="setting-item">
        <span class="setting-label">버전</span>
        <span class="setting-value">1.0.0</span>
    </div>
    
    <div class="setting-item">
        <span class="setting-label">Python 버전</span>
        <span class="setting-value">3.9+</span>
    </div>
    
    <div class="setting-item">
        <span class="setting-label">플랫폼</span>
        <span class="setting-value">Windows, macOS, Linux</span>
    </div>
</div>

<div class="info-box">
    <strong>참고:</strong> 한글 자동화는 Windows 환경에서만 작동합니다. macOS/Linux에서는 스크립트 편집 기능만 사용 가능합니다.
</div>
"""
        msg = _create_styled_dialog(self, "설정", settings_content, 550)
        msg.exec()

    def _show_ai_generate_dialog(self) -> None:
        """Show dialog to generate script with ChatGPT."""
        if not self.chatgpt.is_available():
            self._show_error_dialog(
                "ChatGPT API를 사용할 수 없습니다.\n\n"
                "설정 방법:\n"
                "1. OpenAI 계정 생성 (https://openai.com)\n"
                "2. API 키 발급\n"
                "3. OPENAI_API_KEY 환경변수 설정\n"
                "4. 앱 재시작"
            )
            return

        # Use a simple text input via QMessageBox
        text, ok = self._get_text_input(
            "🤖 AI Script Generator",
            "스크립트 생성을 위한 설명을 입력하세요:\n\n"
            "예: '처음에 \"수학 문제\"라는 제목을 입력하고, '\n"
            "'그 아래에 이차방정식 공식을 LaTeX로 삽입해주세요'"
        )
        
        if ok and text.strip():
            self._generate_script_with_ai(text)

    def _show_ai_optimize_dialog(self) -> None:
        """Show dialog to optimize current script with ChatGPT."""
        if not self.chatgpt.is_available():
            self._show_error_dialog(
                "ChatGPT API를 사용할 수 없습니다.\n\n"
                "설정 방법:\n"
                "1. OpenAI 계정 생성 (https://openai.com)\n"
                "2. API 키 발급\n"
                "3. OPENAI_API_KEY 환경변수 설정\n"
                "4. 앱 재시작"
            )
            return

        current_script = self.script_edit.toPlainText()
        if not current_script.strip():
            self._show_info_dialog("알림", "최적화할 스크립트가 없습니다.")
            return

        text, ok = self._get_text_input(
            "✨ AI Script Optimizer",
            "최적화 요청사항을 입력하세요 (선택사항):\n\n"
            "예: '코드를 더 간결하게 만들어주세요'\n"
            "또는: '에러 처리를 추가해주세요'\n\n"
            "(비워두면 기본 최적화가 진행됩니다)"
        )
        
        if ok:
            self._optimize_script_with_ai(text)

    def _get_text_input(self, title: str, prompt: str) -> tuple[str, bool]:
        """Get text input from user via dialog."""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(prompt)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        
        # Create input field
        input_field = QTextEdit()
        input_field.setMinimumHeight(100)
        input_field.setMinimumWidth(400)
        
        layout = msg.layout()
        if layout:
            layout.addWidget(input_field)
        
        ok = msg.exec() == QMessageBox.StandardButton.Ok
        return input_field.toPlainText(), ok

    def _generate_script_with_ai(self, description: str) -> None:
        """Generate script using ChatGPT API."""
        self._append_log("🤖 AI가 스크립트를 생성하는 중...")
        self.run_button.setEnabled(False)
        
        # Get available functions context
        context = """
사용 가능한 함수들:
- insert_text(text): 텍스트 삽입
- insert_paragraph(): 문단 추가
- insert_equation(latex_code, font_size_pt=14.0): LaTeX 수식 삽입
- insert_hwpeqn(hwpeqn_code, font_size_pt=12.0): HWP 수식 형식 삽입
- insert_image(image_path): 이미지 삽입
"""
        
        generated_code = self.chatgpt.generate_script(description, context)
        
        if generated_code:
            self.script_edit.setPlainText(generated_code)
            self._append_log("✅ 스크립트 생성 완료!")
            self._show_info_dialog("생성 완료", "AI가 스크립트를 생성했습니다.\n확인하고 실행해주세요.")
        else:
            self._append_log("❌ 스크립트 생성 실패")
            self._show_error_dialog("스크립트 생성 중 오류가 발생했습니다.\nAPI 키를 확인해주세요.")
        
        self.run_button.setEnabled(True)

    def _optimize_script_with_ai(self, feedback: str) -> None:
        """Optimize current script using ChatGPT API."""
        self._append_log("✨ AI가 스크립트를 최적화하는 중...")
        self.run_button.setEnabled(False)
        
        current_script = self.script_edit.toPlainText()
        optimized_code = self.chatgpt.optimize_script(current_script, feedback)
        
        if optimized_code:
            self.script_edit.setPlainText(optimized_code)
            self._append_log("✅ 스크립트 최적화 완료!")
            self._show_info_dialog("최적화 완료", "AI가 스크립트를 최적화했습니다.")
        else:
            self._append_log("❌ 스크립트 최적화 실패")
            self._show_error_dialog("스크립트 최적화 중 오류가 발생했습니다.\nAPI 키를 확인해주세요.")
        
        self.run_button.setEnabled(True)


def run_app() -> None:
    existing_app = QApplication.instance()
    if existing_app is None:
        app = QApplication([])
    else:
        app = existing_app  # type: ignore[assignment]
    assert isinstance(app, QApplication)
    _apply_app_font(app)
    window = MainWindow()
    window.show()
    app.exec()


def _apply_app_font(app: QApplication) -> None:
    font_db = QFontDatabase()
    if "Pretendard" not in font_db.families():
        font_path = (
            Path(__file__).resolve().parents[1] / "resources" / "fonts" / "PretendardVariable.ttf"
        )
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))

    base_font = QFont("Pretendard")
    if base_font.family() != "Pretendard":
        base_font = app.font()
        base_font.setFamily("Pretendard")
    base_font.setPointSize(11)
    app.setFont(base_font)


def _ensure_material_icon_font() -> str:
    font_db = QFontDatabase()
    target_name = "Material Icons Round"
    if target_name in font_db.families():
        return target_name

    font_path = (
        Path(__file__).resolve().parents[1] / "resources" / "fonts" / "MaterialSymbolsRounded.ttf"
    )
    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return families[0]
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app.font().family()
    return "Arial"


"""AMEX AI script console."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QThread, QObject, QSize
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
)

from backend.hwp.hwp_controller import HwpController, HwpControllerError
from backend.hwp.script_runner import HwpScriptRunner

DEFAULT_SCRIPT = """
# 예시: 텍스트 + 수식을 한 번에 삽입
insert_text("AMEX AI가 자동으로 한글 문단을 입력합니다.\\r")
insert_text("Einstein 질량-에너지 등가식은 아래와 같습니다.\\r")
insert_hwpeqn("E = m c ^{2}", font_size_pt=12.0, eq_font_name="HYhwpEQ")
"""


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
        self.resize(680, 780)
        self._worker: Optional[ScriptWorker] = None
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
        main_column.setContentsMargins(48, 0, 48, 32)
        main_column.setSpacing(32)
        main_column.addWidget(self._build_header())
        main_column.addWidget(self._build_editor())
        main_column.addWidget(self._build_log_panel(), 1)

        layout.addWidget(main_area, 1)
        layout.addWidget(self._build_sidebar(), 0)
        self.setCentralWidget(central)

    def _build_header(self) -> QWidget:
        frame = QFrame()
        lyt = QVBoxLayout(frame)
        lyt.setSpacing(8)
        lyt.setContentsMargins(0, 40, 0, 20)
        
        title = QLabel("HMATH AI")
        title.setObjectName("app-title")
        
        subtitle = QLabel("Upload a PDF and we'll type everything in for you")
        subtitle.setObjectName("app-subtitle")
        
        lyt.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        lyt.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        return frame

    def _build_editor(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("editor-card")
        lyt = QVBoxLayout(frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(24)
        
        # Action buttons centered
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.howto_button = QPushButton("💡 How to use")
        self.howto_button.setObjectName("action-button")
        self.howto_button.setMinimumWidth(180)
        self.howto_button.clicked.connect(self._show_howto)
        
        self.latex_button = QPushButton("</> Latex Code")
        self.latex_button.setObjectName("action-button")
        self.latex_button.setMinimumWidth(180)
        self.latex_button.clicked.connect(self._show_latex_helper)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.howto_button)
        buttons_layout.addWidget(self.latex_button)
        buttons_layout.addStretch()
        
        lyt.addLayout(buttons_layout)
        
        # Script editor
        self.script_edit = QTextEdit()
        self.script_edit.setObjectName("script-editor")
        self.script_edit.setPlaceholderText("Type your Python script here or paste example code...")
        self.script_edit.setPlainText(DEFAULT_SCRIPT.strip())
        self.script_edit.setMinimumHeight(280)

        # Run button centered at bottom
        run_row = QHBoxLayout()
        run_row.setContentsMargins(0, 0, 0, 0)
        
        self.run_button = QPushButton("▶ Run Script")
        self.run_button.setObjectName("primary-action")
        self.run_button.setMinimumWidth(200)
        self.run_button.clicked.connect(self._handle_run_clicked)
        
        run_row.addStretch()
        run_row.addWidget(self.run_button)
        run_row.addStretch()

        lyt.addWidget(self.script_edit)
        lyt.addLayout(run_row)
        return frame

    def _build_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("sidebar")
        lyt = QVBoxLayout(frame)
        lyt.setContentsMargins(12, 20, 12, 20)
        lyt.setSpacing(12)

        self.always_on_top_btn = QToolButton()
        self.always_on_top_btn.setObjectName("pin-button")
        self.always_on_top_btn.setCheckable(True)
        self.always_on_top_btn.setToolTip("항상 위에 고정")
        self.always_on_top_btn.setAutoRaise(True)
        self._set_pin_glyph(False)
        self.always_on_top_btn.toggled.connect(self._handle_pin_toggled)

        lyt.addWidget(self.always_on_top_btn, alignment=Qt.AlignmentFlag.AlignTop)
        lyt.addStretch()
        return frame

    def _build_log_panel(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("log-card")
        lyt = QVBoxLayout(frame)
        lyt.setContentsMargins(18, 18, 18, 18)
        lyt.setSpacing(12)

        # label = QLabel("실행 로그")
        # label.setObjectName("card-title")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(220)
        self.log_output.setPlaceholderText("스크립트 결과가 여기에 표시됩니다.")

        # lyt.addWidget(label)
        lyt.addWidget(self.log_output)
        return frame

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #fafafa;
                color: #2c2c2c;
                font-family: 'Pretendard', 'Pretendard Variable', 'SF Pro Display', 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            #main-area {
                background-color: #fafafa;
            }
            #sidebar {
                background-color: #f5f5f5;
                border-left: 1px solid #e8e8e8;
                min-width: 48px;
                max-width: 48px;
            }
            QToolButton#pin-button {
                border: none;
                color: #888;
                padding: 8px;
                border-radius: 8px;
                background-color: transparent;
                font-size: 18px;
            }
            QToolButton#pin-button:hover {
                background-color: #e8e8e8;
            }
            QToolButton#pin-button:checked {
                color: #4a90e2;
                background-color: #e3f2fd;
            }
            #app-title {
                font-size: 48px;
                font-weight: 700;
                color: #1a1a1a;
                letter-spacing: -1px;
            }
            #app-subtitle {
                font-size: 16px;
                color: #666;
                font-weight: 400;
            }
            #editor-card {
                background-color: transparent;
            }
            QPushButton#action-button {
                background-color: #ffffff;
                border: 1.5px solid #e0e0e0;
                border-radius: 12px;
                padding: 14px 24px;
                color: #333;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton#action-button:hover {
                background-color: #f8f8f8;
                border-color: #ccc;
            }
            QPushButton#action-button:pressed {
                background-color: #f0f0f0;
            }
            QTextEdit#script-editor {
                background-color: #ffffff;
                border: 1.5px solid #e0e0e0;
                border-radius: 12px;
                padding: 16px;
                color: #2c2c2c;
                font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.6;
            }
            QTextEdit#script-editor:focus {
                border-color: #4a90e2;
            }
            QPushButton#primary-action {
                background-color: #4a90e2;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 14px 32px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton#primary-action:hover {
                background-color: #357abd;
            }
            QPushButton#primary-action:pressed {
                background-color: #2868a8;
            }
            QPushButton#primary-action:disabled {
                background-color: #b8d4f1;
            }
            #log-card {
                background-color: #ffffff;
                border: 1.5px solid #e0e0e0;
                border-radius: 12px;
                padding: 4px;
            }
            QTextEdit {
                background-color: #fafafa;
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: #444;
                font-size: 12px;
                font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
            }
            """
        )

    def _handle_run_clicked(self) -> None:
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "진행 중", "이미 스크립트를 실행 중입니다.")
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
        QMessageBox.critical(self, "실행 오류", message)
        self.run_button.setEnabled(True)

    def _handle_finished(self) -> None:
        self._append_log("=== 실행 완료 ===")
        self.run_button.setEnabled(True)

    def _show_howto(self) -> None:
        """Show how to use dialog."""
        howto_text = """
<h3>HMATH AI 사용 방법</h3>

<p><b>1단계:</b> Windows에서 한컴 한글(HWP)을 실행하세요</p>
<p><b>2단계:</b> 문서를 열고 내용을 입력할 위치에 커서를 놓으세요</p>
<p><b>3단계:</b> 에디터에 파이썬 자동화 코드를 작성하거나 붙여넣으세요</p>
<p><b>4단계:</b> "Run Script" 버튼을 클릭하여 실행하세요</p>

<h4>사용 가능한 함수:</h4>
<ul>
<li><code>insert_text("텍스트\\r")</code> - 텍스트 삽입 (\\r은 줄바꿈)</li>
<li><code>insert_paragraph()</code> - 문단 나누기</li>
<li><code>insert_equation("LaTeX")</code> - LaTeX 수식 삽입</li>
<li><code>insert_hwpeqn("HwpEqn")</code> - HWP 수식 형식으로 삽입</li>
<li><code>insert_image("경로/이미지.png")</code> - 이미지 삽입</li>
</ul>

<p><b>참고:</b> Windows 환경과 한컴 한글이 설치되어 있어야 합니다.</p>
"""
        msg = QMessageBox(self)
        msg.setWindowTitle("사용 방법")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(howto_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _show_latex_helper(self) -> None:
        """Show LaTeX code examples."""
        latex_text = """
<h3>LaTeX 수식 예제</h3>

<p><b>기본 수식:</b></p>
<code>insert_equation(r"x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}")</code>

<p><b>아인슈타인 방정식:</b></p>
<code>insert_equation(r"E = mc^2")</code>

<p><b>적분:</b></p>
<code>insert_equation(r"\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}")</code>

<p><b>합 (시그마):</b></p>
<code>insert_equation(r"\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}")</code>

<p><b>행렬:</b></p>
<code>insert_equation(r"\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}")</code>

<p><b>그리스 문자:</b></p>
<code>\\alpha, \\beta, \\gamma, \\theta, \\pi, \\sigma, \\omega</code>

<p><b>기타 기호:</b></p>
<code>\\leq, \\geq, \\neq, \\approx, \\infty, \\partial, \\nabla</code>
"""
        msg = QMessageBox(self)
        msg.setWindowTitle("LaTeX 수식 가이드")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(latex_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _toggle_always_on_top(self, checked: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()

    def _append_log(self, text: str) -> None:
        self.log_output.append(text)

    def _handle_pin_toggled(self, checked: bool) -> None:
        self._set_pin_glyph(checked)
        self._toggle_always_on_top(checked)

    def _set_pin_glyph(self, active: bool) -> None:
        font_name = _ensure_material_icon_font()
        font = QFont(font_name)
        font.setPointSize(28)
        self.always_on_top_btn.setFont(font)
        glyph = "\ue25c" if active else "\ue25d"  # Google Fonts Material Symbols push_pin
        self.always_on_top_btn.setText(glyph)


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


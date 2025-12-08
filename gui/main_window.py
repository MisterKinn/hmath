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
        self.setWindowTitle("AMEX AI • Script Runner")
        self.resize(520, 820)
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
        main_column.setContentsMargins(32, 24, 24, 24)
        main_column.setSpacing(16)
        main_column.addWidget(self._build_header())
        main_column.addWidget(self._build_log_panel(), 1)
        main_column.addWidget(self._build_editor())

        layout.addWidget(main_area, 1)
        layout.addWidget(self._build_sidebar(), 0)
        self.setCentralWidget(central)

    def _build_header(self) -> QWidget:
        frame = QFrame()
        lyt = QVBoxLayout(frame)
        lyt.setSpacing(4)
        title = QLabel("AMEX AI")
        title.setObjectName("app-title")
        # subtitle = QLabel("한글 문서 전용 파이썬 스니펫을 바로 실행하세요.")
        # subtitle.setObjectName("app-subtitle")
        lyt.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        # lyt.addWidget(subtitle)
        return frame

    def _build_editor(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("editor-card")
        lyt = QVBoxLayout(frame)
        lyt.setContentsMargins(18, 18, 18, 18)
        lyt.setSpacing(16)

        # label = QLabel("한글 자동화 코드")
        # label.setObjectName("card-title")

        self.script_edit = QTextEdit()
        self.script_edit.setObjectName("script-editor")
        self.script_edit.setPlaceholderText("예) insert_text('안녕하세요')")
        self.script_edit.setPlainText(DEFAULT_SCRIPT.strip())
        self.script_edit.setMinimumHeight(320)

        self.run_button = QPushButton("실행")
        self.run_button.setObjectName("primary-action")
        self.run_button.clicked.connect(self._handle_run_clicked)

        run_row = QHBoxLayout()
        run_row.setContentsMargins(0, 0, 0, 0)
        run_row.addStretch()
        run_row.addWidget(self.run_button)

        # lyt.addWidget(label)
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
                background-color: #ffffff;
                color: #1b1d29;
                font-family: 'Pretendard', 'Pretendard Variable', 'Malgun Gothic', sans-serif;
                font-size: 13px;
            }
            #card {
                background-color: #ffffff;
                border-radius: 18px;
                border: 1px solid #f0f2f7;
            }
            #log-card {
                background-color: #ffffff;
                border-radius: 18px;
                border: none;
            }
            #editor-card {
                background-color: #f4f5f6;
                border-radius: 18px;
                border: none;
            }
            #main-area {
                background-color: #ffffff;
            }
            #sidebar {
                background-color: #f4f5f6;
                border-left: 1px solid #f0f2f7;
                min-width: 36px;
                max-width: 36px;
            }
            QToolButton#pin-button {
                border: none;
                color: #8c94ad;
                padding: 4px;
                border-radius: 18px;
                background-color: transparent;
            }
            QToolButton#pin-button:checked {
                color: #2d6bff;
                background-color: #e6edff;
            }
            #card-title {
                font-weight: 600;
                font-size: 14px;
                color: #1f2233;
            }
            #app-title {
                font-size: 22px;
                font-weight: 700;
                color: #13162b;
            }
            #app-subtitle {
                color: #5d6075;
            }
            QTextEdit {
                border: 1px solid #d6dae8;
                border-radius: 14px;
                padding: 10px;
                background-color: #ffffff;
                color: #15172a;
            }
            QTextEdit#script-editor {
                background-color: #f4f5f6;
                border: none;
            }
            QPushButton {
                border-radius: 14px;
                padding: 10px 16px;
                background-color: #f0f2f8;
                border: 1px solid #d8dced;
                color: #1f2233;
            }
            QPushButton:hover {
                background-color: #e4e8f5;
            }
            QPushButton#primary-action {
                background-color: #2d6bff;
                color: #ffffff;
                border: none;
            }
            QPushButton#primary-action:disabled {
                background-color: #a6bdfd;
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


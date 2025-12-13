"""AMEX AI script console."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Optional

# Optional speech recognition
try:
    import speech_recognition as sr  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    sr = None  # type: ignore[assignment]

from PySide6.QtCore import Qt, Signal, QThread, QObject, QSize, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QUrl
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPixmap, QTextCursor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
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
    QMenu,
    QLineEdit,
    QDialogButtonBox,
)

from backend.hwp.hwp_controller import HwpController, HwpControllerError
from backend.hwp.script_runner import HwpScriptRunner
from backend.chatgpt_helper import ChatGPTHelper
from backend.backup_manager import BackupManager


class AIWorker(QObject):
    """Worker for running AI tasks in a separate thread."""
    finished = Signal(str)  # Emits the generated/optimized script
    error = Signal(str)  # Emits error message
    thought = Signal(str)  # Emits thought process updates
    
    def __init__(self, chatgpt: ChatGPTHelper, task_type: str, **kwargs):
        super().__init__()
        self.chatgpt = chatgpt
        self.task_type = task_type
        self.kwargs = kwargs
    
    def run(self):
        """Run the AI task."""
        import traceback
        try:
            print(f"[AIWorker] Starting {self.task_type} task...")
            
            def on_thought(message: str):
                print(f"[AIWorker] Thought: {message}")
                self.thought.emit(message)
            
            if self.task_type == "generate":
                print(f"[AIWorker] Calling generate_script...")
                result = self.chatgpt.generate_script(
                    self.kwargs['description'],
                    self.kwargs.get('context', ''),
                    on_thought=on_thought
                )
                print(f"[AIWorker] Generate result: {len(result) if result else 0} chars")
            elif self.task_type == "optimize":
                print(f"[AIWorker] Calling optimize_script...")
                result = self.chatgpt.optimize_script(
                    self.kwargs['script'],
                    self.kwargs.get('feedback', ''),
                    on_thought=on_thought
                )
                print(f"[AIWorker] Optimize result: {len(result) if result else 0} chars")
            else:
                error_msg = "Unknown task type"
                print(f"[AIWorker] ERROR: {error_msg}")
                self.error.emit(error_msg)
                return
            
            if result:
                print(f"[AIWorker] Success! Emitting finished signal")
                self.finished.emit(result)
            else:
                error_msg = "AI returned no result"
                print(f"[AIWorker] ERROR: {error_msg}")
                self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"[AIWorker] EXCEPTION: {error_msg}")
            print(f"[AIWorker] Traceback:\n{error_trace}")
            self.error.emit(f"{error_msg}\n\nTraceback:\n{error_trace}")


class SpeechRecognitionWorker(QThread):
    """Worker for speech recognition in a separate thread."""
    text_recognized = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()

    def run(self) -> None:  # type: ignore[override]
        if sr is None:
            self.error_signal.emit("speech_recognition 라이브러리가 설치되어 있지 않습니다.\npip install SpeechRecognition pyaudio")
            self.finished_signal.emit()
            return

        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=1)
                self.error_signal.emit("🎤 듣는 중... 조용한 곳에서 말씀해주세요.")
                audio = recognizer.listen(source, timeout=10)

            try:
                text = recognizer.recognize_google(audio, language='ko-KR')  # type: ignore[attr-defined]
                self.text_recognized.emit(text)
            except sr.UnknownValueError:
                self.error_signal.emit("음성을 인식할 수 없습니다. 더 명확하게 말씀해주세요.")
            except sr.RequestError as e:
                self.error_signal.emit(f"음성 인식 서비스 오류: {e}")
        except sr.WaitTimeoutError:
            self.error_signal.emit("시간 초과로 음성을 받지 못했습니다.")
        except Exception as e:  # pragma: no cover - hardware dependent
            self.error_signal.emit(f"마이크 오류: {e}")
        finally:
            self.finished_signal.emit()


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

def _create_styled_dialog(parent, title: str, content: str, min_width: int = 500, min_height: int = 0, dark_mode: bool = False, icon_path: str | None = None) -> QMessageBox:
    """Create a styled dialog with enhanced OK button."""
    css = _load_dialog_css()
    dark_class = "dark-mode" if dark_mode else ""
    full_html = f"<style>{css}</style><body class='{dark_class}'>{content}</body>"
    
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setTextFormat(Qt.TextFormat.RichText)
    msg.setText(full_html)
    if icon_path:
        msg.setIconPixmap(QPixmap(icon_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    if icon_path:
        pix = QPixmap(icon_path)
        if not pix.isNull():
            msg.setIconPixmap(pix.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            msg.setIcon(QMessageBox.Icon.NoIcon)
    else:
        msg.setIcon(QMessageBox.Icon.NoIcon)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    
    # Apply QSS styling to the OK button
    button_style = """
        QPushButton {
            background-color: #5377f6;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 24px;
            font-size: 13px;
            font-weight: 600;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #3e5fc7;
        }
        QPushButton:pressed {
            background-color: #2e47a0;
        }
    """
    msg.setStyleSheet(button_style)
    
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
        "icon_key": "write_icon",
        "fallback": "[T]",
        "use_theme": True,
        "code": 'insert_text("여기에 텍스트를 입력하세요.\r")\ninsert_paragraph()'
    },
    "벡터": {
        "icon_key": "vector_icon",
        "fallback": "[V]",
        "use_theme": True,
        "code": 'insert_equation(r"\\vec{a} = \\begin{pmatrix} a_1 \\\\ a_2 \\\\ a_3 \\end{pmatrix}", font_size_pt=14.0)'
    },
    "행렬": {
        "icon_key": "matrix_icon",
        "fallback": "🔢",
        "use_theme": True,
        "code": 'insert_equation(r"A = \\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}", font_size_pt=14.0)'
    },
    "표": {
        "icon_key": "chart_icon",
        "fallback": "📊",
        "use_theme": True,
        "code": '# 3x3 표 생성 예시\ninsert_table(rows=3, cols=3, treat_as_char=False)\n\n# 데이터가 있는 표 생성 예시\n# data = [["항목", "값1", "값2"], ["A", "10", "20"], ["B", "30", "40"]]\n# insert_table(rows=3, cols=3, cell_data=data)'
    },
    "시그마": {
        "icon_key": "",
        "fallback": "Σ",
        "code": 'insert_equation(r"\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}", font_size_pt=14.0)'
    },
    "미분": {
        "icon_key": "",
        "fallback": "∂",
        "code": 'insert_equation(r"\\frac{d}{dx}f(x) = \\lim_{h \\to 0} \\frac{f(x+h)-f(x)}{h}", font_size_pt=13.0)'
    },
    "적분": {
        "icon_key": "",
        "fallback": "∫",
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
            self.error_signal.emit(f"HWP 연결 실패: {exc}\n한컴 에디터가 실행 중인지 확인해보세요.")
        except Exception as exc:
            self.error_signal.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FormuLite")
        self.resize(900, 900)
        self._worker: Optional[ScriptWorker] = None
        self.sr_worker: Optional[SpeechRecognitionWorker] = None
        self.dark_mode = True
        self.chatgpt = ChatGPTHelper()
        self.backup_manager = BackupManager()  # Initialize backup manager
        self.selected_files: list[str] = []  # Track selected files/images
        self._last_hwp_filename = "한글 문서"  # Track last known HWP filename
        self._hwp_detection_timer = QTimer()
        self._hwp_detection_timer.timeout.connect(self._update_hwp_filename)
        self._progress_active = False  # Track if progress message is active
        self._progress_base_text = ""  # Current progress text
        self._progress_fade_count = 0  # Frame counter for fade animation (0-9)
        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._animate_progress_fade)
        self._build_ui()
        self._apply_styles()
        self._hwp_detection_timer.start(500)  # Check every 500ms

    def _apply_button_icon(
        self,
        button,
        icon_key: str,
        fallback_text: str,
        icon_size: QSize = QSize(22, 22),
        preserve_text: bool = False,
    ) -> None:
        """Set an icon on a button if the asset exists, otherwise fall back to text."""
        icon_path = self._get_icon_path(icon_key)
        button.setIcon(QIcon())
        if icon_path:
            button.setIcon(QIcon(str(icon_path)))
            button.setIconSize(icon_size)
            if not preserve_text:
                button.setText("")
        else:
            button.setText(fallback_text)

    def _apply_button_icon_themed(
        self,
        button,
        icon_key: str,
        fallback_text: str,
        icon_size: QSize = QSize(22, 22),
        preserve_text: bool = False,
    ) -> None:
        """Set a theme-aware icon on a button."""
        icon_path = self._get_icon_path(icon_key, use_theme=True)
        button.setIcon(QIcon())
        if icon_path:
            button.setIcon(QIcon(str(icon_path)))
            button.setIconSize(icon_size)
            if not preserve_text:
                button.setText("")
        else:
            if not preserve_text:
                button.setText(fallback_text)

    def _get_icon_path(self, icon_key: str, use_theme: bool = True) -> Path | None:
        """Return themed icon path if available."""
        assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
        theme_suffix = "dark" if self.dark_mode else "light"
        
        if use_theme:
            candidates = [
                f"{icon_key}-{theme_suffix}.svg",
                f"{icon_key}_{theme_suffix}.svg",
                f"{icon_key}.svg",
                f"{icon_key}-{theme_suffix}.png",
                f"{icon_key}_{theme_suffix}.png",
                f"{icon_key}.png",
            ]
            # Prefer explicit black variant in light mode for better contrast
            if not self.dark_mode:
                candidates = [
                    f"{icon_key}_black.png",
                    f"{icon_key}-black.png",
                    *candidates,
                ]
        else:
            candidates = [
                f"{icon_key}.png",
                f"{icon_key}.svg",
            ]
        
        for filename in candidates:
            icon_path = assets_dir / filename
            if icon_path.exists():
                return icon_path
        return None

    def _get_icon_path_str(self, icon_key: str) -> str | None:
        path = self._get_icon_path(icon_key)
        return str(path) if path else None

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
        
        # Header area (title, help buttons, templates)
        self.header_area = QWidget()
        header_layout = QVBoxLayout(self.header_area)
        header_layout.setContentsMargins(40, 40, 40, 0)
        header_layout.setSpacing(20)
        
        header_layout.addWidget(self._build_header())
        header_layout.addWidget(self._build_help_buttons())
        header_layout.addWidget(self._build_templates(), 0)  # No stretch
        
        # Output area (conversation/chat display)
        self.output_area = QWidget()
        self.output_area.setObjectName("output-container")
        output_layout = QVBoxLayout(self.output_area)
        output_layout.setContentsMargins(40, 20, 40, 20)
        output_layout.setSpacing(16)
        
        # Conversation-style output area
        self.log_output = QTextEdit()
        self.log_output.setObjectName("log-output")
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(150)
        # Context menu for log output
        self.log_output.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.log_output.customContextMenuRequested.connect(self._show_log_context_menu)
        output_layout.addWidget(self.log_output, 1)  # Take most space
        
        # Input area at bottom (fixed)
        input_area = QWidget()
        input_area.setObjectName("input-container")
        input_layout = QVBoxLayout(input_area)
        input_layout.setContentsMargins(40, 0, 40, 40)
        input_layout.setSpacing(12)
        
        # Image preview area (initially hidden)
        self.image_preview_container = QWidget()
        self.image_preview_container.setObjectName("image-preview-container")
        self.image_preview_layout = QHBoxLayout(self.image_preview_container)
        self.image_preview_layout.setContentsMargins(0, 0, 0, 8)
        self.image_preview_layout.setSpacing(8)
        self.image_preview_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.image_preview_container.hide()
        input_layout.addWidget(self.image_preview_container)
        
        # Script editor container with buttons inside
        script_container = QWidget()
        script_container.setObjectName("script-input-container")
        script_layout = QVBoxLayout(script_container)
        script_layout.setContentsMargins(14, 14, 14, 14)
        script_layout.setSpacing(12)
        
        # Script editor
        self.script_edit = QTextEdit()
        self.script_edit.setObjectName("script-editor")
        self.script_edit.setPlaceholderText("코드를 작성하거나 붙여넣으세요")
        self.script_edit.setPlainText(DEFAULT_SCRIPT.strip())
        self.script_edit.setMaximumHeight(180)
        self.script_edit.setMinimumHeight(140)
        # Custom context menu in Korean
        self.script_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.script_edit.customContextMenuRequested.connect(self._show_editor_context_menu)
        
        script_layout.addWidget(self.script_edit)
        
        # Bottom row with '+' button for files/images, AI selector, and Run button
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(12)
        
        # Left side: Combined file/image button
        self.add_file_btn = QPushButton("+")
        self.add_file_btn.setObjectName("upload-button")
        self.add_file_btn.setMaximumWidth(40)
        self.add_file_btn.setMinimumWidth(40)
        self.add_file_btn.setMinimumHeight(48)
        self.add_file_btn.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.add_file_btn.setToolTip("파일 또는 이미지 추가")
        self.add_file_btn.clicked.connect(self._handle_add_file)
        self.add_file_btn.setText("")
        self.add_file_btn.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.add_file_btn.setStyleSheet("""
            QToolTip {
                font-size: 11px;
                padding: 4px 8px;
            }
        """)
        self._apply_button_icon(self.add_file_btn, "plus", "+", QSize(32, 32))
        bottom_row.addWidget(self.add_file_btn)
        
        # AI selector button
        self.ai_selector_btn = QPushButton("[AI]")
        self.ai_selector_btn.setObjectName("upload-button")
        self.ai_selector_btn.setMaximumWidth(44)
        self.ai_selector_btn.setMinimumWidth(44)
        self.ai_selector_btn.setMinimumHeight(44)
        self.ai_selector_btn.setToolTip("AI 모델 선택")
        self.ai_selector_btn.clicked.connect(self._show_ai_selector)
        self._apply_button_icon(self.ai_selector_btn, "ai", "[AI]", QSize(28, 28))
        bottom_row.addWidget(self.ai_selector_btn)

        # Model label to the right of the flash/AI icon
        self.model_label = QLabel("GPT-5-nano")
        self.model_label.setObjectName("model-label")
        self.model_label.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #666;"
            "background: transparent; padding: 0 6px; margin: 0;"
        )
        bottom_row.addWidget(self.model_label)
        
        bottom_row.addStretch()
        
        # HWP filename display
        self.hwp_filename_label = QLabel("한글 문서")
        self.hwp_filename_label.setObjectName("hwp-filename")
        self.hwp_filename_label.setStyleSheet("""
            color: #666;
            font-size: 13px;
            font-weight: 500;
            padding: 4px 12px;
            background-color: rgba(128, 128, 128, 0.1);
            border-radius: 6px;
            margin-right: 12px;
        """)
        bottom_row.addWidget(self.hwp_filename_label)
        
        # Microphone button
        self.mic_btn = QPushButton("[MIC]")
        self.mic_btn.setObjectName("upload-button")
        self.mic_btn.setMaximumWidth(44)
        self.mic_btn.setMinimumWidth(44)
        self.mic_btn.setMinimumHeight(44)
        self.mic_btn.setToolTip("음성 입력")
        self.mic_btn.clicked.connect(self._handle_voice_input)
        self._apply_button_icon(self.mic_btn, "mic", "[MIC]", QSize(28, 28))
        bottom_row.addWidget(self.mic_btn)
        
        # Right side: Run button (play icon)
        self.run_button = QPushButton("▶")
        self.run_button.setObjectName("primary-action")
        self.run_button.setMaximumWidth(60)
        self.run_button.setMinimumWidth(60)
        self.run_button.setMinimumHeight(44)
        self.run_button.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.run_button.setToolTip("스크립트를 한글에서 실행합니다 (Ctrl+Enter)")
        self.run_button.clicked.connect(self._handle_run_clicked)
        bottom_row.addWidget(self.run_button)
        
        script_layout.addLayout(bottom_row)
        
        input_layout.addWidget(script_container)

        # Add areas to main column with proper spacing
        main_column.addWidget(self.header_area, 0)      # Header with fixed height
        main_column.addWidget(self.output_area, 2)      # Output takes 2/3 space
        main_column.addWidget(input_area, 1)            # Input takes 1/3 space

        layout.addWidget(main_area, 1)
        layout.addWidget(self._build_sidebar(), 0)
        self.setCentralWidget(central)

    def _build_header(self) -> QWidget:
        frame = QFrame()
        lyt = QVBoxLayout(frame)
        lyt.setSpacing(8)
        lyt.setContentsMargins(0, 0, 0, 0)
        
        # Title with logo
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)
        title_layout.addStretch()
        
        # Logo
        self.logo_label = QLabel()
        self.logo_label.setObjectName("app-logo")
        self.logo_label.setStyleSheet("font-size: 36px; color: #5377f6;")
        self._set_app_logo()
        title_layout.addWidget(self.logo_label)
        
        # Title text
        title = QLabel("FormuLite")
        title.setObjectName("app-title")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        subtitle = QLabel("최고의 한글 수식 자동화 에이전트")
        subtitle.setObjectName("app-subtitle")
        
        lyt.addWidget(title_container, alignment=Qt.AlignmentFlag.AlignCenter)
        lyt.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        return frame

    def _build_help_buttons(self) -> QWidget:
        """Build horizontally aligned help buttons."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        layout.addStretch()
        
        self.howto_button = QPushButton("도움말")
        self.howto_button.setObjectName("help-button")
        self.howto_button.setMaximumWidth(140)
        self.howto_button.setFixedHeight(38)
        self.howto_button.setToolTip("프로그램 사용 방법과 함수 가이드를 제공합니다")
        self.howto_button.clicked.connect(self._show_howto)
        self.howto_button.setText("도움말")
        self._apply_button_icon(self.howto_button, "help", "[?]", QSize(20, 20), preserve_text=True)
        layout.addWidget(self.howto_button)
        
        self.latex_button = QPushButton("</> LaTeX")
        self.latex_button.setObjectName("help-button")
        self.latex_button.setMaximumWidth(140)
        self.latex_button.setFixedHeight(38)
        self.latex_button.setToolTip("LaTeX 수식 문법 가이드를 제공합니다")
        self.latex_button.clicked.connect(self._show_latex_helper)
        layout.addWidget(self.latex_button)
        
        self.ai_generate_button = QPushButton("AI 생성")
        self.ai_generate_button.setObjectName("help-button")
        self.ai_generate_button.setMaximumWidth(140)
        self.ai_generate_button.setFixedHeight(38)
        self.ai_generate_button.setToolTip("AI가 스크립트를 생성합니다")
        self.ai_generate_button.clicked.connect(self._show_ai_generate_dialog)
        self.ai_generate_button.setText("AI 생성")
        self._apply_button_icon(self.ai_generate_button, "generate", "[+]", QSize(20, 20), preserve_text=True)
        layout.addWidget(self.ai_generate_button)
        
        self.ai_optimize_button = QPushButton("AI 최적화")
        self.ai_optimize_button.setObjectName("help-button")
        self.ai_optimize_button.setMaximumWidth(140)
        self.ai_optimize_button.setFixedHeight(38)
        self.ai_optimize_button.setToolTip("AI가 스크립트를 최적화합니다")
        self.ai_optimize_button.clicked.connect(self._show_ai_optimize_dialog)
        self.ai_optimize_button.setText("AI 최적화")
        self._apply_button_icon(self.ai_optimize_button, "optimize", "[*]", QSize(20, 20), preserve_text=True)
        layout.addWidget(self.ai_optimize_button)
        
        layout.addStretch()
        # Apply distinct styling to help buttons based on theme
        self._apply_help_button_style()
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
        
        self.template_buttons: list[tuple[QPushButton, dict]] = []
        for name, template in TEMPLATES.items():
            icon_key = template.get("icon_key", "")
            fallback = template.get("fallback", name[0])
            
            if icon_key:
                btn = QPushButton()
                btn.setObjectName("template-btn")
                btn.setMaximumWidth(140)
                btn.setMinimumHeight(44)
                btn.clicked.connect(lambda checked, code=template["code"]: self._load_template(code))
                btn.setStyleSheet("text-align: right; padding-right: 12px;")
                use_theme = template.get("use_theme", False)
                btn.setText(name)
                if use_theme:
                    self._apply_button_icon_themed(btn, icon_key, fallback, QSize(16, 16), preserve_text=True)
                else:
                    self._apply_button_icon(btn, icon_key, fallback, QSize(16, 16), preserve_text=True)
            else:
                btn = QPushButton(f"{fallback} {name}")
                btn.setObjectName("template-btn")
                btn.setMaximumWidth(140)
                btn.setMinimumHeight(44)
                btn.clicked.connect(lambda checked, code=template["code"]: self._load_template(code))
                btn.setStyleSheet("text-align: right; padding-right: 12px;")
            
            template["label"] = name
            template["fallback_display"] = fallback
            self.template_buttons.append((btn, template))
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
        widget.setStyleSheet(original_style + "\nborder-color: #5377f6 !important;")
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
        self.save_btn.setText("[S]")
        self._apply_button_icon(self.save_btn, "save", "[S]", QSize(32, 32))
        self.save_btn.clicked.connect(self._save_script)

        # Load script button
        self.load_btn = QToolButton()
        self.load_btn.setObjectName("pin-button")
        self.load_btn.setToolTip("스크립트 불러오기")
        self.load_btn.setAutoRaise(True)
        self.load_btn.setText("[L]")
        self._apply_button_icon(self.load_btn, "load", "[L]", QSize(32, 32))
        self.load_btn.clicked.connect(self._load_script)

        # Backup button
        self.backup_icon_btn = QToolButton()
        self.backup_icon_btn.setObjectName("pin-button")
        self.backup_icon_btn.setToolTip("백업 및 복원")
        self.backup_icon_btn.setAutoRaise(True)
        self.backup_icon_btn.setText("[B]")
        self._apply_button_icon_themed(self.backup_icon_btn, "backup_icon", "[B]", QSize(32, 32))
        self.backup_icon_btn.clicked.connect(self._show_backup_menu)

        # Theme button
        self.theme_btn = QToolButton()
        self.theme_btn.setObjectName("pin-button")
        self.theme_btn.setCheckable(True)
        self.theme_btn.setToolTip("다크 모드")
        self.theme_btn.setAutoRaise(True)
        self.theme_btn.setChecked(self.dark_mode)
        self._set_theme_glyph(self.dark_mode)
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
        lyt.addWidget(self.backup_icon_btn, alignment=Qt.AlignmentFlag.AlignTop)
        lyt.addWidget(self.theme_btn, alignment=Qt.AlignmentFlag.AlignTop)
        lyt.addStretch()
        lyt.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        return frame

    def _apply_styles(self) -> None:
        theme = "light" if not self.dark_mode else "dark"
        stylesheet = _load_theme(theme)
        self.setStyleSheet(stylesheet)
        # Re-apply distinct styling for help buttons after loading theme
        self._apply_help_button_style()

    def _apply_help_button_style(self) -> None:
        """Apply a distinct, elegant style for the four help buttons."""
        if not hasattr(self, "howto_button"):
            return

        if self.dark_mode:
            base_bg = "#182036"
            hover_bg = "#202b45"
            press_bg = "#1b2440"
            border_color = "#3b4a6a"
            hover_border = "#4b5d85"
            press_border = "#35466b"
            text_color = "#e8ecf8"
        else:
            base_bg = "#eef3ff"      # gentle blue tint
            hover_bg = "#e3ebff"
            press_bg = "#d8e1ff"
            border_color = "#cad8ff"
            hover_border = "#b9c9fb"
            press_border = "#aebff8"
            text_color = "#1c2d5a"

        style = f"""
        QPushButton {{
            background-color: {base_bg};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 10px;
            padding: 8px 14px;
            font-weight: 600;
            text-align: left;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
            border-color: {hover_border};
        }}
        QPushButton:pressed {{
            background-color: {press_bg};
            border-color: {press_border};
        }}
        """

        for btn in (
            getattr(self, "howto_button", None),
            getattr(self, "latex_button", None),
            getattr(self, "ai_generate_button", None),
            getattr(self, "ai_optimize_button", None),
        ):
            if btn:
                btn.setStyleSheet(style)

    def _set_app_logo(self) -> None:
        """Set main title logo based on theme."""
        if hasattr(self, "logo_label"):
            # Use the formulite_logo files
            assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
            
            # Try .jpg first, then .png
            logo_paths = [
                assets_dir / "formulite_logo.png"
            ]
            
            logo_loaded = False
            for logo_path in logo_paths:
                if logo_path.exists():
                    pix = QPixmap(str(logo_path)).scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.logo_label.setPixmap(pix)
                    self.logo_label.setText("")
                    logo_loaded = True
                    break
            
            if not logo_loaded:
                self.logo_label.setPixmap(QPixmap())
                self.logo_label.setText("[∑]")
                self.logo_label.setStyleSheet("font-size: 36px; color: #5377f6;")

    def _refresh_icons(self) -> None:
        """Reapply themed icons after a theme change."""
        self._apply_button_icon(self.add_file_btn, "plus", "+", QSize(32, 32))
        self._apply_button_icon(self.ai_selector_btn, "ai", "[AI]", QSize(28, 28))
        self._apply_button_icon(self.mic_btn, "mic", "[MIC]", QSize(28, 28))
        self.howto_button.setText("도움말")
        self._apply_button_icon(self.howto_button, "help", "[?]", QSize(20, 20), preserve_text=True)
        self.ai_generate_button.setText("AI 생성")
        self._apply_button_icon(self.ai_generate_button, "generate", "[+]", QSize(20, 20), preserve_text=True)
        self.ai_optimize_button.setText("AI 최적화")
        self._apply_button_icon(self.ai_optimize_button, "optimize", "[*]", QSize(20, 20), preserve_text=True)
        # Ensure help buttons keep their distinct inline styling after icon refresh
        self._apply_help_button_style()
        self._apply_button_icon(self.save_btn, "save", "[S]", QSize(32, 32))
        self._apply_button_icon(self.load_btn, "load", "[L]", QSize(32, 32))
        self._apply_button_icon_themed(self.backup_icon_btn, "backup_icon", "[B]", QSize(32, 32))
        self._set_theme_glyph(self.dark_mode)
        self._set_settings_glyph()
        if hasattr(self, "template_buttons"):
            for btn, template in self.template_buttons:
                icon_key = template.get("icon_key", "")
                fallback = template.get("fallback_display", btn.text()[:1])
                label = template.get("label", "")
                use_theme = template.get("use_theme", False)
                
                if icon_key:
                    btn.setText(label)
                    if use_theme:
                        self._apply_button_icon_themed(
                            btn,
                            icon_key,
                            fallback,
                            QSize(16, 16),
                            preserve_text=True,
                        )
                    else:
                        self._apply_button_icon(
                            btn,
                            icon_key,
                            fallback,
                            QSize(16, 16),
                            preserve_text=True,
                        )
                else:
                    btn.setText(f"{fallback} {label}")
        self._set_app_logo()

    def _show_log_context_menu(self, pos) -> None:
        """Custom right-click menu for the log output (Korean labels)."""
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: rgba(40, 40, 40, 0.96);
                color: #f4f4f4;
                border: 1px solid #4a4a4a;
                padding: 6px 4px;
                border-radius: 8px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: #5377f6;
                color: white;
            }
            """
        )

        actions = [
            ("잘라내기", self.log_output.cut),
            ("복사", self.log_output.copy),
            ("모두 선택", self.log_output.selectAll),
        ]

        for label, handler in actions:
            act = menu.addAction(label)
            act.triggered.connect(handler)

        menu.exec(self.log_output.mapToGlobal(pos))

    def _show_editor_context_menu(self, pos) -> None:
        """Custom right-click menu for the editor (Korean labels)."""
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: rgba(40, 40, 40, 0.96);
                color: #f4f4f4;
                border: 1px solid #4a4a4a;
                padding: 6px 4px;
                border-radius: 8px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: #5377f6;
                color: white;
            }
            """
        )

        actions = [
            ("실행 취소", self.script_edit.undo),
            ("다시 실행", self.script_edit.redo),
            ("잘라내기", self.script_edit.cut),
            ("복사", self.script_edit.copy),
            ("붙여넣기", self.script_edit.paste),
            ("모두 선택", self.script_edit.selectAll),
            ("내용 지우기", self.script_edit.clear),
        ]

        for label, handler in actions:
            act = menu.addAction(label)
            act.triggered.connect(handler)

        menu.exec(self.script_edit.mapToGlobal(pos))

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
        self._append_log(f"❌ {message}")
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

    def _handle_file_upload(self) -> None:
        """Handle file upload button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "파일 선택",
            "",
            "All Files (*)"
        )
        if file_path:
            # Insert file path reference into script
            file_ref = f'insert_image("{file_path}")'
            current = self.script_edit.toPlainText()
            self.script_edit.setPlainText(current + "\n" + file_ref)

    def _handle_photo_upload(self) -> None:
        """Handle photo upload button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "파일 선택",
            "",
            "All Files (*)"
        )
        if file_path:
            # Insert image path reference into script
            img_ref = f'insert_image("{file_path}")'
            current = self.script_edit.toPlainText()
            self.script_edit.setPlainText(current + "\n" + img_ref)

    def _handle_add_file(self) -> None:
        """Handle combined file/image upload button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "파일 또는 이미지 선택",
            "",
            "All Files (*)"
        )
        if file_path:
            # Insert file path reference into script
            file_ref = f'insert_image("{file_path}")'
            current = self.script_edit.toPlainText()
            self.script_edit.setPlainText(current + "\n" + file_ref)
            self._append_log(f"파일 추가됨: {Path(file_path).name}")
            self._add_image_preview(file_path)
            
            # Update HWP filename if it's a document
            filename = Path(file_path).name
            if filename.lower().endswith(('.hwp', '.hwpx')):
                self.hwp_filename_label.setText(filename)

    def _add_image_preview(self, file_path: str) -> None:
        """Add image preview thumbnail."""
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale to higher-quality thumbnail size
                scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                # Create preview label
                preview_label = QLabel()
                preview_label.setPixmap(scaled)
                preview_label.setFixedSize(120, 120)
                preview_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                preview_label.setStyleSheet("""
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    padding: 2px;
                    background-color: white;
                """)
                
                self.image_preview_layout.addWidget(preview_label, alignment=Qt.AlignmentFlag.AlignLeft)
                self.image_preview_container.show()
        except Exception as e:
            print(f"Error adding image preview: {e}")

    def _show_ai_selector(self) -> None:
        """Show AI model selector dialog."""
        # Placeholder for AI model selection
        # TODO: Implement AI model dropdown/menu with options like GPT-4, GPT-3.5, etc.
        # Suppress alert until feature is implemented
        return

    def _handle_voice_input(self) -> None:
        """Handle microphone/voice input button click."""
        if sr is None:
            self._show_error_dialog(
                "음성 인식을 위해 SpeechRecognition 패키지가 필요합니다.\n\npip install SpeechRecognition pyaudio"
            )
            return

        if self.sr_worker and self.sr_worker.isRunning():
            self._append_log("🎤 이미 음성을 듣고 있어요. 잠시만 기다려주세요.")
            return

        self.mic_btn.setEnabled(False)
        self.mic_btn.setText("")
        self._apply_button_icon(self.mic_btn, "mic", "[MIC]", QSize(28, 28))
        self._append_log("🎤 음성을 듣는 중...")

        self.sr_worker = SpeechRecognitionWorker()
        self.sr_worker.text_recognized.connect(self._on_voice_text)
        self.sr_worker.error_signal.connect(self._on_voice_error)
        self.sr_worker.finished_signal.connect(self._on_voice_finished)
        self.sr_worker.start()

    def _on_voice_text(self, text: str) -> None:
        """Handle recognized speech text."""
        clean = text.strip()
        if not clean:
            self._append_log("받은 음성 텍스트가 비어 있습니다.")
            return

        self._append_log(f"🗣️ 음성 입력: {clean}")

        cursor = self.script_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        insert_text = clean
        if self.script_edit.toPlainText().strip():
            insert_text = "\n" + clean
        cursor.insertText(insert_text)
        self.script_edit.setTextCursor(cursor)
        self._animate_focus(self.script_edit)
        self._append_log("📝 음성 인식 결과를 편집기에 추가했습니다.")

    def _on_voice_error(self, message: str) -> None:
        """Handle speech recognition errors or status updates."""
        self._append_log(message)

    def _on_voice_finished(self) -> None:
        """Re-enable mic button after speech recognition completes."""
        self.mic_btn.setEnabled(True)
        self.mic_btn.setText("[MIC]")
        self._apply_button_icon(self.mic_btn, "mic", "[MIC]", QSize(28, 28))
        self.sr_worker = None

    def _show_help_menu(self) -> None:
        """Show help menu dialog."""
        content = """
<h2>도움말</h2>

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
        <span class="setting-label">스크립트 저장</span>
        <span class="setting-value">작성한 코드 저장</span>
    </div>
    <div class="setting-item">
        <span class="setting-label">스크립트 불러오기</span>
        <span class="setting-value">저장된 코드 불러오기</span>
    </div>
    <div class="setting-item">
        <span class="setting-label">다크 모드</span>
        <span class="setting-value">테마 전환</span>
    </div>
    <div class="setting-item">
        <span class="setting-label">설정</span>
        <span class="setting-value">앱 정보 및 설정</span>
    </div>
</div>

<div class="info-box">
    <strong>문의사항:</strong> GitHub Issues를 통해 버그 리포트 및 기능 제안을 해주세요
</div>
"""
        msg = _create_styled_dialog(
            self,
            "도움말",
            content,
            550,
            dark_mode=self.dark_mode,
            icon_path=self._get_icon_path_str("help"),
        )
        msg.exec()

    def _show_error_dialog(self, message: str) -> None:
        """Show elegant error dialog."""
        error_content = f"""
<div class="error-container">
    <span class="error-title">실행 오류가 발생했습니다</span>
    
    <div class="error-message">
        {message}
    </div>
    
    <div class="help-text">
        <strong>도움말:</strong> Windows에서 한글이 실행 중인지 확인하세요. 문서가 열려있고 커서가 입력 가능한 위치에 있어야 합니다.
    </div>
</div>
"""
        msg = _create_styled_dialog(
            self,
            "오류",
            error_content,
            500,
            dark_mode=self.dark_mode,
            icon_path=self._get_icon_path_str("error"),
        )
        msg.exec()

    def _show_info_dialog(self, title: str, message: str) -> None:
        """Show elegant info dialog."""
        info_content = f"""
<div class="info-container">
    <span class="info-title">{title}</span>
    
    <div class="info-message">
        {message}
    </div>
</div>
"""
        msg = _create_styled_dialog(
            self,
            title,
            info_content,
            450,
            dark_mode=self.dark_mode,
            icon_path=self._get_icon_path_str("info"),
        )
        msg.exec()

    def _show_warning_dialog(self, title: str, message: str) -> None:
        """Show warning dialog."""
        warning_content = f"""
<div class="warning-container">
    <span class="warning-title">{title}</span>
    
    <div class="warning-message">
        {message}
    </div>
</div>
"""
        msg = _create_styled_dialog(
            self,
            title,
            warning_content,
            400,
            dark_mode=self.dark_mode,
            icon_path=self._get_icon_path_str("warning"),
        )
        msg.exec()

    def _handle_finished(self) -> None:
        self._append_log("=== 실행 완료 ===")
        self.run_button.setEnabled(True)
        self._show_success_animation()

    def _show_success_animation(self) -> None:
        """Show success indicator animation."""
        success = QLabel("")
        success.setObjectName("success-indicator")
        success.setStyleSheet("color: #5377f6; font-size: 28px;")
        
        # Show briefly in the conversation area
        self._append_log("[V] 스크립트가 성공적으로 완료되었습니다!")

    def _toggle_theme(self, checked: bool) -> None:
        """Toggle between light and dark theme."""
        self.dark_mode = checked
        self._apply_styles()
        self._refresh_icons()

    def _set_theme_glyph(self, active: bool) -> None:
        """Set theme toggle icon."""
        self.theme_btn.setText("[o]")
        if active:
            self._apply_button_icon(self.theme_btn, "light", "[O]", QSize(32, 32))
        else:
            self._apply_button_icon(self.theme_btn, "moon", "[o]", QSize(32, 32))

    def _show_howto(self) -> None:
        """Show how to use dialog."""
        # Get icon paths
        save_icon = self._get_icon_path_str("save") or ""
        load_icon = self._get_icon_path_str("load") or ""
        light_icon = self._get_icon_path_str("light") or ""
        settings_icon = self._get_icon_path_str("settings") or ""
        
        howto_content = f"""
<style>
  .functions {{ margin-top: 12px; }}
  .func-item {{ display: flex; flex-direction: column; gap: 2px; margin-bottom: 10px; }}
  .func-item code {{ background: #f3f4f6; color: #111827; padding: 6px 8px; border-radius: 8px; display: inline-block; }}
  .dark-mode .func-item code {{ background: #1f2937; color: #e5e7eb; }}
  .func-item small {{ color: #666; }}
  .dark-mode .func-item small {{ color: #9ca3af; }}
</style>

<h2>❓ HMATH AI 사용 가이드</h2>

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
    <h3>텍스트 작성 함수</h3>
    
    <div class="func-item">
        <code>insert_text("텍스트\\r")</code>
        <small>텍스트 삽입 (\\r은 줄바꿈)</small>
    </div>
    
    <div class="func-item">
        <code>insert_paragraph()</code>
        <small>문단 나누기</small>
    </div>
    
    <div class="func-item">
        <code>insert_equation("LaTeX")</code>
        <small>LaTeX 수식 삽입</small>
    </div>
    
    <div class="func-item">
        <code>insert_hwpeqn("HwpEqn")</code>
        <small>HWP 수식 형식으로 삽입</small>
    </div>
    
    <div class="func-item">
        <code>insert_image("경로/이미지.png")</code>
        <small>이미지 삽입</small>
    </div>
</div>

<div class="functions">
    <h3>주요 기능</h3>
    
    <div class="func-item">
        <img src='{save_icon}' style='width:18px; height:18px; vertical-align:middle; padding-right:12px;' />스크립트 저장
        <small style="padding-left: 5px; margin-left: 5px;">현재 에디터의 코드를 Python 파일로 저장</small>
    </div>
    
    <div class="func-item">
        <img src='{load_icon}' style='width:18px; height:18px; vertical-align:middle; padding-right:12px;' />스크립트 불러오기
        <small style="padding-left: 5px; margin-left: 5px;" >저장된 코드 파일을 에디터에 불러오기</small>
    </div>
    
    <div class="func-item">
        <img src='{light_icon}' style='width:18px; height:18px; vertical-align:middle; padding-right:12px;' />다크 모드
        <small style="padding-left: 5px; margin-left: 5px;">밝은 테마와 어두운 테마 전환</small>
    </div>
    
    <div class="func-item">
        <img src='{settings_icon}' style='width:18px; height:18px; vertical-align:middle; padding-right:12px;' />설정
        <small style="padding-left: 5px; margin-left: 5px;">앱 정보 및 단축키 확인</small>
    </div>
</div>
"""
        msg = _create_styled_dialog(
            self,
            "사용 방법",
            howto_content,
            600,
            dark_mode=self.dark_mode,

        )
        msg.exec()

    def _show_latex_helper(self) -> None:
        """Show LaTeX code examples."""
        latex_content = r"""
<style>
    table.guide { width: 100%; border-collapse: collapse; }
    table.guide td { vertical-align: top; padding: 0 12px 0 0; }
    .section { margin-bottom: 16px; }
    .section-title { font-weight: 700; margin-bottom: 6px; }
    .codes { display: block; }
    .codes code { display: block; background: #f3f4f6; color: #111827; padding: 6px 8px; border-radius: 8px; margin-bottom: 6px; }
    .dark-mode .codes code { background: #1f2937; color: #e5e7eb; }
    .codes.inline code { display: inline-block; margin-right: 8px; margin-bottom: 6px; background: transparent; color: #111827; padding: 0; border-radius: 0; }
    .dark-mode .codes.inline code { background: #1f2937; color: #e5e7eb; }
</style>

<h2>📐 LaTeX 수식 가이드</h2>

<table class="guide">
    <tr>
        <td width="33%">
            <div class="section">
                <div class="section-title">기본 수식</div>
                <div class="codes">
                    <code>x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}</code>
                    <code>E = mc^2</code>
                </div>
            </div>
            <div class="section">
                <div class="section-title">적분</div>
                <div class="codes">
                    <code>\int_{0}^{\infty} e^{-x^2} dx</code>
                    <code>\int x^n dx = \frac{x^{n+1}}{n+1}</code>
                </div>
            </div>
            <div class="section">
                <div class="section-title">합 & 곱</div>
                <div class="codes">
                    <code>\sum_{i=1}^{n} i = \frac{n(n+1)}{2}</code>
                    <code>\prod_{i=1}^{n} a_i</code>
                </div>
            </div>
            <div class="section">
                <div class="section-title">분수 & 제곱근</div>
                <div class="codes">
                    <code>\frac{a}{b}</code>
                    <code>\sqrt{x}, \sqrt[n]{x}</code>
                </div>
            </div>
        </td>
        <td width="33%">
            <div class="section">
                <div class="section-title">미분 & 극한</div>
                <div class="codes">
                    <code>\frac{df}{dx}, f'(x)</code>
                    <code>\lim_{x \to \infty} f(x)</code>
                </div>
            </div>
            <div class="section">
                <div class="section-title">행렬</div>
                <div class="codes">
                    <code>\begin{bmatrix}<br>a & b \\<br>c & d<br>\end{bmatrix}</code>
                    <code>\begin{pmatrix}<br>1 & 2 \\<br>3 & 4<br>\end{pmatrix}</code>
                </div>
            </div>
            <div class="section">
                <div class="section-title">괄호</div>
                <div class="codes">
                    <code>\left( x \right)</code>
                    <code>\left[ x \right)</code>
                    <code>\left\{ x \right\}</code>
                </div>
            </div>
            <div class="section">
                <div class="section-title">분할 식</div>
                <div class="codes">
                    <code>f(x) = \begin{cases}<br>x^2 & x \geq 0 \\<br>-x & x < 0<br>\end{cases}</code>
                </div>
            </div>
        </td>
        <td width="33%">
            <div class="section">
                <div class="section-title">기타</div>
                <div class="codes">
                    <code>\binom{n}{k}</code>
                    <code>\frac{\partial f}{\partial x}</code>
                </div>
            </div>
            <div class="section">
                <div class="section-title">그리스 문자 (소문자)</div>
                <div class="codes inline">
                    <code>\alpha</code><code>\beta</code><code>\gamma</code><code>\delta</code>
                    <code>\epsilon</code><code>\theta</code><code>\lambda</code><code>\mu</code>
                    <code>\pi</code><code>\sigma</code><code>\phi</code><code>\omega</code>
                </div>
            </div>
            <div class="section">
                <div class="section-title">그리스 문자 (대문자)</div>
                <div class="codes inline">
                    <code>\Gamma</code><code>\Delta</code><code>\Theta</code><code>\Lambda</code>
                    <code>\Pi</code><code>\Sigma</code><code>\Phi</code><code>\Omega</code>
                </div>
            </div>
            <div class="section">
                <div class="section-title">관계 & 집합</div>
                <div class="codes inline">
                    <code>\leq</code><code>\geq</code><code>\neq</code><code>\approx</code>
                    <code>\in</code><code>\subset</code><code>\cap</code><code>\cup</code>
                </div>
            </div>
            <div class="section">
                <div class="section-title">논리 & 기타</div>
                <div class="codes inline">
                    <code>\exists</code><code>\forall</code><code>\Rightarrow</code>
                    <code>\infty</code><code>\partial</code><code>\nabla</code>
                </div>
            </div>
        </td>
    </tr>
</table>
"""
        msg = _create_styled_dialog(
            self,
            "LaTeX 수식 가이드",
            latex_content,
            900,
            600,
            dark_mode=self.dark_mode,

        )
        msg.exec()

    def _append_log(self, text: str) -> None:
        """Append message to log output."""
        self.log_output.append(text)

    def _append_user_input(self, text: str) -> None:
        """Append user input to log output with right alignment and speech balloon emoji."""
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # Add spacing if there's already content
        if self.log_output.toPlainText().strip():
            cursor.insertBlock()
        
        # Create block format for right alignment
        block_format = cursor.blockFormat()
        block_format.setAlignment(Qt.AlignmentFlag.AlignRight)
        cursor.setBlockFormat(block_format)
        
        # Set character format for user message
        char_format = cursor.charFormat()
        char_format.setForeground(QColor(100, 150, 200))
        
        cursor.setCharFormat(char_format)
        # Add speech balloon emoji to the left of the text
        cursor.insertText(f"\n\n💬 {text}")
        
        # Add newline for spacing
        cursor.insertBlock()
        block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor.setBlockFormat(block_format)
        
        self.log_output.setTextCursor(cursor)

    def _update_progress_message(self, base_text: str) -> None:
        """Update progress message with fade animation on text change."""
        # If this is a new progress message (different text), trigger fade animation
        if self._progress_base_text != base_text:
            self._progress_base_text = base_text
            self._progress_fade_count = 0  # Reset fade animation
            
            # If no progress started yet, add a new line
            if not self._progress_active:
                self.log_output.append(base_text)
                self._progress_active = True  # Mark that progress is active
            else:
                # Progress already active, replace the last line with new text
                cursor = self.log_output.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                cursor.select(cursor.SelectionType.LineUnderCursor)
                if cursor.selectedText():
                    cursor.removeSelectedText()
                self.log_output.append(base_text)
            
            # Start fade animation (20 frames total: 10 fade-out, 10 fade-in)
            self._progress_timer.start(50)  # 50ms per frame = 500ms total transition
        else:
            # Same text, continue animation
            pass

    def _animate_progress_fade(self) -> None:
        """Apply fade-in/fade-out animation when text changes with cycling dots."""
        if not self._progress_active:
            self._progress_timer.stop()
            return
        
        # Fade animation: frames 0-19 (total 20 frames)
        frame = self._progress_fade_count
        self._progress_fade_count = (self._progress_fade_count + 1) % 20
        
        # Calculate opacity: fade out (0-9), then fade in (10-19)
        if frame < 10:  # Fade out: 1.0 to 0.0
            opacity = 1.0 - (frame / 10.0)
        else:  # Fade in: 0.0 to 1.0
            opacity = (frame - 10) / 10.0
        
        # Cycling dots: . → .. → ... → (empty) → repeat (slower cycle with 8 states)
        # Hide dots when completion message appears
        if "생성 완료:" in self._progress_base_text or "최적화 완료:" in self._progress_base_text:
            dots = ""  # No dots for completion messages
        else:
            dot_cycle = frame % 100  # Even slower: 16 states instead of 8
            if dot_cycle < 3:
                dots = "."  # 1 dot
            elif dot_cycle < 6:
                dots = ".."  # 2 dots
            elif dot_cycle < 9:
                dots = "..."  # 3 dots
            else:
                dots = ""  # Empty
        
        updated_text = f"{self._progress_base_text}{dots}"
        
        # Interpolate color from dim (100) to normal (150)
        dim_gray = 100
        normal_gray = 150
        color_value = int(dim_gray + (normal_gray - dim_gray) * opacity)
        
        # Apply the fade effect to the last line
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # Select entire last line
        cursor.select(cursor.SelectionType.LineUnderCursor)
        selected_text = cursor.selectedText()
        
        # Only apply formatting if we have a progress message
        if selected_text:
            # Remove the old text and insert new one with dots
            cursor.removeSelectedText()
            cursor.insertText(updated_text)
            
            # Apply the color to the selected text
            char_format = cursor.charFormat()
            char_format.setForeground(QColor(color_value, color_value, color_value))
            cursor.setCharFormat(char_format)

    def _clear_progress_message(self) -> None:
        """Clear the active progress message."""
        self._progress_timer.stop()
        self._progress_active = False
        self._progress_base_text = ""
        self._progress_fade_count = 0

    def _set_settings_glyph(self) -> None:
        """Set settings icon."""
        self.settings_btn.setText("[#]")
        self._apply_button_icon(self.settings_btn, "settings", "[#]", QSize(32, 32))

    def _show_settings(self) -> None:
        """Show settings dialog."""
        settings_icon = self._get_icon_path_str("settings") or ""
        settings_content = f"""
    <div style='margin-bottom: 20px;'>
        <h2 style='font-size: 20px; margin: 0; padding: 0;'>⚙️ 설정</h2>
    </div>

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
        msg = _create_styled_dialog(
            self,
            "⚙️ 설정",
            settings_content,
            550,
            dark_mode=self.dark_mode,
            icon_path=None,
        )
        msg.exec()

    def _voice_to_text(self) -> Optional[str]:
        """Convert voice input to text using speech recognition."""
        if sr is None:
            self._show_error_dialog(
                "음성 인식 기능을 사용할 수 없습니다.\n\n"
                "speech_recognition 패키지를 설치해주세요:\n"
                "pip install SpeechRecognition pyaudio"
            )
            return None
        
        recognizer = sr.Recognizer()  # type: ignore[attr-defined]
        try:
            with sr.Microphone() as source:  # type: ignore[attr-defined]
                self._append_log("🎤 음성을 듣고 있습니다...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)  # type: ignore[attr-defined]
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)  # type: ignore[attr-defined]
                self._append_log("🔄 음성을 텍스트로 변환 중...")
                
                # Try Korean first, then fallback to English
                try:
                    text = recognizer.recognize_google(audio, language="ko-KR")  # type: ignore[attr-defined]
                    self._append_log(f"✅ 인식 완료: {text}")
                    return text
                except sr.UnknownValueError:  # type: ignore[attr-defined]
                    try:
                        text = recognizer.recognize_google(audio, language="en-US")  # type: ignore[attr-defined]
                        self._append_log(f"✅ 인식 완료: {text}")
                        return text
                    except sr.UnknownValueError:  # type: ignore[attr-defined]
                        self._append_log("❌ 음성을 인식할 수 없습니다.")
                        return None
        except sr.WaitTimeoutError:  # type: ignore[attr-defined]
            self._append_log("❌ 음성 입력 시간이 초과되었습니다.")
            return None
        except Exception as e:
            self._append_log(f"❌ 음성 인식 오류: {str(e)}")
            return None

    def _show_ai_generate_dialog(self) -> None:
        """Show dialog to generate script with ChatGPT."""
        if not self.chatgpt.is_available():
            self._show_error_dialog(
                "ChatGPT API를 사용할 수 없습니다.\n\n"
                "자세한 사항은 개발진에게 문의해주세요."
            )
            return

        # Use a simple text input via QMessageBox
        text, ok = self._get_text_input(
            "[+] AI 스크립트 생성",
            "스크립트 생성을 위한 설명을 입력하세요\n\n"
            "예) '처음에 \"수학 문제\"라는 제목을 입력하고,\n"
            "그 아래에 이차방정식 공식을 삽입하는 코드를 작성해줘.'",
            enable_voice=True
        )
        
        if ok and text.strip():
            self._generate_script_with_ai(text)

    def _show_ai_optimize_dialog(self) -> None:
        """Show dialog to optimize current script with ChatGPT."""
        if not self.chatgpt.is_available():
            self._show_error_dialog(
                "ChatGPT API를 사용할 수 없습니다.\n\n"
                "자세한 사항은 개발진에게 문의해주세요."
            )
            return

        current_script = self.script_edit.toPlainText()
        if not current_script.strip():
            self._show_info_dialog("알림", "최적화할 스크립트가 없습니다.")
            return

        text, ok = self._get_text_input(
            "[*] AI 스크립트 최적화",
            "최적화 요청사항을 입력하세요\n\n"
            "예) '코드를 더 간결하게 만들어줘'\n"
            "'오류 처리를 추가해줘'\n\n"
            "(비워두면 기본적인 최적화가 진행됩니다)",
            enable_voice=True
        )
        
        if ok:
            self._optimize_script_with_ai(text)

    def _get_text_input(self, title: str, prompt: str, enable_voice: bool = False) -> tuple[str, bool]:
        """Get text input from user via custom styled dialog with buttons inside form."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        
        # Set dialog background color
        dialog.setStyleSheet("""
            QDialog {
                background-color: %s;
            }
        """ % ("#000000" if self.dark_mode else "#ffffff"))
        
        # Create main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Centered description label
        desc_label = QLabel(prompt)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #e8e8e8;
                font-size: 13px;
                line-height: 1.6;
            }
        """ if self.dark_mode else """
            QLabel {
                color: #2c2c2c;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        
        main_layout.addWidget(desc_label)
        
        # Create input container with buttons inside
        input_container = QWidget()
        input_container.setObjectName("input-container")
        input_container.setStyleSheet("""
            QWidget#input-container {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 12px;
            }
        """ % (
            "#1a1a1a" if self.dark_mode else "#f3f4f6",
            "#4a4a4a" if self.dark_mode else "#d1d5db"
        ))
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(12)
        
        # Styled input field to match main page
        input_field = QTextEdit()
        input_field.setObjectName("script-editor")
        input_field.setMinimumHeight(120)
        input_field.setMinimumWidth(400)
        input_field.setMaximumHeight(200)
        input_field.setPlaceholderText("여기에 입력하세요")
        
        input_layout.addWidget(input_field)
        
        # Button row at bottom (inside input form)
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(12)
        
        # Voice button on the left (if enabled)
        voice_btn = None
        if enable_voice and sr is not None:
            voice_btn = QPushButton("[MIC]")
            voice_btn.setObjectName("upload-button")
            voice_btn.setMaximumWidth(44)
            voice_btn.setMinimumWidth(44)
            voice_btn.setMinimumHeight(36)
            voice_btn.setToolTip("음성으로 입력하기")
            
            def on_voice_click():
                dialog.hide()  # Hide dialog while recording
                voice_text = self._voice_to_text()
                dialog.show()  # Show dialog again
                if voice_text:
                    current_text = input_field.toPlainText()
                    if current_text:
                        input_field.setPlainText(current_text + " " + voice_text)
                    else:
                        input_field.setPlainText(voice_text)
            
            voice_btn.clicked.connect(on_voice_click)
            button_row.addWidget(voice_btn)
        
        button_row.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary-button")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.setMaximumWidth(100)
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setStyleSheet(
            "background: transparent; border: none; font-weight: bold; padding: 8px 14px;"
        )
        
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primary-action")
        ok_btn.setMaximumWidth(80)
        ok_btn.setMinimumHeight(32)
        
        button_row.addWidget(cancel_btn)
        button_row.addWidget(ok_btn)
        
        input_layout.addLayout(button_row)
        
        main_layout.addWidget(input_container)
        
        # Apply theme to text editor
        theme_name = "dark" if self.dark_mode else "light"
        theme_qss = _load_theme(theme_name)
        input_field.setStyleSheet(theme_qss)
        
        # Apply mic icon to voice button (same as main window)
        if voice_btn is not None:
            self._apply_button_icon(voice_btn, "mic", "[MIC]", QSize(28, 28))
        
        # Handle button clicks
        ok_clicked = False
        def on_ok():
            nonlocal ok_clicked
            print("[Dialog] OK button clicked!")
            ok_clicked = True
            dialog.accept()
        
        def on_cancel():
            nonlocal ok_clicked
            print("[Dialog] Cancel button clicked!")
            ok_clicked = False
            dialog.reject()
        
        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(on_cancel)
        
        print("[Dialog] Showing dialog...")
        result = dialog.exec()
        print(f"[Dialog] Dialog closed. Result: {result}, OK clicked: {ok_clicked}")
        return input_field.toPlainText(), ok_clicked

    def _generate_script_with_ai(self, description: str) -> None:
        """Generate script using ChatGPT API."""
        print("[MainWindow] _generate_script_with_ai called")
        
        # Display user's input on the right side
        self._append_user_input(description)
        
        self.run_button.setEnabled(False)
        self.ai_generate_button.setEnabled(False)
        self.ai_optimize_button.setEnabled(False)
        
        # Get available functions context
        context = """
사용 가능한 함수들:
- insert_text(text): 텍스트 삽입
- insert_paragraph(): 문단 추가
- insert_equation(latex_code, font_size_pt=14.0): LaTeX 수식 삽입
- insert_hwpeqn(hwpeqn_code, font_size_pt=12.0): HWP 수식 형식 삽입
- insert_image(image_path): 이미지 삽입
"""
        
        # Create worker and thread
        print("[MainWindow] Creating QThread and AIWorker...")
        self.ai_thread = QThread()
        self.ai_worker = AIWorker(self.chatgpt, "generate", description=description, context=context)
        self.ai_worker.moveToThread(self.ai_thread)
        print("[MainWindow] Worker moved to thread")
        
        # Connect signals
        print("[MainWindow] Connecting signals...")
        self.ai_thread.started.connect(self.ai_worker.run)
        self.ai_worker.thought.connect(self._on_ai_thought)
        self.ai_worker.finished.connect(self._on_generate_finished)
        self.ai_worker.error.connect(self._on_generate_error)
        self.ai_worker.finished.connect(self.ai_thread.quit)
        self.ai_worker.error.connect(self.ai_thread.quit)
        self.ai_thread.finished.connect(self.ai_thread.deleteLater)
        print("[MainWindow] Signals connected")
        
        # Start the thread
        print("[MainWindow] Starting thread...")
        self.ai_thread.start()
        print("[MainWindow] Thread started!")
    
    def _on_generate_finished(self, generated_code: str) -> None:
        """Handle successful script generation."""
        # Replace the progress line with completion message - triggers fade transition
        completion_msg = "✅ 스크립트 생성 완료!"
        
        # Update with completion message (will trigger fade animation)
        self._update_progress_message(completion_msg)
        
        # Parse all sections from response
        code = ""
        description = ""
        
        def extract_section(text: str, tag: str) -> str:
            """Extract content between tags."""
            open_tag = f"[{tag}]"
            close_tag = f"[/{tag}]"
            if open_tag in text and close_tag in text:
                start = text.index(open_tag) + len(open_tag)
                end = text.index(close_tag)
                return text[start:end].strip()
            return ""
        
        code = extract_section(generated_code, "CODE")
        description = extract_section(generated_code, "DESCRIPTION")
        
        # Wait for animation to complete before clearing
        def finish_animation():
            self._clear_progress_message()
            # Display code with Korean label
            if code:
                self._append_log("\n\n💻 코드")
                self._append_log(code)
            # Display description with Korean label
            if description:
                self._append_log("\n📝 설명")
                self._append_log(description)
            # Put code in editor
            if code:
                self.script_edit.setPlainText(code)
            self.run_button.setEnabled(True)
            self.ai_generate_button.setEnabled(True)
            self.ai_optimize_button.setEnabled(True)
        
        QTimer.singleShot(600, finish_animation)
    
    def _on_generate_error(self, error_msg: str) -> None:
        """Handle script generation error."""
        self._clear_progress_message()
        self._append_log(f"❌ 스크립트 생성 실패: {error_msg}")
        self._show_error_dialog(f"스크립트 생성 중 오류가 발생했습니다.\n\n{error_msg}")
        self.run_button.setEnabled(True)
        self.ai_generate_button.setEnabled(True)
        self.ai_optimize_button.setEnabled(True)

    def _on_ai_thought(self, msg: str) -> None:
        """Handle AI thought updates on the UI thread with animated progress."""
        self._update_progress_message(f"📝 {msg}")

    def _optimize_script_with_ai(self, feedback: str) -> None:
        """Optimize current script using ChatGPT API."""
        print("[MainWindow] _optimize_script_with_ai called")
        
        # Display user's input on the right side
        self._append_user_input(feedback if feedback.strip() else "(기본 최적화 요청)")
        
        self.run_button.setEnabled(False)
        self.ai_generate_button.setEnabled(False)
        self.ai_optimize_button.setEnabled(False)
        
        current_script = self.script_edit.toPlainText()
        
        # Create worker and thread
        print("[MainWindow] Creating QThread and AIWorker...")
        self.ai_thread = QThread()
        self.ai_worker = AIWorker(self.chatgpt, "optimize", script=current_script, feedback=feedback)
        self.ai_worker.moveToThread(self.ai_thread)
        print("[MainWindow] Worker moved to thread")
        
        # Connect signals
        print("[MainWindow] Connecting signals...")
        self.ai_thread.started.connect(self.ai_worker.run)
        self.ai_worker.thought.connect(self._on_ai_thought)
        self.ai_worker.finished.connect(self._on_optimize_finished)
        self.ai_worker.error.connect(self._on_optimize_error)
        self.ai_worker.finished.connect(self.ai_thread.quit)
        self.ai_worker.error.connect(self.ai_thread.quit)
        self.ai_thread.finished.connect(self.ai_thread.deleteLater)
        print("[MainWindow] Signals connected")
        
        # Start the thread
        print("[MainWindow] Starting thread...")
        self.ai_thread.start()
        print("[MainWindow] Thread started!")
    
    def _on_optimize_finished(self, optimized_code: str) -> None:
        """Handle successful script optimization."""
        # Replace the progress line with completion message - triggers fade transition
        completion_msg = "✅ 스크립트 최적화 완료!"
        
        # Update with completion message (will trigger fade animation)
        self._update_progress_message(completion_msg)
        
        # Parse all sections from response
        code = ""
        description = ""
        
        def extract_section(text: str, tag: str) -> str:
            """Extract content between tags."""
            open_tag = f"[{tag}]"
            close_tag = f"[/{tag}]"
            if open_tag in text and close_tag in text:
                start = text.index(open_tag) + len(open_tag)
                end = text.index(close_tag)
                return text[start:end].strip()
            return ""
        
        code = extract_section(optimized_code, "CODE")
        description = extract_section(optimized_code, "DESCRIPTION")
        
        # Wait for animation to complete before clearing
        def finish_animation():
            self._clear_progress_message()
            # Display code with Korean label
            if code:
                self._append_log("💻 코드\n")
                self._append_log(code)
                self._append_log("\n")
            # Display description with Korean label
            if description:
                self._append_log("\n📝 설명\n")
                self._append_log(description)
            # Put code in editor
            if code:
                self.script_edit.setPlainText(code)
            self.run_button.setEnabled(True)
            self.ai_generate_button.setEnabled(True)
            self.ai_optimize_button.setEnabled(True)
        
        QTimer.singleShot(600, finish_animation)
    
    def _on_optimize_error(self, error_msg: str) -> None:
        """Handle script optimization error."""
        self._clear_progress_message()
        self._append_log(f"❌ 스크립트 최적화 실패: {error_msg}")
        self._show_error_dialog(f"스크립트 최적화 중 오류가 발생했습니다.\n\n{error_msg}")
        self.run_button.setEnabled(True)
        self.ai_generate_button.setEnabled(True)
        self.ai_optimize_button.setEnabled(True)

    def _show_backup_menu(self) -> None:
        """Show backup menu with options."""
        menu = QMenu(self)
        menu.setMinimumWidth(250)
        
        # Apply custom styling based on theme
        if self.dark_mode:
            menu.setStyleSheet("""
                QMenu {
                    background-color: #1a1a1a;
                    border: 1px solid #4a4a4a;
                    border-radius: 8px;
                    padding: 8px;
                    color: #e8e8e8;
                    font-size: 13px;
                }
                QMenu::item {
                    background-color: transparent;
                    padding: 10px 20px;
                    border-radius: 6px;
                    margin: 2px 4px;
                }
                QMenu::item:selected {
                    background-color: #2a2a2a;
                    color: #ffffff;
                }
                QMenu::item:pressed {
                    background-color: #3a3a3a;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #4a4a4a;
                    margin: 8px 12px;
                }
                QMenu::icon {
                    padding-left: 10px;
                }
            """)
        else:
            menu.setStyleSheet("""
                QMenu {
                    background-color: #ffffff;
                    border: 1px solid #d1d5db;
                    border-radius: 8px;
                    padding: 8px;
                    color: #2c2c2c;
                    font-size: 13px;
                }
                QMenu::item {
                    background-color: transparent;
                    padding: 10px 20px;
                    border-radius: 6px;
                    margin: 2px 4px;
                }
                QMenu::item:selected {
                    background-color: #f3f4f6;
                    color: #000000;
                }
                QMenu::item:pressed {
                    background-color: #e5e7eb;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #d1d5db;
                    margin: 8px 12px;
                }
                QMenu::icon {
                    padding-left: 10px;
                }
            """)
        
        # Backup current script
        backup_script_action = menu.addAction("💾 현재 스크립트 백업")
        backup_script_action.triggered.connect(self._backup_current_script)
        
        # Backup session
        backup_session_action = menu.addAction("📦 세션 백업 (스크립트 + 출력)")
        backup_session_action.triggered.connect(self._backup_session)
        
        menu.addSeparator()
        
        # Restore script
        restore_script_action = menu.addAction("📄 스크립트 복원...")
        restore_script_action.triggered.connect(self._restore_script_dialog)
        
        # Restore session
        restore_session_action = menu.addAction("🔄 세션 복원...")
        restore_session_action.triggered.connect(self._restore_session_dialog)
        
        menu.addSeparator()
        
        # View backup info
        view_backups_action = menu.addAction("ℹ️  백업 정보 보기")
        view_backups_action.triggered.connect(self._show_backup_info)
        
        # Show menu at button position
        menu.exec(self.backup_icon_btn.mapToGlobal(self.backup_icon_btn.rect().bottomLeft()))
    
    def _backup_current_script(self) -> None:
        """Create a backup of the current script."""
        script_content = self.script_edit.toPlainText()
        if not script_content.strip():
            self._show_warning_dialog("백업 실패", "백업할 스크립트가 없습니다.")
            return
        
        # Get custom name from user
        from datetime import datetime
        default_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        custom_name, ok = self._get_text_input(
            "스크립트 백업",
            f"백업 이름을 입력하세요\n(비워두면 '{default_name}'으로 저장됩니다)",
            enable_voice=False
        )
        
        if not ok:
            return
        
        custom_name = custom_name.strip() or default_name
        
        try:
            backup_file = self.backup_manager.backup_script(script_content, "script", custom_name)
            file_size_kb = backup_file.stat().st_size / 1024
            backup_dir = backup_file.parent
            
            dialog = QDialog(self)
            dialog.setWindowTitle("스크립트 백업")
            dialog.setMinimumWidth(500)
            layout = QVBoxLayout(dialog)
            
            title = QLabel("✅ 백업이 완료되었습니다")
            title.setStyleSheet("font-size:16px; font-weight:700;")
            layout.addWidget(title)
            
            grid = QWidget()
            gl = QGridLayout(grid)
            gl.setHorizontalSpacing(10)
            gl.setVerticalSpacing(8)
            lbl_color = "#999" if self.dark_mode else "#6b7280"
            val_color = "#e8e8e8" if self.dark_mode else "#2c2c2c"
            gl.addWidget(QLabel(f"<span style='font-weight:600; color:{lbl_color}'>파일명</span>"), 0, 0)
            gl.addWidget(QLabel(f"<span style='color:{val_color}'>{backup_file.name}</span>"), 0, 1)
            gl.addWidget(QLabel(f"<span style='font-weight:600; color:{lbl_color}'>크기</span>"), 1, 0)
            gl.addWidget(QLabel(f"<span style='color:{val_color}'>{file_size_kb:.2f} KB</span>"), 1, 1)
            layout.addWidget(grid)
            
            row = QWidget()
            row_lyt = QHBoxLayout(row)
            row_lyt.setContentsMargins(0, 8, 0, 0)
            row_lyt.setSpacing(8)
            label = QLabel("백업 위치")
            label.setStyleSheet(f"font-weight:600; color:{lbl_color};")
            row_lyt.addWidget(label)
            path_edit = QLineEdit(str(backup_dir))
            path_edit.setReadOnly(True)
            path_edit.setStyleSheet("font-size:12px;")
            row_lyt.addWidget(path_edit, 1)
            menu_btn = QToolButton()
            menu_btn.setText("⋯")
            menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            menu_btn.setStyleSheet("""
                QToolButton { border:1px solid #d1d5db; border-radius:6px; padding:4px 8px; background:transparent; font-size:16px; font-weight:bold; }
                QToolButton:hover { background:#f3f4f6; border-color:#9ca3af; }
                QToolButton:pressed { background:#e5e7eb; }
            """ if not self.dark_mode else """
                QToolButton { border:1px solid #4a4a4a; border-radius:6px; padding:4px 8px; background:transparent; font-size:16px; font-weight:bold; }
                QToolButton:hover { background:#2a2a2a; border-color:#6b7280; }
                QToolButton:pressed { background:#1a1a1a; }
            """)
            menu = QMenu(menu_btn)
            menu_style = "QMenu { padding:8px; border:1px solid #d1d5db; border-radius:8px; background:#ffffff; } QMenu::item { padding:8px 12px; border-radius:4px; } QMenu::item:selected { background:#e5e7eb; }" if not self.dark_mode else "QMenu { padding:8px; border:1px solid #4a4a4a; border-radius:8px; background:#1a1a1a; } QMenu::item { padding:8px 12px; border-radius:4px; } QMenu::item:selected { background:#2a2a2a; }"
            menu.setStyleSheet(menu_style)
            open_action = menu.addAction("📂 Finder에서 열기")
            copy_action = menu.addAction("📋 경로 복사")
            menu_btn.setMenu(menu)
            row_lyt.addWidget(menu_btn)
            layout.addWidget(row)
            
            def open_in_finder() -> None:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(backup_dir)))
            def copy_path() -> None:
                QApplication.clipboard().setText(str(backup_dir))
            open_action.triggered.connect(open_in_finder)
            copy_action.triggered.connect(copy_path)
            path_edit.mousePressEvent = lambda e: open_in_finder()
            
            tip = QLabel("💡 백업 메뉴에서 언제든지 복원할 수 있습니다")
            tip.setStyleSheet(f"font-size:12px; color:{lbl_color};")
            layout.addWidget(tip)
            
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            layout.addWidget(btns)
            btns.accepted.connect(dialog.accept)
            dialog.exec()
        except Exception as e:
            self._show_error_dialog(f"백업 실패:\n{str(e)}")
    
    def _backup_session(self) -> None:
        """Create a backup of the current session (script + output)."""
        script_content = self.script_edit.toPlainText()
        output_content = self.log_output.toPlainText()
        
        if not script_content.strip() and not output_content.strip():
            self._show_warning_dialog("백업 실패", "백업할 내용이 없습니다.")
            return
        
        # Get custom name from user
        from datetime import datetime
        default_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        custom_name, ok = self._get_text_input(
            "세션 백업",
            f"백업 이름을 입력하세요\n(비워두면 '{default_name}'으로 저장됩니다)",
            enable_voice=False
        )
        
        if not ok:
            return
        
        custom_name = custom_name.strip() or default_name
        
        try:
            session_data = {
                "script": script_content,
                "output": output_content,
                "timestamp": None  # Will be set by backup_manager
            }
            backup_file = self.backup_manager.backup_session(session_data, custom_name)
            file_size_kb = backup_file.stat().st_size / 1024
            backup_dir = backup_file.parent
            
            dialog = QDialog(self)
            dialog.setWindowTitle("세션 백업")
            dialog.setMinimumWidth(500)
            layout = QVBoxLayout(dialog)
            
            title = QLabel("✅ 백업이 완료되었습니다")
            title.setStyleSheet("font-size:16px; font-weight:700;")
            layout.addWidget(title)
            
            grid = QWidget()
            gl = QGridLayout(grid)
            gl.setHorizontalSpacing(10)
            gl.setVerticalSpacing(8)
            lbl_color = "#999" if self.dark_mode else "#6b7280"
            val_color = "#e8e8e8" if self.dark_mode else "#2c2c2c"
            gl.addWidget(QLabel(f"<span style='font-weight:600; color:{lbl_color}'>파일명</span>"), 0, 0)
            gl.addWidget(QLabel(f"<span style='color:{val_color}'>{backup_file.name}</span>"), 0, 1)
            gl.addWidget(QLabel(f"<span style='font-weight:600; color:{lbl_color}'>크기</span>"), 1, 0)
            gl.addWidget(QLabel(f"<span style='color:{val_color}'>{file_size_kb:.2f} KB</span>"), 1, 1)
            layout.addWidget(grid)
            
            row = QWidget()
            row_lyt = QHBoxLayout(row)
            row_lyt.setContentsMargins(0, 8, 0, 0)
            row_lyt.setSpacing(8)
            label = QLabel("백업 위치")
            label.setStyleSheet(f"font-weight:600; color:{lbl_color};")
            row_lyt.addWidget(label)
            path_edit = QLineEdit(str(backup_dir))
            path_edit.setReadOnly(True)
            path_edit.setStyleSheet("font-size:12px;")
            row_lyt.addWidget(path_edit, 1)
            menu_btn = QToolButton()
            menu_btn.setText("⋯")
            menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            menu_btn.setStyleSheet("""
                QToolButton { border:1px solid #d1d5db; border-radius:6px; padding:4px 8px; background:transparent; font-size:16px; font-weight:bold; }
                QToolButton:hover { background:#f3f4f6; border-color:#9ca3af; }
                QToolButton:pressed { background:#e5e7eb; }
            """ if not self.dark_mode else """
                QToolButton { border:1px solid #4a4a4a; border-radius:6px; padding:4px 8px; background:transparent; font-size:16px; font-weight:bold; }
                QToolButton:hover { background:#2a2a2a; border-color:#6b7280; }
                QToolButton:pressed { background:#1a1a1a; }
            """)
            menu = QMenu(menu_btn)
            menu_style = "QMenu { padding:8px; border:1px solid #d1d5db; border-radius:8px; background:#ffffff; } QMenu::item { padding:8px 12px; border-radius:4px; } QMenu::item:selected { background:#e5e7eb; }" if not self.dark_mode else "QMenu { padding:8px; border:1px solid #4a4a4a; border-radius:8px; background:#1a1a1a; } QMenu::item { padding:8px 12px; border-radius:4px; } QMenu::item:selected { background:#2a2a2a; }"
            menu.setStyleSheet(menu_style)
            open_action = menu.addAction(" 파일 탐색기에서 열기")
            copy_action = menu.addAction(" 경로 복사")
            menu_btn.setMenu(menu)
            row_lyt.addWidget(menu_btn)
            layout.addWidget(row)
            
            def open_in_finder() -> None:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(backup_dir)))
            def copy_path() -> None:
                QApplication.clipboard().setText(str(backup_dir))
            open_action.triggered.connect(open_in_finder)
            copy_action.triggered.connect(copy_path)
            path_edit.mousePressEvent = lambda e: open_in_finder()
            
            tip = QLabel("📝 스크립트와 출력이 함께 저장되었습니다 · 💡 세션 복원 메뉴에서 복원할 수 있습니다")
            tip.setStyleSheet(f"font-size:12px; color:{lbl_color};")
            layout.addWidget(tip)
            
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            layout.addWidget(btns)
            btns.accepted.connect(dialog.accept)
            dialog.exec()
        except Exception as e:
            self._show_error_dialog(f"세션 백업 실패:\n{str(e)}")
    
    def _restore_script_dialog(self) -> None:
        """Show dialog to restore a backed up script."""
        try:
            backups = self.backup_manager.get_recent_backups("scripts", limit=20)
            if not backups:
                self._show_warning_dialog("복원 실패", "백업된 스크립트가 없습니다.")
                return
            
            # Create a simple selection dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("스크립트 복원")
            dialog.setMinimumWidth(400)
            layout = QVBoxLayout(dialog)
            
            # List of backups
            backup_list_widget = QWidget()
            backup_list_layout = QVBoxLayout(backup_list_widget)
            
            selected_backup: list[Path] = []
            
            for backup_file in backups:
                info = self.backup_manager.get_backup_info(backup_file)
                display_text = f"📄 {info['custom_name']}\n🕒 {info['formatted_time']}"
                btn = QPushButton(display_text)
                btn.setObjectName("primary-action")
                btn.setMinimumHeight(50)
                btn.setStyleSheet("text-align: left; padding: 10px;")
                btn.clicked.connect(lambda checked, bf=backup_file: selected_backup.append(bf))
                backup_list_layout.addWidget(btn)
            
            layout.addWidget(backup_list_widget)
            
            # Buttons
            button_layout = QHBoxLayout()
            cancel_btn = QPushButton("취소")
            cancel_btn.clicked.connect(dialog.reject)
            ok_btn = QPushButton("복원")
            ok_btn.setObjectName("primary-action")
            ok_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(ok_btn)
            layout.addLayout(button_layout)
            
            if dialog.exec():
                if selected_backup:
                    try:
                        content = self.backup_manager.restore_backup(selected_backup[-1])
                        if isinstance(content, str):
                            self.script_edit.setPlainText(content)
                        self._show_info_dialog("복원 완료", "스크립트가 복원되었습니다.")
                    except Exception as e:
                        self._show_error_dialog(f"복원 실패:\n{str(e)}")
        except Exception as e:
            self._show_error_dialog(f"백업 로드 실패:\n{str(e)}")
    
    def _restore_session_dialog(self) -> None:
        """Show dialog to restore a backed up session."""
        try:
            backups = self.backup_manager.get_recent_backups("sessions", limit=20)
            if not backups:
                self._show_warning_dialog("복원 실패", "백업된 세션이 없습니다.")
                return
            
            # Create a simple selection dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("세션 복원")
            dialog.setMinimumWidth(400)
            layout = QVBoxLayout(dialog)
            
            # List of backups
            backup_list_widget = QWidget()
            backup_list_layout = QVBoxLayout(backup_list_widget)
            
            selected_backup: list[Path] = []
            
            for backup_file in backups:
                info = self.backup_manager.get_backup_info(backup_file)
                display_text = f"📦 {info['custom_name']}\n🕒 {info['formatted_time']}"
                btn = QPushButton(display_text)
                btn.setObjectName("primary-action")
                btn.setMinimumHeight(50)
                btn.setStyleSheet("text-align: left; padding: 10px;")
                btn.clicked.connect(lambda checked, bf=backup_file: selected_backup.append(bf))
                backup_list_layout.addWidget(btn)
            
            layout.addWidget(backup_list_widget)
            
            # Buttons
            button_layout = QHBoxLayout()
            cancel_btn = QPushButton("취소")
            cancel_btn.clicked.connect(dialog.reject)
            ok_btn = QPushButton("복원")
            ok_btn.setObjectName("primary-action")
            ok_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(ok_btn)
            layout.addLayout(button_layout)
            
            if dialog.exec():
                if selected_backup:
                    try:
                        content = self.backup_manager.restore_backup(selected_backup[-1])
                        if isinstance(content, dict):
                            self.script_edit.setPlainText(content.get("script", ""))
                            self.log_output.setPlainText(content.get("output", ""))
                        self._show_info_dialog("복원 완료", "세션이 복원되었습니다.")
                    except Exception as e:
                        self._show_error_dialog(f"복원 실패:\n{str(e)}")
        except Exception as e:
            self._show_error_dialog(f"백업 로드 실패:\n{str(e)}")

    def _show_backup_info(self) -> None:
        """Show backup statistics and information with enhanced design and context menu."""
        try:
            stats = self.backup_manager.get_all_backup_stats()
            scripts_count = stats['scripts']['count']
            sessions_count = stats['sessions']['count']
            scripts_size_kb = stats['scripts']['total_size'] / 1024 if scripts_count else 0
            sessions_size_kb = stats['sessions']['total_size'] / 1024 if sessions_count else 0
            backup_dir = Path(stats['backup_dir'])

            dialog = QDialog(self)
            dialog.setWindowTitle("백업 정보")
            dialog.setMinimumWidth(520)
            layout = QVBoxLayout(dialog)

            # Title
            title = QLabel("ℹ️ 백업 정보")
            title.setStyleSheet("font-size:16px; font-weight:700;")
            layout.addWidget(title)

            # Cards container
            cards = QWidget()
            cards_lyt = QHBoxLayout(cards)
            cards_lyt.setSpacing(12)
            cards_lyt.setContentsMargins(0, 8, 0, 0)

            def make_card(name: str, count: int, size_kb: float) -> QWidget:
                w = QWidget()
                l = QVBoxLayout(w)
                l.setContentsMargins(12, 12, 12, 12)
                l.setSpacing(8)
                w.setStyleSheet("border:none; border-radius:10px;")
                head = QLabel(name)
                head.setStyleSheet("font-weight:700; margin-bottom:4px;")
                l.addWidget(head)
                grid = QWidget()
                gl = QGridLayout(grid)
                gl.setHorizontalSpacing(10)
                gl.setVerticalSpacing(8)
                lbl_color = "#999" if self.dark_mode else "#6b7280"
                val_color = "#e8e8e8" if self.dark_mode else "#2c2c2c"
                gl.addWidget(QLabel(f"<span style='color:{lbl_color}'>개수</span>"), 0, 0)
                gl.addWidget(QLabel(f"<span style='color:{val_color}'>{count}개</span>"), 0, 1)
                gl.addWidget(QLabel(f"<span style='color:{lbl_color}'>용량</span>"), 1, 0)
                gl.addWidget(QLabel(f"<span style='color:{val_color}'>{size_kb:.2f} KB</span>"), 1, 1)
                l.addWidget(grid)
                return w

            cards_lyt.addWidget(make_card("💾 스크립트", scripts_count, scripts_size_kb))
            cards_lyt.addWidget(make_card("📦 세션", sessions_count, sessions_size_kb))
            layout.addWidget(cards)

            # Backup path row
            row = QWidget()
            row_lyt = QHBoxLayout(row)
            row_lyt.setContentsMargins(0, 8, 0, 0)
            row_lyt.setSpacing(8)
            label = QLabel("백업 위치")
            label.setStyleSheet("font-weight:600; color:#6b7280;")
            row_lyt.addWidget(label)

            path_edit = QLineEdit(str(backup_dir))
            path_edit.setReadOnly(True)
            path_edit.setStyleSheet("font-size:12px;")
            row_lyt.addWidget(path_edit, 1)

            # Context menu button
            menu_btn = QToolButton()
            menu_btn.setText("⋯")
            menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            menu_btn.setStyleSheet("""
                QToolButton {
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    padding: 4px 8px;
                    background: transparent;
                    font-size: 16px;
                    font-weight: bold;
                }
                QToolButton:hover {
                    background: #f3f4f6;
                    border-color: #9ca3af;
                }
                QToolButton:pressed {
                    background: #e5e7eb;
                }
            """ if not self.dark_mode else """
                QToolButton {
                    border: 1px solid #4a4a4a;
                    border-radius: 6px;
                    padding: 4px 8px;
                    background: transparent;
                    font-size: 16px;
                    font-weight: bold;
                }
                QToolButton:hover {
                    background: #2a2a2a;
                    border-color: #6b7280;
                }
                QToolButton:pressed {
                    background: #1a1a1a;
                }
            """)
            menu = QMenu(menu_btn)
            menu_style = "QMenu { padding:8px; border:1px solid #d1d5db; border-radius:8px; background:#ffffff; } QMenu::item { padding:8px 12px; border-radius:4px; } QMenu::item:selected { background:#e5e7eb; }" if not self.dark_mode else "QMenu { padding:8px; border:1px solid #4a4a4a; border-radius:8px; background:#1a1a1a; } QMenu::item { padding:8px 12px; border-radius:4px; } QMenu::item:selected { background:#2a2a2a; }"
            menu.setStyleSheet(menu_style)
            open_action = menu.addAction("📂 Finder에서 열기")
            copy_action = menu.addAction("📋 경로 복사")
            menu_btn.setMenu(menu)
            row_lyt.addWidget(menu_btn)
            layout.addWidget(row)

            # Tip
            tip = QLabel("💡 백업 수가 많아지면 오래된 항목은 정리하세요")
            tip.setStyleSheet("font-size:12px; color:#6b7280;")
            layout.addWidget(tip)

            # Wire actions
            def open_in_finder() -> None:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(backup_dir)))
            def copy_path() -> None:
                QApplication.clipboard().setText(str(backup_dir))
            open_action.triggered.connect(open_in_finder)
            copy_action.triggered.connect(copy_path)

            # Also open on path click
            path_edit.mousePressEvent = lambda e: open_in_finder()

            # Buttons
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            btns.setStyleSheet("""
                QPushButton {
                    background-color: #5377f6;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 24px;
                    font-size: 13px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #3e5fc7;
                }
                QPushButton:pressed {
                    background-color: #2e47a0;
                }
            """)
            layout.addWidget(btns)
            btns.accepted.connect(dialog.accept)

            dialog.exec()
        except Exception as e:
            self._show_error_dialog(f"백업 정보 로드 실패:\n{str(e)}")

    def _update_hwp_filename(self) -> None:
        """Automatically detect and update the currently open HWP document filename."""
        try:
            if platform.system() == "Windows":
                import win32gui  # type: ignore[import-not-found]
                import re
                
                # Find HWP window
                hwp_window = win32gui.FindWindow("HwpFrame", None)
                if hwp_window:
                    # Get window title which contains the filename
                    title = win32gui.GetWindowText(hwp_window)
                    # Title format: "filename.hwp - 한글" or "filename.hwp"
                    # Extract filename from title
                    match = re.search(r"([^\\\/]+\.hwp[x]?)", title, re.IGNORECASE)
                    if match:
                        filename = match.group(1)
                        if filename != self._last_hwp_filename:
                            self._last_hwp_filename = filename
                            self.hwp_filename_label.setText(filename)
                    return
                
                # If no HWP window found, reset to default
                if self._last_hwp_filename != "한글 문서":
                    self._last_hwp_filename = "한글 문서"
                    self.hwp_filename_label.setText("한글 문서")
            else:
                # macOS/Linux: Only update from file picker, not from active window
                pass
        except Exception as e:
            # Silently fail - this is a background detection feature
            print(f"[HWP Detection] Error: {e}")


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


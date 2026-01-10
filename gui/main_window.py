"""AMEX AI script console."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Optional
import uuid
import time

# Optional speech recognition
try:
    import speech_recognition as sr  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    sr = None  # type: ignore[assignment]

from PySide6.QtCore import Qt, Signal, QThread, QObject, QSize, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QUrl, QRect
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QTextCursor, QDesktopServices, QCursor, QPen, QPainterPath, QImage
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
    QSizePolicy,
    QDialogButtonBox,
    QGraphicsDropShadowEffect, QWidgetAction,
)

from . import design

from backend.hwp.hwp_controller import HwpController, HwpControllerError
from backend.hwp.script_runner import HwpScriptRunner
from backend.hwp.hwp_detector import HwpDetector
from backend.chatgpt_helper import ChatGPTHelper
from backend.ai_model_helper import MultiModelAIHelper
from backend.backup_manager import BackupManager


class FileDropTextEdit(QTextEdit):
    """Custom QTextEdit that forwards file drops to parent window instead of inserting file paths."""
    
    file_dropped = Signal(str)  # Signal to emit when file is dropped
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        """Accept file drops but don't process them here."""
        if event.mimeData().hasUrls():
            # Check if any URL is an image or PDF
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf')):
                    event.acceptProposedAction()
                    return
        # For non-file drops (like text), use default behavior
        super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """Accept drag move for files."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        """Handle file drops by forwarding to parent, not inserting paths."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf')):
                    # Emit signal instead of inserting text
                    self.file_dropped.emit(file_path)
                    event.acceptProposedAction()
                    return
        # For non-file drops (like text), use default behavior
        super().dropEvent(event)


class AIWorker(QObject):
    """Worker for running AI tasks in a separate thread."""
    finished = Signal(str)  # Emits the generated/optimized script
    error = Signal(str)  # Emits error message
    thought = Signal(str)  # Emits thought process updates
    
    def __init__(self, ai_helper, task_type: str, **kwargs):
        super().__init__()
        self.ai_helper = ai_helper  # Can be ChatGPTHelper or MultiModelAIHelper
        self.task_type = task_type
        self.kwargs = kwargs
    
    def run(self):
        """Run the AI task."""
        import traceback
        from pathlib import Path
        try:
            print(f"[AIWorker] Starting {self.task_type} task...")
            
            def on_thought(message: str):
                print(f"[AIWorker] Thought: {message}")
                self.thought.emit(message)
            
            # Get model parameter
            model = self.kwargs.get('model', 'auto')
            
            if self.task_type == "generate":
                print(f"[AIWorker] Calling generate_script with model: {model}...")
                
                # Check if we have multiple images to process
                image_paths = self.kwargs.get('image_paths', [])
                image_path = self.kwargs.get('image_path')  # Single image (legacy)
                
                if image_paths and len(image_paths) > 1:
                    # Process multiple images
                    print(f"[AIWorker] Processing {len(image_paths)} images")
                    all_results = []
                    
                    for idx, img_path in enumerate(image_paths, 1):
                        on_thought(f"파일 {idx}/{len(image_paths)} 분석 중: {Path(img_path).name}")
                        
                        desc = self.kwargs['description']
                        if idx > 1:
                            # For subsequent images, modify description
                            desc = f"다음 파일을 분석합니다 (파일 {idx}/{len(image_paths)})"
                        
                        result = self.ai_helper.generate_script(
                            desc,
                            self.kwargs.get('context', ''),
                            image_path=img_path,
                            on_thought=on_thought,
                            model=model
                        )
                        
                        if result:
                            all_results.append(result)
                            print(f"[AIWorker] File {idx} processed: {len(result)} chars")
                        else:
                            print(f"[AIWorker] WARNING: File {idx} returned no result")
                    
                    # Combine all results with paragraph separators
                    if all_results:
                        # Extract CODE sections and combine
                        combined_code = []
                        for result in all_results:
                            # Extract [CODE]...[/CODE] section
                            import re
                            match = re.search(r'\[CODE\](.*?)\[/CODE\]', result, re.DOTALL)
                            if match:
                                code = match.group(1).strip()
                                combined_code.append(code)
                        
                        # Create combined result
                        code_with_separators = '\ninsert_paragraph()\ninsert_paragraph()\n'.join(combined_code)
                        result = f"[DESCRIPTION]\n모든 파일을 분석하여 내용을 추출했습니다.\n[/DESCRIPTION]\n\n[CODE]\n{code_with_separators}\n[/CODE]"
                    else:
                        result = None
                else:
                    # Single image or no image
                    result = self.ai_helper.generate_script(
                        self.kwargs['description'],
                        self.kwargs.get('context', ''),
                        image_path=image_path or (image_paths[0] if image_paths else None),
                        on_thought=on_thought,
                        model=model
                    )
                
                print(f"[AIWorker] Generate result: {len(result) if result else 0} chars")
            elif self.task_type == "optimize":
                print(f"[AIWorker] Calling optimize_script with model: {model}...")
                result = self.ai_helper.optimize_script(
                    self.kwargs['script'],
                    self.kwargs.get('feedback', ''),
                    on_thought=on_thought,
                    model=model
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
    """Load external CSS file for dialogs (delegates to gui.design)."""
    return design.load_dialog_css()


def _load_theme(theme_name: str) -> str:
    """Load external QSS theme file (delegates to gui.design)."""
    return design.load_theme(theme_name)


def _create_styled_dialog(parent, title: str, content: str, min_width: int = 500, min_height: int = 0, dark_mode: bool = False, icon_path: str | None = None) -> QMessageBox:
    """Create a styled dialog (delegates to gui.design)."""
    return design.create_styled_dialog(parent, title, content, min_width=min_width, min_height=min_height, dark_mode=dark_mode, icon_path=icon_path)
    return msg

DEFAULT_SCRIPT = """
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
    def _export_chats(self) -> None:
        """Export all chats to a JSON file with enhanced dialog design."""
        from PySide6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QLabel, QPushButton
        import json
        file_path, _ = QFileDialog.getSaveFileName(self, "채팅 내보내기", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self._chats, f, ensure_ascii=False, indent=2)
                # Custom dialog
                dlg = QDialog(self)
                dlg.setWindowTitle("내보내기 완료")
                dlg.setMinimumWidth(340)
                layout = QVBoxLayout(dlg)
                layout.setContentsMargins(32, 32, 32, 32)
                layout.setSpacing(24)
                title = QLabel("채팅을 성공적으로 저장했습니다.")
                title_color = "#fff" if self.dark_mode else "#222"
                title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {title_color}; letter-spacing: 0.5px; text-shadow: 0 2px 8px #e0e0e0;")
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(title)
                path_label = QLabel(file_path)
                path_label.setStyleSheet("font-size: 16px; color: #444; font-weight: 600; margin-bottom: 12px;")
                path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(path_label)
                ok_btn = QPushButton("OK")
                ok_btn.setStyleSheet("background-color: #5377f6; color: white; border: none; border-radius: 8px; padding: 12px 36px; font-size: 17px; font-weight: 700; min-width: 80px; max-width: 120px;")
                ok_btn.setFixedWidth(100)
                ok_btn.clicked.connect(dlg.accept)
                layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)
                dlg.exec()
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "내보내기 오류", f"채팅 내보내기에 실패했습니다.\n{e}")

    def _import_chats(self) -> None:
        """Import chats from a JSON file with enhanced dialog design."""
        from PySide6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
        import json
        file_path, _ = QFileDialog.getOpenFileName(self, "채팅 가져오기", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    chats = json.load(f)
                if isinstance(chats, list):
                    self._chats = chats
                    self._current_chat_id = None
                    self._render_chat_list()
                    # Custom dialog
                    dlg = QDialog(self)
                    dlg.setWindowTitle("가져오기 완료")
                    dlg.setMinimumWidth(340)
                    layout = QVBoxLayout(dlg)
                    layout.setContentsMargins(32, 32, 32, 32)
                    layout.setSpacing(24)
                    title = QLabel("채팅을 성공적으로 불러왔습니다.")
                    title_color = "#fff" if self.dark_mode else "#222"
                    title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {title_color}; letter-spacing: 0.5px; text-shadow: 0 2px 8px #e0e0e0;")
                    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(title)
                    path_label = QLabel(file_path)
                    path_label.setStyleSheet("font-size: 16px; color: #444; font-weight: 600; margin-bottom: 12px;")
                    path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(path_label)
                    ok_btn = QPushButton("OK")
                    ok_btn.setStyleSheet("background-color: #5377f6; color: white; border: none; border-radius: 8px; padding: 12px 36px; font-size: 17px; font-weight: 700; min-width: 80px; max-width: 120px;")
                    ok_btn.setFixedWidth(100)
                    ok_btn.clicked.connect(dlg.accept)
                    layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)
                    dlg.exec()
                else:
                    QMessageBox.warning(self, "가져오기 오류", "올바른 채팅 데이터가 아닙니다.")
            except Exception as e:
                QMessageBox.critical(self, "가져오기 오류", f"채팅 가져오기에 실패했습니다.\n{e}")
    def _show_welcome_message(self):
        self._clear_chat_transcript()
        row = QWidget()
        row_lyt = QHBoxLayout(row)
        row_lyt.setContentsMargins(0, 0, 0, 0)
        row_lyt.setSpacing(0)
        label = QLabel("무엇이든 물어보세요")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = "#ffffff" if getattr(self, "dark_mode", False) else "#000000"
        label.setStyleSheet(f"font-size: 28px; color: {color}; font-weight: 700; margin: 32px 0;")
        row_lyt.addWidget(label, 0, Qt.AlignmentFlag.AlignCenter)
        self.chat_transcript_layout.addWidget(row, 0)
        self.chat_transcript_layout.addStretch(1)
    def _chat_add_message(self, role: str, content: str) -> None:
        """Add a message to the current chat, update UI, and persist immediately. Also auto-scrolls chat to bottom."""
        # Add to UI
        self._add_message_to_ui_only(role, content)
        # Auto-scroll to bottom after adding message
        self._scroll_chat_to_bottom()
        # Add to chat data
        for chat in self._chats:
            if chat.get("id") == self._current_chat_id:
                if "messages" not in chat or not isinstance(chat["messages"], list):
                    chat["messages"] = []
                chat["messages"].append({"role": role, "content": content})
                break
        # Persist immediately
        self._save_current_chat_state()
        self._schedule_persist()

    def _scroll_chat_to_bottom(self):
        """Scroll the chat transcript area to the bottom."""
        try:
            if hasattr(self, 'chat_transcript_scroll') and self.chat_transcript_scroll:
                # If using QScrollArea for chat transcript
                scroll = self.chat_transcript_scroll.verticalScrollBar()
                scroll.setValue(scroll.maximum())
            elif hasattr(self, 'chat_transcript') and isinstance(self.chat_transcript, QTextEdit):
                # If using QTextEdit for chat transcript
                self.chat_transcript.moveCursor(QTextCursor.End)
                self.chat_transcript.ensureCursorVisible()
            # If using a custom widget/layout, try to update geometry and scroll
            elif hasattr(self, 'chat_transcript_layout'):
                # Try to find parent scroll area
                parent = getattr(self, 'chat_transcript_layout').parentWidget()
                while parent:
                    if isinstance(parent, QScrollArea):
                        parent.verticalScrollBar().setValue(parent.verticalScrollBar().maximum())
                        break
                    parent = parent.parentWidget()
        except Exception as e:
            print(f"[MainWindow] Auto-scroll failed: {e}")
    
    def _on_hwp_state_changed(self, state) -> None:
        """Handle HWP state changes from the detector."""
        try:
            display_text = self.hwp_detector.get_display_filename()
            
            # Update UI with filename only (no status indicators)
            if state.is_hwp_running:
                if state.current_hwp_filename and state.current_hwp_filename not in {"", "한글 문서"}:
                    # Valid filename - show filename only
                    self.hwp_filename_label.setText(state.current_hwp_filename)
                else:
                    # HWP running but no valid document
                    self.hwp_filename_label.setText("Untitled HWP document")
            else:
                # HWP not running
                self.hwp_filename_label.setText("HWP not running")
            
            print(f"[MainWindow] HWP state updated: {display_text}")
        except Exception as e:
            print(f"[MainWindow] Error updating HWP state: {e}")
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Nova AI")
        # Narrow, mobile-like initial window (portrait ratio)
        # Taller initial height for better sidebar display
        self.resize(420, 920)
        self.setMinimumWidth(320)
        self.setMinimumHeight(700)
        self._worker: Optional[ScriptWorker] = None
        self.sr_worker: Optional[SpeechRecognitionWorker] = None
        # AI thread management - support multiple concurrent threads
        self.ai_threads: list[QThread] = []  # List of active AI threads
        self.ai_workers: list[AIWorker] = []  # List of active AI workers
        # Default to light theme (pure white background)
        self.dark_mode = False
        self.chatgpt = ChatGPTHelper()  # Legacy support
        self.ai_helper = MultiModelAIHelper()  # New multi-model helper
        self.current_model = self.ai_helper.get_cheapest_model() or "gpt-5-nano"  # Default to cheapest
        self.backup_manager = BackupManager()  # Initialize backup manager
        # Profile defaults (ensure drawer/profile UI can be built safely)
        self.profile_display_name = "사용자"
        self.profile_handle = ""
        self.profile_plan = "Free"
        # Drawer state
        self._drawer_open = False
        # Simple in-memory chat store and UI helpers
        self._chats: list[dict] = []
        self._current_chat_id: str | None = None
        self._chat_filter = ""
        # Debounced persist timer for chat store
        self._persist_timer = QTimer()
        self._persist_timer.setSingleShot(True)
        self._persist_timer.timeout.connect(lambda: self._persist_chats())
        # Drawer in-panel popup (used for profile/backup menus)
        self._drawer_popup: QFrame | None = None
        self.selected_files: list[str] = []  # Track selected files/images
        
        # Initialize HWP detector with polling
        self.hwp_detector = HwpDetector(poll_interval_ms=500)
        self.hwp_detector.state_changed.connect(self._on_hwp_state_changed)
        self._progress_active = False  # Track if progress message is active
        self._progress_base_text = ""  # Current progress text
        self._progress_fade_count = 0  # Frame counter for fade animation (0-9)
        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._animate_progress_fade)
        # Drawer animation object (persisted to avoid GC & make single-click reliable)
        self._drawer_anim: QPropertyAnimation | None = None
        
        # Set application-wide font to Pretendard
        app_font = QFont("Pretendard")
        app_font.setPointSize(14)
        self.setFont(app_font)
        
        self._build_ui()
        self._apply_styles()
        # Load persisted state (e.g., selected model) from disk and apply
        try:
            self._load_persisted_state()
        except Exception:
            pass
        # Always clear current chat ID at startup and show welcome message
        self._current_chat_id = None
        self._show_welcome_message()
        # Render chat list if there are existing chats
        if self._chats:
            self._render_chat_list()
        # Apply responsive UI tweaks immediately and on resize
        self._apply_responsive_layout()
        
        # Start HWP detection if adapter is available
        if self.hwp_detector.is_adapter_available():
            self.hwp_detector.start_polling()
            print("[MainWindow] HWP detector started")
        else:
            print("[MainWindow] HWP detector not available on this platform")
        
        # Enable drag and drop for images and PDFs
        self.setAcceptDrops(True)

    def closeEvent(self, event) -> None:
        """Ensure floating/overlay widgets are hidden/deleted to avoid leaking top-level windows."""
        try:
            # Stop HWP detector
            if hasattr(self, 'hwp_detector'):
                self.hwp_detector.stop_polling()
            
            # Hide and delete potentially top-level widgets so they don't remain after close
            for name in ("top_model_display", "top_model_btn", "add_file_btn", "ai_selector_btn", "hwp_add_btn", "mic_btn", "image_preview_container", "_drawer_popup"):
                if hasattr(self, name):
                    obj = getattr(self, name)
                    try:
                        obj.hide()
                        # Reparent away from Qt ownership so widget will be deleted properly
                        obj.setParent(None)
                        obj.deleteLater()
                    except Exception:
                        pass
        except Exception:
            pass
        # Proceed with normal close
        super().closeEvent(event)

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter event for files."""
        if event.mimeData().hasUrls():
            # Check if any of the URLs are image or PDF files
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        """Handle drag move event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """Handle drop event for image/PDF files - supports multiple files."""
        if event.mimeData().hasUrls():
            files_added = False
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf')):
                    print(f"[MainWindow] File dropped: {file_path}")
                    # Add to selected files and show preview
                    if file_path not in self.selected_files:
                        self.selected_files.append(file_path)
                        self._add_image_preview(file_path)
                        files_added = True
            if files_added:
                event.acceptProposedAction()
                return
        event.ignore()
    
    def _handle_file_drop_in_input(self, file_path: str) -> None:
        """Handle file drop in the input text field - add to attachments instead of inserting path."""
        print(f"[MainWindow] File dropped in input field: {file_path}")
        if file_path not in self.selected_files:
            self.selected_files.append(file_path)
            self._add_image_preview(file_path)

    def _snapshot_current_chat(self) -> None:
        """Save brief snapshot of the currently active chat into the in-memory store.

        This is intentionally lightweight and tolerant — used before creating a new
        chat so we don't lose the current editor/log state.
        """
        try:
            if not self._current_chat_id:
                return
            for chat in self._chats:
                if chat.get("id") == self._current_chat_id:
                    chat["script"] = getattr(self, "script_edit", None).toPlainText() if hasattr(self, "script_edit") else chat.get("script", "")
                    chat["log"] = getattr(self, "log_output", None).toPlainText() if hasattr(self, "log_output") else chat.get("log", "")
                    chat["updated_at"] = time.time()
                    return
            # If no existing chat matches, append one
            self._chats.insert(0, {
                "id": self._current_chat_id,
                "title": "Saved chat",
                "log": getattr(self, "log_output", None).toPlainText() if hasattr(self, "log_output") else "",
                "script": getattr(self, "script_edit", None).toPlainText() if hasattr(self, "script_edit") else "",
                "created_at": time.time(),
                "updated_at": time.time(),
            })
        except Exception:
            # Be defensive — snapshot failure should not crash the UI
            pass

    def _schedule_persist(self) -> None:
        """Schedule a debounced persist of the chat store to disk (no-op quick save).

        The real persistence layer can be added later; for now we keep a lightweight
        on-disk JSON so state survives simple restarts during development.
        """
        try:
            # Always save the current chat's state (including messages) before persisting
            self._save_current_chat_state()
            self._persist_timer.start(400)
        except Exception:
            pass

    def _persist_chats(self) -> None:
        """Persist the in-memory chat store to a file under the user's home dir.

        This is a best-effort implementation to avoid raising exceptions during
        UI operations.
        """
        try:
            # Always save the current chat's state (including messages) before persisting
            self._save_current_chat_state()
            import json, os
            folder = Path.home() / "formulite_chats"
            folder.mkdir(parents=True, exist_ok=True)
            file_path = folder / "chat_history.json"
            data = {"chats": self._chats, "current": self._current_chat_id, "model": getattr(self, '_current_model', None)}
            file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[Persist] Failed to write chats: {e}")

    def _load_persisted_state(self) -> None:
        """Load persisted UI/chat state from disk and apply to the running session.

        Currently this reads the lightweight JSON file used by _persist_chats and
        applies the saved model selection if present. This is intentionally
        best-effort and tolerant of malformed files.
        """
        try:
            storage = Path.home() / "formulite_chats" / "chat_history.json"
            print(f"[Persist] Checking for storage file: {storage}")
            if not storage.exists():
                print("[Persist] No storage file found, starting fresh")
                return
            import json
            data = json.loads(storage.read_text(encoding='utf-8'))
            
            # Load chats if available
            if "chats" in data and isinstance(data["chats"], list):
                self._chats = data["chats"]
                print(f"[Persist] ✅ Loaded {len(self._chats)} chats from storage")
            else:
                print("[Persist] No chats found in storage file")
            
            # Load current chat ID
            if "current" in data:
                self._current_chat_id = data["current"]
                print(f"[Persist] Current chat ID: {self._current_chat_id}")
            
            # Try a couple of places for the model so we remain tolerant to schema changes
            model = data.get("model") or (data.get("settings") or {}).get("model")
            if model:
                try:
                    self._set_model(str(model))
                    print(f"[Persist] Model set to: {model}")
                except Exception:
                    pass
            # Restore messages for the current chat if available
            if self._current_chat_id:
                for chat in self._chats:
                    if chat.get("id") == self._current_chat_id:
                        self._restore_chat_messages(chat)
                        break
        except Exception as e:
            print(f"[Persist] Failed to load persisted state: {e}")

    def _ensure_default_chat(self) -> None:
        """No longer activates or selects any chat by default. Only renders chat list."""
        try:
            print(f"[MainWindow] _ensure_default_chat called. Current chats: {len(self._chats)}")
            self._current_chat_id = None
            self._render_chat_list()
        except Exception as e:
            print(f"[MainWindow] Error ensuring default chat: {e}")

    def _render_chat_list(self) -> None:
        """Render the simple chat list inside the drawer (if present)."""
        try:
            if not hasattr(self, "drawer_chat_list_layout"):
                return
            # Update visibility of reset button depending on active filter
            try:
                if getattr(self, 'drawer_reset_btn', None):
                    self.drawer_reset_btn.setVisible(bool(self._chat_filter))
            except Exception:
                pass
            # Clear existing items
            layout = self.drawer_chat_list_layout
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            # Apply filter
            # No longer seeding placeholder chats - we handle empty state with _ensure_default_chat
            
            chats = [c for c in self._chats if (self._chat_filter.lower() in (c.get("title", "").lower()))]
            for chat in chats:
                item_wrap = QWidget()
                item_wrap.setObjectName("drawer-chat-item-wrap")
                # Prevent chat items from expanding vertically when list is short
                item_wrap.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
                item_wrap.setFixedHeight(30)
                item_wrap.setMaximumHeight(30)
                h = QHBoxLayout(item_wrap)
                # Slightly tighter wrap padding and spacing for compact sidebar
                h.setContentsMargins(4, 0, 4, 0)
                h.setSpacing(10)

                btn = QPushButton(chat.get("title", "Untitled"))
                btn.setObjectName("drawer-chat-item")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                # Adjust height and padding to fit the smaller row and center text vertically
                btn.setMinimumHeight(28)
                try:
                    orig_btn_style = btn.styleSheet() if hasattr(btn, 'styleSheet') else ""
                    # Adjust padding based on theme
                    padding_top = "2px" if self.dark_mode else "-5px"
                    btn.setStyleSheet((orig_btn_style or "") + f"padding-top:{padding_top}; padding-left:12px;")
                except Exception:
                    pass
                font = btn.font()
                font.setPointSize(14)
                # Use DemiBold weight for slightly lighter emphasis
                try:
                    font.setWeight(QFont.Weight.DemiBold)
                except Exception:
                    font.setWeight(QFont.Weight.Bold)
                btn.setFont(font)

                # Active state
                if chat.get("id") == self._current_chat_id:
                    btn.setProperty("active", True)
                else:
                    btn.setProperty("active", False)
                # Ensure stylesheet updates when property changes
                try:
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)
                except Exception:
                    pass

                def make_activate(cid: str):
                    return lambda checked=False, cid=cid: self._activate_chat(cid)

                btn.clicked.connect(make_activate(chat.get("id")))
                h.addWidget(btn)

                # Edit button (shown on hover) - allows renaming the chat
                edit_btn = QToolButton()
                edit_btn.setObjectName("drawer-chat-edit")
                edit_btn.setText("")
                edit_btn.setToolTip("이름 변경")
                edit_btn.setCursor(Qt.PointingHandCursor)
                edit_btn.setAutoRaise(False)
                edit_btn.setFixedSize(28, 28)
                try:
                    assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
                    write_icon = assets_dir / ("write-dark.svg" if getattr(self, "dark_mode", False) else "write-light.svg")
                    if not write_icon.exists():
                        alt = assets_dir / ("write-light.svg" if getattr(self, "dark_mode", False) else "write-dark.svg")
                        write_icon = alt if alt.exists() else write_icon
                    if write_icon.exists():
                        edit_btn.setIcon(QIcon(str(write_icon)))
                        edit_btn.setIconSize(QSize(18, 18))
                    else:
                        edit_btn.setIcon(QIcon())
                except Exception:
                    edit_btn.setIcon(QIcon())
                edit_btn.clicked.connect(lambda checked=False, cid=chat.get("id"): self._rename_chat(cid))
                try:
                    edit_btn.hide()
                except Exception:
                    pass
                h.addWidget(edit_btn)

                # Delete button (shown on hover via stylesheet)
                del_btn = QToolButton()
                del_btn = QToolButton()
                del_btn.setObjectName("drawer-chat-delete")
                del_btn.setText("")
                del_btn.setToolTip("채팅 삭제")
                del_btn.setCursor(Qt.PointingHandCursor)
                del_btn.setAutoRaise(False)
                del_btn.setFixedSize(28, 28)
                try:
                    assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
                    remove_icon = assets_dir / ("remove-dark.svg" if getattr(self, "dark_mode", False) else "remove-light.svg")
                    if not remove_icon.exists():
                        alt = assets_dir / ("remove-light.svg" if getattr(self, "dark_mode", False) else "remove-dark.svg")
                        remove_icon = alt if alt.exists() else remove_icon
                    if remove_icon.exists():
                        del_btn.setIcon(QIcon(str(remove_icon)))
                        del_btn.setIconSize(QSize(16, 16))
                    else:
                        del_btn.setIcon(QIcon())
                except Exception:
                    del_btn.setIcon(QIcon())
                del_btn.clicked.connect(lambda checked=False, cid=chat.get("id"): self._delete_chat(cid))
                # Start hidden; reveal on hover of the entire chat row
                try:
                    del_btn.hide()
                except Exception:
                    pass
                h.addWidget(del_btn)

                # Show/hide delete button when hovering the row
                try:
                    orig_enter = getattr(item_wrap, "enterEvent", None)
                    orig_leave = getattr(item_wrap, "leaveEvent", None)
                    # Preserve original styles so we can restore them on leave
                    orig_btn_style = btn.styleSheet() if hasattr(btn, 'styleSheet') else ''
                    orig_wrap_style = item_wrap.styleSheet() if hasattr(item_wrap, 'styleSheet') else ''

                    def _enter(e, dbtn=del_btn, ebtn=edit_btn, o=orig_enter, cbtn=btn, wrap=item_wrap, cbs=orig_btn_style, wbs=orig_wrap_style):
                        try:
                            # Show delete and edit icons
                            try:
                                dbtn.show()
                            except Exception:
                                pass
                            try:
                                ebtn.show()
                            except Exception:
                                pass
                        except Exception:
                            pass
                        try:
                            # Apply rounded background to the whole row and temporarily remove button border
                            # Use a theme-aware hover color (black in dark mode, light gray in light mode)
                            bg = "#222222" if getattr(self, 'dark_mode', False) else "#f3f4f6"
                            wrap.setStyleSheet((wbs or "") + f"background-color: {bg}; border-radius: 12px;")
                            cbtn.setStyleSheet((cbs or "") + "background: transparent; border: none;")
                        except Exception:
                            pass
                        if callable(o):
                            try:
                                o(e)
                            except Exception:
                                pass

                    def _leave(e, dbtn=del_btn, ebtn=edit_btn, o=orig_leave, cbtn=btn, wrap=item_wrap, cbs=orig_btn_style, wbs=orig_wrap_style):
                        try:
                            try:
                                dbtn.hide()
                            except Exception:
                                pass
                            try:
                                ebtn.hide()
                            except Exception:
                                pass
                        except Exception:
                            pass
                        try:
                            # Restore original styles
                            cbtn.setStyleSheet(cbs or "")
                            wrap.setStyleSheet(wbs or "")
                        except Exception:
                            pass
                        if callable(o):
                            try:
                                o(e)
                            except Exception:
                                pass

                    item_wrap.enterEvent = _enter
                    item_wrap.leaveEvent = _leave
                except Exception:
                    pass

                layout.addWidget(item_wrap)
        except Exception:
            pass

    def _delete_chat(self, chat_id: str) -> None:
        """Remove a chat by id from in-memory store and refresh list."""
        try:
            self._chats = [c for c in self._chats if c.get("id") != chat_id]
            if self._current_chat_id == chat_id:
                self._current_chat_id = None
                if hasattr(self, "script_edit"):
                    self.script_edit.setPlainText(DEFAULT_SCRIPT.strip())
                if hasattr(self, "log_output"):
                    self.log_output.clear()
            self._schedule_persist()
            self._render_chat_list()
        except Exception:
            pass

    def _reset_chat_filter(self) -> None:
        """Reset the current chat filter and refresh the list."""
        try:
            if getattr(self, '_chat_filter', None):
                self._chat_filter = ""
                # Re-render the list and hide reset button
                try:
                    if getattr(self, 'drawer_reset_btn', None):
                        self.drawer_reset_btn.hide()
                except Exception:
                    pass
                self._render_chat_list()
        except Exception:
            pass

    def _rename_chat(self, chat_id: str) -> None:
        """Open a dialog to rename the chat and persist the change."""
        try:
            for c in self._chats:
                if c.get("id") == chat_id:
                    old = c.get("title", "")
                    # Custom rename dialog matching the chat search UI
                    dlg = QDialog(self)
                    dlg.setWindowTitle("이름 변경")
                    dlg.setModal(True)
                    try:
                        central = self.centralWidget()
                        available_w = central.width() if central is not None else self.width()
                        # Make rename dialog smaller than the page: use 65% of available width and clamp between 360 and 520px
                        dlg_w = int(max(360, min(520, int(available_w * 0.65))))
                    except Exception:
                        dlg_w = 420
                    dlg.setMinimumHeight(180)
                    dlg.setFixedWidth(dlg_w)
                    try:
                        parent_tl = self.mapToGlobal(self.rect().topLeft())
                        x = parent_tl.x() + max(8, (self.width() - dlg.width()) // 2)
                        y = parent_tl.y() + 96
                        dlg.move(x, y)
                    except Exception:
                        pass
                    if self.dark_mode:
                        dlg.setStyleSheet("QDialog { background: #000000; color: #e8e8e8; }")
                    else:
                        dlg.setStyleSheet("QDialog { background: #ffffff; color: #0f1724; }")
                    v = QVBoxLayout(dlg)
                    v.setContentsMargins(24, 20, 24, 18)
                    v.setSpacing(12)
                    heading = QLabel("새 제목을 입력하세요")
                    heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    heading.setStyleSheet("font-size:20px; font-weight:700;")
                    v.addWidget(heading)
                    box = QFrame()
                    box_lyt = QVBoxLayout(box)
                    box_lyt.setContentsMargins(12, 12, 12, 12)
                    box_lyt.setSpacing(8)
                    # Use single-line QLineEdit styled like the search input
                    edit = QLineEdit()
                    edit.setObjectName("rename-editor")
                    edit.setText(old)
                    edit.setMinimumHeight(48)
                    edit.setMaximumHeight(64)
                    edit.setPlaceholderText("새 제목을 입력하세요")
                    # Make the input wider within the rename dialog (use a percent of dialog width)
                    try:
                        min_edit_w = int(dlg.width() * 0.75)
                        max_edit_w = int(dlg.width() * 0.95)
                        edit.setMinimumWidth(min_edit_w)
                        edit.setMaximumWidth(max_edit_w)
                        edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                    except Exception:
                        pass
                    if self.dark_mode:
                        edit.setStyleSheet("QLineEdit { background: #0f0f0f; border: 1px solid #2a2a2a; border-radius: 12px; color: #e8e8e8; padding: 12px; }")
                    else:
                        edit.setStyleSheet("QLineEdit { background: #f6f7f9; border: 1px solid #e5e7eb; border-radius: 12px; color: #0f1724; padding: 12px; }")
                    box_lyt.addWidget(edit, 0, Qt.AlignmentFlag.AlignHCenter)
                    # Buttons
                    bottom = QWidget()
                    b_lyt = QHBoxLayout(bottom)
                    b_lyt.setContentsMargins(0, 0, 0, 0)
                    b_lyt.setSpacing(8)
                    b_lyt.addStretch()
                    cancel_btn = QPushButton("취소")
                    cancel_btn.clicked.connect(dlg.reject)
                    try:
                        cancel_btn.setStyleSheet("background: transparent; border: none; font-weight:700; font-size:15px; padding: 8px 16px;")
                    except Exception:
                        pass
                    b_lyt.addWidget(cancel_btn, 0, Qt.AlignmentFlag.AlignRight)
                    ok_btn = QPushButton("확인")
                    ok_btn.setFixedSize(84, 40)
                    try:
                        ok_btn.setStyleSheet("background: #5377f6; color: white; border-radius: 10px; font-weight:700; font-size:15px;")
                    except Exception:
                        pass
                    b_lyt.addWidget(ok_btn, 0, Qt.AlignmentFlag.AlignRight)
                    box_lyt.addWidget(bottom)
                    v.addWidget(box)
                    def on_ok():
                        try:
                            txt = (edit.text() or "").strip()
                            if txt and txt != old:
                                c["title"] = txt
                                c["updated_at"] = time.time()
                                self._schedule_persist()
                                self._render_chat_list()
                            dlg.accept()
                        except Exception:
                            dlg.reject()
                    ok_btn.clicked.connect(on_ok)
                    # Allow Enter to confirm
                    edit.returnPressed.connect(on_ok)
                    dlg.exec()
                    return
        except Exception:
            pass
    def _close_drawer(self) -> None:
        """Close the drawer panel (explicit slot for close button)."""
        try:
            # Use animated close so the X button triggers the same animation as the toggle
            self._set_drawer_open(False, animate=True)
        except Exception:
            # Defensive: ensure no exception bubbles up to UI event handler
            try:
                # Fallback: immediately hide and move off-screen
                if hasattr(self, "drawer_panel"):
                    w = self.drawer_panel.width()
                    self.drawer_panel.move(QPoint(-w, 0))
                    self.drawer_panel.hide()
                if hasattr(self, "drawer_overlay"):
                    self.drawer_overlay.hide()
            except Exception:
                pass

    def _hide_drawer_popup(self) -> None:
        """Hide and delete any in-drawer popup (profile/backup)."""
        try:
            if getattr(self, "_drawer_popup", None):
                try:
                    self._drawer_popup.hide()
                except Exception:
                    pass
                try:
                    self._drawer_popup.deleteLater()
                except Exception:
                    pass
                self._drawer_popup = None
        except Exception:
            pass

    def keyPressEvent(self, event) -> None:
        """Close drawer/popups on ESC key for convenience."""
        try:
            if event.key() == Qt.Key.Key_Escape and getattr(self, "_drawer_open", False):
                self._set_drawer_open(False, animate=True)
                return
        except Exception:
            pass
        try:
            super().keyPressEvent(event)
        except Exception:
            pass

    def eventFilter(self, obj, event) -> bool:
        """Event filter for handling various widget events."""
        # Pass event to parent class
        try:
            return super().eventFilter(obj, event)
        except Exception:
            return False

    def _activate_chat(self, chat_id: str, close_drawer: bool = True) -> None:
        """Activate the chat with the given id, loading its content into the UI.
        Args:
            chat_id: The ID of the chat to activate
            close_drawer: Whether to close the drawer after activation (default: True)
        """
        try:
            for chat in self._chats:
                if chat.get("id") == chat_id:
                    # Do NOT save current chat's UI state here to avoid overwriting messages
                    # Switch to new chat
                    self._current_chat_id = chat_id
                    # Restore script and log
                    if hasattr(self, "script_edit"):
                        self.script_edit.setPlainText(chat.get("script", ""))
                    if hasattr(self, "log_output"):
                        self.log_output.setPlainText(chat.get("log", ""))
                    # Clear and restore chat transcript
                    self._clear_chat_transcript()
                    self._restore_chat_messages(chat)
                    self._render_chat_list()
                    if close_drawer:
                        self._set_drawer_open(False)
                    return
        except Exception as e:
            print(f"[MainWindow] Error activating chat: {e}")
            import traceback
            traceback.print_exc()

    def _save_current_chat_state(self) -> None:
        """Save the current chat's UI state (messages, script, log) to the chat object."""
        try:
            for chat in self._chats:
                if chat.get("id") == self._current_chat_id:
                    # Save script and log
                    if hasattr(self, "script_edit"):
                        chat["script"] = self.script_edit.toPlainText()
                    if hasattr(self, "log_output"):
                        chat["log"] = self.log_output.toPlainText()

                    # Save chat messages (excluding thinking animation)
                    messages = []
                    for role, row, bubble in self._chat_widgets:
                        try:
                            # Skip if this is a thinking/loading message
                            html_text = bubble.text()
                            if html_text and not html_text.startswith("Thinking"):
                                # Convert HTML back to plain text
                                plain_text = (
                                    html_text
                                    .replace("<br/>", "\n")
                                    .replace("<br>", "\n")
                                    .replace("&lt;", "<")
                                    .replace("&gt;", ">")
                                    .replace("&amp;", "&")
                                )
                                messages.append({"role": role, "content": plain_text})
                        except Exception:
                            pass
                    # Only update messages if there are any in the UI; otherwise, leave as is
                    if messages:
                        chat["messages"] = messages
                        print(f"[MainWindow] Saved {len(messages)} messages for chat {self._current_chat_id}")
                    else:
                        print(f"[MainWindow] No messages in UI, not overwriting chat history for chat {self._current_chat_id}")
                    return
        except Exception as e:
            print(f"[MainWindow] Error saving chat state: {e}")

    def _clear_chat_transcript(self) -> None:
        """Clear all messages from the chat transcript UI."""
        try:
            # Remove all widgets from the layout (including welcome message)
            while self.chat_transcript_layout.count():
                item = self.chat_transcript_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.spacerItem():
                    # Don't delete spacer items, just remove them
                    pass
            
            # Clear chat widgets list
            self._chat_widgets.clear()
            
            # Clear thinking widget reference if present
            if self._thinking_widget:
                self._thinking_widget = None
            
            # Re-add stretch
            self.chat_transcript_layout.addStretch(1)
            print("[MainWindow] Chat transcript cleared")
        except Exception as e:
            print(f"[MainWindow] Error clearing chat transcript: {e}")

    def _restore_chat_messages(self, chat: dict) -> None:
        """Restore chat messages from the chat object to the UI."""
        try:
            messages = chat.get("messages", [])
            print(f"[MainWindow] Restoring {len(messages)} messages for chat {chat.get('id')}")
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content and role in ("user", "assistant", "system"):
                    # Directly add to UI without saving again (to avoid duplication)
                    self._add_message_to_ui_only(role, content)
        except Exception as e:
            print(f"[MainWindow] Error restoring chat messages: {e}")
            import traceback
            traceback.print_exc()

    def _add_message_to_ui_only(self, role: str, text: str) -> None:
        """Add a message to the UI without saving it to chat data (used for restoration)."""
        try:
            self._ensure_chat_transcript_visible()

            # Remove the stretch spacer at the end, append, then add it back.
            try:
                if self.chat_transcript_layout.count() > 0:
                    last_item = self.chat_transcript_layout.itemAt(self.chat_transcript_layout.count() - 1)
                    if last_item and last_item.spacerItem():
                        self.chat_transcript_layout.takeAt(self.chat_transcript_layout.count() - 1)
            except Exception:
                pass

            row = QWidget()
            row.setObjectName("chat-row")
            row_lyt = QHBoxLayout(row)
            row_lyt.setContentsMargins(0, 0, 0, 0)
            row_lyt.setSpacing(0)

            bubble = QLabel()
            bubble.setObjectName("chat-bubble")
            bubble.setWordWrap(True)
            bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            bubble.setTextFormat(Qt.TextFormat.RichText)
            bubble.setMaximumWidth(520)

            # Simple HTML escape + preserve newlines
            safe = (
                (text or "")
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br/>")
            )
            bubble.setText(safe)
            self._apply_chat_bubble_style(role, bubble)

            if role == "user":
                row_lyt.addStretch(1)
                row_lyt.addWidget(bubble, 0, Qt.AlignmentFlag.AlignRight)
            else:
                row_lyt.addWidget(bubble, 0, Qt.AlignmentFlag.AlignLeft)
                row_lyt.addStretch(1)

            self.chat_transcript_layout.addWidget(row, 0)
            self.chat_transcript_layout.addStretch(1)
            self._chat_widgets.append((role, row, bubble))

            # Scroll to bottom
            try:
                QTimer.singleShot(0, lambda: self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum()))
            except Exception:
                pass
        except Exception as e:
            print(f"[MainWindow] Error adding message to UI: {e}")

    def _apply_button_icon(
        self,
        button,
        icon_key: str,
        fallback_text: str,
        icon_size: QSize = QSize(22, 22),
        preserve_text: bool = False,
    ) -> None:
        """Set an icon on a button if the asset exists, otherwise fall back to text."""
        from pathlib import Path
        assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
        themed_keys = {"new": ("new-dark.svg", "new-light.svg"), "search": ("search-dark.svg", "search-light.svg")}
        button.setIcon(QIcon())
        if icon_key == "new":
            icon_file = assets_dir / ("new-dark.svg" if getattr(self, "dark_mode", False) else "new-light.svg")
            button.setIcon(QIcon(str(icon_file)))
            button.setIconSize(icon_size)
            if not preserve_text:
                button.setText("")
            return
        if icon_key == "search":
            icon_file = assets_dir / ("search-dark.svg" if getattr(self, "dark_mode", False) else "search-light.svg")
            if icon_file.exists():
                button.setIcon(QIcon(str(icon_file)))
                button.setIconSize(icon_size)
                if not preserve_text:
                    button.setText("")
                return
        icon_path = self._get_icon_path(icon_key)
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
        # Special-case: prefer specific light-themed assets for some icons regardless of current theme
        if not icon_path and icon_key in ("light", "settings"):
            try:
                # Try resolving with dark_mode=False so 'light-light.svg' or 'settings-light.svg' are found
                alt = design.get_icon_path(icon_key, False, use_theme=True)
                if alt:
                    icon_path = alt
            except Exception:
                pass

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
        """Return themed icon path if available (delegates to gui.design)."""
        return design.get_icon_path(icon_key, getattr(self, "dark_mode", False), use_theme=use_theme)

    def _get_icon_path_str(self, icon_key: str) -> str | None:
        path = self._get_icon_path(icon_key)
        return str(path) if path else None

    def _make_pixmap_background_transparent(self, pix: QPixmap, tolerance: int = 8) -> QPixmap | None:
        """Make a uniform background color transparent by sampling a corner pixel and making nearby colors transparent."""
        try:
            img = pix.toImage().convertToFormat(QImage.Format_ARGB32)
            w = img.width()
            h = img.height()
            sample = None
            for sx, sy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
                c = QColor(img.pixel(sx, sy))
                if c.alpha() > 16:
                    sample = c
                    break
            if sample is None:
                return pix
            sr, sg, sb = sample.red(), sample.green(), sample.blue()
            for y in range(h):
                for x in range(w):
                    c = QColor(img.pixel(x, y))
                    dr = abs(c.red() - sr)
                    dg = abs(c.green() - sg)
                    db = abs(c.blue() - sb)
                    if dr <= tolerance and dg <= tolerance and db <= tolerance:
                        img.setPixelColor(x, y, QColor(0, 0, 0, 0))
            return QPixmap.fromImage(img)
        except Exception:
            return None

    def _set_drawer_toggle_icon(self, size_px: int = 28) -> None:
        """Set the drawer toggle button icon, using a dark variant when in dark mode and stripping any uniform background color."""
        try:
            assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
            if getattr(self, 'drawer_toggle_btn', None) is None:
                return
            # Prefer a theme-specific openbtn asset: use openbtn-dark.png in dark mode, otherwise openbtn.png
            if getattr(self, 'dark_mode', False):
                candidate = assets_dir / "openbtn-dark.png"
                if not candidate.exists():
                    alt = assets_dir / "openbtn.png"
                    candidate = alt if alt.exists() else None
            else:
                candidate = assets_dir / "openbtn.png"
                if not candidate.exists():
                    alt = assets_dir / "openbtn-dark.png"
                    candidate = alt if alt.exists() else None
            if candidate is not None:
                # First try setting the file icon directly (no processing) using a slightly smaller size
                try:
                    direct_icon = QIcon(str(candidate))
                    direct_size = max(12, size_px - 8)
                    self.drawer_toggle_btn.setIcon(direct_icon)
                    self.drawer_toggle_btn.setIconSize(QSize(direct_size, direct_size))
                    # Quick transparency test on the direct pixmap; if too transparent, fall back to processing
                    direct_pix = direct_icon.pixmap(direct_size, direct_size)
                    def _almost_transparent(pix: QPixmap, thresh: float = 0.7) -> bool:
                        try:
                            img = pix.toImage().convertToFormat(QImage.Format_ARGB32)
                            w = img.width(); h = img.height()
                            total = w * h
                            if total == 0:
                                return True
                            transparent = 0
                            for y in range(h):
                                for x in range(w):
                                    if QColor(img.pixel(x, y)).alpha() < 16:
                                        transparent += 1
                            return (transparent / total) >= thresh
                        except Exception:
                            return False
                    if not _almost_transparent(direct_pix, thresh=0.85):
                        # direct icon looks fine — keep it
                        return
                except Exception:
                    # fall through to processing
                    pass

                # Otherwise, attempt to strip uniform backgrounds (use higher tolerance) and aggressive border removal
                pix = QPixmap(str(candidate))
                processed = self._make_pixmap_background_transparent(pix, tolerance=40) or pix
                try:
                    corner_alpha = processed.toImage().pixelColor(0, 0).alpha()
                except Exception:
                    corner_alpha = 255
                if corner_alpha > 16:
                    try:
                        img = pix.toImage().convertToFormat(QImage.Format_ARGB32)
                        w = img.width()
                        h = img.height()
                        sr = sg = sb = count = 0
                        for x in range(w):
                            for y in (0, h - 1):
                                c = QColor(img.pixel(x, y))
                                if c.alpha() > 16:
                                    sr += c.red(); sg += c.green(); sb += c.blue(); count += 1
                        for y in range(h):
                            for x in (0, w - 1):
                                c = QColor(img.pixel(x, y))
                                if c.alpha() > 16:
                                    sr += c.red(); sg += c.green(); sb += c.blue(); count += 1
                        if count > 0:
                            sr //= count; sg //= count; sb //= count
                            tol = 80
                            for yy in range(h):
                                for xx in range(w):
                                    c = QColor(img.pixel(xx, yy))
                                    if abs(c.red() - sr) <= tol and abs(c.green() - sg) <= tol and abs(c.blue() - sb) <= tol:
                                        img.setPixelColor(xx, yy, QColor(0, 0, 0, 0))
                            processed = QPixmap.fromImage(img)
                    except Exception:
                        pass

                processed = processed.scaled(size_px, size_px, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.drawer_toggle_btn.setIcon(QIcon(processed))
                self.drawer_toggle_btn.setIconSize(QSize(size_px, size_px))
            else:
                self._set_material_symbol(self.drawer_toggle_btn, "menu", fallback="≡", px=size_px - 6)
        except Exception:
            try:
                self._set_material_symbol(self.drawer_toggle_btn, "menu", fallback="≡", px=20)
            except Exception:
                pass

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
        # Allow targeted styling and transparency for the top navbar
        self.header_area.setObjectName("header-area")
        try:
            self.header_area.setStyleSheet("background-color: transparent;")
        except Exception:
            pass
        header_layout = QVBoxLayout(self.header_area)
        header_layout.setContentsMargins(40, 40, 40, 0)
        header_layout.setSpacing(20)
        
        header_layout.addWidget(self._build_header())
        header_layout.addWidget(self._build_templates(), 0)  # No stretch
        
        # Output area (conversation/chat display)
        self.output_area = QWidget()
        self.output_area.setObjectName("output-container")
        output_layout = QVBoxLayout(self.output_area)
        output_layout.setContentsMargins(40, 20, 40, 20)
        output_layout.setSpacing(16)
        
        # ChatGPT-style transcript (shown above the input when the user asks AI)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setObjectName("chat-scroll")
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chat_scroll.setStyleSheet("QScrollArea{ background: transparent; border: none; }")

        self.chat_transcript = QWidget()
        self.chat_transcript.setObjectName("chat-transcript")
        self.chat_transcript_layout = QVBoxLayout(self.chat_transcript)
        self.chat_transcript_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_transcript_layout.setSpacing(10)
        self.chat_transcript_layout.addStretch(1)
        self.chat_scroll.setWidget(self.chat_transcript)
        output_layout.addWidget(self.chat_scroll, 1)

        # Existing conversation-style output area (used by script logs/progress). Keep it for compatibility,
        # but hide it by default so the visible UI resembles ChatGPT.
        self.log_output = QTextEdit()
        self.log_output.setObjectName("log-output")
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(150)
        # Context menu for log output
        self.log_output.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.log_output.customContextMenuRequested.connect(self._show_log_context_menu)
        self.log_output.hide()
        output_layout.addWidget(self.log_output, 0)
        
        # Input area at bottom (fixed)
        input_area = QWidget()
        input_area.setObjectName("input-container")
        input_layout = QVBoxLayout(input_area)
        # Keep the composer compact (shorter input form height).
        input_layout.setContentsMargins(20, 0, 20, 16)
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
        script_layout.setContentsMargins(16, 16, 16, 16)
        script_layout.setSpacing(12)
        
        # Natural language input field (changed from code editor to chat-like input)
        self.script_edit = FileDropTextEdit()
        self.script_edit.setObjectName("script-editor")
        self.script_edit.setPlaceholderText("무엇을 하고 싶으신가요? (예: '수학 문제'라는 제목을 입력하고 이차방정식 공식을 삽입해줘)")
        self.script_edit.setPlainText("")  # Start with empty input
        # Smaller editor height to reduce overall input form height.
        self.script_edit.setMaximumHeight(220)
        # Connect file drop signal
        self.script_edit.file_dropped.connect(self._handle_file_drop_in_input)
        self.script_edit.setMinimumHeight(140)
        # Custom context menu in Korean
        self.script_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.script_edit.customContextMenuRequested.connect(self._show_editor_context_menu)
        
        # Override keyPressEvent for Enter/Shift+Enter handling
        original_key_press = self.script_edit.keyPressEvent
        def custom_key_press(event):
            # Check if Enter or Return key is pressed
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Check if Shift is held down
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    # Shift+Enter: insert new line (default behavior)
                    original_key_press(event)
                else:
                    # Enter alone: send message
                    try:
                        self._handle_run_clicked()
                    except Exception as e:
                        print(f"Error in custom_key_press: {e}")
            else:
                # Other keys: default behavior
                original_key_press(event)
        
        self.script_edit.keyPressEvent = custom_key_press  # type: ignore[method-assign]
        
        script_layout.addWidget(self.script_edit)
        
        # Bottom row with '+' button for files/images, AI selector, and Run button
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(12)
        
        # (Removed) add_file_btn: the circular plus upload button was removed per UX request.

        # Small plus button to the left of the HWP pill (theme-aware asset: plus.png / plus-dark.png)
        # Recreate add button from scratch (minimal, modern, SVG plus icon)
        self.hwp_add_btn = QPushButton("")
        self.hwp_add_btn.setObjectName("hwp-add-button")
        self.hwp_add_btn.setToolTip("파일 또는 이미지 추가")
        self.hwp_add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hwp_add_btn.setFixedSize(64, 64)
        self.hwp_add_btn.setStyleSheet("QPushButton#hwp-add-button { background: transparent; border: none; border-radius: 16px; font-size: 40px; }")
        try:
            assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
            if getattr(self, 'dark_mode', False):
                plus_icon_path = assets_dir / "plus-dark.png"
            else:
                plus_icon_path = assets_dir / "plus.png"
            if plus_icon_path.exists():
                self.hwp_add_btn.setIcon(QIcon(str(plus_icon_path)))
                self.hwp_add_btn.setIconSize(QSize(40, 40))
                self.hwp_add_btn.setText("")
            else:
                self.hwp_add_btn.setText("+")
        except Exception:
            self.hwp_add_btn.setText("+")
        self.hwp_add_btn.clicked.connect(self._handle_add_file)
        bottom_row.addWidget(self.hwp_add_btn)

        # HWP filename display (text only)
        self.hwp_filename_label = QLabel("한글 문서")
        self.hwp_filename_label.setObjectName("hwp-filename-text")
        self.hwp_filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_row.addWidget(self.hwp_filename_label)
        bottom_row.addSpacing(8)

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

        # Model label to the right of the flash/AI icon (hidden in simplified layout)
        initial_model = getattr(self, "current_model", None) or "gpt-5-nano"
        self.model_label = QLabel(initial_model)
        self.model_label.setObjectName("model-label")
        self.model_label.setStyleSheet(
            "font-size: 14px; font-weight: 800; color: #0f1724;"
            "background: transparent; padding: 0 6px; margin: 0;"
        )
        bottom_row.addWidget(self.model_label)
        # Initialize current model state and ensure default selection is applied
        try:
            # Ensure everything (top display, bottom label, icon) is updated consistently
            self._set_model(initial_model)
        except Exception:
            try:
                self._set_model("gpt-5-nano")
            except Exception:
                # Fallback: set internal state directly
                self._current_model = "gpt-5-nano"
                try:
                    if hasattr(self, "top_model_display"):
                        self.top_model_display.setText(self._current_model)
                except Exception:
                    pass
        
        bottom_row.addStretch()
        # HWP pill already added near the upload button

        # Microphone button (hidden in simplified layout)
        self.mic_btn = QPushButton("[MIC]")
        self.mic_btn.setObjectName("upload-button")
        self.mic_btn.setMaximumWidth(44)
        self.mic_btn.setMinimumWidth(44)
        self.mic_btn.setMinimumHeight(44)
        self.mic_btn.setToolTip("음성 입력")
        self.mic_btn.clicked.connect(self._handle_voice_input)
        self._apply_button_icon(self.mic_btn, "mic", "[MIC]", QSize(28, 28))
        bottom_row.addWidget(self.mic_btn)
        # Hide non-essential composer controls per simplified layout
        try:
            self.ai_selector_btn.hide()
            self.model_label.hide()
            self.hwp_filename_label.hide()
            self.mic_btn.hide()
        except Exception:
            pass
        
        # Send button - just the icon, no border
        self.send_btn = QPushButton()
        self.send_btn.setObjectName("send-button")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setToolTip("메시지 전송")
        self.send_btn.setFixedSize(44, 44)
        self.send_btn.setStyleSheet("QPushButton { background: transparent; border: none; padding: 0; }")
        self.send_btn.clicked.connect(self._handle_run_clicked)
        self._set_send_svg_icon()
        bottom_row.addWidget(self.send_btn)
        
        script_layout.addLayout(bottom_row)
        
        input_layout.addWidget(script_container)

        # Add areas to main column with proper spacing
        # NOTE: keep the main screen minimal — don't add the header or output area
        # Hero area (centered prompt + pill buttons)
        hero_area = QWidget()
        hero_layout = QVBoxLayout(hero_area)
        hero_layout.setContentsMargins(40, 0, 40, 0)
        hero_layout.setSpacing(0)
        hero_layout.addStretch(1)
        hero_prompt = QLabel("무엇이든 입력하세요")
        hero_prompt.setObjectName("hero-prompt")
        hero_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cp_color = "#000000" if not self.dark_mode else "#ffffff"
        # Keep hero prompt size fixed to the light theme size (avoid jumping on theme toggle).
        hero_prompt.setStyleSheet(f"font-size:36px; font-weight:800; color:{cp_color};")
        self.center_prompt = hero_prompt
        hero_layout.addWidget(self.center_prompt, alignment=Qt.AlignmentFlag.AlignCenter)
        hero_layout.addSpacing(18)
        hero_layout.addStretch(1)
        # Store hero area so we can hide it when chat transcript becomes active.
        self.hero_area = hero_area
        main_column.addWidget(hero_area, 1)

        # Top-left hamburger (drawer toggle)
        top_bar = QWidget()
        top_bar.setObjectName("top-bar-hamburger")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(12, 12, 12, 0)
        top_bar_layout.setSpacing(0)
        self.drawer_toggle_btn = QToolButton()
        self.drawer_toggle_btn.setObjectName("drawer-toggle")
        # Keep a visible rounded background for the hamburger (not auto-raise)
        self.drawer_toggle_btn.setAutoRaise(False)
        self.drawer_toggle_btn.setToolTip("메뉴 열기")
        self.drawer_toggle_btn.setFixedSize(36, 36)
        self.drawer_toggle_btn.clicked.connect(self._toggle_drawer)
        # Set drawer toggle icon (handles dark-mode variant, background removal, and sizing)
        try:
            self._set_drawer_toggle_icon(size_px=36)
        except Exception:
            try:
                self._set_material_symbol(self.drawer_toggle_btn, "menu", fallback="≡", px=22)
            except Exception:
                self.drawer_toggle_btn.setText("≡")
        top_bar_layout.addWidget(self.drawer_toggle_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        # Add spacing between hamburger and model display for better separation
        top_bar_layout.addSpacing(12)

        # Model display (container) to the right of the open/hamburger button
        try:
            # Use a lightweight QWidget so we can precisely control spacing between text and icon
            self.top_model_display = QWidget(top_bar)
            self.top_model_display.setObjectName("top-model-display")
            h = QHBoxLayout(self.top_model_display)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(2)
            # Text label
            self._top_model_text = QLabel(getattr(self, "_current_model_display", None) or getattr(self, "current_model", "gpt-5-nano"))
            self._top_model_text.setObjectName("top-model-text")
            # Apply theme-aware styling (kept in one place so theme toggles don't drift).
            self._apply_top_model_text_style()
            h.addWidget(self._top_model_text)
            # Icon label (arrow) placed to the right; we'll nudge it left to create consistent spacing
            self._top_model_icon = QLabel()
            self._top_model_icon.setObjectName("top-model-icon")
            # Place icon to the right of the text with a moderate left margin
            self._top_model_icon.setStyleSheet("margin-left: 2px;")
            # Keep a small square so the chevron looks crisp (avoid scaling a raster asset).
            self._top_model_icon.setFixedSize(14, 14)
            self._top_model_icon.setScaledContents(False)
            self._top_model_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            h.addWidget(self._top_model_icon)
            # Make the whole widget clickable
            self.top_model_display.setCursor(Qt.CursorShape.PointingHandCursor)
            def _click_ev(ev):
                try:
                    self._show_ai_selector()
                except Exception:
                    pass
            self.top_model_display.mouseReleaseEvent = _click_ev

            # Helper adapter methods so existing code can call setText/setIcon/text()
            def _set_text(txt: str) -> None:
                try:
                    self._top_model_text.setText(txt)
                except Exception:
                    pass
            def _text() -> str:
                try:
                    return self._top_model_text.text()
                except Exception:
                    return ""
            def _set_icon_from_path(path_str: str, w: int = 18, h: int = 10) -> None:
                try:
                    pm = QPixmap(str(path_str))
                    if not pm.isNull():
                        # scale to the requested rectangle size; keep aspect ratio for safety
                        pm = pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self._top_model_icon.setPixmap(pm)
                except Exception:
                    pass
            def _set_icon(icon: QIcon) -> None:
                try:
                    pm = icon.pixmap(QSize(18, 10))
                    self._top_model_icon.setPixmap(pm)
                except Exception:
                    pass
            def _set_icon_size(sz: QSize) -> None:
                try:
                    pm = self._top_model_icon.pixmap()
                    if pm is not None:
                        pm = pm.scaled(sz.width(), sz.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self._top_model_icon.setPixmap(pm)
                except Exception:
                    pass
            # Attach adapter functions
            setattr(self.top_model_display, "setText", _set_text)
            setattr(self.top_model_display, "text", _text)
            setattr(self.top_model_display, "setIcon", _set_icon)
            setattr(self.top_model_display, "setIconFromPath", _set_icon_from_path)
            setattr(self.top_model_display, "setIconSize", _set_icon_size)
            setattr(self.top_model_display, "setLayoutDirection", lambda *_: None)

            # Draw a crisp chevron (avoids blurry raster scaling).
            try:
                self._set_top_model_chevron()
            except Exception:
                try:
                    self._top_model_icon.setText("▾")
                except Exception:
                    pass

            top_bar_layout.addWidget(self.top_model_display, alignment=Qt.AlignmentFlag.AlignLeft)
            top_bar_layout.addSpacing(6)
            # If an older pill button exists, hide it to avoid duplication
            if hasattr(self, "top_model_btn"):
                try:
                    self.top_model_btn.hide()
                except Exception:
                    pass
        except Exception:
            pass

        top_bar_layout.addStretch()
        main_column.insertWidget(0, top_bar, 0)

        # Insert chat transcript area above the input. Hidden until first AI message.
        try:
            self.output_area.hide()
        except Exception:
            pass
        main_column.insertWidget(2, self.output_area, 1)

        # Input pinned to bottom; height managed by _update_composer_height()
        main_column.addWidget(input_area, 0)

        # Ensure the central/main area object name is set; theme is applied in _apply_styles
        central.setObjectName("central")
        try:
            # Do not set inline background here; use _apply_styles() to control light/dark backgrounds
            main_area.setStyleSheet("")
        except Exception:
            pass

        # Build drawer overlay and panel (initially hidden)
        self._build_drawer(central)
        self._update_drawer_geometry()

        layout.addWidget(main_area, 1)
        self.setCentralWidget(central)

        # Chat transcript state
        self._chat_widgets: list[tuple[str, QWidget, QLabel]] = []  # (role, row_widget, bubble_label)
        self._thinking_widget: tuple[QWidget, QLabel] | None = None  # (row_widget, bubble_label)
        self._thinking_timer: QTimer | None = None
        self._thinking_dots = 0
        self._auto_execute_mode = False  # Flag to auto-execute generated code without showing it


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
        title = QLabel("Nova AI")
        title.setObjectName("app-title")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        subtitle = QLabel("최고의 한글 수식 자동화 에이전트")
        subtitle.setObjectName("app-subtitle")
        
        lyt.addWidget(title_container, alignment=Qt.AlignmentFlag.AlignCenter)
        lyt.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        return frame

    def _build_help_buttons(self) -> QWidget:
        """Build compact help buttons for the top-left area."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.howto_button = QPushButton("도움말")
        self.howto_button.setObjectName("help-button")
        self.howto_button.setFixedHeight(34)
        self.howto_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.howto_button.setToolTip("프로그램 사용 방법과 함수 가이드를 제공합니다")
        self.howto_button.clicked.connect(self._show_howto)
        self.howto_button.setText("도움말")
        self._apply_button_icon(self.howto_button, "help", "[?]", QSize(18, 18), preserve_text=True)
        layout.addWidget(self.howto_button)
        
        self.latex_button = QPushButton("</> LaTeX")
        self.latex_button.setObjectName("help-button")
        self.latex_button.setFixedHeight(34)
        self.latex_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.latex_button.setToolTip("LaTeX 수식 문법 가이드를 제공합니다")
        self.latex_button.clicked.connect(self._show_latex_helper)
        layout.addWidget(self.latex_button)
        
        self.ai_generate_button = QPushButton("AI 생성")
        self.ai_generate_button.setObjectName("help-button")
        self.ai_generate_button.setFixedHeight(34)
        self.ai_generate_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.ai_generate_button.setToolTip("AI가 스크립트를 생성합니다")
        self.ai_generate_button.clicked.connect(self._show_ai_generate_dialog)
        self.ai_generate_button.setText("AI 생성")
        self._apply_button_icon(self.ai_generate_button, "generate", "[+]", QSize(18, 18), preserve_text=True)
        layout.addWidget(self.ai_generate_button)

        # Apply distinct styling to help buttons after loading theme
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
        """Build the actual sidebar content (used inside the hidden drawer panel)."""
        frame = QFrame()
        frame.setObjectName("sidebar-content")
        lyt = QVBoxLayout(frame)
        # Use compact margins so the sidebar content occupies top and bottom tightly
        lyt.setContentsMargins(6, 6, 6, 6)
        # Slight spacing for readable grouping
        lyt.setSpacing(8)

        # Header: title + close button
        header = QWidget()
        header.setObjectName("drawer-header")
        hl = QHBoxLayout(header)
        # Match the left/top inset of drawer action buttons so the title lines up vertically/ horizontally
        hl.setContentsMargins(12, 12, 12, 0)
        hl.setSpacing(8)
        title = QLabel("Nova AI")
        title.setObjectName("drawer-title")
        title.setStyleSheet("font-weight:800; font-size:20px;")
        hl.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        hl.addStretch()
        close_btn = QToolButton()
        close_btn.setObjectName("drawer-close-btn")
        close_btn.setAutoRaise(False)
        close_btn.setFixedSize(36, 36)
        close_btn.setText("✕")
        close_btn.setToolTip("닫기")
        close_btn.clicked.connect(self._close_drawer)
        # Keep close button at the far right
        hl.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        lyt.addWidget(header)

        # Primary actions (New Chat / Search)
        self.drawer_new_chat_btn = QPushButton("새 채팅")
        self.drawer_new_chat_btn.setObjectName("drawer-action")
        self.drawer_new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.drawer_new_chat_btn.setMinimumHeight(48)
        self.drawer_new_chat_btn.clicked.connect(self._new_chat)
        # Use theme-specific SVG assets for the icon
        try:
            assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
            # Always check the current theme before loading the icon
            is_dark = self.dark_mode if hasattr(self, 'dark_mode') else False
            icon_name = "new-dark.svg" if is_dark else "new-light.svg"
            new_icon = assets_dir / icon_name
            if new_icon.exists():
                self.drawer_new_chat_btn.setIcon(QIcon(str(new_icon)))
                self.drawer_new_chat_btn.setIconSize(QSize(22, 22))
            else:
                # fallback: try the other icon
                alt_icon = assets_dir / ("new-light.svg" if is_dark else "new-dark.svg")
                if alt_icon.exists():
                    self.drawer_new_chat_btn.setIcon(QIcon(str(alt_icon)))
                    self.drawer_new_chat_btn.setIconSize(QSize(22, 22))
                else:
                    self.drawer_new_chat_btn.setIcon(QIcon())
        except Exception:
            self.drawer_new_chat_btn.setIcon(QIcon())
        # Group primary actions into a compact container so the spacing between them is narrower
        actions_wrap = QWidget()
        aw_lyt = QVBoxLayout(actions_wrap)
        aw_lyt.setContentsMargins(0, 0, 0, 0)
        # Narrower spacing between the two primary buttons only
        aw_lyt.setSpacing(0)
        try:
            # Inline styling for tight vertical rhythm without touching global QSS
            # Reduce bottom margin to bring the buttons closer
            self.drawer_new_chat_btn.setStyleSheet("padding:8px 10px; margin-top:2px; margin-bottom:0px;")
        except Exception:
            pass
        aw_lyt.addWidget(self.drawer_new_chat_btn)

        # Remove spacer and directly style the search button to sit closer to the new-chat button
        self.drawer_search_btn = QPushButton("채팅 검색")
        self.drawer_search_btn.setObjectName("drawer-action")
        self.drawer_search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.drawer_search_btn.setMinimumHeight(48)
        self.drawer_search_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        try:
            self.drawer_search_btn.setStyleSheet("margin-top:-8px; margin-bottom: 4px; padding:6px 10px; font-size:15px; font-weight:800;")
        except Exception:
            pass
        self.drawer_search_btn.clicked.connect(self._open_chat_search)
        # Use theme-specific SVG assets for the icon
        try:
            search_icon = assets_dir / ("search-dark.svg" if getattr(self, "dark_mode", False) else "search-light.svg")
            if not search_icon.exists():
                alt = assets_dir / ("search-light.svg" if getattr(self, "dark_mode", False) else "search-dark.svg")
                search_icon = alt if alt.exists() else search_icon
            if search_icon.exists():
                self.drawer_search_btn.setIcon(QIcon(str(search_icon)))
                self.drawer_search_btn.setIconSize(QSize(22, 22))
            else:
                self.drawer_search_btn.setIcon(QIcon())
        except Exception:
            self.drawer_search_btn.setIcon(QIcon())
        aw_lyt.addWidget(self.drawer_search_btn)
        lyt.addWidget(actions_wrap)

        # Section title
        # Section title with reset-search button on the right
        section_wrap = QWidget()
        sw_lyt = QHBoxLayout(section_wrap)
        sw_lyt.setContentsMargins(0, 0, 0, 0)
        sw_lyt.setSpacing(8)
        section = QLabel("내 채팅")
        section.setObjectName("drawer-section-title")
        sw_lyt.addWidget(section, 0, Qt.AlignmentFlag.AlignLeft)
        # Reset search button: clears the current chat filter
        reset_btn = QToolButton()
        reset_btn.setObjectName('drawer-section-reset')
        reset_btn.setToolTip('검색 초기화')
        # Use auto-raise for a flat look and remove any border via inline style
        reset_btn.setAutoRaise(True)
        # Increase size for easier tapping and visual balance
        reset_btn.setFixedSize(36, 36)
        reset_btn.setText('✕')
        # Remove the gray border and use a neutral muted color
        try:
            reset_btn.setStyleSheet('background: transparent; border: none; font-size: 16px; color: #6b7280;')
        except Exception:
            pass
        reset_btn.clicked.connect(self._reset_chat_filter)
        # hidden by default until a filter is active
        reset_btn.hide()
        sw_lyt.addWidget(reset_btn, 0, Qt.AlignmentFlag.AlignRight)
        lyt.addWidget(section_wrap)
        # expose for update when filter changes
        self.drawer_reset_btn = reset_btn

        # Add spacing between "내 채팅" and the chat list
        lyt.addSpacing(12)

        # Scrollable chat list
        scroll = QScrollArea()
        scroll.setObjectName("drawer-chat-scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        list_host = QWidget()
        list_host.setObjectName("drawer-chat-list")
        v = QVBoxLayout(list_host)
        v.setContentsMargins(0, 0, 0, 0)
        # Add a small vertical gap between chat rows so their gray hover backgrounds don't touch
        v.setSpacing(8)
        # Anchor items to the top so a short list doesn't vertically distribute items
        try:
            v.setAlignment(Qt.AlignmentFlag.AlignTop)
        except Exception:
            pass
        self.drawer_chat_list_layout = v
        scroll.setWidget(list_host)
        lyt.addWidget(scroll, 1)

        # Divider
        divider = QFrame()
        divider.setObjectName("drawer-divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Plain)
        # In dark mode the default HLine can look like a harsh black line; hide it and rely on the profile-wrap border instead
        try:
            if getattr(self, 'dark_mode', False):
                divider.hide()
        except Exception:
            pass
        lyt.addWidget(divider)
        # Small gap between divider and profile area for breathing room
        lyt.addSpacing(8)

        # Profile area (opens profile menu with Save/Load/Backup/Theme/Settings)
        profile_wrap = QWidget()
        profile_wrap.setObjectName("drawer-profile-wrap")
        pwl = QHBoxLayout(profile_wrap)
        # Increase vertical padding so the profile area becomes taller and feels roomier
        pwl.setContentsMargins(8, 10, 8, 10)
        pwl.setSpacing(10)

        avatar = QLabel()
        avatar.setObjectName("drawer-avatar")
        # Try to load a profile photo if present (user-provided only)
        try:
            assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
            # Prefer explicit user-provided path only. Do NOT fallback to bundled images — show an initial-letter avatar when no user image is set.
            candidate = getattr(self, "profile_avatar_path", None)
            if candidate:
                candidate = Path(candidate)
            if candidate and Path(candidate).exists():
                # Load and make a rounded pixmap
                def _rounded_pixmap(pth, size=48):
                    pix = QPixmap(str(pth))
                    if pix.isNull():
                        return None
                    pix = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                    out = QPixmap(size, size)
                    out.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(out)
                    try:
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                        pathp = QPainterPath()
                        pathp.addEllipse(0, 0, size, size)
                        painter.setClipPath(pathp)
                        painter.drawPixmap(0, 0, pix)
                    finally:
                        painter.end()
                    return out
                rounded = _rounded_pixmap(candidate, 48)
                if rounded:
                    avatar.setPixmap(rounded)
                    avatar.setFixedSize(48, 48)
                    avatar.setStyleSheet("border-radius: 24px; background: transparent;")
                else:
                    raise Exception("invalid pixmap")
            else:
                # No explicit user avatar provided — fall back to initial-letter avatar (handled below in except)
                raise Exception("no avatar found")
        except Exception:
            # Fallback: initial letter avatar with prominent blue background
            initial = (self.profile_display_name[:1] or "U").upper()
            avatar.setText(initial)
            avatar.setFixedSize(48, 48)
            try:
                avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
                avatar.setStyleSheet("background:#2b7bf6; color:#ffffff; border-radius:24px; font-weight:800; font-size:16px;")
                f = avatar.font()
                f.setPointSize(16)
                try:
                    f.setWeight(QFont.Weight.DemiBold)
                except Exception:
                    f.setWeight(QFont.Weight.Bold)
                avatar.setFont(f)
            except Exception:
                pass
            # Center the initial and apply the strong blue circle style from the design
            try:
                avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
                avatar.setStyleSheet("background:#2b7bf6; color:#ffffff; border-radius:20px; font-weight:800; font-size:16px;")
                f = avatar.font()
                f.setPointSize(16)
                try:
                    f.setWeight(QFont.Weight.DemiBold)
                except Exception:
                    f.setWeight(QFont.Weight.Bold)
                avatar.setFont(f)
            except Exception:
                pass

        name_box = QWidget()
        nb_lyt = QVBoxLayout(name_box)
        nb_lyt.setContentsMargins(0, 0, 0, 0)
        nb_lyt.setSpacing(2)
        name_lbl = QLabel(self.profile_display_name)
        name_lbl.setObjectName("drawer-user-name")
        self.drawer_name_label = name_lbl  # Store reference for style updates
        # Apply theme-aware typography: bold name, darker in light mode, white in dark mode
        try:
            if getattr(self, 'dark_mode', False):
                name_lbl.setStyleSheet('font-weight:800; font-size:16px; color:#ffffff;')
            else:
                name_lbl.setStyleSheet('font-weight:800; font-size:16px; color:#0f1724;')
        except Exception:
            name_lbl.setStyleSheet('font-weight:800;')
        plan_lbl = QLabel(self.profile_plan)
        plan_lbl.setObjectName("drawer-user-plan")
        # Subtle plan label styling (smaller, slightly muted)
        try:
            if getattr(self, 'dark_mode', False):
                plan_lbl.setStyleSheet('font-weight:700; font-size:13px; color:#9ca3af;')
            else:
                plan_lbl.setStyleSheet('font-weight:700; font-size:13px; color:#374151;')
        except Exception:
            pass
        nb_lyt.addWidget(name_lbl)
        nb_lyt.addWidget(plan_lbl)

        profile_btn = QToolButton()
        profile_btn.setObjectName("drawer-profile-btn")
        profile_btn.setToolTip("계정")
        profile_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        profile_btn.clicked.connect(self._show_profile_menu)
        # expose for use by popup positioning / other helpers
        self.drawer_profile_btn = profile_btn

        # Make the whole profile area act as the toggle: hide small corner button and make wrapper clickable
        try:
            profile_btn.hide()
        except Exception:
            pass
        try:
            profile_wrap.setCursor(Qt.CursorShape.PointingHandCursor)
            profile_wrap.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        except Exception:
            pass

        def _profile_click(e, s=self):
            try:
                s._show_profile_menu()
            except Exception:
                pass

        def _profile_key(e, s=self):
            try:
                if e.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                    s._show_profile_menu()
            except Exception:
                pass

        # Attach handlers to the wrapper
        try:
            profile_wrap.mousePressEvent = _profile_click  # type: ignore[assignment]
            profile_wrap.keyPressEvent = _profile_key  # type: ignore[assignment]
        except Exception:
            pass

        pwl.addWidget(avatar)
        pwl.addWidget(name_box)
        pwl.addStretch()
        pwl.addWidget(profile_btn)

        lyt.addWidget(profile_wrap, 0)

        lyt.addStretch()
        return frame

    def _build_drawer(self, parent: QWidget) -> None:
        """Create a drawer panel and overlay attached to `parent` (hidden by default)."""
        overlay = QWidget(parent)
        overlay.setObjectName("drawer-overlay")
        overlay.hide()
        overlay.mousePressEvent = lambda e: self._set_drawer_open(False)  # type: ignore[assignment]
        self.drawer_overlay = overlay

        drawer = QFrame(parent)
        drawer.setObjectName("drawer")
        # Responsive drawer width (narrower: max 300, leave at least 120px of main content visible)
        parent_rect = parent.rect()
        # Ensure the drawer doesn't cover the whole screen on narrow windows — reserve 120px for main area
        desired_w = max(180, min(300, parent_rect.width() - 120))
        drawer.setFixedWidth(desired_w)
        drawer.move(-desired_w, 0)
        drawer.hide()
        self.drawer_panel = drawer
        # Install a global event filter once so clicks inside the drawer (but outside any popup)
        # will close transient in-drawer popups (profile, backups, etc.). We guard to avoid re-installing.
        try:
            if not getattr(self, '_drawer_global_filter_installed', False):
                app = QApplication.instance()
                if app:
                    app.installEventFilter(self)
                    self._drawer_global_filter_installed = True
        except Exception:
            pass

        dlyt = QVBoxLayout(drawer)
        # Use minimal outer padding so content can use the full drawer area
        dlyt.setContentsMargins(0, 0, 0, 0)
        dlyt.setSpacing(6)

        # Add sidebar content built by _build_sidebar
        content = self._build_sidebar()
        dlyt.addWidget(content) 
        # Ensure any in-drawer popup is hidden when drawer initially built
        self._hide_drawer_popup()
        # Populate chat list from in-memory store
        try:
            self._render_chat_list()
        except Exception:
            pass

    def _set_drawer_open(self, open_: bool, animate: bool = True) -> None:
        self._drawer_open = open_
        
        # Render chat list when opening drawer to show latest state
        if open_:
            self._render_chat_list()
        
        self._apply_drawer_state(animate=animate)
        if not open_:
            # hide any popups when closing the drawer
            self._hide_drawer_popup()

    def eventFilter(self, obj: QObject, event) -> bool:  # type: ignore[override]
        """Global event filter to close the drawer popup when clicking elsewhere inside the drawer.

        Behavior:
        - If a mouse press occurs and the profile popup is visible, and the click is inside the drawer
          but outside the popup, hide the popup and allow the event to continue (do not swallow it).
        """
        try:
            from PySide6.QtCore import QEvent
            if event.type() == QEvent.Type.MouseButtonPress:
                if getattr(self, '_drawer_popup', None) and getattr(self, 'drawer_panel', None) and self._drawer_popup.isVisible():
                    # Get global click position (Qt6: globalPosition returns QPointF)
                    try:
                        gp = event.globalPosition().toPoint()
                    except Exception:
                        try:
                            gp = event.globalPos()
                        except Exception:
                            gp = None
                    if gp is None:
                        return super().eventFilter(obj, event)

                    popup = self._drawer_popup
                    # Map popup rect to global coordinates
                    try:
                        popup_tl = popup.mapToGlobal(popup.rect().topLeft())
                        popup_rect_global = QRect(popup_tl, popup.size())
                    except Exception:
                        popup_rect_global = QRect()

                    # If click is inside popup, do nothing
                    if popup_rect_global.contains(gp):
                        return super().eventFilter(obj, event)

                    # Map drawer rect to global coords and check if click inside drawer
                    try:
                        drawer_tl = self.drawer_panel.mapToGlobal(self.drawer_panel.rect().topLeft())
                        drawer_rect_global = QRect(drawer_tl, self.drawer_panel.size())
                    except Exception:
                        drawer_rect_global = QRect()

                    if drawer_rect_global.contains(gp):
                        # Clicked inside drawer but outside popup -> close popup
                        try:
                            self._hide_drawer_popup()
                        except Exception:
                            pass
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def _toggle_drawer(self) -> None:
        self._drawer_open = not getattr(self, "_drawer_open", False)
        self._apply_drawer_state(animate=True)

    def _apply_drawer_state(self, animate: bool = True) -> None:
        if not hasattr(self, "drawer_panel") or not hasattr(self, "drawer_overlay"):
            return
        self._update_drawer_geometry()
        drawer_w = self.drawer_panel.width()

        # Recompute start/end relative positions
        if self._drawer_open:
            start = QPoint(-drawer_w, 0)
            end = QPoint(0, 0)
        else:
            start = QPoint(0, 0)
            end = QPoint(-drawer_w, 0)

        # Immediate show/hide behavior when animation is disabled
        if not animate:
            try:
                if self._drawer_open:
                    self.drawer_overlay.show()
                    self.drawer_panel.show()
                    self.drawer_overlay.raise_()
                    self.drawer_panel.raise_()
                    self.drawer_panel.move(end)
                else:
                    # Move off-screen and hide immediately
                    self.drawer_panel.move(end)
                    self.drawer_panel.hide()
                    self.drawer_overlay.hide()
            except Exception:
                pass
            # Re-enable toggle button if present
            if hasattr(self, "drawer_toggle_btn"):
                try:
                    self.drawer_toggle_btn.setEnabled(True)
                except Exception:
                    pass
            return

        # Overlay visibility
        if self._drawer_open:
            try:
                self.drawer_overlay.show()
                self.drawer_panel.show()
                self.drawer_overlay.raise_()
                self.drawer_panel.raise_()
            except Exception:
                pass
        else:
            try:
                self.drawer_overlay.raise_()
                self.drawer_panel.raise_()
            except Exception:
                pass

        # Disable the toggle to ensure a single click is effective while animating
        if hasattr(self, "drawer_toggle_btn"):
            try:
                self.drawer_toggle_btn.setEnabled(False)
            except Exception:
                pass

        # Stop previous animations if any and animate to the target using persistent animations
        try:
            # Drawer position animation
            if getattr(self, "_drawer_anim", None):
                try:
                    self._drawer_anim.stop()
                except Exception:
                    pass
            self._drawer_anim = QPropertyAnimation(self.drawer_panel, b"pos", self)
            self._drawer_anim.setDuration(220)
            self._drawer_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._drawer_anim.setStartValue(start)
            self._drawer_anim.setEndValue(end)

            # Overlay fade animation (fade in on open, fade out on close)
            if getattr(self, "_overlay_anim", None):
                try:
                    self._overlay_anim.stop()
                except Exception:
                    pass
            self._overlay_anim = QPropertyAnimation(self.drawer_overlay, b"windowOpacity", self)
            self._overlay_anim.setDuration(220)
            self._overlay_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            if self._drawer_open:
                # show overlay and fade it in
                try:
                    self.drawer_overlay.setWindowOpacity(0.0)
                    self.drawer_overlay.show()
                except Exception:
                    pass
                self._overlay_anim.setStartValue(0.0)
                self._overlay_anim.setEndValue(1.0)
            else:
                # fade overlay out
                try:
                    self._overlay_anim.setStartValue(self.drawer_overlay.windowOpacity())
                except Exception:
                    self._overlay_anim.setStartValue(1.0)
                self._overlay_anim.setEndValue(0.0)

            def _finish():
                # Restore final visibility
                if not self._drawer_open:
                    try:
                        self.drawer_panel.hide()
                        # hide overlay after fade-out completes
                        self.drawer_overlay.hide()
                        # reset overlay opacity for next open
                        self.drawer_overlay.setWindowOpacity(1.0)
                    except Exception:
                        pass
                # Re-enable toggle button
                if hasattr(self, "drawer_toggle_btn"):
                    try:
                        self.drawer_toggle_btn.setEnabled(True)
                    except Exception:
                        pass

            # Wire up animations
            self._overlay_anim.finished.connect(_finish)
            self._drawer_anim.start()
            self._overlay_anim.start()
        except Exception:
            # Fallback to immediate state change
            try:
                if self._drawer_open:
                    self.drawer_panel.move(end)
                    try:
                        self.drawer_overlay.setWindowOpacity(1.0)
                        self.drawer_overlay.show()
                    except Exception:
                        pass
                else:
                    self.drawer_panel.move(end)
                    self.drawer_panel.hide()
                    self.drawer_overlay.hide()
            except Exception:
                pass
            if hasattr(self, "drawer_toggle_btn"):
                try:
                    self.drawer_toggle_btn.setEnabled(True)
                except Exception:
                    pass

    def _update_drawer_geometry(self) -> None:
        if not hasattr(self, "drawer_overlay") or not hasattr(self, "drawer_panel"):
            return
        central = self.centralWidget()
        if central is None:
            return
        rect = central.rect()
        self.drawer_overlay.setGeometry(rect)
        # Adjust drawer width responsively when the central widget resizes
        try:
            # Ensure the drawer doesn't cover the whole screen on narrow windows — reserve 120px for main area
            desired_w = max(180, min(300, rect.width() - 120))
            self.drawer_panel.setFixedWidth(desired_w)
        except Exception:
            pass
        self.drawer_panel.setFixedHeight(rect.height())

    def resizeEvent(self, event) -> None:
        """Reapply responsive layout when the window resizes."""
        try:
            self._apply_responsive_layout()
            self._update_drawer_geometry()
        except Exception:
            pass
        try:
            super().resizeEvent(event)
        except Exception:
            pass

    def _apply_styles(self) -> None:
        theme = "light" if not self.dark_mode else "dark"
        theme_qss = _load_theme(theme)
        # Adaptive overrides depending on theme
        if not self.dark_mode:
            override = "\nQWidget#main-area { background-color: #ffffff; color: #000000; }\nQWidget#central { background-color: #ffffff; color: #000000; }\nQMainWindow { background-color: #ffffff; color: #000000; }\n"
            # Drawer-specific overrides + overlay dim for modal feeling
            override += "\nQFrame#drawer { background-color: transparent; border-left: none; color: #000000; }\nQWidget#drawer-profile { padding: 8px; }\nQWidget#drawer-overlay { background: rgba(0,0,0,0.14); }\n"
            # Ensure basic widgets inherit black text by default in simplified layout
            override += "\nQWidget, QLabel, QTextEdit { color: #000000; }\n"
            # Ensure profile popup rows have consistent sizing across themes
            override += "\nQFrame#profile-popup QPushButton#profile-popup-action { font-size: 15px; padding: 6px 8px; font-weight:700; }\nQWidget#profile-popup-row { padding: 0px; }\nQCheckBox { min-width: 40px; min-height: 24px; }\n"
        else:
            # Dark mode colors
            override = "\nQWidget#main-area { background-color: #000000; color: #ffffff; }\nQWidget#central { background-color: #000000; color: #ffffff; }\nQMainWindow { background-color: #000000; color: #ffffff; }\n"
            override += "\nQFrame#drawer { background-color: transparent; border-left: none; color: #e8e8e8; }\nQWidget#drawer-profile { padding: 8px; }\nQWidget#drawer-overlay { background: rgba(0,0,0,0.36); }\n"
            override += "\nQWidget, QLabel, QTextEdit { color: #e8e8e8; }\n"
            override += "\nQLabel#drawer-user-name { color: #ffffff !important; }\n"
            override += "\nQFrame#profile-popup { background: #111111; color: #ffffff; }\nQFrame#profile-popup QPushButton#profile-popup-action { font-size: 15px; padding: 6px 8px; font-weight:700; color: #ffffff; }\nQFrame#profile-popup QLabel { color: #ffffff; }\nQWidget#profile-popup-row { padding: 0px; }\nQCheckBox { min-width: 40px; min-height: 24px; }\n"

        self.setStyleSheet(theme_qss + override)
        # Re-apply distinct styling for help buttons after loading theme
        self._apply_help_button_style()
        # Top model display: keep text color in sync with theme
        try:
            self._apply_top_model_text_style()
            self._set_top_model_chevron()
        except Exception:
            pass
        # Log icon used for new chat after theme switch
        try:
            if hasattr(self, 'drawer_new_chat_btn'):
                self._refresh_icons()
        except Exception as e:
            print(f"[MainWindow] Error refreshing icons after theme switch: {e}")
        # Chat transcript bubbles should update on theme toggle
        try:
            self._refresh_chat_transcript_styles()
        except Exception:
            pass
        # Drawer profile name should be white in dark mode
        try:
            self._refresh_drawer_name_style()
        except Exception:
            pass
        # Additional adaptive styling to match simplified layout
        try:
            # Make heading large and centered
            if hasattr(self, "center_prompt"):
                try:
                    # Center prompt color follows theme
                    cp_color = "#000000" if not self.dark_mode else "#ffffff"
                    self.center_prompt.setStyleSheet(f"font-size:36px; font-weight:800; color:{cp_color};")
                except Exception:
                    pass

            # Composer / script container: rounded, light background, subtle drop shadow
            if hasattr(self, "script_container") and isinstance(self.script_container, QWidget):
                try:
                    sc_bg = "#ffffff" if not self.dark_mode else "#0f1724"
                    sc_border = "#e5e7eb" if not self.dark_mode else "#374151"
                    self.script_container.setStyleSheet(
                        f"QFrame#composer-pill, QWidget#script-input-container {{ background: {sc_bg}; border: 1px solid {sc_border}; border-radius: 20px; }}")
                except Exception:
                    pass
                try:
                    shadow = QGraphicsDropShadowEffect(self.script_container)
                    shadow.setBlurRadius(10)
                    shadow.setOffset(0, 4)
                    shadow.setColor(QColor(0, 0, 0, 18))
                    self.script_container.setGraphicsEffect(shadow)
                except Exception:
                    pass

            # Editor style — monospace and neutral color
            if hasattr(self, "script_edit") and isinstance(self.script_edit, QTextEdit):
                try:
                    # Prefer UI app font (e.g., Inter) but keep monospace fallback for code blocks
                    cp_color = "#000000" if not self.dark_mode else "#ffffff"
                    self.script_edit.setStyleSheet(f"QTextEdit#composer-editor, QTextEdit#script-editor {{ background: transparent; border: none; font-family: 'Inter','Menlo','Monaco', monospace; font-size: 14px; color: {cp_color}; }}")
                except Exception:
                    pass

            # HWP file text (no longer styled as pill)
            if hasattr(self, "hwp_filename_label"):
                try:
                    text_color = "#000000" if not self.dark_mode else "#ffffff"
                    self.hwp_filename_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {text_color}; background: transparent; padding: 4px 8px;")
                except Exception:
                    pass

            # Send button: circular, larger
            if hasattr(self, "send_btn") and isinstance(self.send_btn, QPushButton):
                try:
                    self._apply_send_button_style()
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_responsive_layout(self) -> None:
        """Adjust UI visibility and sizes for narrower (mobile) windows."""
        try:
            w = self.width()
            # Mobile threshold
            mobile = w <= 480

            # Hero font sizing
            if hasattr(self, "center_prompt"):
                try:
                    if mobile:
                        cp_color = "#000000" if not self.dark_mode else "#ffffff"
                        self.center_prompt.setStyleSheet(f"font-size:32px; font-weight:800; color:{cp_color}; margin-top: 6px;")
                    else:
                        cp_color = "#000000" if not self.dark_mode else "#ffffff"
                        self.center_prompt.setStyleSheet(f"font-size:36px; font-weight:800; color:{cp_color};")
                except Exception:
                    pass

            # Composer controls: show upload, mic, hwp pill on mobile, hide on desktop simplified layout
            try:
                if mobile:
                    if hasattr(self, "mic_btn"):
                        self.mic_btn.show()
                    if hasattr(self, "hwp_filename_label"):
                        self.hwp_filename_label.show()
                    if hasattr(self, "hwp_add_btn"):
                        self.hwp_add_btn.show()
                    # Keep the model label hidden on mobile so the document pill can center
                    if hasattr(self, "model_label"):
                        self.model_label.hide()
                    # Keep a compact model display visible on narrow windows and preserve the arrow icon
                    if hasattr(self, "top_model_display"):
                        try:
                            # Prefer the display label, then canonical id so compacting doesn't remove important qualifiers
                            full = (
                                getattr(self, "_current_model_display", None)
                                or getattr(self, "_current_model", None)
                                or (self.model_label.text() if hasattr(self, "model_label") else (self.top_model_display.text() if hasattr(self.top_model_display, 'text') else ""))
                            )
                            compact = full if len(full) <= 12 else full[:12]
                            self.top_model_display.setText(compact)
                            try:
                                self._set_top_model_chevron()
                            except Exception:
                                pass
                            self.top_model_display.show()
                        except Exception:
                            try:
                                self.top_model_display.show()
                            except Exception:
                                pass
                    if hasattr(self, "top_model_btn"):
                        self.top_model_btn.hide()
                    # Neutral send button on mobile (light gray)
                    if hasattr(self, "send_btn"):
                        try:
                            self._apply_send_button_style()
                        except Exception:
                            pass
                else:

                    if hasattr(self, "mic_btn"):
                        self.mic_btn.hide()
                    if hasattr(self, "hwp_filename_label"):
                        self.hwp_filename_label.hide()
                    if hasattr(self, "model_label"):
                        self.model_label.hide()
                    if hasattr(self, "top_model_display"):
                        try:
                            # restore the full model label on wider screens
                            if hasattr(self, "model_label"):
                                self.top_model_display.setText(self.model_label.text())
                            self.top_model_display.show()
                        except Exception:
                            try:
                                self.top_model_display.show()
                            except Exception:
                                pass
                    if hasattr(self, "top_model_btn"):
                        self.top_model_btn.hide()
            except Exception:
                pass

            # Composer styling tweaks
            try:
                if hasattr(self, "script_container"):
                    if mobile:
                        self.script_container.setStyleSheet("QWidget#script-input-container { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 24px; padding: 14px; }")
                    else:
                        self.script_container.setStyleSheet("QWidget#script-input-container { background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 20px; padding: 12px; }")
            except Exception:
                pass

            # Editor height tweaks (keep composer compact)
            try:
                if hasattr(self, "script_edit") and isinstance(self.script_edit, QTextEdit):
                    if mobile:
                        self.script_edit.setMaximumHeight(190)
                        self.script_edit.setMinimumHeight(120)
                    else:
                        self.script_edit.setMaximumHeight(220)
                        self.script_edit.setMinimumHeight(140)
            except Exception:
                pass

            # Ensure preview box is compact on mobile
            if hasattr(self, "image_preview_container"):
                try:
                    if mobile:
                        self.image_preview_container.setFixedHeight(140)
                    else:
                        self.image_preview_container.setFixedHeight(0)
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_hwp_pill_style(self) -> None:
        """Apply the theme-aware style for the '한글 문서' pill (HWP filename display)."""
        lbl = getattr(self, "hwp_filename_label", None)
        if lbl is None:
            return

        # Match the target compact pill (left screenshot): subtle fill, thin border, small padding, bold text.
        if getattr(self, "dark_mode", False):
            bg = "#111111"
            border = "#374151"
            text = "#ffffff"
        else:
            bg = "#f4f4f5"
            border = "#e5e7eb"
            text = "#0f1724"

        try:
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except Exception:
            pass

        lbl.setStyleSheet(
            f"""
            QLabel#hwp-filename {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 14px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 700;
                color: {text};
            }}
            """
        )

    def _apply_help_button_style(self) -> None:
        """Apply a distinct, elegant style for the help buttons (and the HWP label button)."""
        if (
            not hasattr(self, "howto_button")
            and not hasattr(self, "hwp_filename_label")
            and not hasattr(self, "send_btn")
        ):
            return
        # Theme-aware style:
        # - Dark: solid #303030
        # - Light: match composer background/border, black text/icons
        if self.dark_mode:
            bg = "#303030"
            border = "#303030"
            hover_bg = "#383838"
            hover_border = "#404040"
            press_bg = "#2a2a2a"
            press_border = "#4a4a4a"
            text_color = "#e8e8e8"
        else:
            bg = "#f4f4f5"          # same as light composer background
            border = "#e5e7eb"      # same as light composer border
            hover_bg = "#ececf1"
            hover_border = "#d1d5db"
            press_bg = "#e5e7eb"
            press_border = "#cbd5e1"
            text_color = "#000000"  # black

        help_style = f"""
        QPushButton {{
            background-color: {bg};
            color: {text_color};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 8px 14px;
            font-weight: 700;
            font-size: 13px;
            text-align: center;
            qproperty-iconSize: 18px 18px;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
            border: 1px solid {hover_border};
        }}
        QPushButton:pressed {{
            background-color: {press_bg};
            border: 1px solid {press_border};
        }}
        """

        for btn in (
            getattr(self, "howto_button", None),
            getattr(self, "latex_button", None),
            getattr(self, "ai_generate_button", None),
        ):
            if btn:
                btn.setStyleSheet(help_style)

        # HWP pill (QLabel): keep a consistent "document pill" style (not hover/press states).
        try:
            self._apply_hwp_pill_style()
        except Exception:
            pass

        # Send button: match HWP hover color as the base background.
        if getattr(self, "send_btn", None):
            try:
                self._apply_send_button_style()
            except Exception:
                pass

    def _set_app_logo(self) -> None:
        """Set main title logo based on theme."""
        if hasattr(self, "logo_label"):
            # Use the formulite_logo files
            assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"

    def _set_send_svg_icon(self):
        """Set the send button icon to send-light.svg / send-dark.svg based on theme."""
        if getattr(self, 'send_btn', None) is None:
            return
        assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
        svg_file = assets_dir / ("send-dark.svg" if getattr(self, 'dark_mode', False) else "send-light.svg")
        
        if svg_file.exists():
            icon = QIcon(str(svg_file))
            self.send_btn.setIcon(icon)
            self.send_btn.setIconSize(QSize(24, 24))
        else:
            self.send_btn.setIcon(QIcon())

    def _set_material_symbol(self, widget, ligature: str, fallback: str, px: int = 22) -> None:
        """Set a Material Symbols Outlined ligature; fall back to plain text (delegates to design)."""
        try:
            design.set_material_symbol(widget, ligature, fallback, px, getattr(self, "_material_symbols_available", False), getattr(self, "dark_mode", False))
        except Exception:
            # Do not crash UI when setting icons
            widget.setText(fallback)

    def _set_material_symbol_icon(self, widget, ligature: str, px: int = 20) -> None:
        """Render a Material Symbols Outlined ligature into a QIcon (delegates to design)."""
        try:
            design.set_material_symbol_icon(widget, ligature, px, getattr(self, "_material_symbols_available", False), getattr(self, "dark_mode", False))
        except Exception:
            widget.setIcon(QIcon())

    def _render_material_symbol_icon(self, ligature: str, px: int, color: QColor) -> QIcon:
        """Return a QIcon rendered via design helper."""
        return design.render_material_symbol_icon(ligature, px, color)

    def _render_delete_icon(self, px: int = 16, color: QColor | None = None) -> QIcon:
        """Render a small, crisp trash-outline QIcon using QPainter.

        This avoids relying on external fonts or assets and ensures consistent
        visuals across platforms.
        """
        try:
            if color is None:
                color = QColor("#9ca3af") if not getattr(self, "dark_mode", False) else QColor("#e8e8e8")

            pm = QPixmap(px, px)
            pm.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pm)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            pen = QPen(color)
            pen.setWidthF(max(1.0, px * 0.09))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # Draw trash lid (a short rounded rectangle / line)
            lid_y = px * 0.28
            left = px * 0.22
            right = px * 0.78
            painter.drawLine(int(left), int(lid_y), int(right), int(lid_y))

            # Draw small handle center above lid
            handle_w = px * 0.20
            handle_left = (px - handle_w) / 2
            painter.drawRect(int(handle_left), int(lid_y - (px * 0.06)), int(handle_w), int(px * 0.06))

            # Draw body (rounded rect)
            body_x = px * 0.20
            body_y = px * 0.40
            body_w = px * 0.60
            body_h = px * 0.48
            painter.drawRoundedRect(int(body_x), int(body_y), int(body_w), int(body_h), 2, 2)

            # Draw inner vertical guide lines to suggest slats
            slat_x1 = int(px * 0.36)
            slat_x2 = int(px * 0.5)
            slat_x3 = int(px * 0.64)
            top = int(body_y + body_h * 0.2)
            bottom = int(body_y + body_h * 0.78)
            painter.drawLine(slat_x1, top, slat_x1, bottom)
            painter.drawLine(slat_x2, top, slat_x2, bottom)
            painter.drawLine(slat_x3, top, slat_x3, bottom)

            painter.end()
            return QIcon(pm)
        except Exception:
            return QIcon()

    def _set_top_model_chevron(self) -> None:
        """Render and set a crisp chevron-down icon for the top model display."""
        icon_lbl = getattr(self, "_top_model_icon", None)
        if icon_lbl is None:
            return

        w = max(8, int(getattr(icon_lbl, "width", lambda: 14)() or 14))
        h = max(8, int(getattr(icon_lbl, "height", lambda: 14)() or 14))

        # Slightly softer than pure black in light mode; bright in dark mode.
        if getattr(self, "dark_mode", False):
            color = QColor(255, 255, 255, 220)
        else:
            color = QColor(17, 17, 17, 200)

        try:
            dpr = float(icon_lbl.devicePixelRatioF())
        except Exception:
            dpr = 1.0

        pm = QPixmap(int(w * dpr), int(h * dpr))
        pm.setDevicePixelRatio(dpr)
        pm.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(color)
        pen.setWidthF(max(1.6, h * 0.12))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw a "v" chevron (down caret) centered in the box.
        left_x = w * 0.20
        right_x = w * 0.80
        top_y = h * 0.38
        mid_x = w * 0.50
        mid_y = h * 0.70
        path = QPainterPath()
        path.moveTo(left_x, top_y)
        path.lineTo(mid_x, mid_y)
        path.lineTo(right_x, top_y)
        painter.drawPath(path)
        painter.end()

        try:
            icon_lbl.setText("")
        except Exception:
            pass
        icon_lbl.setPixmap(pm)

    def _apply_top_model_text_style(self) -> None:
        """Apply theme-aware styling for the top model display text."""
        lbl = getattr(self, "_top_model_text", None)
        if lbl is None:
            return
        cp_color = "#ffffff" if getattr(self, "dark_mode", False) else "#000000"
        # Match the reference header: slightly thinner weight and tight spacing to the chevron.
        lbl.setStyleSheet(f"font-size:18px; font-weight:700; color: {cp_color}; padding-right: 3px;")



    def _set_drawer_item_icon(self, button: QPushButton, ligature: str, fallback: str = "", px: int = 20) -> None:
        """Set an icon for a drawer item. Uses Material Symbols if available, else prefixes fallback text."""
        color = QColor("#000000") if not getattr(self, "dark_mode", False) else QColor("#e8e8e8")
        if getattr(self, "_material_symbols_available", False):
            try:
                button.setIcon(self._render_material_symbol_icon(ligature, px, color))
                button.setIconSize(QSize(px, px))
                return
            except Exception:
                pass
        # Fallback: prefix text
        if fallback and not button.text().startswith(fallback):
            button.setText(f"{fallback} {button.text()}".strip())

    def _refresh_icons(self) -> None:
        """Reapply themed icons after a theme change."""
        # (Removed) upload/add-file icon application — add-file button was removed per UX request.
        # Refresh HWP + button with theme-aware asset when available
        try:
            assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
            candidate = assets_dir / ("plus-dark.png" if getattr(self, 'dark_mode', False) else "plus.png")
            if not candidate.exists():
                alt = assets_dir / ("plus.png" if getattr(self, 'dark_mode', False) else "plus-dark.png")
                if alt.exists():
                    candidate = alt
                else:
                    candidate = None
            if getattr(self, 'hwp_add_btn', None) and candidate is not None:
                self.hwp_add_btn.setIcon(QIcon(str(candidate)))
                self.hwp_add_btn.setIconSize(QSize(24, 24))
            elif getattr(self, 'hwp_add_btn', None):
                self._apply_button_icon(self.hwp_add_btn, "plus", "+", QSize(24, 24))
        except Exception:
            if getattr(self, 'hwp_add_btn', None):
                self._apply_button_icon(self.hwp_add_btn, "plus", "+", QSize(24, 24))
        self._apply_button_icon(self.ai_selector_btn, "ai", "[AI]", QSize(28, 28))
        self._apply_button_icon(self.mic_btn, "mic", "[MIC]", QSize(28, 28))
        if hasattr(self, "howto_button"):
            self.howto_button.setText("도움말")
            self._apply_button_icon(self.howto_button, "help", "[?]", QSize(20, 20), preserve_text=True)
        if hasattr(self, "ai_generate_button"):
            self.ai_generate_button.setText("AI 생성")
            self._apply_button_icon(self.ai_generate_button, "generate", "[+]", QSize(20, 20), preserve_text=True)
        # AI Optimize button removed from main UI; keep handler methods but no button present.
        # Ensure help buttons keep their distinct inline styling after icon refresh
        self._apply_help_button_style()
        if hasattr(self, "save_btn"):
            self._apply_button_icon(self.save_btn, "save", "[S]", QSize(32, 32))
        if hasattr(self, "load_btn"):
            self._apply_button_icon(self.load_btn, "load", "[L]", QSize(32, 32))
        if hasattr(self, "backup_icon_btn"):
            self._apply_button_icon_themed(self.backup_icon_btn, "backup_icon", "[B]", QSize(32, 32))
        # Ensure the top model display's chevron icon matches the current theme
        try:
            self._apply_top_model_text_style()
            self._set_top_model_chevron()
        except Exception:
            pass
        try:
            self._refresh_chat_transcript_styles()
        except Exception:
            pass
        # Drawer primary actions: swap between write/search light and dark variants on theme change.
        try:
            assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
            # Update new chat button icon (theme-aware)
            if getattr(self, "drawer_new_chat_btn", None):
                is_dark = getattr(self, 'dark_mode', False)
                icon_name = "new-dark.svg" if is_dark else "new-light.svg"
                new_icon = assets_dir / icon_name
                if new_icon.exists():
                    self.drawer_new_chat_btn.setIcon(QIcon(str(new_icon)))
                    self.drawer_new_chat_btn.setIconSize(QSize(22, 22))
                else:
                    # fallback: try the other icon
                    alt_icon = assets_dir / ("new-light.svg" if is_dark else "new-dark.svg")
                    if alt_icon.exists():
                        self.drawer_new_chat_btn.setIcon(QIcon(str(alt_icon)))
                        self.drawer_new_chat_btn.setIconSize(QSize(22, 22))
                    else:
                        self.drawer_new_chat_btn.setIcon(QIcon())
            # Update search button icon (legacy logic, can be updated similarly if needed)
            if getattr(self, "drawer_search_btn", None):
                search_icon = assets_dir / ("search-dark.svg" if getattr(self, "dark_mode", False) else "search-light.svg")
                if not search_icon.exists():
                    alt = assets_dir / ("search-light.svg" if getattr(self, "dark_mode", False) else "search-dark.svg")
                    search_icon = alt if alt.exists() else search_icon
                if search_icon.exists():
                    self.drawer_search_btn.setIcon(QIcon(str(search_icon)))
                    self.drawer_search_btn.setIconSize(QSize(22, 22))
                else:
                    self.drawer_search_btn.setIcon(QIcon())
        except Exception:
            pass
        if hasattr(self, "theme_btn"):
            self._set_theme_glyph(self.dark_mode)
        if hasattr(self, "settings_btn"):
            self._set_settings_glyph()
        # Update drawer hamburger icon (use processing helper so background is stripped & sizing is consistent)
        try:
            if getattr(self, 'drawer_toggle_btn', None):
                self._set_drawer_toggle_icon(size_px=36)
        except Exception:
            pass
        # Refresh the send button icon using themed asset when applicable
        try:
            if getattr(self, 'send_btn', None):
                self._set_send_svg_icon()
        except Exception:
            pass
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
        # Refresh chat list so per-row icons (edit/delete) are rebuilt with current theme
        try:
            self._render_chat_list()
        except Exception:
            pass
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
        """Handle run button click - now triggers AI generation and auto-execution."""
        if self._worker and self._worker.isRunning():
            self._show_info_dialog("진행 중", "이미 작업을 실행 중입니다.")
            try:
                assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
                is_dark = self.dark_mode if hasattr(self, 'dark_mode') else False
                icon_name = "new-dark.svg" if is_dark else "new-light.svg"
                new_icon = assets_dir / icon_name
                if hasattr(self, 'drawer_new_chat_btn'):
                    if new_icon.exists():
                        self.drawer_new_chat_btn.setIcon(QIcon(str(new_icon)))
                        self.drawer_new_chat_btn.setIconSize(QSize(22, 22))
                    else:
                        alt_icon = assets_dir / ("new-light.svg" if is_dark else "new-dark.svg")
                        if alt_icon.exists():
                            self.drawer_new_chat_btn.setIcon(QIcon(str(alt_icon)))
                            self.drawer_new_chat_btn.setIconSize(QSize(22, 22))
                        else:
                            self.drawer_new_chat_btn.setIcon(QIcon())
                # Plus icon logic (existing)
                candidate = assets_dir / ("plus-dark.png" if is_dark else "plus.png")
                if not candidate.exists():
                    alt = assets_dir / ("plus.png" if is_dark else "plus-dark.png")
                    if alt.exists():
                        candidate = alt
                    else:
                        candidate = None
                if getattr(self, 'hwp_add_btn', None) and candidate is not None:
                    self.hwp_add_btn.setIcon(QIcon(str(candidate)))
                    self.hwp_add_btn.setIconSize(QSize(24, 24))
                elif getattr(self, 'hwp_add_btn', None):
                    self._apply_button_icon(self.hwp_add_btn, "plus", "+", QSize(24, 24))
            except Exception:
                pass
        # Fetch user input from the input field
        user_input = self.script_edit.toPlainText().strip()
        # If no chat is selected, create a new chat, otherwise append to current chat
        if not self._current_chat_id or not any(chat.get("id") == self._current_chat_id for chat in self._chats):
            new_id = str(uuid.uuid4())
            now = time.time()
            new_chat = {
                "id": new_id,
                "title": "새 채팅",
                "log": "",
                "script": DEFAULT_SCRIPT.strip(),
                "messages": [],
                "created_at": now,
                "updated_at": now,
            }
            self._snapshot_current_chat()
            self._chats.insert(0, new_chat)
            self._current_chat_id = new_id
            self._activate_chat(new_id)
        # Clear input field
        self.script_edit.setPlainText("")
        # Generate code with AI and auto-execute (it will add the user message internally)
        self._generate_and_execute_with_ai(user_input)

    def _handle_error(self, message: str) -> None:
        self._append_log(f"❌ {message}")
        self.send_btn.setEnabled(True)

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
        """Handle combined file/image upload button click - supports multiple selections."""
        file_paths, _ = QFileDialog.getOpenFileNames(  # Changed to getOpenFileNames for multiple selection
            self,
            "파일 또는 이미지 선택 (여러 개 선택 가능)",
            "",
            "이미지 파일 (*.png *.jpg *.jpeg *.gif *.bmp);;PDF 파일 (*.pdf);;모든 파일 (*)"
        )
        if file_paths:
            for file_path in file_paths:
                # Store the uploaded file path for AI to use
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
                    self._add_image_preview(file_path)
                    self._append_log(f"📎 파일 추가됨: {Path(file_path).name}")
                    print(f"[MainWindow] File uploaded and added to selected_files: {file_path}")

            
            # Update HWP filename if it's a document
            filename = Path(file_path).name
            if filename.lower().endswith(('.hwp', '.hwpx')):
                self.hwp_filename_label.setText(filename)

    def _add_image_preview(self, file_path: str) -> None:
        """Add image preview thumbnail with remove button at top-right corner."""
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Create container for preview
                preview_container = QFrame()
                preview_container.setObjectName("image-preview-item")
                preview_container.setFixedSize(130, 155)  # Fixed size container
                
                # Use absolute positioning for overlaying close button
                preview_container.setStyleSheet("""
                    QFrame#image-preview-item {
                        background-color: transparent;
                    }
                """)
                
                # Create image label
                preview_label = QLabel(preview_container)
                scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                preview_label.setPixmap(scaled)
                preview_label.setFixedSize(120, 120)
                preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                preview_label.setStyleSheet("""
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    padding: 2px;
                    background-color: white;
                """)
                preview_label.move(5, 0)
                
                # Create filename label
                filename = Path(file_path).name
                if len(filename) > 15:
                    filename = filename[:12] + "..."
                filename_label = QLabel(filename, preview_container)
                filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                filename_label.setStyleSheet("""
                    font-size: 10px;
                    color: #666;
                    background-color: transparent;
                """)
                filename_label.setFixedWidth(120)
                filename_label.move(5, 125)
                
                # Create remove button at top-right corner (overlaid)
                remove_btn = QPushButton("✕", preview_container)
                remove_btn.setFixedSize(20, 20)
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(0, 0, 0, 0.6);
                        color: white;
                        border: none;
                        border-radius: 10px;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: rgba(0, 0, 0, 0.8);
                    }
                """)
                remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                # Use default argument to capture file_path correctly (avoid late binding issue)
                remove_btn.clicked.connect(lambda checked=False, fp=file_path, widget=preview_container: self._remove_image_preview(fp, widget))
                # Position at top-right corner of the image (moved higher)
                remove_btn.move(107, -1)
                remove_btn.raise_()  # Bring to front
                
                # Store file path as property for later removal
                preview_container.setProperty("file_path", file_path)
                
                self.image_preview_layout.addWidget(preview_container, alignment=Qt.AlignmentFlag.AlignLeft)
                self.image_preview_container.show()
        except Exception as e:
            print(f"Error adding image preview: {e}")
    
    def _remove_image_preview(self, file_path: str, preview_widget: QWidget) -> None:
        """Remove an image preview and its associated file from selected_files."""
        try:
            # Remove from selected files list
            if file_path in self.selected_files:
                self.selected_files.remove(file_path)
                print(f"[MainWindow] File removed: {file_path}")
            
            # Remove the preview widget
            self.image_preview_layout.removeWidget(preview_widget)
            preview_widget.deleteLater()
            
            # Hide container if no more previews
            if len(self.selected_files) == 0:
                self.image_preview_container.hide()
        except Exception as e:
            print(f"Error removing image preview: {e}")

    def _set_model(self, model_name: str) -> None:
        """Set the active model (canonical + display) and update UI labels."""
        try:
            raw = (model_name or "").strip()
            normalized = raw.lower()

            # Map friendly/short names to canonical cheapest vision-capable models
            canonical_map = {
                "gpt": "gpt-5-nano",
                "gpt-4o-mini": "gpt-5-nano",
                "gpt-4o-mini-2024-08-06": "gpt-5-nano",
                "gpt-5-nano": "gpt-5-nano",
                "gemini": "gemini-2.0-flash",
                "gemini-1.5-flash": "gemini-2.0-flash",
                "gemini-2.0-flash": "gemini-2.0-flash",
                "claude": "claude-3-haiku-20240307",
                "claude-3-haiku": "claude-3-haiku-20240307",
                "claude-3-haiku-20240307": "claude-3-haiku-20240307",
            }
            canonical = canonical_map.get(normalized, raw if raw else "gpt-5-nano")

            # User-facing display text (keep short while hinting variant)
            display_map = {
                "gpt-5-nano": "gpt-5-nano",
                "gemini-2.0-flash": "gemini-2.0-flash",
                "claude-3-haiku-20240307": "claude-3-haiku",
            }
            display = display_map.get(canonical, canonical)

            self._current_model = canonical
            self._current_model_display = display
            # Keep current_model in sync for AIWorker
            self.current_model = canonical

            if hasattr(self, "model_label"):
                try:
                    self.model_label.setText(display)
                except Exception:
                    pass
            if hasattr(self, "top_model_display"):
                try:
                    # Update text (no extra caret) and refresh chevron icon color to match theme
                    self.top_model_display.setText(display)
                    try:
                        self._set_top_model_chevron()
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass
        # Persist selection so it survives restarts (debounced)
        try:
            self._schedule_persist()
        except Exception:
            pass

    def _show_ai_selector(self) -> None:
        """Show AI model selector dropdown — styled popup with richer option rows."""
        try:
            menu = QMenu(self)
            # Theme-aware visual style (match the profile menu in dark mode).
            if getattr(self, "dark_mode", False):
                # Match the app's darkest background tone (used in dark sidebar).
                menu_bg = "#0a0a0a"
                # Keep the outline non-white but visible enough to separate from a black window.
                menu_border = "#111111"
                name_color = "#ffffff"
                desc_color = "#9ca3af"
                hover_bg = "#111111"
            else:
                menu_bg = "#ffffff"
                menu_border = "#e5e7eb"
                name_color = "#0f1724"
                desc_color = "#6b7280"
                hover_bg = "#f3f4f6"

            # Ensure the menu paints a solid background (important with QWidgetAction rows).
            try:
                menu.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            except Exception:
                pass
            menu.setStyleSheet(
                f"""
                QMenu {{
                    background-color: {menu_bg};
                    border: 1px solid {menu_border};
                    border-radius: 8px;
                    padding: 6px;
                }}
                QMenu QWidget {{
                    background-color: transparent;
                }}
                QMenu::item:selected {{
                    background: {hover_bg};
                }}
                """
            )

            # Model families and human-friendly descriptions (cheapest vision-capable tiers)
            models = [
                ("gpt-5-nano", "GPT (gpt-5-nano) — 전반적인 업무 능력이 좋고, 가장 저렴합니다."),
                ("gemini-2.0-flash", "Gemini 2.0 Flash — 이미지 처리 능력이 좋고, 속도가 빠릅니다."),
                ("claude-3-haiku-20240307", "Claude 3 Haiku — 수식 설명에 강하고, 창의적인 업무에 유용합니다."),
            ]

            # Create rich menu rows using QWidgetAction
            for m, desc in models:
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(8, 6, 8, 6)
                row_layout.setSpacing(8)
                v = QVBoxLayout()
                v.setContentsMargins(0, 0, 0, 0)
                name_lbl = QLabel(m)
                name_lbl.setStyleSheet(f"font-weight:600; font-size:13px; color:{name_color};")
                desc_lbl = QLabel(desc)
                # Use a slightly darker gray for better visibility
                improved_gray = "#7a869a" if not getattr(self, "dark_mode", False) else "#b0b8c1"
                desc_lbl.setStyleSheet(f"font-size:12px; color:{improved_gray};")
                v.addWidget(name_lbl)
                v.addWidget(desc_lbl)
                row_layout.addLayout(v)
                # Right-side checkmark for currently selected model
                check_lbl = QLabel("")
                check_lbl.setStyleSheet("font-size:14px; color:#10b981; font-weight:700;")
                if getattr(self, "_current_model", None) == m:
                    check_lbl.setText("✓")
                row_layout.addStretch()
                row_layout.addWidget(check_lbl)

                act = QWidgetAction(menu)
                act.setDefaultWidget(row)

                # clicking the row should set the model
                def make_clicked(name):
                    def _clicked(_=None):
                        try:
                            self._set_model(name)
                        except Exception:
                            pass
                    return _clicked

                # Connect both widget and action triggers
                act.triggered.connect(make_clicked(m))
                row.mouseReleaseEvent = lambda ev, nm=m: (make_clicked(nm)(), menu.close())
                menu.addAction(act)

            # Anchor the menu to the top display if present
            if hasattr(self, "top_model_display"):
                pos = self.top_model_display.mapToGlobal(self.top_model_display.rect().bottomLeft())
            elif hasattr(self, "top_model_btn"):
                pos = self.top_model_btn.mapToGlobal(self.top_model_btn.rect().bottomLeft())
            elif hasattr(self, "model_label"):
                pos = self.model_label.mapToGlobal(self.model_label.rect().bottomLeft())
            else:
                pos = QCursor.pos()
            menu.exec(pos)
        except Exception:
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

    def _show_profile_menu(self) -> None:
        """Show compact profile menu anchored to the drawer profile button.

        Includes: 다운로드(저장), 불러오기(열기), 백업 및 복원, 다크 모드 토글, 설정, 도움말, 로그아웃
        """
        btn = getattr(self, "drawer_profile_btn", None)
        if btn is None or not hasattr(self, "drawer_panel"):
            return

        # Toggle existing popup
        if self._drawer_popup and self._drawer_popup.isVisible():
            self._hide_drawer_popup()
            return

        popup = QFrame(self.drawer_panel)
        popup.setObjectName("profile-popup")
        popup.setFrameShape(QFrame.Shape.StyledPanel)
        # Use theme-aware background and text color so popup matches light/dark mode
        try:
            if self.dark_mode:
                popup.setStyleSheet("background: #111111; color: #ffffff; border: none; border-radius:10px;")
            else:
                popup.setStyleSheet("background: #ffffff; color: #0f1724; border: none; border-radius:10px;")
        except Exception:
            pass
        # subtle shadow for depth
        try:
            shadow = QGraphicsDropShadowEffect(popup)
            # Use a slightly larger blur and zero offset so the shadow appears evenly around all edges
            shadow.setBlurRadius(22)
            shadow.setOffset(0, 0)
            shadow.setColor(QColor(0, 0, 0, 30) if not self.dark_mode else QColor(0, 0, 0, 60))
            popup.setGraphicsEffect(shadow)
        except Exception:
            pass

        layout = QVBoxLayout(popup)
        # Add extra left and top padding in dark mode for better spacing
        if self.dark_mode:
            layout.setContentsMargins(16, 16, 12, 12)
        else:
            layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Top: avatar + name + handle
        top = QWidget()
        t_lyt = QHBoxLayout(top)
        t_lyt.setContentsMargins(0, 0, 0, 0)
        t_lyt.setSpacing(10)
        avatar_src = getattr(self, 'profile_avatar_path', None)
        avatar_lbl = QLabel()
        avatar_lbl.setFixedSize(48, 48)
        avatar_lbl.setObjectName('profile-popup-avatar')
        try:
            assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
            # Only use an explicit user-provided avatar path (do not fall back to bundled placeholders)
            candidate = avatar_src
            if candidate:
                candidate = Path(candidate)
            if candidate and Path(candidate).exists():
                pix = QPixmap(str(candidate)).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                out = QPixmap(48, 48)
                out.fill(Qt.GlobalColor.transparent)
                painter = QPainter(out)
                try:
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    pathp = QPainterPath()
                    pathp.addEllipse(0, 0, 48, 48)
                    painter.setClipPath(pathp)
                    painter.drawPixmap(0, 0, pix)
                finally:
                    painter.end()
                avatar_lbl.setPixmap(out)
                avatar_lbl.setStyleSheet('border-radius: 24px; background: transparent;')
            else:
                # Fallback to initial letter blue circle
                initial = (self.profile_display_name[:1] or 'U').upper()
                avatar_lbl.setText(initial)
                avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                avatar_lbl.setFixedSize(48, 48)
                avatar_lbl.setStyleSheet('background:#2b7bf6; color:#fff; border-radius:24px; font-weight:800; font-size:18px;')
                f = avatar_lbl.font()
                f.setPointSize(18)
                try:
                    f.setWeight(QFont.Weight.DemiBold)
                except Exception:
                    f.setWeight(QFont.Weight.Bold)
                avatar_lbl.setFont(f)
        except Exception:
            initial = (self.profile_display_name[:1] or 'U').upper()
            avatar_lbl.setText(initial)
            avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar_lbl.setFixedSize(48, 48)
            avatar_lbl.setStyleSheet('background:#2b7bf6; color:#fff; border-radius:24px; font-weight:800; font-size:18px;')
            f = avatar_lbl.font()
            f.setPointSize(18)
            try:
                f.setWeight(QFont.Weight.DemiBold)
            except Exception:
                f.setWeight(QFont.Weight.Bold)
            avatar_lbl.setFont(f)

        name_col = QWidget()
        nc_lyt = QVBoxLayout(name_col)
        nc_lyt.setContentsMargins(0, 0, 0, 0)
        nc_lyt.setSpacing(2)
        name_label = QLabel(self.profile_display_name)
        # Explicitly set white color in dark mode
        name_label.setStyleSheet('font-weight:800; font-size:16px; color:%s;' % (
            '#ffffff' if self.dark_mode else '#0f1724'
        ))
        handle_label = QLabel(f"@{(self.profile_handle or 'kinn')}" )
        handle_label.setStyleSheet('color:#9ca3af;')
        nc_lyt.addWidget(name_label)
        nc_lyt.addWidget(handle_label)

        t_lyt.addWidget(avatar_lbl)
        t_lyt.addWidget(name_col)
        layout.addWidget(top)

        # divider
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('color:#e6e7eb;')
        layout.addWidget(sep)

        # Helper to add a menu row with icon
        def add_row(icon_key: str, text: str, handler=None, checkable=False, checked=False):
            row = QWidget()
            row.setObjectName('profile-popup-row')
            # remove any default background so rows are unboxed
            try:
                row.setStyleSheet('background: transparent; border: none;')
            except Exception:
                pass
            r_lyt = QHBoxLayout(row)
            # center items vertically and reduce vertical padding
            r_lyt.setContentsMargins(0, 4, 0, 4)
            r_lyt.setSpacing(12)
            r_lyt.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            ic = QLabel()
            # slightly smaller icon container for tighter layout
            ic.setFixedSize(32, 32)
            # Align icons vertically center for better alignment
            ic.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            try:
                ic.setStyleSheet('background: transparent; margin-left: 8px; margin-top: 2px;')
            except Exception:
                pass

            # Helper to load local assets with fallback to theme icons, and optionally tint
            def _load_icon_for(key: str, sz: int = 18, tint_black: bool = False):
                """Load an icon from public/img or themed paths. If tint_black is True, tint to black in light mode or to light gray in dark mode."""
                try:
                    assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
                    candidate = None
                    # prefer explicit file names and theme-specific variants
                    candidates = [
                        f"{key}.png",
                        f"{key}.svg",
                        f"{key}-icon.png",
                        f"{key}-icon.svg",
                        f"{key}-light.png",
                        f"{key}-light.svg",
                        f"{key}_light.png",
                        f"{key}_light.svg",
                        f"{key}-black.png",
                        f"{key}_black.png",
                    ]
                    for name in candidates:
                        p = assets_dir / name
                        if p.exists():
                            candidate = p
                            break

                    pix = None
                    if candidate:
                        pix = QPixmap(str(candidate))
                    else:
                        # fallback to themed resolver (checks icon-key-light/dark variants)
                        icon_path = design.get_icon_path(key, False, use_theme=True)
                        if icon_path:
                            pix = QPixmap(str(icon_path))
                        else:
                            # last resort: try without theme
                            icon_path = self._get_icon_path_str(key)
                            if icon_path:
                                pix = QPixmap(icon_path)

                    if pix and not pix.isNull():
                        pix = pix.scaled(sz, sz, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        if tint_black:
                            # choose tint color depending on current theme: black for light mode, light gray for dark mode
                            tint_color = QColor(0, 0, 0) if not self.dark_mode else QColor(255, 255, 255)
                            out = QPixmap(pix.size())
                            out.fill(Qt.GlobalColor.transparent)
                            p = QPainter(out)
                            try:
                                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                                p.fillRect(out.rect(), tint_color)
                                p.setCompositionMode(QPainter.CompositionMode.DestinationIn)
                                p.drawPixmap(0, 0, pix)
                            finally:
                                p.end()
                            return out
                        return pix
                except Exception:
                    pass
                return None

            # Use specific keys to decide size and tint; apply special cases
            icon_pix = None
            icon_size = 22
            icon_file = None
            if icon_key == 'upgrade':
                icon_file = ("upgrade-dark.svg" if self.dark_mode else "upgrade-light.svg")
            elif icon_key == 'profile':
                icon_file = ("profile-dark.svg" if self.dark_mode else "profile-light.svg")
            elif icon_key == 'edit':
                icon_file = ("write-dark.svg" if self.dark_mode else "write-light.svg")
            elif icon_key == 'light':
                icon_file = ("light.svg" if self.dark_mode else "dark.svg")
            elif icon_key == 'settings':
                icon_file = ("settings-dark.svg" if self.dark_mode else "settings-light.svg")
            elif icon_key == 'logout':
                icon_file = ("logout-dark.svg" if self.dark_mode else "logout-light.svg")
            if icon_file:
                assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
                svg_file = assets_dir / icon_file
                if svg_file.exists():
                    ic.setPixmap(QIcon(str(svg_file)).pixmap(icon_size, icon_size))
            else:
                icon_pix = _load_icon_for(icon_key, sz=18, tint_black=False)

            try:
                if icon_pix:
                    # In dark mode, tint icons to white for high contrast
                    try:
                        if self.dark_mode:
                            out = QPixmap(icon_pix.size())
                            out.fill(Qt.GlobalColor.transparent)
                            p = QPainter(out)
                            try:
                                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                                p.fillRect(out.rect(), QColor(255,255,255))
                                p.setCompositionMode(QPainter.CompositionMode.DestinationIn)
                                p.drawPixmap(0, 0, icon_pix)
                            finally:
                                p.end()
                            icon_pix = out
                    except Exception:
                        pass
                    ic.setPixmap(icon_pix)
                else:
                    # Explicit fallback for the theme icon: try <key>-icon.png (e.g., light-icon.png)
                    try:
                        assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
                        fallback_name = f"{icon_key}-icon.png"
                        fb = assets_dir / fallback_name
                        if fb.exists():
                            # Use 22px for 'light' and 'logout' icons, else 20px
                            sz = 22 if icon_key in ('light', 'logout') else 20
                            fb_pix = QPixmap(str(fb)).scaled(sz, sz, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            # Tint fallback to white in dark mode as well
                            try:
                                if self.dark_mode:
                                    out = QPixmap(fb_pix.size())
                                    out.fill(Qt.GlobalColor.transparent)
                                    p = QPainter(out)
                                    try:
                                        p.setRenderHint(QPainter.RenderHint.Antialiasing)
                                        p.fillRect(out.rect(), QColor(255,255,255))
                                        p.setCompositionMode(QPainter.CompositionMode.DestinationIn)
                                        p.drawPixmap(0, 0, fb_pix)
                                    finally:
                                        p.end()
                                    fb_pix = out
                            except Exception:
                                pass
                            ic.setPixmap(fb_pix)
                        else:
                            ic.setStyleSheet('background: transparent; margin-left: 8px; margin-top: 2px;')
                    except Exception:
                        ic.setStyleSheet('background: transparent; margin-left: 8px; margin-top: 2px;')
            except Exception:
                pass

            lbl = QPushButton(text)
            lbl.setObjectName('profile-popup-action')
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            lbl.setFlat(True)
            # Ensure the row button does not get global dialog button styling
            try:
                lbl.setStyleSheet("background: transparent; border: none; text-align: left; font-weight:700; font-size:15px; padding: 6px 8px;")
            except Exception:
                pass
            if handler:
                lbl.clicked.connect(lambda checked=False, h=handler: (h(), self._hide_drawer_popup()))
            if checkable:
                # Remove checkbox: clicking the row toggles theme directly
                def _row_click(e, s=self):
                    try:
                        new_state = not s.dark_mode
                        s._toggle_theme(new_state)
                    except Exception:
                        pass
                try:
                    lbl.clicked.connect(lambda checked=False, s=self: s._toggle_theme(not s.dark_mode))
                except Exception:
                    pass
                try:
                    row.mousePressEvent = _row_click  # type: ignore[assignment]
                except Exception:
                    pass
                r_lyt.addWidget(ic)
                r_lyt.addWidget(lbl)
                r_lyt.addStretch()
            else:
                r_lyt.addWidget(ic)
                r_lyt.addWidget(lbl)
            layout.addWidget(row)

        # Upgrade (opens billing/upgrade page)
        def _open_upgrade():
            try:
                QDesktopServices.openUrl(QUrl('https://formulite.vercel.app/pricing'))
            except Exception:
                pass

        def _open_profile():
            try:
                QDesktopServices.openUrl(QUrl('https://formulite.vercel.app/profile'))
            except Exception:
                pass

        add_row('upgrade', '플랜 업그레이드', _open_upgrade)
        add_row('profile', '프로필 관리', _open_profile)
        add_row('edit', '코드 입력', self._show_code_input_dialog)
        # Show action text based on current theme: suggest switching to the opposite mode
        theme_row_label = '라이트 모드' if self.dark_mode else '다크 모드'
        add_row('light', theme_row_label, handler=None, checkable=True, checked=self.dark_mode)
        # Removed save/load chat from profile menu
        add_row('settings', '설정', self._show_settings)

        # spacer + logout (use add_row so logout has an icon)
        layout.addStretch()
        add_row('logout', '로그아웃', lambda: (self._account_logout()), checkable=False)

        # Position the popup under the profile button
        anchor = btn.mapTo(self.drawer_panel, btn.rect().bottomLeft())
        # Set fixed width to ensure consistent size in both light and dark mode
        popup.setFixedWidth(220)
        popup.adjustSize()
        pw = 220
        ph = popup.height()
        x = max(8, anchor.x())
        # Prefer placing popup above the bottom edge so it doesn't overflow
        y = min(self.drawer_panel.height() - ph - 8, anchor.y())
        popup.setGeometry(x, y, pw, ph)
        popup.show()
        popup.raise_()
        self._drawer_popup = popup

    def _show_account_popup(self) -> None:
        """Compatibility shim: show the profile menu (redirects to _show_profile_menu)."""
        self._show_profile_menu()
    
    def _show_code_input_dialog(self) -> None:
        """Show code input dialog for advanced users who want to write Python code directly."""
        dialog = QDialog(self)
        dialog.setWindowTitle("코드 입력")
        dialog.setModal(True)
        dialog.setMinimumSize(400, 400)
        dialog.resize(420, 420)
        
        # Modern dialog styling with rounded corners and shadow effect
        bg_color = "#0f0f0f" if self.dark_mode else "#ffffff"
        border_color = "#2a2a2a" if self.dark_mode else "#e5e7eb"
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 16px;
            }}
        """)
        
        # Create main layout with better spacing
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(24, 28, 24, 20)
        main_layout.setSpacing(16)
        
        # Header section with icon and title
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # Title with better typography
        title_label = QLabel("Python 코드 입력")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {'#ffffff' if self.dark_mode else '#111827'};
                font-size: 20px;
                font-weight: 800;
                font-family: 'Pretendard', sans-serif;
                letter-spacing: -0.5px;
            }}
        """)
        header_layout.addWidget(title_label)
        
        # Description with better styling
        desc_label = QLabel("한글 문서 자동화를 위한 Python 코드를 작성하세요.\n사용 가능한 함수는 LaTeX 가이드를 참고하세요.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {'#9ca3af' if self.dark_mode else '#6b7280'};
                font-size: 14px;
                font-weight: 400;
                font-family: 'Pretendard', sans-serif;
                line-height: 1.5;
            }}
        """)
        header_layout.addWidget(desc_label)
        main_layout.addLayout(header_layout)
        
        # Code editor with modern styling
        code_editor = QTextEdit()
        code_editor.setObjectName("code-input-editor")
        code_editor.setPlaceholderText("# Python 코드를 입력하세요\n# 예: insert_text('Hello World')\n#     insert_paragraph()\n#     insert_equation('x^2 + y^2 = z^2')")
        code_editor.setPlainText("")
        code_editor.setMinimumHeight(240)
        
        # Enhanced code editor styling
        editor_bg = "#1a1a1a" if self.dark_mode else "#f9fafb"
        editor_border = "#3a3a3a" if self.dark_mode else "#e5e7eb"
        editor_text = "#e5e7eb" if self.dark_mode else "#111827"
        editor_placeholder = "#6b7280" if self.dark_mode else "#9ca3af"
        
        code_editor.setStyleSheet(f"""
            QTextEdit#code-input-editor {{
                background-color: {editor_bg};
                border: 2px solid {editor_border};
                border-radius: 12px;
                padding: 12px;
                color: {editor_text};
                font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.6;
                selection-background-color: {'#3b82f6' if self.dark_mode else '#3b82f6'};
                selection-color: #ffffff;
            }}
            QTextEdit#code-input-editor:focus {{
                border: 2px solid {'#3b82f6' if self.dark_mode else '#2563eb'};
                background-color: {editor_bg};
            }}
            QTextEdit#code-input-editor::placeholder {{
                color: {editor_placeholder};
            }}
        """)
        
        main_layout.addWidget(code_editor, 1)  # Stretch factor
        
        # Button row with improved styling
        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.setContentsMargins(0, 8, 0, 0)
        
        # LaTeX helper button with modern design
        latex_btn = QPushButton("LaTeX 가이드")
        latex_btn.setObjectName("latex-helper-button")
        latex_btn.setMinimumWidth(100)
        latex_btn.setMinimumHeight(44)
        latex_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        latex_bg = "#1f1f1f" if self.dark_mode else "#f3f4f6"
        latex_border = "#3a3a3a" if self.dark_mode else "#d1d5db"
        latex_text = "#e5e7eb" if self.dark_mode else "#374151"
        latex_hover = "#2a2a2a" if self.dark_mode else "#e5e7eb"
        
        latex_btn.setStyleSheet(f"""
            QPushButton#latex-helper-button {{
                background-color: {latex_bg};
                border: 1.5px solid {latex_border};
                color: {latex_text};
                font-weight: 600;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 10px;
                font-family: 'Pretendard', sans-serif;
            }}
            QPushButton#latex-helper-button:hover {{
                background-color: {latex_hover};
                border-color: {'#4a4a4a' if self.dark_mode else '#9ca3af'};
            }}
            QPushButton#latex-helper-button:pressed {{
                background-color: {'#2a2a2a' if self.dark_mode else '#e5e7eb'};
            }}
        """)
        latex_btn.clicked.connect(self._show_latex_helper)
        button_row.addWidget(latex_btn)
        
        button_row.addStretch()
        
        # Cancel button with refined styling
        cancel_btn = QPushButton("취소")
        cancel_btn.setObjectName("secondary-button")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        cancel_text = "#9ca3af" if self.dark_mode else "#6b7280"
        cancel_hover = "#2a2a2a" if self.dark_mode else "#f3f4f6"
        
        cancel_btn.setStyleSheet(f"""
            QPushButton#secondary-button {{
                background-color: transparent;
                border: none;
                color: {cancel_text};
                font-weight: 600;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 10px;
                font-family: 'Pretendard', sans-serif;
            }}
            QPushButton#secondary-button:hover {{
                background-color: {cancel_hover};
            }}
            QPushButton#secondary-button:pressed {{
                background-color: {'#1f1f1f' if self.dark_mode else '#e5e7eb'};
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_row.addWidget(cancel_btn)
        
        # Run button with modern primary action styling
        run_btn = QPushButton("▶ 실행")
        run_btn.setObjectName("primary-action")
        run_btn.setMinimumWidth(100)
        run_btn.setMinimumHeight(44)
        run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        run_btn.setStyleSheet("""
            QPushButton#primary-action {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-weight: 700;
                font-size: 14px;
                padding: 10px 24px;
                font-family: 'Pretendard', sans-serif;
            }
            QPushButton#primary-action:hover {
                background-color: #2563eb;
            }
            QPushButton#primary-action:pressed {
                background-color: #1d4ed8;
            }
        """)
        
        def on_run():
            code = code_editor.toPlainText().strip()
            if not code:
                self._show_info_dialog("알림", "코드를 입력해주세요.")
                return
            
            # Execute the code
            dialog.accept()
            self._execute_code_directly(code)
        
        run_btn.clicked.connect(on_run)
        button_row.addWidget(run_btn)
        
        main_layout.addLayout(button_row)
        
        dialog.exec()
    
    def _execute_code_directly(self, code: str) -> None:
        """Execute Python code directly without AI generation."""
        if self._worker and self._worker.isRunning():
            self._show_info_dialog("진행 중", "이미 작업을 실행 중입니다.")
            return
        
        # Show execution message in chat
        try:
            self._chat_add_message("user", "코드 실행")
            self._chat_add_message("assistant", "코드를 실행하고 있습니다...")
        except Exception:
            pass
        
        # Execute the code
        self._worker = ScriptWorker(code, self)
        self._worker.log_signal.connect(lambda msg: None)  # Suppress log messages
        self._worker.error_signal.connect(lambda err: self._chat_add_message("assistant", f"❌ 오류: {err}"))
        self._worker.finished_signal.connect(lambda: self._on_code_execution_finished())
        self.send_btn.setEnabled(False)
        if hasattr(self, "ai_generate_button"):
            self.ai_generate_button.setEnabled(False)
        if hasattr(self, "ai_optimize_button"):
            self.ai_optimize_button.setEnabled(False)
        self._worker.start()
    
    def _on_code_execution_finished(self) -> None:
        """Handle completion of code execution from code input dialog."""
        try:
            self._chat_add_message("assistant", "✅ 코드 실행이 완료되었습니다!")
        except Exception:
            pass
        self.send_btn.setEnabled(True)
        if hasattr(self, "ai_generate_button"):
            self.ai_generate_button.setEnabled(True)
        if hasattr(self, "ai_optimize_button"):
            self.ai_optimize_button.setEnabled(True)
    
    def _show_error_dialog(self, message: str) -> None:
        """Show elegant error dialog."""
        error_content = f"""
<div class="error-container">
    <span class="error-title">실행 오류가 발생했습니다</span>
    
    <div class="error-message">
        {message}
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
        self.send_btn.setEnabled(True)
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
        # If the profile popup is visible, refresh it so styles update (avoid leaving stale sizes)
        try:
            if getattr(self, "_drawer_popup", None) and self._drawer_popup.isVisible():
                # Hide then schedule a re-show so the popup is rebuilt with the new styles
                self._hide_drawer_popup()
                QTimer.singleShot(80, self._show_profile_menu)
        except Exception:
            pass

    def _set_theme_glyph(self, active: bool) -> None:
        """Set theme toggle icon.

        Prefer explicit themed assets when available:
        - In light mode (active=False): show `moon-light.svg`
        - In dark mode (active=True): show `light-dark.svg`
        Falls back to icon-key resolver when explicit assets are missing.
        """
        self.theme_btn.setText("[o]")
        try:
            assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
            if active:
                # Dark mode active -> show the 'light-dark' icon to indicate switching to light
                explicit = assets_dir / "light-dark.svg"
                if explicit.exists():
                    self.theme_btn.setIcon(QIcon(str(explicit)))
                    self.theme_btn.setIconSize(QSize(32, 32))
                    return
            else:
                # Light mode active -> show the 'moon-light' icon to indicate switching to dark
                explicit = assets_dir / "moon-light.svg"
                if explicit.exists():
                    self.theme_btn.setIcon(QIcon(str(explicit)))
                    self.theme_btn.setIconSize(QSize(32, 32))
                    return
        except Exception:
            pass
        # Fallback to existing themed resolver
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
  .func-item code {{ background: #f3f4f6; color: #000000; padding: 6px 8px; border-radius: 8px; display: inline-block; }}

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
        <img src='{save_icon}' width='18' height='18' style='vertical-align:middle; padding-right:12px;' />스크립트 저장
        <small style="padding-left: 5px; margin-left: 5px;">현재 에디터의 코드를 Python 파일로 저장</small>
    </div>
    
    <div class="func-item">
        <img src='{load_icon}' width='18' height='18' style='vertical-align:middle; padding-right:12px;' />스크립트 불러오기
        <small style="padding-left: 5px; margin-left: 5px;" >저장된 코드 파일을 에디터에 불러오기</small>
    </div>
    
    <div class="func-item">
        <img src='{light_icon}' width='18' height='18' style='vertical-align:middle; padding-right:12px;' />다크 모드
        <small style="padding-left: 5px; margin-left: 5px;">밝은 테마와 어두운 테마 전환</small>
    </div>
    
    <div class="func-item">
        <img src='{settings_icon}' width='18' height='18' style='vertical-align:middle; padding-right:12px;' />설정
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
    .codes code { display: block; background: #f3f4f6; color: #000000; padding: 6px 8px; border-radius: 8px; margin-bottom: 6px; }
    .dark-mode .codes code { background: #1f2937; color: #e5e7eb; }
    .codes.inline code { display: inline-block; margin-right: 8px; margin-bottom: 6px; background: transparent; color: #000000; padding: 0; border-radius: 0; }
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

    def _ensure_chat_transcript_visible(self) -> None:
        """Show the chat transcript area and hide the hero prompt area."""
        try:
            if getattr(self, "output_area", None):
                self.output_area.show()
        except Exception:
            pass
        try:
            if getattr(self, "hero_area", None):
                self.hero_area.hide()
        except Exception:
            pass

    def _apply_chat_bubble_style(self, role: str, bubble: QLabel) -> None:
        """Apply theme-aware styles to a chat bubble label."""
        is_dark = getattr(self, "dark_mode", False)
        if role == "user":
            bg = "#5377f6"
            fg = "#ffffff"
            border = "transparent"
        else:
            bg = "#111111" if is_dark else "#f4f4f5"
            fg = "#ffffff" if is_dark else "#0f1724"
            border = "#1f2937" if is_dark else "#e5e7eb"

        bubble.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 16px;
                padding: 10px 12px;
                font-size: 14px;
                line-height: 1.5;
            }}
            """
        )


    def _save_message_to_current_chat(self, role: str, text: str) -> None:
        """Save a message to the current chat's messages list."""
        try:
            if self._current_chat_id:
                for chat in self._chats:
                    if chat.get("id") == self._current_chat_id:
                        if "messages" not in chat:
                            chat["messages"] = []
                        # Save plain text, not HTML
                        chat["messages"].append({"role": role, "content": text})
                        return
        except Exception as e:
            print(f"[MainWindow] Error saving message to chat: {e}")

    def _refresh_chat_transcript_styles(self) -> None:
        """Reapply theme-aware bubble styles (e.g. after theme toggle)."""
        try:
            for role, _row, bubble in getattr(self, "_chat_widgets", []):
                self._apply_chat_bubble_style(role, bubble)
        except Exception:
            pass

    def _refresh_drawer_name_style(self) -> None:
        """Reapply theme-aware style to drawer profile name label."""
        lbl = getattr(self, "drawer_name_label", None)
        if lbl is None:
            return
        try:
            if self.dark_mode:
                lbl.setStyleSheet('font-weight:800; font-size:16px; color:#ffffff;')
            else:
                lbl.setStyleSheet('font-weight:800; font-size:16px; color:#0f1724;')
        except Exception:
            pass

    def _show_thinking_animation(self) -> None:
        """Show animated 'thinking...' indicator in chat."""
        self._remove_thinking_animation()  # Remove any existing one first
        self._ensure_chat_transcript_visible()

        # Remove the stretch spacer at the end
        try:
            if self.chat_transcript_layout.count() > 0:
                last_item = self.chat_transcript_layout.itemAt(self.chat_transcript_layout.count() - 1)
                if last_item and last_item.spacerItem():
                    self.chat_transcript_layout.takeAt(self.chat_transcript_layout.count() - 1)
        except Exception:
            pass

        row = QWidget()
        row.setObjectName("chat-row")
        row_lyt = QHBoxLayout(row)
        row_lyt.setContentsMargins(0, 0, 0, 0)
        row_lyt.setSpacing(0)

        bubble = QLabel()
        bubble.setObjectName("chat-bubble-thinking")
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(520)
        bubble.setTextFormat(Qt.TextFormat.RichText)
        bubble.setText("생각하는 중")
        self._apply_chat_bubble_style("assistant", bubble)

        row_lyt.addWidget(bubble, 0, Qt.AlignmentFlag.AlignLeft)
        row_lyt.addStretch(1)

        self.chat_transcript_layout.addWidget(row, 0)
        self.chat_transcript_layout.addStretch(1)
        self._thinking_widget = (row, bubble)

        # Start animation timer
        self._thinking_dots = 0
        if self._thinking_timer is None:
            self._thinking_timer = QTimer()
            self._thinking_timer.timeout.connect(self._update_thinking_animation)
        self._thinking_timer.start(400)  # Update every 400ms

        # Scroll to bottom
        try:
            QTimer.singleShot(0, lambda: self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum()))
        except Exception:
            pass

    def _update_thinking_animation(self) -> None:
        """Update the thinking animation dots."""
        if self._thinking_widget is None:
            return
        _, bubble = self._thinking_widget
        self._thinking_dots = (self._thinking_dots + 1) % 4
        dots = "." * self._thinking_dots
        bubble.setText(f"생각하는 중{dots}")

    def _remove_thinking_animation(self) -> None:
        """Remove the thinking animation indicator."""
        if self._thinking_timer is not None:
            self._thinking_timer.stop()
        if self._thinking_widget is not None:
            row, _ = self._thinking_widget
            try:
                # Remove the stretch spacer at the end first
                if self.chat_transcript_layout.count() > 0:
                    last_item = self.chat_transcript_layout.itemAt(self.chat_transcript_layout.count() - 1)
                    if last_item and last_item.spacerItem():
                        self.chat_transcript_layout.takeAt(self.chat_transcript_layout.count() - 1)
                # Remove the thinking widget
                self.chat_transcript_layout.removeWidget(row)
                row.deleteLater()
                # Add stretch back
                self.chat_transcript_layout.addStretch(1)
            except Exception:
                pass
            self._thinking_widget = None

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
        """Set settings icon using settings-light.svg/settings-dark.svg."""
        assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
        svg_file = assets_dir / ("settings-dark.svg" if self.dark_mode else "settings-light.svg")
        if svg_file.exists():
            self.settings_btn.setIcon(QIcon(str(svg_file)))
            self.settings_btn.setIconSize(QSize(32, 32))
            self.settings_btn.setText("")
        else:
            self.settings_btn.setIcon(QIcon())

    def _show_settings(self) -> None:
        """Show settings dialog."""
        settings_icon = self._get_icon_path_str("settings") or ""
        settings_content = f"""
    <div style='margin-bottom: 20px;'>
        <h2 style='font-size: 20px; margin: 0; padding: 0;'>설정</h2>
    </div>

    <div class="setting-section">
    <div class="setting-title"><br>애플리케이션 정보<br></div>
    
    <div class="setting-item">
        <span class="setting-label">버전</span>
        <span class="setting-value">1.0.0<br></span>
    </div>
    
    <div class="setting-item">
        <span class="setting-label">Python 버전</span>
        <span class="setting-value">3.9+<br></span>
    </div>
    
    <div class="setting-item">
        <span class="setting-label">플랫폼</span>
        <span class="setting-value">Windows, macOS, Linux<br></span>
    </div>
</div>
"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
        dlg = QDialog(self)
        dlg.setWindowTitle("설정")
        dlg.setMinimumWidth(420)
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
        dlg = QDialog(self)
        dlg.setWindowTitle("설정")
        dlg.setMinimumWidth(420)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)
        info_label = QLabel()
        info_label.setText(settings_content)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info_label)
        # Save/load chat buttons in a horizontal layout on the right
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)
        btn_layout.addStretch(1)
        save_btn = QPushButton('채팅 저장하기')
        save_btn.setIcon(QIcon(str(self._get_icon_path('save-light' if not self.dark_mode else 'save-dark'))))
        save_btn.setIconSize(QSize(32, 32))
        save_btn.setStyleSheet("font-size:16px; font-weight:700; padding:4px 18px; border-radius:8px; border: 2px solid #222; min-height:28px;")
        save_btn.clicked.connect(self._export_chats)
        btn_layout.addWidget(save_btn)
        load_btn = QPushButton('채팅 불러오기')
        load_btn.setIcon(QIcon(str(self._get_icon_path('load-light' if not self.dark_mode else 'load-dark'))))
        load_btn.setIconSize(QSize(32, 32))
        load_btn.setStyleSheet("font-size:16px; font-weight:700; padding:4px 18px; border-radius:8px; border: 2px solid #222; min-height:28px;")
        load_btn.clicked.connect(self._import_chats)
        btn_layout.addWidget(load_btn)
        layout.addWidget(btn_row)
        dlg.exec()

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
        if not self.ai_helper.is_available():
            self._show_error_dialog(
                "AI API를 사용할 수 없습니다.\n\n"
                "API 키를 설정해주세요. 자세한 사항은 개발진에게 문의해주세요."
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
        if not self.ai_helper.is_available():
            self._show_error_dialog(
                "AI 기능을 사용할 수 없습니다.\n\n"
                "API 키를 설정해주세요. 자세한 사항은 개발진에게 문의해주세요."
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
        """Get text input from user with optional voice recognition and image upload.
        
        Returns:
            Tuple of (text, ok_clicked, image_path)
        """"""Get text input from user via custom styled dialog with buttons inside form."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setMinimumWidth(520)
        
        # Set dialog background color (theme-aware)
        dialog.setStyleSheet("""
            QDialog {
                background-color: %s;
            }
        """ % ("#1a1a1a" if self.dark_mode else "#ffffff"))
        
        # Create main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Banner section with prompt text (prominent dark banner in dark mode)
        banner = QWidget()
        banner.setObjectName("prompt-banner")
        banner.setStyleSheet("""
            QWidget#prompt-banner {
                background-color: %s;
                padding: 24px;
            }
        """ % (
            "#000000" if self.dark_mode else "#f9fafb"
        ))
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(24, 20, 24, 20)
        banner_layout.setSpacing(0)
        
        # Centered description label with better typography
        desc_label = QLabel(prompt)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: %s;
                font-size: 14px;
                font-weight: 500;
                line-height: 1.6;
                background: transparent;
            }
        """ % ("#ffffff" if self.dark_mode else "#1f2937"))
        banner_layout.addWidget(desc_label)
        main_layout.addWidget(banner)
        
        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)
        
        # Create input container with buttons inside
        input_container = QWidget()
        input_container.setObjectName("input-container")
        input_container.setStyleSheet("""
            QWidget#input-container {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 16px;
            }
        """ % (
            "#0f0f0f" if self.dark_mode else "#f9fafb",
            "#2a2a2a" if self.dark_mode else "#d1d5db"
        ))
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(14)
        
        # Styled input field to match main page
        input_field = QTextEdit()
        input_field.setObjectName("script-editor")
        input_field.setMinimumHeight(160)
        input_field.setMinimumWidth(440)
        input_field.setMaximumHeight(280)
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
            voice_btn.setObjectName("voice-input-button")
            voice_btn.setFixedSize(44, 44)
            voice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            voice_btn.setToolTip("음성으로 입력하기")
            voice_btn.setStyleSheet("""
                QPushButton#voice-input-button {
                    background-color: %s;
                    border: 1px solid %s;
                    border-radius: 8px;
                }
                QPushButton#voice-input-button:hover {
                    background-color: %s;
                }
            """ % (
                ("#1a1a1a", "#2a2a2a", "#252525") if self.dark_mode else ("#ffffff", "#d1d5db", "#f3f4f6")
            ))
            
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
        
        # Cancel button - text only, no background
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary-button")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.setMaximumWidth(110)
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton#secondary-button {
                background: transparent;
                border: none;
                color: %s;
                font-weight: 600;
                font-size: 15px;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton#secondary-button:hover {
                background: %s;
            }
        """ % (
            ("#9ca3af", "#1f1f1f") if self.dark_mode else ("#6b7280", "#f3f4f6")
        ))
        
        # OK button - prominent blue button
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primary-action")
        ok_btn.setMinimumWidth(90)
        ok_btn.setMaximumWidth(110)
        ok_btn.setMinimumHeight(40)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton#primary-action {
                background-color: #4169e1;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: 700;
                font-size: 15px;
                padding: 8px 20px;
            }
            QPushButton#primary-action:hover {
                background-color: #5177e8;
            }
            QPushButton#primary-action:pressed {
                background-color: #3459c9;
            }
        """)
        
        button_row.addWidget(cancel_btn)
        button_row.addWidget(ok_btn)
        
        input_layout.addLayout(button_row)
        
        content_layout.addWidget(input_container)
        main_layout.addWidget(content)
        
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
        """Generate script using ChatGPT API - processes multiple files if available."""
        print("[MainWindow] _generate_script_with_ai called")
        
        # Check if too many AI threads are already running (limit to 5 concurrent)
        active_threads = [t for t in self.ai_threads if t.isRunning()]
        if len(active_threads) >= 5:
            print(f"[MainWindow] Too many AI threads running ({len(active_threads)}), ignoring new request")
            try:
                self._chat_add_message("system", "⚠️ 동시 작업이 너무 많습니다 (최대 5개). 일부 작업이 완료될 때까지 기다려주세요.")
            except:
                pass
            return
        
        # Import Path at the top to avoid local variable error
        from pathlib import Path
        import re
        
        # Check for uploaded files first (from file upload button)
        image_paths = []
        user_display_description = description  # For showing to user
        ai_description = description  # For sending to AI
        
        if self.selected_files:
            # Use all uploaded files
            image_paths = self.selected_files.copy()
            print(f"[MainWindow] Processing {len(image_paths)} files: {image_paths}")
            if len(image_paths) > 1:
                file_names = ", ".join([Path(p).name for p in image_paths])
                user_display_description = f"{description}\n\n📸 {len(image_paths)}개의 파일을 분석합니다: {file_names}"
                # Internal instruction for AI (not shown to user)
                ai_description = f"{description}\n\n📸 {len(image_paths)}개의 파일을 분석합니다: {file_names}\n\n⚠️ IMPORTANT: Process ALL {len(image_paths)} files separately. After analyzing the first file, add insert_paragraph() separator and process the next file."
            else:
                user_display_description = f"{description}\n\n📸 업로드된 파일을 분석합니다: {Path(image_paths[0]).name}"
                ai_description = user_display_description
        else:
            # Check if description contains an image file path
            # Look for image file extensions in the description
            image_pattern = r'([^\s]+\.(?:png|jpg|jpeg|gif|bmp|pdf))'
            match = re.search(image_pattern, description, re.IGNORECASE)
            if match:
                potential_path = match.group(1)
                # Check if the file exists
                if Path(potential_path).exists():
                    image_paths = [potential_path]
                    print(f"[MainWindow] Detected image file in description: {potential_path}")
                    user_display_description = f"{description}\n\n📸 이미지 파일을 분석하여 수식을 추출합니다."
                    ai_description = user_display_description
        
        # Process all files (for now, use first one)
        image_path = image_paths[0] if image_paths else None
        
        # Display user's prompt in the chat transcript (ChatGPT-style) - show clean version
        try:
            self._chat_add_message("user", user_display_description)
            self._show_thinking_animation()
        except Exception:
            self._append_user_input(user_display_description)
        context = """
사용 가능한 함수들:
- insert_text(text): 텍스트 삽입
- insert_paragraph(): 문단 추가
- insert_equation(latex_code, font_size_pt=14.0): LaTeX 수식 삽입
- insert_hwpeqn(hwpeqn_code, font_size_pt=12.0): HWP 수식 형식 삽입
- insert_table(rows, cols): 표 삽입

🚫 절대 사용 금지: insert_image() 함수는 존재하지 않습니다!
⚠️ 이미지/PDF 분석 시: 파일을 삽입하지 말고, 내용을 추출하여 작성하세요!
"""
        
        # Create worker and thread
        print("[MainWindow] Creating QThread and AIWorker...")
        ai_thread = QThread()
        
        # Track if image is being used
        self._last_image_used = bool(image_path)
        print(f"[MainWindow] Image used: {self._last_image_used}")
        
        ai_worker = AIWorker(
            self.ai_helper, 
            "generate", 
            description=ai_description,  # Use AI version with internal instructions
            context=context,
            image_path=image_path,  # Legacy single image support
            image_paths=image_paths,  # New multi-image support
            model=self.current_model  # Use selected model
        )
        ai_worker.moveToThread(ai_thread)
        print("[MainWindow] Worker moved to thread")
        
        # Add to active threads/workers list
        self.ai_threads.append(ai_thread)
        self.ai_workers.append(ai_worker)
        print(f"[MainWindow] Active threads: {len([t for t in self.ai_threads if t.isRunning()])} running, {len(self.ai_threads)} total")
        
        # Connect signals
        print("[MainWindow] Connecting signals...")
        ai_thread.started.connect(ai_worker.run)
        ai_worker.thought.connect(self._on_ai_thought)
        ai_worker.finished.connect(self._on_generate_finished)
        ai_worker.error.connect(self._on_generate_error)
        ai_worker.finished.connect(ai_thread.quit)
        ai_worker.error.connect(ai_thread.quit)
        
        # Clean up thread from list when finished
        def cleanup_thread():
            if ai_thread in self.ai_threads:
                self.ai_threads.remove(ai_thread)
            if ai_worker in self.ai_workers:
                self.ai_workers.remove(ai_worker)
            print(f"[MainWindow] Thread cleaned up. Remaining: {len(self.ai_threads)}")
        
        ai_thread.finished.connect(cleanup_thread)
        ai_thread.finished.connect(ai_thread.deleteLater)
        print("[MainWindow] Signals connected")
        
        # Start the thread
        print("[MainWindow] Starting thread...")
        ai_thread.start()
        print("[MainWindow] Thread started!")
    
    def _generate_and_execute_with_ai(self, description: str) -> None:
        """Generate script using ChatGPT API and auto-execute it (without showing code to user)."""
        print("[MainWindow] _generate_and_execute_with_ai called")
        
        # Check if too many AI threads are already running (limit to 5 concurrent)
        active_threads = [t for t in self.ai_threads if t.isRunning()]
        if len(active_threads) >= 5:
            print(f"[MainWindow] Too many AI threads running ({len(active_threads)}), ignoring new request")
            try:
                self._chat_add_message("system", "⚠️ 동시 작업이 너무 많습니다 (최대 5개). 일부 작업이 완료될 때까지 기다려주세요.")
            except:
                pass
            return
        
        # Import Path at the top to avoid local variable error
        from pathlib import Path
        import re
        
        # Check for uploaded files first (from file upload button)
        image_paths = []
        user_display_description = description  # For showing to user
        ai_description = description  # For sending to AI
        
        if self.selected_files:
            # Use all uploaded files
            image_paths = self.selected_files.copy()
            print(f"[MainWindow] Processing {len(image_paths)} files: {image_paths}")
            if len(image_paths) > 1:
                file_names = ", ".join([Path(p).name for p in image_paths])
                user_display_description = f"{description}\n\n📸 {len(image_paths)}개의 파일을 분석합니다: {file_names}"
                # Internal instruction for AI (not shown to user)
                ai_description = f"{description}\n\n📸 {len(image_paths)}개의 파일을 분석합니다: {file_names}\n\n⚠️ IMPORTANT: Process ALL {len(image_paths)} files separately. After analyzing the first file, add insert_paragraph() separator and process the next file."
            else:
                user_display_description = f"{description}\n\n📸 업로드된 파일을 분석합니다: {Path(image_paths[0]).name}"
                ai_description = user_display_description
        else:
            # Check if description contains an image file path
            # Look for image file extensions in the description
            image_pattern = r'([^\s]+\.(?:png|jpg|jpeg|gif|bmp|pdf))'
            match = re.search(image_pattern, description, re.IGNORECASE)
            if match:
                potential_path = match.group(1)
                # Check if the file exists
                if Path(potential_path).exists():
                    image_paths = [potential_path]
                    print(f"[MainWindow] Detected image file in description: {potential_path}")
                    user_display_description = f"{description}\n\n📸 이미지 파일을 분석하여 수식을 추출합니다."
                    ai_description = user_display_description
        
        # Process all files (for now, use first one)
        image_path = image_paths[0] if image_paths else None
        
        # Display user's prompt in the chat transcript (ChatGPT-style) - show clean version
        try:
            self._chat_add_message("user", user_display_description)
            self._show_thinking_animation()
        except Exception:
            self._append_user_input(user_display_description)
        
        self.send_btn.setEnabled(False)
        if hasattr(self, "ai_generate_button"):
            self.ai_generate_button.setEnabled(False)
        if hasattr(self, "ai_optimize_button"):
            self.ai_optimize_button.setEnabled(False)
        
        # Set auto-execute flag
        self._auto_execute_mode = True
        
        # Get available functions context (platform-aware)
        if platform.system() == "Darwin":  # macOS
            context = """
사용 가능한 함수들 (macOS):
- insert_text(text): 텍스트 삽입 ✅
- insert_math_text(latex): 수식 삽입 (LaTeX를 Unicode로 변환) ✅
- open_formula_editor(): 수식 편집기 창 열기 (Ctrl+N+M) ✅
- insert_equation_via_editor(formula): 실제 수식 객체 삽입 (Ctrl+N+M 사용) ✅
- insert_paragraph(): 문단 추가 ✅

수식 삽입 방법:

1. insert_math_text() - 빠른 Unicode 변환 (텍스트로 삽입):
   - insert_math_text("x^2 + y^2 = z^2") → x² + y² = z²
   - insert_math_text("\\int_{0}^{\\infty} e^{-x} dx") → ∫₀^∞ e⁻ˣ dx
   - insert_math_text("\\sum_{i=1}^{n} x_i") → ∑ᵢ₌₁ⁿ xᵢ
   - insert_math_text("\\alpha + \\beta = \\gamma") → α + β = γ

2. open_formula_editor() - 수식 편집기 창 열기:
   - open_formula_editor() → 수식 편집기 창을 열어서 수동으로 수식 입력 가능
   - 사용자가 직접 수식을 입력하고 "넣기" 버튼을 클릭할 수 있음

3. insert_equation_via_editor() - 실제 수식 객체 (더 나은 품질):
   - insert_equation_via_editor("a over b") → 분수 a/b (실제 수식)
   - insert_equation_via_editor("x^2 + y^2") → 제곱 수식
   - insert_equation_via_editor("int from 0 to infinity") → 적분 수식
   
   수식 편집기 문법:
   - "a over b" → 분수
   - "x^2" → 제곱
   - "x_1" → 아래첨자
   - "int from a to b" → 적분
   - "sum from i=1 to n" → 합

⚠️ macOS에서는 지원되지 않는 기능:
- insert_equation(): LaTeX 수식 삽입 (Windows 전용)
- insert_hwpeqn(): HWP 수식 삽입 (Windows 전용)
- insert_image(): 이미지 삽입 (Windows 전용)
- insert_table(): 표 삽입 (Windows 전용)

추천: 실제 수식 객체가 필요하면 insert_equation_via_editor()를 사용하세요!
"""
        else:  # Windows
            context = """
사용 가능한 함수들:
- insert_text(text): 텍스트 삽입
- insert_math_text(latex): 수식 삽입 (LaTeX를 Unicode로 변환) ✅
- insert_paragraph(): 문단 추가
- insert_equation(latex_code, font_size_pt=14.0): LaTeX 수식 삽입 (실제 수식 객체)
- insert_hwpeqn(hwpeqn_code, font_size_pt=12.0): HWP 수식 형식 삽입
- insert_image(image_path): 이미지 삽입
- insert_table(rows, cols): 표 삽입

수식 삽입 방법:
- insert_math_text(): 빠른 Unicode 변환 (텍스트로 삽입)
- insert_equation(): 실제 수식 객체 삽입 (더 나은 품질)
"""
        
        # Create worker and thread
        print("[MainWindow] Creating QThread and AIWorker...")
        ai_thread = QThread()
        
        # Track if image is being used
        self._last_image_used = bool(image_path)
        print(f"[MainWindow] Image used: {self._last_image_used}")
        
        ai_worker = AIWorker(
            self.ai_helper, 
            "generate", 
            description=ai_description,  # Use AI version with internal instructions
            context=context,
            image_path=image_path,  # Legacy single image support
            image_paths=image_paths,  # New multi-image support
            model=self.current_model  # Use selected model
        )
        ai_worker.moveToThread(ai_thread)
        print("[MainWindow] Worker moved to thread")
        
        # Add to active threads/workers list
        self.ai_threads.append(ai_thread)
        self.ai_workers.append(ai_worker)
        print(f"[MainWindow] Active threads: {len([t for t in self.ai_threads if t.isRunning()])} running, {len(self.ai_threads)} total")
        
        # Connect signals
        print("[MainWindow] Connecting signals...")
        ai_thread.started.connect(ai_worker.run)
        ai_worker.thought.connect(self._on_ai_thought)
        ai_worker.finished.connect(self._on_generate_finished)
        ai_worker.error.connect(self._on_generate_error)
        ai_worker.finished.connect(ai_thread.quit)
        ai_worker.error.connect(ai_thread.quit)
        
        # Clean up thread from list when finished
        def cleanup_thread():
            if ai_thread in self.ai_threads:
                self.ai_threads.remove(ai_thread)
            if ai_worker in self.ai_workers:
                self.ai_workers.remove(ai_worker)
            print(f"[MainWindow] Thread cleaned up. Remaining: {len(self.ai_threads)}")
        
        ai_thread.finished.connect(cleanup_thread)
        ai_thread.finished.connect(ai_thread.deleteLater)
        print("[MainWindow] Signals connected")
        
        # Start the thread
        print("[MainWindow] Starting thread...")
        ai_thread.start()
        print("[MainWindow] Thread started!")
    
    def _on_generate_finished(self, generated_code: str) -> None:
        """Handle successful script generation."""
        # Replace the progress line with completion message - triggers fade transition
        completion_msg = "✅ 스크립트 생성 완료!"
        
        # Update with completion message (will trigger fade animation)
        self._update_progress_message(completion_msg)
        
        # Clear selected files after successful generation (AI has processed the image)
        if self.selected_files:
            print(f"[MainWindow] Clearing selected_files after AI generation: {self.selected_files}")
            # Clear the preview widgets from UI
            while self.image_preview_layout.count() > 0:
                widget = self.image_preview_layout.takeAt(0)
                if widget and widget.widget():
                    widget.widget().deleteLater()
            self.image_preview_container.hide()
            self.selected_files.clear()
        
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
        
        # Validation: If image was used, check if description has line listings
        if hasattr(self, '_last_image_used') and self._last_image_used:
            if "📋 Line" not in description and "Line 1:" not in description:
                print("[WARNING] AI did not list lines from image! May have missed content.")
                # Don't reject - just log the warning
        
        # Wait for animation to complete before clearing
        def finish_animation():
            self._clear_progress_message()
            self._remove_thinking_animation()
            
            # Always auto-execute (users want results, not code)
            self._auto_execute_mode = False  # Reset flag
            
            if code:
                # Show description first (what AI will do)
                if description:
                    try:
                        self._chat_add_message("assistant", description)
                    except Exception:
                        pass
                
                # Check if HWP is available before executing (cross-platform)
                hwp_available = False
                try:
                    test_hwp = HwpController()
                    test_hwp.connect()
                    hwp_available = True
                except Exception:
                    pass
                
                if hwp_available:
                    # Execute the code to modify HWP
                    self._worker = ScriptWorker(code, self)
                    self._worker.log_signal.connect(lambda msg: None)  # Suppress log messages
                    self._worker.error_signal.connect(lambda err: self._chat_add_message("assistant", f"❌ 오류: {err}"))
                    self._worker.finished_signal.connect(lambda: self._on_auto_execution_finished())
                    self._worker.start()
                else:
                    # HWP not available, just show response
                    try:
                        self._chat_add_message("assistant", "💡 한글(HWP)이 실행 중이지 않아 작업을 수행할 수 없습니다. 한글 문서를 열고 다시 시도해주세요.")
                    except Exception:
                        pass
                    self.send_btn.setEnabled(True)
                    if hasattr(self, "ai_generate_button"):
                        self.ai_generate_button.setEnabled(True)
                    if hasattr(self, "ai_optimize_button"):
                        self.ai_optimize_button.setEnabled(True)
            else:
                # No code generated
                try:
                    msg = description if description else "작업을 수행할 수 없었습니다."
                    self._chat_add_message("assistant", msg)
                except Exception:
                    pass
                self.send_btn.setEnabled(True)
                if hasattr(self, "ai_generate_button"):
                    self.ai_generate_button.setEnabled(True)
                if hasattr(self, "ai_optimize_button"):
                    self.ai_optimize_button.setEnabled(True)
        
        QTimer.singleShot(600, finish_animation)
    
    def _on_auto_execution_finished(self) -> None:
        """Handle completion of auto-executed script."""
        try:
            self._chat_add_message("assistant", "✅ 한글 문서에 적용되었습니다!")
        except Exception:
            pass
        self.send_btn.setEnabled(True)
        if hasattr(self, "ai_generate_button"):
            self.ai_generate_button.setEnabled(True)
        if hasattr(self, "ai_optimize_button"):
            self.ai_optimize_button.setEnabled(True)
    
    def _on_generate_error(self, error_msg: str) -> None:
        """Handle script generation error."""
        self._clear_progress_message()
        self._remove_thinking_animation()
        self._auto_execute_mode = False  # Reset flag on error
        try:
            self._chat_add_message("assistant", f"❌ 스크립트 생성 실패: {error_msg}")
        except Exception:
            self._append_log(f"❌ 스크립트 생성 실패: {error_msg}")
        self._show_error_dialog(f"스크립트 생성 중 오류가 발생했습니다.\n\n{error_msg}")
        self.send_btn.setEnabled(True)
        if hasattr(self, "ai_generate_button"):
            self.ai_generate_button.setEnabled(True)
        if hasattr(self, "ai_optimize_button"):
            self.ai_optimize_button.setEnabled(True)

    def _on_ai_thought(self, msg: str) -> None:
        """Handle AI thought updates on the UI thread with animated progress."""
        self._update_progress_message(f"📝 {msg}")

    def _optimize_script_with_ai(self, feedback: str) -> None:
        """Optimize current script using ChatGPT API."""
        print("[MainWindow] _optimize_script_with_ai called")
        
        # Check if too many AI threads are already running (limit to 5 concurrent)
        active_threads = [t for t in self.ai_threads if t.isRunning()]
        if len(active_threads) >= 5:
            print(f"[MainWindow] Too many AI threads running ({len(active_threads)}), ignoring new request")
            try:
                self._chat_add_message("system", "⚠️ 동시 작업이 너무 많습니다 (최대 5개). 일부 작업이 완료될 때까지 기다려주세요.")
            except:
                pass
            return
        
        # Display user's prompt in the chat transcript (ChatGPT-style)
        try:
            self._chat_add_message("user", feedback if feedback.strip() else "(기본 최적화 요청)")
            self._show_thinking_animation()
        except Exception:
            self._append_user_input(feedback if feedback.strip() else "(기본 최적화 요청)")
        
        self.send_btn.setEnabled(False)
        if hasattr(self, "ai_generate_button"):
            self.ai_generate_button.setEnabled(False)
        if hasattr(self, "ai_optimize_button"):
            self.ai_optimize_button.setEnabled(False)
        
        current_script = self.script_edit.toPlainText()
        
        # Create worker and thread
        print("[MainWindow] Creating QThread and AIWorker...")
        ai_thread = QThread()
        ai_worker = AIWorker(
            self.ai_helper, 
            "optimize", 
            script=current_script, 
            feedback=feedback,
            model=self.current_model  # Use selected model
        )
        ai_worker.moveToThread(ai_thread)
        print("[MainWindow] Worker moved to thread")
        
        # Add to active threads/workers list
        self.ai_threads.append(ai_thread)
        self.ai_workers.append(ai_worker)
        print(f"[MainWindow] Active threads: {len([t for t in self.ai_threads if t.isRunning()])} running, {len(self.ai_threads)} total")
        
        # Connect signals
        print("[MainWindow] Connecting signals...")
        ai_thread.started.connect(ai_worker.run)
        ai_worker.thought.connect(self._on_ai_thought)
        ai_worker.finished.connect(self._on_optimize_finished)
        ai_worker.error.connect(self._on_optimize_error)
        ai_worker.finished.connect(ai_thread.quit)
        ai_worker.error.connect(ai_thread.quit)
        
        # Clean up thread from list when finished
        def cleanup_thread():
            if ai_thread in self.ai_threads:
                self.ai_threads.remove(ai_thread)
            if ai_worker in self.ai_workers:
                self.ai_workers.remove(ai_worker)
            print(f"[MainWindow] Thread cleaned up. Remaining: {len(self.ai_threads)}")
        
        ai_thread.finished.connect(cleanup_thread)
        ai_thread.finished.connect(ai_thread.deleteLater)
        print("[MainWindow] Signals connected")
        
        # Start the thread
        print("[MainWindow] Starting thread...")
        ai_thread.start()
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
            self._remove_thinking_animation()
            # Display result in chat transcript
            try:
                parts: list[str] = []
                if code:
                    parts.append("💻 코드\n" + code)
                if description:
                    parts.append("📝 설명\n" + description)
                self._chat_add_message("assistant", "\n\n".join(parts) if parts else "완료되었습니다.")
            except Exception:
                if code:
                    self._append_log("💻 코드\n")
                    self._append_log(code)
                    self._append_log("\n")
                if description:
                    self._append_log("\n📝 설명\n")
                    self._append_log(description)
            # Put code in editor
            if code:
                self.script_edit.setPlainText(code)
            self.send_btn.setEnabled(True)
            self.ai_generate_button.setEnabled(True)
            if hasattr(self, "ai_optimize_button"):
                self.ai_optimize_button.setEnabled(True)
        
        QTimer.singleShot(600, finish_animation)
    
    def _on_optimize_error(self, error_msg: str) -> None:
        """Handle script optimization error."""
        self._clear_progress_message()
        self._remove_thinking_animation()
        try:
            self._chat_add_message("assistant", f"❌ 스크립트 최적화 실패: {error_msg}")
        except Exception:
            self._append_log(f"❌ 스크립트 최적화 실패: {error_msg}")
        self._show_error_dialog(f"스크립트 최적화 중 오류가 발생했습니다.\n\n{error_msg}")
        self.send_btn.setEnabled(True)
        if hasattr(self, "ai_generate_button"):
            self.ai_generate_button.setEnabled(True)
        if hasattr(self, "ai_optimize_button"):
            self.ai_optimize_button.setEnabled(True)

    def _show_backup_menu(self) -> None:
        """Show backup menu with options in-drawer (avoid opening separate windows)."""
        # If the drawer panel is present, show an in-drawer popup anchored to the backup anchor
        anchor_btn = getattr(self, "backup_icon_btn", None) or getattr(self, "drawer_profile_btn", None)
        if hasattr(self, "drawer_panel") and anchor_btn and getattr(self, "drawer_panel"):
            # Toggle existing popup
            if self._drawer_popup and self._drawer_popup.isVisible():
                self._hide_drawer_popup()
                return

            popup = QFrame(self.drawer_panel)
            popup.setObjectName("drawer-popup")
            popup.setFrameShape(QFrame.Shape.StyledPanel)
            popup.setStyleSheet("background:#ffffff; border:1px solid #e6e7eb; border-radius:8px;")
            layout = QVBoxLayout(popup)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(6)

            def add_action(text: str, handler):
                b = QPushButton(text)
                b.setObjectName("drawer-popup-action")
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setFlat(True)
                b.clicked.connect(lambda checked=False, h=handler: (h(), self._hide_drawer_popup()))
                layout.addWidget(b)

            add_action("💾 현재 스크립트 백업", self._backup_current_script)
            add_action("📦 세션 백업 (스크립트 + 출력)", self._backup_session)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            layout.addWidget(sep)
            add_action("📄 스크립트 복원...", self._restore_script_dialog)
            add_action("🔄 세션 복원...", self._restore_session_dialog)
            sep2 = QFrame()
            sep2.setFrameShape(QFrame.Shape.HLine)
            layout.addWidget(sep2)
            add_action("ℹ️  백업 정보 보기", self._show_backup_info)

            # Position the popup under the anchor button
            anchor = anchor_btn.mapTo(self.drawer_panel, anchor_btn.rect().bottomLeft())
            popup.adjustSize()
            pw = popup.width() or 220
            ph = popup.height()
            x = max(8, anchor.x())
            y = min(self.drawer_panel.height() - ph - 8, anchor.y())
            popup.setGeometry(x, y, pw, ph)
            popup.show()
            popup.raise_()
            self._drawer_popup = popup
            return

        # Fallback: use menu if no drawer panel present (legacy behavior)
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
        
        # Show menu at button position (fallback to profile button or cursor if backup button missing)
        anchor_btn = getattr(self, "backup_icon_btn", None) or getattr(self, "drawer_profile_btn", None)
        try:
            if anchor_btn is not None:
                menu.exec(anchor_btn.mapToGlobal(anchor_btn.rect().bottomLeft()))
            else:
                from PySide6.QtGui import QCursor
                menu.exec(QCursor.pos())
        except Exception:
            try:
                from PySide6.QtGui import QCursor
                menu.exec(QCursor.pos())
            except Exception:
                # Last-resort: show in the center of the main window
                menu.exec(self.mapToGlobal(self.rect().center()))
    
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

    def _check_hwp_on_startup(self) -> None:
        """Check if HWP is running when the app starts and show a friendly reminder if not."""
        try:
            # Try to connect to HWP
            test_hwp = HwpController()
            test_hwp.connect()
            # Successfully connected - HWP is running!
            print("[Startup Check] ✅ HWP is running")
            self._update_hwp_status_indicator(connected=True)
        except Exception as e:
            # HWP is not running - show a friendly dialog
            print(f"[Startup Check] ⚠️ HWP not running: {e}")
            self._update_hwp_status_indicator(connected=False)
            
            # Get the correct app name based on platform
            if platform.system() == "Darwin":
                app_name = "Hancom Office HWP"
            else:
                app_name = "한글(HWP)"
            
            # Create a friendly info dialog
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("HWP 실행 안내")
            msg.setText(f"💡 {app_name} 프로그램이 실행되지 않았습니다")
            msg.setInformativeText(
                f"AI가 문서를 작성하려면 먼저 {app_name}을(를) 실행해주세요.\n\n"
                f"1. {app_name} 실행\n"
                f"2. 문서 열기 또는 새로 만들기\n"
                f"3. 이 앱에서 명령 입력\n\n"
                f"지금 {app_name}을(를) 실행하고 문서를 여신 후,\n"
                f"다시 명령을 입력해주세요."
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDefaultButton(QMessageBox.Ok)
            
            # Apply theme-appropriate styling
            if self.dark_mode:
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #1a1a1a;
                        color: #ffffff;
                    }
                    QMessageBox QLabel {
                        color: #ffffff;
                    }
                    QPushButton {
                        background-color: #2a2a2a;
                        color: #ffffff;
                        border: 1px solid #3a3a3a;
                        padding: 8px 16px;
                        border-radius: 4px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #3a3a3a;
                    }
                """)
            else:
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #ffffff;
                    }
                    QPushButton {
                        background-color: #f0f0f0;
                        border: 1px solid #d0d0d0;
                        padding: 8px 16px;
                        border-radius: 4px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                """)
            
            msg.exec()

    def _update_hwp_filename(self) -> None:
        """Automatically detect and update the currently open HWP document filename."""
        try:
            # Check connection status
            hwp_connected = False
            try:
                test_hwp = HwpController()
                test_hwp.connect()
                hwp_connected = True
            except Exception:
                pass
            
            # Update status indicator
            self._update_hwp_status_indicator(connected=hwp_connected)
            
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
                        if self._last_hwp_filename != filename:
                            self._last_hwp_filename = filename
                            # Preserve status indicator
                            current_text = self.hwp_filename_label.text()
                            if "🟢 " in current_text or "🔴 " in current_text:
                                indicator = current_text.split(" ")[0] + " "
                                self.hwp_filename_label.setText(indicator + filename)
                            else:
                                self.hwp_filename_label.setText(filename)
                    return
                
                # If no HWP window found, reset to default
                if self._last_hwp_filename != "한글 문서":
                    self._last_hwp_filename = "한글 문서"
                    current_text = self.hwp_filename_label.text()
                    if "🟢 " in current_text or "🔴 " in current_text:
                        indicator = current_text.split(" ")[0] + " "
                        self.hwp_filename_label.setText(indicator + "한글 문서")
                    else:
                        self.hwp_filename_label.setText("한글 문서")
            else:
                # macOS/Linux: Only update from file picker, not from active window
                pass
        except Exception as e:
            # Silently fail - this is a background detection feature
            print(f"[HWP Detection] Error: {e}")

    def _new_chat(self) -> None:
        """Create and switch to a new chat, clearing UI and persisting state."""
        try:
            self._snapshot_current_chat()
            new_id = str(uuid.uuid4())
            now = time.time()
            self._chats.insert(
                0,
                {
                    "id": new_id,
                    "title": "New chat",
                    "log": "",
                    "script": DEFAULT_SCRIPT.strip(),
                    "messages": [],  # Initialize empty messages list
                    "created_at": now,
                    "updated_at": now,
                },
            )
            # Activate the new chat so UI updates consistently and the drawer closes via _activate_chat
            self._activate_chat(new_id)
            # Show big black '무엇이든 물어보세요' in the chat area (not as a chat message)
            self._clear_chat_transcript()
            self.chat_transcript_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            row = QWidget()
            row_lyt = QHBoxLayout(row)
            row_lyt.setContentsMargins(0, 0, 0, 0)
            row_lyt.setSpacing(0)
            label = QLabel("무엇이든 물어보세요")
            label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            label.setStyleSheet("font-size: 36px; color: #000; font-weight: 800; margin: 0 0 0 12px;")
            row_lyt.addWidget(label, 0, Qt.AlignmentFlag.AlignTop)
            row.setLayout(row_lyt)
            self.chat_transcript_layout.addWidget(row, 0, Qt.AlignmentFlag.AlignTop)
            # Ensure editor is focused and set to default script
            try:
                if hasattr(self, "script_edit"):
                    self.script_edit.setPlainText(DEFAULT_SCRIPT.strip())
                    self.script_edit.setFocus()
                    self._animate_focus(self.script_edit)
            except Exception:
                pass
            # Persist and update layout
            self._schedule_persist()
            self._update_composer_height()
        except Exception:
            pass

    def _open_chat_search(self) -> None:
        """Custom search dialog: large input area with mic, Cancel and OK buttons."""
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("채팅 검색")
            dlg.setModal(True)
            # Make dialog width follow main content width (leave small margins) and reduce height
            try:
                central = self.centralWidget()
                available_w = central.width() if central is not None else self.width()
                dlg_w = max(420, available_w - 40)
            except Exception:
                dlg_w = 520
            dlg.setMinimumHeight(260)
            dlg.setFixedWidth(dlg_w)

            # Center dialog horizontally over the main window and offset slightly from top
            try:
                parent_tl = self.mapToGlobal(self.rect().topLeft())
                x = parent_tl.x() + max(8, (self.width() - dlg.width()) // 2)
                y = parent_tl.y() + 72
                dlg.move(x, y)
            except Exception:
                pass

            # Theme aware background
            if self.dark_mode:
                dlg.setStyleSheet("QDialog { background: #000000; color: #e8e8e8; }")
            else:
                dlg.setStyleSheet("QDialog { background: #ffffff; color: #0f1724; }")

            v = QVBoxLayout(dlg)
            v.setContentsMargins(24, 20, 24, 18)
            v.setSpacing(12)

            # Heading
            heading = QLabel("채팅 제목을 검색하세요")
            heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                heading.setStyleSheet("font-size:20px; font-weight:700;")
            except Exception:
                pass
            v.addWidget(heading)

            # Smaller rounded input area (QTextEdit) inside a frame
            box = QFrame()
            box.setObjectName("search-box")
            box_lyt = QVBoxLayout(box)
            box_lyt.setContentsMargins(12, 12, 12, 12)
            box_lyt.setSpacing(8)

            text_edit = QTextEdit()
            text_edit.setObjectName("search-editor")
            text_edit.setPlaceholderText("여기에 입력하세요")
            # Reduce input height and limit its width relative to dialog width
            text_edit.setMinimumHeight(80)
            text_edit.setMaximumHeight(140)
            text_edit.setAcceptRichText(False)
            # Limit the input width so it appears narrower within the dialog
            try:
                # Make the input fill most of the dialog width for a more comfortable input area
                min_edit_w = int(dlg.width() * 0.75)
                max_edit_w = int(dlg.width() * 0.95)
                text_edit.setMinimumWidth(min_edit_w)
                text_edit.setMaximumWidth(max_edit_w)
                text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            except Exception:
                pass
            # Light theme styling for the input area
            if self.dark_mode:
                text_edit.setStyleSheet("QTextEdit { background: #0f0f0f; border: 1px solid #2a2a2a; border-radius: 12px; color: #e8e8e8; padding: 12px; }")
            else:
                text_edit.setStyleSheet("QTextEdit { background: #f6f7f9; border: 1px solid #e5e7eb; border-radius: 12px; color: #0f1724; padding: 12px; }")
            box_lyt.addWidget(text_edit, 0, Qt.AlignmentFlag.AlignHCenter)

            # Bottom row: buttons right
            bottom = QWidget()
            b_lyt = QHBoxLayout(bottom)
            b_lyt.setContentsMargins(0, 0, 0, 0)
            b_lyt.setSpacing(8)

            b_lyt.addStretch()

            cancel_btn = QPushButton("취소")
            cancel_btn.clicked.connect(dlg.reject)
            try:
                cancel_btn.setStyleSheet("background: transparent; border: none; font-weight:700; font-size:15px; padding: 8px 16px;")
            except Exception:
                pass
            b_lyt.addWidget(cancel_btn, 0, Qt.AlignmentFlag.AlignRight)

            ok_btn = QPushButton("확인")
            ok_btn.setFixedSize(84, 40)
            try:
                ok_btn.setStyleSheet("background: #5377f6; color: white; border-radius: 10px; font-weight:700; font-size:15px;")
            except Exception:
                pass
            b_lyt.addWidget(ok_btn, 0, Qt.AlignmentFlag.AlignRight)

            box_lyt.addWidget(bottom)
            v.addWidget(box)

            def on_ok():
                try:
                    text = text_edit.toPlainText().strip()
                    if text:
                        self._chat_filter = text
                        self._render_chat_list()
                    dlg.accept()
                except Exception:
                    dlg.reject()

            ok_btn.clicked.connect(on_ok)

            dlg.exec()
        except Exception:
            pass


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
    """Delegate font loading to gui.design.apply_app_font."""
    design.apply_app_font(app)


def _ensure_material_icon_font() -> str:
    """Delegate material icon font resolution to gui.design.ensure_material_icon_font."""
    return design.ensure_material_icon_font()

from PySide6.QtCore import Signal, QThread, QObject
from backend.hwp.hwp_controller import HwpController, HwpControllerError
from backend.hwp.script_runner import HwpScriptRunner
import time

class AIWorker(QObject):
    finished = Signal(str)
    error = Signal(str)
    thought = Signal(str)
    def __init__(self, ai_helper, task_type: str, **kwargs):
        super().__init__()
        self.ai_helper = ai_helper
        self.task_type = task_type
        self.kwargs = kwargs
    def run(self):
        import traceback
        from pathlib import Path
        try:
            def on_thought(message: str):
                self.thought.emit(message)
            model = self.kwargs.get('model', 'auto')
            if self.task_type == "generate":
                image_paths = self.kwargs.get('image_paths', [])
                image_path = self.kwargs.get('image_path')
                if image_paths and len(image_paths) > 1:
                    all_results = []
                    for idx, img_path in enumerate(image_paths, 1):
                        desc = self.kwargs['description']
                        if idx > 1:
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
                    if all_results:
                        import re
                        combined_code = []
                        for result in all_results:
                            match = re.search(r'\[CODE\](.*?)\[/CODE\]', result, re.DOTALL)
                            if match:
                                code = match.group(1).strip()
                                combined_code.append(code)
                        code_with_separators = '\ninsert_paragraph()\ninsert_paragraph()\n'.join(combined_code)
                        result = f"[DESCRIPTION]\n모든 파일을 분석하여 내용을 추출했습니다.\n[/DESCRIPTION]\n\n[CODE]\n{code_with_separators}\n[/CODE]"
                    else:
                        result = None
                else:
                    result = self.ai_helper.generate_script(
                        self.kwargs['description'],
                        self.kwargs.get('context', ''),
                        image_path=image_path or (image_paths[0] if image_paths else None),
                        on_thought=on_thought,
                        model=model
                    )
            elif self.task_type == "optimize":
                result = self.ai_helper.optimize_script(
                    self.kwargs['script'],
                    self.kwargs.get('feedback', ''),
                    on_thought=on_thought,
                    model=model
                )
            else:
                error_msg = "Unknown task type"
                self.error.emit(error_msg)
                return
            if result:
                self.finished.emit(result)
            else:
                error_msg = "AI returned no result"
                self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            error_trace = traceback.format_exc()
            self.error.emit(f"{error_msg}\n\nTraceback:\n{error_trace}")

class SpeechRecognitionWorker(QThread):
    text_recognized = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()
    def run(self) -> None:
        try:
            import speech_recognition as sr
        except ImportError:
            sr = None
        if sr is None:
            self.error_signal.emit("speech_recognition 라이브러리가 설치되어 있지 않습니다.\npip install SpeechRecognition pyaudio")
            self.finished_signal.emit()
            return
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                self.error_signal.emit("🎤 듣는 중... 조용한 곳에서 말씀해주세요.")
                audio = recognizer.listen(source, timeout=10)
            try:
                text = recognizer.recognize_google(audio, language='ko-KR')
                self.text_recognized.emit(text)
            except sr.UnknownValueError:
                self.error_signal.emit("음성을 인식할 수 없습니다. 더 명확하게 말씀해주세요.")
            except sr.RequestError as e:
                self.error_signal.emit(f"음성 인식 서비스 오류: {e}")
        except sr.WaitTimeoutError:
            self.error_signal.emit("시간 초과로 음성을 받지 못했습니다.")
        except Exception as e:
            self.error_signal.emit(f"마이크 오류: {e}")
        finally:
            self.finished_signal.emit()

class ScriptWorker(QThread):
    log_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()
    def __init__(self, script: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._script = script
    def run(self) -> None:
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

"""Speech Recognition Worker."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal
import speech_recognition as sr


class SpeechRecognitionWorker(QThread):
    """Worker thread for speech recognition."""

    text_recognized = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

    def run(self) -> None:
        """Run speech recognition."""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source)
                text = self.recognizer.recognize_google(audio, language="ko-KR")
                self.text_recognized.emit(text)
        except Exception as exc:
            self.error_signal.emit(str(exc))
        finally:
            self.finished_signal.emit()
"""AI Worker for background processing."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal


class AIWorker(QThread):
    """Worker thread for AI operations."""

    thought = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, chatgpt_helper, mode: str, **kwargs):
        super().__init__()
        self.chatgpt_helper = chatgpt_helper
        self.mode = mode
        self.kwargs = kwargs

    def run(self) -> None:
        """Run the AI operation."""
        try:
            if self.mode == "generate":
                description = self.kwargs.get("description", "")
                context = self.kwargs.get("context", "")
                result = self.chatgpt_helper.generate_script(description, context)
            elif self.mode == "optimize":
                script = self.kwargs.get("script", "")
                feedback = self.kwargs.get("feedback", "")
                result = self.chatgpt_helper.optimize_script(script, feedback)
            else:
                raise ValueError(f"Unknown mode: {self.mode}")

            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))
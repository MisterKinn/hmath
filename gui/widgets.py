# Custom QTextEdit that forwards file drops to parent window instead of inserting file paths.
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTextEdit

class FileDropTextEdit(QTextEdit):
    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith((
                    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf')):
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith((
                    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf')):
                    self.file_dropped.emit(file_path)
                    event.acceptProposedAction()
                    return
        super().dropEvent(event)

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSize  # type: ignore[reportMissingImports]
from PySide6.QtGui import QIcon  # type: ignore[reportMissingImports]
from PySide6.QtWidgets import (  # type: ignore[reportMissingImports]
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QWidget,
    QSpacerItem,
    QSizePolicy,
)

from . import design


class LoginWindow(QDialog):
    """Standalone login/info dialog shown before MainWindow or when logged out.

    This dialog is intentionally separate from `MainWindow` so it can be shown on
    its own (e.g. login-first experience). It shows a prominent title, a short
    description, optional instructions, and an action button that triggers the
    provided `on_login` callback.
    """

    def __init__(self, parent: Optional[QWidget] = None, dark_mode: bool = False, on_login=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("로그인")
        self.dark_mode = dark_mode
        self.on_login = on_login
        self._init_ui()

    def _init_ui(self) -> None:
        self.setModal(False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(360)
        self.setStyleSheet("QDialog { background-color: %s; }" % ("#0f1724" if self.dark_mode else "#ffffff"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Nova AI에 오신 것을 환영합니다")
        title.setStyleSheet("font-size:22px; font-weight:900; color: %s;" % ("#e8e8e8" if self.dark_mode else "#0f1724"))
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Nova AI는 한글 문서 자동화를 위한 AI 도우미입니다.\n로그인하고 효율적인 한글 문서 작업을 시작하세요."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size:14px; color: %s;" % ("#cbd5e1" if self.dark_mode else "#475569"))
        layout.addWidget(desc)

        # Spacer
        layout.addItem(QSpacerItem(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Buttons row
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)

        row_layout.addStretch(1)

        login_btn = QPushButton("로그인")
        login_btn.setObjectName("primary-action")
        login_btn.setCursor(Qt.PointingHandCursor)
        # Slightly larger, more prominent login button
        login_btn.setFixedHeight(40)
        login_btn.setMinimumWidth(96)
        login_btn.setStyleSheet(
            "QPushButton#primary-action { background-color: #3b82f6; color: #ffffff; border: none; border-radius: 10px; padding: 8px 16px; font-weight:700; font-size:15px; min-width:96px; }"
            "QPushButton#primary-action:hover { background-color: #2563eb; }"
        )
        login_btn.clicked.connect(self._on_login_click)
        row_layout.addWidget(login_btn)
        row_layout.addStretch(1)

        layout.addWidget(row)

    def _on_login_click(self) -> None:
        if callable(self.on_login):
            try:
                self.on_login()
            except Exception:
                pass
        self.accept()


if __name__ == "__main__":
    # Quick manual test
    from PySide6.QtWidgets import QApplication  # type: ignore[reportMissingImports]
    import sys

    app = QApplication(sys.argv)
    w = LoginWindow()
    w.show()
    sys.exit(app.exec())

from . import design
from PySide6.QtWidgets import QMessageBox

def _load_dialog_css() -> str:
    return design.load_dialog_css()

def _load_theme(theme_name: str) -> str:
    return design.load_theme(theme_name)

def _create_styled_dialog(parent, title: str, content: str, min_width: int = 500, min_height: int = 0, dark_mode: bool = False, icon_path: str | None = None) -> QMessageBox:
    return design.create_styled_dialog(parent, title, content, min_width=min_width, min_height=min_height, dark_mode=dark_mode, icon_path=icon_path)

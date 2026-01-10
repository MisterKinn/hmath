from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QColor, QPixmap, QPainter, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QMessageBox


def load_dialog_css() -> str:
    css_path = Path(__file__).parent / "styles" / "dialog_styles.css"
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


def load_theme(theme_name: str) -> str:
    qss_path = Path(__file__).parent / "styles" / f"{theme_name}_theme.qss"
    if qss_path.exists():
        return qss_path.read_text(encoding="utf-8")
    return ""


def create_styled_dialog(parent, title: str, content: str, min_width: int = 500, min_height: int = 0, dark_mode: bool = False, icon_path: str | None = None) -> QMessageBox:
    """Create a styled dialog used by the app (ported from MainWindow)."""
    css = load_dialog_css()
    dark_class = "dark-mode" if dark_mode else ""
    full_html = f"<style>{css}</style><body class='{dark_class}'>{content}</body>"

    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    # Use Qt's RichText enum for rich HTML content
    msg.setTextFormat(Qt.RichText)
    msg.setText(full_html)
    if icon_path:
        pix = QPixmap(icon_path)
        if not pix.isNull():
            msg.setIconPixmap(pix.scaled(48, 48))
        else:
            msg.setIcon(QMessageBox.Icon.NoIcon)
    else:
        msg.setIcon(QMessageBox.Icon.NoIcon)

    msg.setStandardButtons(QMessageBox.StandardButton.Ok)

    # OK button style
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


def apply_help_button_style(window) -> None:
    """Apply help/hwp/send button styling to the given MainWindow-like object."""
    if (
        not hasattr(window, "howto_button")
        and not hasattr(window, "hwp_filename_label")
        and not hasattr(window, "run_button")
    ):
        return

    dark_mode = getattr(window, "dark_mode", False)
    if dark_mode:
        bg = "#303030"
        border = "#303030"
        hover_bg = "#383838"
        hover_border = "#404040"
        press_bg = "#2a2a2a"
        press_border = "#4a4a4a"
        text_color = "#e8e8e8"
    else:
        # Slightly more neutral/light backgrounds with pure black text for clarity
        bg = "#ffffff"
        border = "#e6e7eb"
        hover_bg = "#f4f6f8"
        hover_border = "#dfe3ea"
        press_bg = "#eef2f7"
        press_border = "#d1d5db"
        text_color = "#000000"

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
        getattr(window, "howto_button", None),
        getattr(window, "latex_button", None),
        getattr(window, "ai_generate_button", None),
    ):
        if btn:
            btn.setStyleSheet(help_style)

    # HWP label button
    hwp_bg = hover_bg
    hwp_border = hover_border
    hwp_style = f"""
    QPushButton {{
        background-color: {hwp_bg};
        color: {text_color};
        border: 1px solid {hwp_border};
        border-radius: 12px;
        padding: 6px 12px;
        font-weight: 700;
        font-size: 13px;
        text-align: center;
    }}
    QPushButton:hover {{
        background-color: {hwp_bg};
        border: 1px solid {hwp_border};
    }}
    QPushButton:pressed {{
        background-color: {press_bg};
        border: 1px solid {press_border};
    }}
    """
    if getattr(window, "hwp_filename_label", None):
        window.hwp_filename_label.setStyleSheet(hwp_style)

    # Send button style (no border, no circle, just icon)
    send_style = f"""
    QPushButton#composer-send {{
        background-color: transparent;
        color: #222;
        border: none !important;
        border-radius: 0 !important;
        min-width: 44px;
        min-height: 44px;
        max-width: 44px;
        max-height: 44px;
        font-weight: 700;
        font-size: 26px;
        box-shadow: none !important;
        outline: none !important;
    }}
    QPushButton#composer-send:hover {{
        background-color: #ececf1;
        border: none !important;
        box-shadow: none !important;
    }}
    QPushButton#composer-send:pressed {{
        background-color: #e5e7eb;
        border: none !important;
        box-shadow: none !important;
    }}
    """
    if getattr(window, "run_button", None):
        window.run_button.setStyleSheet(send_style)
        # Reapply material symbol if needed
        if hasattr(window, "_set_material_symbol"):
            try:
                window._set_material_symbol(window.run_button, "arrow_upward", fallback="↑", px=20)
            except Exception:
                pass


def set_material_symbol(widget, ligature: str, fallback: str, px: int, material_symbols_available: bool, dark_mode: bool = False) -> None:
    widget.setIcon(QIcon())
    if material_symbols_available:
        widget.setText(ligature)
        widget.setStyleSheet(
            widget.styleSheet()
            + f"font-family: 'Material Symbols Outlined'; font-size: {px}px;"
              "font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;"
        )
    else:
        widget.setText(fallback)


def set_material_symbol_icon(widget, ligature: str, px: int, material_symbols_available: bool, dark_mode: bool = False) -> None:
    widget.setText("")
    if material_symbols_available:
        color = QColor("#000000") if not dark_mode else QColor("#e8e8e8")
        widget.setIcon(render_material_symbol_icon(ligature, px, color))
        widget.setIconSize(QSize(px, px))
        return
    widget.setIcon(QIcon())


def render_material_symbol_icon(ligature: str, px: int, color: QColor) -> QIcon:
    font = QFont("Material Symbols Outlined")
    font.setPixelSize(px)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)

    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setPen(color)
    painter.setFont(font)
    painter.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, ligature)
    painter.end()
    return QIcon(pm)


def get_icon_path(icon_key: str, dark_mode: bool, use_theme: bool = True) -> Optional[Path]:
    assets_dir = Path(__file__).resolve().parents[1] / "public" / "img"
    theme_suffix = "dark" if dark_mode else "light"

    if use_theme:
        # Prefer explicit "-icon" or "-icon-<theme>" variants, then theme-specific svg/pngs, then generic names
        candidates = [
            f"{icon_key}-icon-{theme_suffix}.png",
            f"{icon_key}-icon-{theme_suffix}.svg",
            f"{icon_key}-icon.png",
            f"{icon_key}-icon.svg",
            f"{icon_key}-{theme_suffix}.svg",
            f"{icon_key}_{theme_suffix}.svg",
            f"{icon_key}.svg",
            f"{icon_key}-{theme_suffix}.png",
            f"{icon_key}_{theme_suffix}.png",
            f"{icon_key}.png",
        ]
        if not dark_mode:
            candidates = [
                f"{icon_key}_black.png",
                f"{icon_key}-black.png",
                *candidates,
            ]
    else:
        candidates = [f"{icon_key}.png", f"{icon_key}.svg"]

    for filename in candidates:
        icon_path = assets_dir / filename
        if icon_path.exists():
            return icon_path
    return None


def apply_app_font(app: QApplication) -> None:
    font_db = QFontDatabase()
    resources_dir = Path(__file__).resolve().parents[1] / "resources" / "fonts"

    pretendard_families: list[str] = []
    if "Pretendard" not in font_db.families() and "Pretendard Variable" not in font_db.families():
        font_path = resources_dir / "PretendardVariable.ttf"
        if font_path.exists():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            pretendard_families = QFontDatabase.applicationFontFamilies(font_id)

    if "Material Symbols Outlined" not in font_db.families():
        ms_path = resources_dir / "MaterialSymbolsOutlined.ttf"
        if ms_path.exists():
            QFontDatabase.addApplicationFont(str(ms_path))

    family = None
    # Prefer Pretendard first (reinforce app-wide), then fall back to Inter if necessary
    # If Pretendard is bundled in resources, prefer it explicitly
    if "Pretendard" in font_db.families():
        family = "Pretendard"
    elif "Pretendard Variable" in font_db.families():
        family = "Pretendard Variable"
    elif pretendard_families:
        # if we just loaded Pretendard from resources, use it
        family = pretendard_families[0]
    else:
        # fall back to Inter if present, else use current app font
        for cand in ("Inter", "Inter Variable"):
            if cand in font_db.families():
                family = cand
                break
        if not family:
            family = app.font().family()

    # Enforce Pretendard where possible by setting the application font explicitly
    base_font = QFont(family)
    base_font.setPointSize(11)
    app.setFont(base_font)
    try:
        # Also set a named Pretendard font explicitly if available to ensure stronger enforcement
        if "Pretendard" in font_db.families():
            app.setFont(QFont("Pretendard", 11))
    except Exception:
        pass


def ensure_material_icon_font() -> str:
    font_db = QFontDatabase()
    target_name = "Material Icons Round"
    if target_name in font_db.families():
        return target_name

    font_path = Path(__file__).resolve().parents[1] / "resources" / "fonts" / "MaterialSymbolsRounded.ttf"
    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return families[0]
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app.font().family()
    return "Arial"

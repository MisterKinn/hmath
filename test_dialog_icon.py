#!/usr/bin/env python3
"""Quick manual test for dialog icons (error & info) and HiDPI loader."""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from gui import design


def run_test():
    app = QApplication.instance() or QApplication(sys.argv)

    assets = Path(__file__).resolve().parents[1] / "public" / "img"
    # Error icon (should appear larger)
    err_icon = assets / "error-light.svg"
    dlg = design.create_styled_dialog(None, "실행 오류가 발생했습니다", "스크립트 생성 중 오류가 발생했습니다.\nAI returned no result", min_width=500, dark_mode=False, icon_path=str(err_icon))
    dlg.exec()

    # Info icon (normal size)
    info_icon = assets / "info-light.svg"
    dlg2 = design.create_styled_dialog(None, "정보", "이 메시지는 정보용입니다.", min_width=420, dark_mode=False, icon_path=str(info_icon))
    dlg2.exec()


if __name__ == "__main__":
    run_test()

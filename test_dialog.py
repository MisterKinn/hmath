#!/usr/bin/env python3
"""Test dialog styling."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

def test_button_style():
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Test styled message box
    msg = QMessageBox()
    msg.setWindowTitle("Test Dialog")
    msg.setText("This is a test dialog with styled button")
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    
    # Apply button style
    button_style = """
        QPushButton {
            background-color: #5377f6;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 32px;
            font-size: 14px;
            font-weight: 600;
            min-width: 100px;
            min-height: 36px;
        }
        QPushButton:hover {
            background-color: #3e5fc7;
        }
        QPushButton:pressed {
            background-color: #2e47a0;
        }
    """
    msg.setStyleSheet(button_style)
    
    print("Showing dialog with blue button...")
    msg.exec()
    print("Dialog closed")

if __name__ == "__main__":
    test_button_style()

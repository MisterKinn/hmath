#!/usr/bin/env python3
"""Test AI dialog button functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Qt

def test_ai_dialog():
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Simulate the AI input dialog
    dialog = QMessageBox()
    dialog.setWindowTitle("🤖 AI Script Generator")
    dialog.setIcon(QMessageBox.Icon.NoIcon)
    dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
    
    # Create main content widget
    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(20, 20, 20, 20)
    content_layout.setSpacing(20)
    
    # Description label
    desc_label = QLabel("Test AI dialog with clickable buttons")
    desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    content_layout.addWidget(desc_label)
    
    # Create input container
    input_container = QWidget()
    input_container.setObjectName("input-container")
    input_container.setStyleSheet("""
        QWidget#input-container {
            background-color: #1a1a1a;
            border: 1px solid #4a4a4a;
            border-radius: 12px;
        }
    """)
    input_layout = QVBoxLayout(input_container)
    input_layout.setContentsMargins(16, 16, 16, 16)
    input_layout.setSpacing(12)
    
    # Input field
    input_field = QTextEdit()
    input_field.setMinimumHeight(120)
    input_field.setMinimumWidth(400)
    input_field.setMaximumHeight(200)
    input_field.setPlaceholderText("Enter text here...")
    input_layout.addWidget(input_field)
    
    # Button row
    button_row = QHBoxLayout()
    button_row.setContentsMargins(0, 0, 0, 0)
    button_row.setSpacing(12)
    button_row.addStretch()
    
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setStyleSheet("""
        QPushButton {
            background-color: #666;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 24px;
            font-size: 13px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #888;
        }
    """)
    cancel_btn.setMaximumWidth(80)
    cancel_btn.setMinimumHeight(32)
    
    ok_btn = QPushButton("OK")
    ok_btn.setStyleSheet("""
        QPushButton {
            background-color: #5377f6;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 24px;
            font-size: 13px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #3e5fc7;
        }
    """)
    ok_btn.setMaximumWidth(80)
    ok_btn.setMinimumHeight(32)
    
    button_row.addWidget(cancel_btn)
    button_row.addWidget(ok_btn)
    input_layout.addLayout(button_row)
    
    content_layout.addWidget(input_container)
    
    # Add to dialog
    dialog_layout = dialog.layout()
    if dialog_layout:
        dialog_layout.addWidget(content_widget)
    
    # Handle button clicks
    ok_clicked = False
    def on_ok():
        nonlocal ok_clicked
        ok_clicked = True
        print(f"OK clicked! Text: {input_field.toPlainText()}")
        dialog.close()
    
    def on_cancel():
        nonlocal ok_clicked
        ok_clicked = False
        print("Cancel clicked!")
        dialog.close()
    
    ok_btn.clicked.connect(on_ok)
    cancel_btn.clicked.connect(on_cancel)
    
    print("Showing dialog...")
    dialog.exec()
    print(f"Dialog closed. OK clicked: {ok_clicked}")

if __name__ == "__main__":
    test_ai_dialog()

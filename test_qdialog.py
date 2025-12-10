#!/usr/bin/env python3
"""Test QDialog-based AI input dialog."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Qt

def test_qdialog_input():
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create QDialog (not QMessageBox)
    dialog = QDialog()
    dialog.setWindowTitle("🤖 AI Script Generator")
    dialog.setModal(True)
    
    # Set dialog background
    dialog.setStyleSheet("""
        QDialog {
            background-color: #000000;
        }
    """)
    
    # Create main layout
    main_layout = QVBoxLayout(dialog)
    main_layout.setContentsMargins(20, 20, 20, 20)
    main_layout.setSpacing(20)
    
    # Description label
    desc_label = QLabel("Test QDialog with clickable buttons\nClick OK or Cancel to test")
    desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    desc_label.setWordWrap(True)
    desc_label.setStyleSheet("""
        QLabel {
            color: #e8e8e8;
            font-size: 13px;
        }
    """)
    main_layout.addWidget(desc_label)
    
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
    input_field.setStyleSheet("""
        QTextEdit {
            background-color: transparent;
            color: #e8e8e8;
            border: none;
            font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
        }
    """)
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
        QPushButton:pressed {
            background-color: #2e47a0;
        }
    """)
    ok_btn.setMaximumWidth(80)
    ok_btn.setMinimumHeight(32)
    
    button_row.addWidget(cancel_btn)
    button_row.addWidget(ok_btn)
    input_layout.addLayout(button_row)
    
    main_layout.addWidget(input_container)
    
    # Handle button clicks
    ok_clicked = False
    def on_ok():
        nonlocal ok_clicked
        print(f"✅ OK clicked! Text: '{input_field.toPlainText()}'")
        ok_clicked = True
        dialog.accept()
    
    def on_cancel():
        nonlocal ok_clicked
        print("❌ Cancel clicked!")
        ok_clicked = False
        dialog.reject()
    
    ok_btn.clicked.connect(on_ok)
    cancel_btn.clicked.connect(on_cancel)
    
    print("📋 Showing QDialog...")
    result = dialog.exec()
    print(f"🔚 Dialog closed. Result code: {result}, OK clicked: {ok_clicked}")
    
    return input_field.toPlainText(), ok_clicked

if __name__ == "__main__":
    text, ok = test_qdialog_input()
    print(f"\n📝 Final result: Text='{text}', OK={ok}")

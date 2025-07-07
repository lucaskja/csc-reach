"""
Message preview dialog for CSC-Reach.
Shows formatted preview of messages with proper sizing.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..core.i18n_manager import tr


class PreviewDialog(QDialog):
    """
    Dialog for previewing messages with proper formatting and sizing.
    """
    
    def __init__(self, customer_name: str, preview_content: str, parent=None):
        super().__init__(parent)
        self.customer_name = customer_name
        self.preview_content = preview_content
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(tr("preview_message"))
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel(f"Preview for: {self.customer_name}")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header_label)
        
        # Preview content area
        self.preview_text = QTextEdit()
        self.preview_text.setPlainText(self.preview_content)
        self.preview_text.setReadOnly(True)
        
        # Set font for better readability
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Monaco", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        self.preview_text.setFont(font)
        
        # Style the preview area with explicit text color
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                line-height: 1.4;
                selection-background-color: #3498db;
                selection-color: #ffffff;
            }
        """)
        
        layout.addWidget(self.preview_text)
        
        # Button area
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton(tr("close"))
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        close_btn.setMinimumWidth(100)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def set_preview_content(self, content: str):
        """Update the preview content."""
        self.preview_content = content
        self.preview_text.setPlainText(content)

# ui/custom_message_box.py
"""
Custom message box dialog with custom title bar.
Replaces QMessageBox with styled version matching GeoWizard theme.
"""

from PySide6.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.custom_dialog import CustomDialog


class CustomMessageBox(CustomDialog):
    """Custom message box with custom title bar."""
    
    # Message types
    Information = 0
    Warning = 1
    Critical = 2
    Question = 3
    
    # Standard buttons
    Ok = 0x00000400
    Cancel = 0x00400000
    Yes = 0x00004000
    No = 0x00010000
    
    def __init__(self, parent=None, title="", message="", message_type=Information, buttons=Ok):
        super().__init__(title, parent, show_logo=True)
        
        self.message_type = message_type
        self.buttons_flags = buttons
        self.clicked_button = None
        
        self.resize(450, 200)
        
        # Aplicar tema
        if parent and hasattr(parent, '_modo_oscuro'):
            self.set_dark_mode(parent._modo_oscuro)
        
        self._create_ui(title, message)
    
    def _create_ui(self, title, message):
        """Create the message box UI."""
        # Icon and message layout
        content_hbox = QHBoxLayout()
        
        # Icon
        icon_label = QLabel()
        icon_label.setStyleSheet(f"font-size: 48px;")
        icon_label.setText(self._get_icon_emoji())
        content_hbox.addWidget(icon_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 11pt;")
        message_label.setTextFormat(Qt.RichText)
        message_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        message_label.setOpenExternalLinks(True)
        content_hbox.addWidget(message_label, 1)
        
        self.content_layout.addLayout(content_hbox)
        self.content_layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if self.buttons_flags & self.Yes:
            btn = QPushButton("Sí")
            btn.clicked.connect(lambda: self._on_button_click(self.Yes))
            btn.setMinimumWidth(80)
            button_layout.addWidget(btn)
        
        if self.buttons_flags & self.No:
            btn = QPushButton("No")
            btn.clicked.connect(lambda: self._on_button_click(self.No))
            btn.setMinimumWidth(80)
            button_layout.addWidget(btn)
        
        if self.buttons_flags & self.Ok:
            btn = QPushButton("Aceptar")
            btn.setDefault(True)
            btn.clicked.connect(lambda: self._on_button_click(self.Ok))
            btn.setMinimumWidth(80)
            button_layout.addWidget(btn)
        
        if self.buttons_flags & self.Cancel:
            btn = QPushButton("Cancelar")
            btn.clicked.connect(lambda: self._on_button_click(self.Cancel))
            btn.setMinimumWidth(80)
            button_layout.addWidget(btn)
        
        self.content_layout.addLayout(button_layout)
    
    def _get_icon_emoji(self):
        """Get emoji icon based on message type."""
        if self.message_type == self.Information:
            return "ℹ️"
        elif self.message_type == self.Warning:
            return "⚠️"
        elif self.message_type == self.Critical:
            return "❌"
        elif self.message_type == self.Question:
            return "❓"
        return "ℹ️"
    
    def _on_button_click(self, button_type):
        """Handle button click."""
        self.clicked_button = button_type
        if button_type in (self.Ok, self.Yes):
            self.accept()
        else:
            self.reject()
    
    def result_button(self):
        """Get which button was clicked."""
        return self.clicked_button
    
    @staticmethod
    def information(parent, title, message):
        """Show information message box."""
        dialog = CustomMessageBox(parent, title, message, CustomMessageBox.Information, CustomMessageBox.Ok)
        dialog.exec()
        return dialog.result_button()
    
    @staticmethod
    def warning(parent, title, message):
        """Show warning message box."""
        dialog = CustomMessageBox(parent, title, message, CustomMessageBox.Warning, CustomMessageBox.Ok)
        dialog.exec()
        return dialog.result_button()
    
    @staticmethod
    def critical(parent, title, message):
        """Show critical message box."""
        dialog = CustomMessageBox(parent, title, message, CustomMessageBox.Critical, CustomMessageBox.Ok)
        dialog.exec()
        return dialog.result_button()
    
    @staticmethod
    def question(parent, title, message, buttons=None):
        """Show question message box."""
        if buttons is None:
            buttons = CustomMessageBox.Yes | CustomMessageBox.No
        dialog = CustomMessageBox(parent, title, message, CustomMessageBox.Question, buttons)
        dialog.exec()
        return dialog.result_button()

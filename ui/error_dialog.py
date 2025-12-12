"""
Styled error dialog for GeoWizard application.

Provides a user-friendly error display with title, message,
suggestions, and expandable technical details.
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit
)
from PySide6.QtGui import QFont
from ui.custom_dialog import CustomDialog


class ErrorDialog(CustomDialog):
    """
    Styled error dialog with user-friendly messages and suggestions.
    """
    
    def __init__(self, parent=None, error_info: dict = None):
        self.error_info = error_info or {}
        title = self.error_info.get('title', 'Error')
        
        super().__init__(title, parent, show_logo=True)
        
        self.resize(500, 400)
        
        # Aplicar tema si el parent tiene _modo_oscuro
        if parent and hasattr(parent, '_modo_oscuro'):
            self.set_dark_mode(parent._modo_oscuro)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the dialog UI."""
        # Usar content_layout heredado de CustomDialog
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        # Error icon (using emoji as fallback)
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(self.error_info.get('title', 'Error'))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.content_layout.addLayout(header_layout)
        
        # Message
        message_label = QLabel(self.error_info.get('message', 'Ocurrió un error.'))
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 11pt; margin: 10px 0;")
        self.content_layout.addWidget(message_label)
        
        # Suggestions
        suggestions = self.error_info.get('suggestions', [])
        if suggestions:
            suggestions_label = QLabel("<b>Sugerencias:</b>")
            suggestions_label.setStyleSheet("font-size: 10pt; margin-top: 10px;")
            self.content_layout.addWidget(suggestions_label)
            
            for suggestion in suggestions:
                suggestion_label = QLabel(f"• {suggestion}")
                suggestion_label.setWordWrap(True)
                suggestion_label.setStyleSheet("font-size: 10pt; margin-left: 20px;")
                self.content_layout.addWidget(suggestion_label)
        
        # Technical details (expandable)
        details = self.error_info.get('details')
        if details:
            self.content_layout.addSpacing(10)
            
            # Details toggle button
            self.details_button = QPushButton("Mostrar detalles técnicos")
            self.details_button.setCheckable(True)
            self.details_button.clicked.connect(self._toggle_details)
            self.content_layout.addWidget(self.details_button)
            
            # Details text (initially hidden)
            self.details_text = QTextEdit()
            self.details_text.setPlainText(str(details))
            self.details_text.setReadOnly(True)
            self.details_text.setMaximumHeight(150)
            self.details_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f5f5f5;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    padding: 5px;
                    font-family: monospace;
                    font-size: 9pt;
                }
            """)
            self.details_text.hide()
            self.content_layout.addWidget(self.details_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("Aceptar")
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)
        ok_button.setMinimumWidth(100)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        button_layout.addWidget(ok_button)
        
        self.content_layout.addSpacing(10)
        self.content_layout.addLayout(button_layout)
    
    def _toggle_details(self):
        """Toggle technical details visibility."""
        if self.details_text.isVisible():
            self.details_text.hide()
            self.details_button.setText("Mostrar detalles técnicos")
        else:
            self.details_text.show()
            self.details_button.setText("Ocultar detalles técnicos")


def show_error_dialog(parent, exception: Exception, error_info: dict = None):
    """
    Show error dialog for an exception.
    
    Args:
        parent: Parent widget
        exception: The exception that occurred
        error_info: Pre-computed error info (optional)
    
    Returns:
        Dialog result
    """
    if error_info is None:
        from utils.error_messages import get_error_message
        error_info = get_error_message(exception)
    
    dialog = ErrorDialog(parent, error_info)
    return dialog.exec()

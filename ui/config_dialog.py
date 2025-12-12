# ui/config_dialog.py
"""
Settings/Configuration dialog for GeoWizard.
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QComboBox, QGroupBox
from PySide6.QtCore import Qt, Signal
from ui.custom_dialog import CustomDialog
from utils.translations import tr, set_language, get_current_language


class ConfigDialog(CustomDialog):
    """Configuration dialog for application settings."""
    
    language_changed = Signal(str)  # Emits when language changes
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(tr("config_title"), parent, show_logo=True)
        
        self.current_settings = current_settings or {}
        self.resize(500, 400)
        
        # Aplicar tema
        if parent and hasattr(parent, '_modo_oscuro'):
            self.set_dark_mode(parent._modo_oscuro)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the settings UI."""
        
        # Appearance group
        appearance_group = QGroupBox(tr("appearance"))
        appearance_layout = QVBoxLayout()
        
        # Dark mode toggle
        self.chk_dark_mode = QCheckBox(tr("dark_mode"))
        self.chk_dark_mode.setChecked(self.current_settings.get('dark_mode', False))
        appearance_layout.addWidget(self.chk_dark_mode)
        
        appearance_group.setLayout(appearance_layout)
        self.content_layout.addWidget(appearance_group)
        
        # General settings group
        general_group = QGroupBox(tr("general"))
        general_layout = QVBoxLayout()
        
        # Language selector
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel(tr("language")))
        self.cb_language = QComboBox()
        self.cb_language.addItems([tr("spanish"), tr("english")])
        # Set current language
        current_lang = get_current_language()
        if current_lang == "en":
            self.cb_language.setCurrentIndex(1)
        else:
            self.cb_language.setCurrentIndex(0)
        lang_layout.addWidget(self.cb_language)
        general_layout.addLayout(lang_layout)
        
        # Auto-save toggle
        self.chk_autosave = QCheckBox(tr("autosave"))
        self.chk_autosave.setChecked(self.current_settings.get('autosave', True))
        general_layout.addWidget(self.chk_autosave)
        
        general_group.setLayout(general_layout)
        self.content_layout.addWidget(general_group)
        
        # Spacer
        self.content_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        btn_save = QPushButton(tr("save_btn"))
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._on_save)
        button_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton(tr("cancel"))
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        self.content_layout.addLayout(button_layout)
    
    def _on_save(self):
        """Handle save button click."""
        # Get selected language
        lang_text = self.cb_language.currentText()
        new_lang = "en" if "English" in lang_text else "es"
        old_lang = get_current_language()
        
        # Change language if different
        if new_lang != old_lang:
            set_language(new_lang)
            self.language_changed.emit(new_lang)
        
        self.accept()
    
    def get_settings(self):
        """Get the current settings from the dialog."""
        return {
            'dark_mode': self.chk_dark_mode.isChecked(),
            'autosave': self.chk_autosave.isChecked(),
            'language': self.cb_language.currentText()
        }
    
    def get_values(self):
        """Alias for get_settings for compatibility."""
        return self.get_settings()

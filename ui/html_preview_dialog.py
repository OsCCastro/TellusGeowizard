# ui/html_preview_dialog.py
"""
Diálogo de previsualización para tablas HTML de coordenadas.
Permite copiar HTML completo o formato simplificado para Word.
"""

import re
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtWidgets import (
    QVBoxLayout, QToolBar, QTextBrowser,
    QMessageBox, QApplication
)
from PySide6.QtGui import QAction, QIcon
from ui.custom_dialog import CustomDialog
from ui.html_table_config_dialog import HTMLTableConfigDialog, HTMLTableSettings


class HTMLPreviewDialog(CustomDialog):
    """Diálogo para previsualizar y copiar tablas HTML."""
    
    def __init__(self, main_window, parent=None):
        super().__init__("Previsualización de Tabla HTML", parent, show_logo=True)
        self.main_window = main_window
        self.current_html = ""
        
        # Ajustar tamaño inicial
        self.resize(360, 600)  # 55% más pequeño en ancho (era 800)
        
        # Aplicar tema del main window
        if hasattr(main_window, '_modo_oscuro'):
            self.set_dark_mode(main_window._modo_oscuro)
        
        self._create_ui()
        self._generate_table()
    
    def _create_ui(self):
        """Construye la interfaz del diálogo."""
        # Usar el content_layout heredado de CustomDialog
        
        # Toolbar
        toolbar = self._create_toolbar()
        self.content_layout.addWidget(toolbar)
        
        # Vista previa
        self.preview_browser = QTextBrowser()
        self.preview_browser.setOpenExternalLinks(False)
        self.content_layout.addWidget(self.preview_browser)
    
    def _create_toolbar(self):
        """Crea la barra de herramientas."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        # Botón Configuración
        action_config = QAction("⚙️ Configuración", self)
        action_config.setToolTip("Abrir configuración de tabla")
        # Intentar cargar icono, sino usar emoji
        try:
            icon = self.main_window._icono("settings-2-fill.svg")
            action_config.setIcon(icon)
        except:
            pass
        action_config.triggered.connect(self._open_config_dialog)
        toolbar.addAction(action_config)
        
        toolbar.addSeparator()
        
        # Botón Copiar HTML
        action_copy_html = QAction("📋 Copiar HTML", self)
        action_copy_html.setToolTip("Copiar código HTML completo al portapapeles")
        try:
            icon = self.main_window._icono("code-box-fill.svg")
            action_copy_html.setIcon(icon)
        except:
            pass
        action_copy_html.triggered.connect(self._copy_html)
        toolbar.addAction(action_copy_html)
        
        # Botón Copiar con Formato
        action_copy_formatted = QAction("📋 Copiar con Formato", self)
        action_copy_formatted.setToolTip("Copiar tabla formateada para pegar en Word, Excel, etc.")
        try:
            icon = self.main_window._icono("Copy.svg")
            action_copy_formatted.setIcon(icon)
        except:
            pass
        action_copy_formatted.triggered.connect(self._copy_formatted)
        toolbar.addAction(action_copy_formatted)
        
        return toolbar
    
    def _generate_table(self):
        """Genera la tabla HTML con la configuración actual."""
        try:
            settings = HTMLTableSettings.load()
            self.current_html = self.main_window._generate_coordinates_html_table(settings)
            self._update_preview(self.current_html)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error al generar tabla",
                f"No se pudo generar la tabla HTML:\\n{str(e)}"
            )
    
    def _update_preview(self, html_content):
        """Actualiza la vista previa con el contenido HTML."""
        self.current_html = html_content
        # Envolver el contenido en un div centrado
        centered_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    display: flex;
                    justify-content: center;
                    align-items: flex-start;
                    padding: 20px;
                    margin: 0;
                }}
                .container {{
                    max-width: 100%;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {html_content}
            </div>
        </body>
        </html>
        """
        self.preview_browser.setHtml(centered_html)
    
    def _copy_html(self):
        """Copia el código HTML completo al portapapeles."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_html)
        
        # Mostrar mensaje temporal
        QMessageBox.information(
            self,
            "HTML Copiado",
            "El código HTML ha sido copiado al portapapeles.",
            QMessageBox.Ok
        )
    
    
    def _copy_formatted(self):
        """Copia la tabla en formato rico (HTML) al portapapeles."""
        # Crear MimeData con formato HTML
        mime_data = QMimeData()
        mime_data.setHtml(self.current_html)
        # También incluir texto plano como respaldo
        mime_data.setText(self.current_html)
        
        # Establecer en clipboard
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)
        
        # Mostrar mensaje
        QMessageBox.information(
            self,
            "Tabla Copiada",
            "La tabla ha sido copiada con formato.\\n\\n"
            "Puedes pegarla directamente en Word, Excel, o cualquier editor usando Ctrl+V.",
            QMessageBox.Ok
        )
    
    
    def _open_config_dialog(self):
        """Abre el diálogo de configuración."""
        config_dialog = HTMLTableConfigDialog(self.main_window, self)
        config_dialog.settingsChanged.connect(self._on_settings_changed)
        config_dialog.exec()
    
    def _on_settings_changed(self, settings):
        """Llamado cuando la configuración cambia."""
        # Regenerar tabla con nueva configuración
        try:
            self.current_html = self.main_window._generate_coordinates_html_table(settings)
            self._update_preview(self.current_html)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error al regenerar tabla",
                f"No se pudo regenerar la tabla con la nueva configuración:\\n{str(e)}"
            )

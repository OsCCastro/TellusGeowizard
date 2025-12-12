# ui/help_dialog.py
"""
Help/About dialog for GeoWizard.
"""

from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QTextBrowser
from PySide6.QtCore import Qt
from ui.custom_dialog import CustomDialog
from utils.translations import tr


class HelpDialog(CustomDialog):
    """Help and about dialog."""
    
    def __init__(self, parent=None):
        super().__init__(tr("help_title"), parent, show_logo=True)
        
        self.resize(600, 500)
        
        # Aplicar tema
        if parent and hasattr(parent, '_modo_oscuro'):
            self.set_dark_mode(parent._modo_oscuro)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the help UI."""
        
        # Title
        title_label = QLabel(f"<h2>{tr('help_subtitle')}</h2>")
        title_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            f"<p><b>{tr('help_description')}</b></p>"
            f"<p>{tr('developed_by')} <b>{tr('tellus_name')}</b></p>"
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(desc_label)
        
        # Features
        features_text = f"""
        <h3>{tr('main_features')}</h3>
        <ul>
            <li>📍 Gestión de coordenadas en múltiples sistemas (UTM, Geográficas, Web Mercator)</li>
            <li>🗺️ Visualización en mapa interactivo OSM</li>
            <li>✏️ Edición de geometrías (Puntos, Polilíneas, Polígonos)</li>
            <li>📊 Cálculo de mediciones (Distancia, Área, Perímetro)</li>
            <li>💾 Exportación a KML, KMZ, Shapefile, CSV</li>
            <li>📥 Importación de KML, Shapefile, CSV</li>
            <li>🌐 Generación de tablas HTML personalizadas</li>
        </ul>
        
        <h3>{tr('contact_support')}</h3>
        <p>
        📧 Email: <a href='mailto:contacto@tellusconsultoria.com'>contacto@tellusconsultoria.com</a><br>
        📸 Facebook: <a href='https://www.facebook.com/TellusConsultoria'>Tellus Consultoría</a>
        </p>
        
        <h3>{tr('about_version')}</h3>
        <p>
        {tr('beta_message')}
        </p>
        
        <hr>
        <p style='text-align: center; color: #666;'>
        <i>{tr('copyright')}</i>
        </p>
        """
        
        help_text = QTextBrowser()
        help_text.setHtml(features_text)
        help_text.setOpenExternalLinks(True)
        self.content_layout.addWidget(help_text, 1)
        
        # Close button
        btn_close = QPushButton(tr("close"))
        btn_close.setDefault(True)
        btn_close.clicked.connect(self.accept)
        btn_close.setMinimumWidth(100)
        
        self.content_layout.addWidget(btn_close, 0, Qt.AlignCenter)

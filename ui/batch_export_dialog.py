# ui/batch_export_dialog.py
"""
Batch Export Dialog - Export to multiple formats in one operation.
"""

from typing import List, Optional
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QLineEdit, QFileDialog, QGroupBox, QProgressBar
)

from ui.custom_titlebar import CustomTitleBar
from utils.logger import get_logger

logger = get_logger(__name__)


class BatchExportDialog(QDialog):
    """
    Dialog for exporting coordinates to multiple formats at once.
    Supports: KML, KMZ, Shapefile, CSV
    """
    
    # Signal emitted with list of formats to export
    exportRequested = Signal(list, str)  # (formats, output_directory)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportación por Lotes")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)
        
        self._output_dir = ""
        self._build_ui()
    
    def _build_ui(self):
        """Build dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Custom title bar
        self.title_bar = CustomTitleBar("Exportación por Lotes", self)
        self.title_bar.closeClicked.connect(self.reject)
        self.title_bar.minimizeClicked.connect(self.showMinimized)
        layout.addWidget(self.title_bar)
        
        # Content
        content = QVBoxLayout()
        content.setContentsMargins(20, 20, 20, 20)
        content.setSpacing(15)
        
        # Description
        desc = QLabel(
            "Seleccione los formatos a exportar y el directorio de destino.\n"
            "Se crearán archivos con el mismo nombre base en cada formato."
        )
        desc.setWordWrap(True)
        content.addWidget(desc)
        
        # Format selection group
        format_group = QGroupBox("📁 Formatos de Exportación")
        format_layout = QVBoxLayout(format_group)
        
        self.chk_kml = QCheckBox("KML (Google Earth)")
        self.chk_kml.setChecked(True)
        format_layout.addWidget(self.chk_kml)
        
        self.chk_kmz = QCheckBox("KMZ (KML comprimido)")
        format_layout.addWidget(self.chk_kmz)
        
        self.chk_shp = QCheckBox("Shapefile (SHP)")
        self.chk_shp.setChecked(True)
        format_layout.addWidget(self.chk_shp)
        
        self.chk_csv = QCheckBox("CSV (Texto delimitado)")
        format_layout.addWidget(self.chk_csv)
        
        self.chk_gwz = QCheckBox("GWZ (Proyecto GeoWizard)")
        format_layout.addWidget(self.chk_gwz)
        
        content.addWidget(format_group)
        
        # Output directory selection
        dir_group = QGroupBox("📂 Directorio de Destino")
        dir_layout = QHBoxLayout(dir_group)
        
        self.txt_output_dir = QLineEdit()
        self.txt_output_dir.setPlaceholderText("Seleccione directorio de salida...")
        self.txt_output_dir.setReadOnly(True)
        dir_layout.addWidget(self.txt_output_dir)
        
        self.btn_browse = QPushButton("...")
        self.btn_browse.setFixedWidth(40)
        self.btn_browse.clicked.connect(self._browse_directory)
        dir_layout.addWidget(self.btn_browse)
        
        content.addWidget(dir_group)
        
        # File name base
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nombre base:"))
        self.txt_basename = QLineEdit()
        self.txt_basename.setPlaceholderText("coordenadas")
        self.txt_basename.setText("coordenadas")
        name_layout.addWidget(self.txt_basename)
        content.addLayout(name_layout)
        
        # Progress bar (hidden by default)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        content.addWidget(self.progress)
        
        # Status label
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: gray; font-style: italic;")
        content.addWidget(self.lbl_status)
        
        content.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_export = QPushButton("🚀 Exportar")
        self.btn_export.setStyleSheet("font-weight: bold;")
        self.btn_export.clicked.connect(self._on_export)
        btn_layout.addWidget(self.btn_export)
        
        content.addLayout(btn_layout)
        
        # Add content to main layout
        content_widget = QLabel()
        content_widget.setLayout(content)
        layout.addWidget(content_widget)
    
    def _browse_directory(self):
        """Open directory selection dialog."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Directorio de Exportación",
            self._output_dir or ""
        )
        if directory:
            self._output_dir = directory
            self.txt_output_dir.setText(directory)
    
    def _get_selected_formats(self) -> List[str]:
        """Get list of selected export formats."""
        formats = []
        if self.chk_kml.isChecked():
            formats.append("kml")
        if self.chk_kmz.isChecked():
            formats.append("kmz")
        if self.chk_shp.isChecked():
            formats.append("shp")
        if self.chk_csv.isChecked():
            formats.append("csv")
        if self.chk_gwz.isChecked():
            formats.append("gwz")
        return formats
    
    def _on_export(self):
        """Handle export button click."""
        from ui.custom_message_box import CustomMessageBox
        
        # Validate
        formats = self._get_selected_formats()
        if not formats:
            CustomMessageBox.warning(
                self,
                "Sin Formatos",
                "Seleccione al menos un formato de exportación."
            )
            return
        
        if not self._output_dir:
            CustomMessageBox.warning(
                self,
                "Sin Directorio",
                "Seleccione un directorio de destino."
            )
            return
        
        basename = self.txt_basename.text().strip() or "coordenadas"
        
        # Emit signal with export parameters
        self.exportRequested.emit(formats, self._output_dir)
        
        # Store for parent access
        self.selected_formats = formats
        self.output_directory = self._output_dir
        self.base_filename = basename
        
        self.accept()
    
    def set_progress(self, value: int, status: str = ""):
        """Update progress bar."""
        self.progress.setVisible(True)
        self.progress.setValue(value)
        if status:
            self.lbl_status.setText(status)
    
    def get_export_params(self) -> tuple:
        """
        Get export parameters after dialog is accepted.
        
        Returns:
            Tuple of (formats: list, directory: str, basename: str)
        """
        return (
            getattr(self, 'selected_formats', []),
            getattr(self, 'output_directory', ''),
            getattr(self, 'base_filename', 'coordenadas')
        )

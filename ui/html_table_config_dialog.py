# ui/html_table_config_dialog.py
"""
Diálogo de configuración para tablas HTML de coordenadas.
Permite personalizar bordes, colores, y formato de datos.
"""

from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QCheckBox, QSpinBox, QComboBox, QPushButton,
    QLabel, QTextBrowser, QColorDialog, QFrame
)
from PySide6.QtGui import QColor, QPalette
from ui.custom_dialog import CustomDialog


class HTMLTableSettings:
    """Clase para almacenar y gestionar configuración de tablas HTML."""
    
    # Paletas predefinidas
    PALETTES = {
        "Profesional": {
            "header_bg": "#2c3e50",
            "header_text": "#ffffff",
            "row_bg1": "#f8f9fa",
            "row_bg2": "#ffffff",
            "cell_text": "#000000"
        },
        "Oceánica": {
            "header_bg": "#1e88e5",
            "header_text": "#ffffff",
            "row_bg1": "#e3f2fd",
            "row_bg2": "#ffffff",
            "cell_text": "#000000"
        },
        "Terrestre": {
            "header_bg": "#2e7d32",
            "header_text": "#ffffff",
            "row_bg1": "#f1f8e9",
            "row_bg2": "#ffffff",
            "cell_text": "#000000"
        },
        "Personalizada": {
            "header_bg": "#2c3e50",
            "header_text": "#ffffff",
            "row_bg1": "#f8f9fa",
            "row_bg2": "#ffffff",
            "cell_text": "#000000"
        }
    }
    
    def __init__(self):
        """Inicializa con valores por defecto."""
        self.load_defaults()
    
    def load_defaults(self):
        """Carga valores por defecto."""
        # Bordes
        self.show_all_borders = True
        self.show_horizontal = False
        self.show_vertical = False
        self.show_outer = False
        self.border_width = 1
        
        # Colores
        self.color_palette = "Profesional"
        self.apply_palette("Profesional")
        
        # Formato
        self.bearing_format = "azimuth"  # "azimuth" o "quadrant"
        self.coord_decimals = 2
        self.bearing_decimals = 1
        self.use_thousands_separator = True  # Separador de miles
    
    def apply_palette(self, palette_name):
        """Aplica una paleta predefinida."""
        if palette_name in self.PALETTES:
            palette = self.PALETTES[palette_name]
            self.header_bg_color = palette["header_bg"]
            self.header_text_color = palette["header_text"]
            self.row_bg_color1 = palette["row_bg1"]
            self.row_bg_color2 = palette["row_bg2"]
            self.cell_text_color = palette["cell_text"]
            self.color_palette = palette_name
    
    def save(self):
        """Guarda configuración en QSettings."""
        settings = QSettings("TellusConsultoria", "GeoWizard")
        settings.beginGroup("HTMLTableExport")
        
        # Bordes
        settings.setValue("show_all_borders", self.show_all_borders)
        settings.setValue("show_horizontal", self.show_horizontal)
        settings.setValue("show_vertical", self.show_vertical)
        settings.setValue("show_outer", self.show_outer)
        settings.setValue("border_width", self.border_width)
        
        # Colores
        settings.setValue("color_palette", self.color_palette)
        settings.setValue("header_bg_color", self.header_bg_color)
        settings.setValue("header_text_color", self.header_text_color)
        settings.setValue("row_bg_color1", self.row_bg_color1)
        settings.setValue("row_bg_color2", self.row_bg_color2)
        settings.setValue("cell_text_color", self.cell_text_color)
        
        # Formato
        settings.setValue("bearing_format", self.bearing_format)
        settings.setValue("coord_decimals", self.coord_decimals)
        settings.setValue("bearing_decimals", self.bearing_decimals)
        settings.setValue("use_thousands_separator", self.use_thousands_separator)
        
        settings.endGroup()
    
    @staticmethod
    def load():
        """Carga configuración desde QSettings."""
        instance = HTMLTableSettings()
        settings = QSettings("TellusConsultoria", "GeoWizard")
        settings.beginGroup("HTMLTableExport")
        
        # Bordes
        instance.show_all_borders = settings.value("show_all_borders", True, type=bool)
        instance.show_horizontal = settings.value("show_horizontal", False, type=bool)
        instance.show_vertical = settings.value("show_vertical", False, type=bool)
        instance.show_outer = settings.value("show_outer", False, type=bool)
        instance.border_width = settings.value("border_width", 1, type=int)
        
        # Colores
        instance.color_palette = settings.value("color_palette", "Profesional", type=str)
        instance.header_bg_color = settings.value("header_bg_color", "#2c3e50", type=str)
        instance.header_text_color = settings.value("header_text_color", "#ffffff", type=str)
        instance.row_bg_color1 = settings.value("row_bg_color1", "#f8f9fa", type=str)
        instance.row_bg_color2 = settings.value("row_bg_color2", "#ffffff", type=str)
        instance.cell_text_color = settings.value("cell_text_color", "#000000", type=str)
        
        # Formato
        instance.bearing_format = settings.value("bearing_format", "azimuth", type=str)
        instance.coord_decimals = settings.value("coord_decimals", 2, type=int)
        instance.bearing_decimals = settings.value("bearing_decimals", 1, type=int)
        instance.use_thousands_separator = settings.value("use_thousands_separator", True, type=bool)
        
        settings.endGroup()
        return instance
    
    def to_dict(self):
        """Serializa a diccionario."""
        return {
            "show_all_borders": self.show_all_borders,
            "show_horizontal": self.show_horizontal,
            "show_vertical": self.show_vertical,
            "show_outer": self.show_outer,
            "border_width": self.border_width,
            "color_palette": self.color_palette,
            "header_bg_color": self.header_bg_color,
            "header_text_color": self.header_text_color,
            "row_bg_color1": self.row_bg_color1,
            "row_bg_color2": self.row_bg_color2,
            "cell_text_color": self.cell_text_color,
            "bearing_format": self.bearing_format,
            "coord_decimals": self.coord_decimals,
            "bearing_decimals": self.bearing_decimals,
            "use_thousands_separator": self.use_thousands_separator
        }


class HTMLTableConfigDialog(CustomDialog):
    """Diálogo para configurar tablas HTML."""
    
    settingsChanged = Signal(HTMLTableSettings)
    
    def __init__(self, parent_window, parent=None):
        super().__init__("Configuración de Tabla HTML", parent, show_logo=True)
        self.parent_window = parent_window
        self.settings = HTMLTableSettings.load()
        
        # Ajustar tamaño
        self.resize(315, 600)  # 55% más pequeño en ancho (era 700)
        
        # Aplicar tema del parent window
        if hasattr(parent_window, '_modo_oscuro'):
            self.set_dark_mode(parent_window._modo_oscuro)
        
        self._create_ui()
        self._load_current_settings()
    
    def _create_ui(self):
        """Construye la interfaz del diálogo."""
        # Usar content_layout heredado de CustomDialog
        
        # Pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self._create_borders_tab(), "Bordes y Líneas")
        self.tab_widget.addTab(self._create_colors_tab(), "Colores y Estilos")
        self.tab_widget.addTab(self._create_format_tab(), "Formato de Datos")
        self.content_layout.addWidget(self.tab_widget)
        
        # Previsualización
        preview_group = QGroupBox("Vista Previa")
        preview_layout = QVBoxLayout()
        
        self.chk_realtime = QCheckBox("Previsualización en tiempo real")
        self.chk_realtime.setChecked(False)
        self.chk_realtime.toggled.connect(self._on_realtime_toggled)
        preview_layout.addWidget(self.chk_realtime)
        
        self.preview_browser = QTextBrowser()
        self.preview_browser.setMinimumHeight(200)
        self.preview_browser.setEnabled(False)
        preview_layout.addWidget(self.preview_browser)
        
        preview_group.setLayout(preview_layout)
        self.content_layout.addWidget(preview_group)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_save = QPushButton("Guardar Configuración")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._on_save)
        buttons_layout.addWidget(btn_save)
        
        btn_restore = QPushButton("Restaurar Valores por Defecto")
        btn_restore.clicked.connect(self._on_restore_defaults)
        buttons_layout.addWidget(btn_restore)
        
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_close)
        
        self.content_layout.addLayout(buttons_layout)
    
    def _create_borders_tab(self):
        """Crea la pestaña de configuración de bordes."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tipo de bordes
        borders_group = QGroupBox("Tipo de Bordes")
        borders_layout = QVBoxLayout()
        
        self.chk_all_borders = QCheckBox("Todos los bordes")
        self.chk_all_borders.toggled.connect(self._on_border_option_changed)
        borders_layout.addWidget(self.chk_all_borders)
        
        self.chk_horizontal = QCheckBox("Solo líneas horizontales")
        self.chk_horizontal.toggled.connect(self._on_border_option_changed)
        borders_layout.addWidget(self.chk_horizontal)
        
        self.chk_vertical = QCheckBox("Solo líneas verticales")
        self.chk_vertical.toggled.connect(self._on_border_option_changed)
        borders_layout.addWidget(self.chk_vertical)
        
        self.chk_outer = QCheckBox("Solo borde exterior")
        self.chk_outer.toggled.connect(self._on_border_option_changed)
        borders_layout.addWidget(self.chk_outer)
        
        borders_group.setLayout(borders_layout)
        layout.addWidget(borders_group)
        
        # Grosor
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Grosor de borde:"))
        self.spin_border_width = QSpinBox()
        self.spin_border_width.setRange(1, 5)
        self.spin_border_width.setSuffix(" px")
        self.spin_border_width.valueChanged.connect(self._on_setting_changed)
        width_layout.addWidget(self.spin_border_width)
        width_layout.addStretch()
        layout.addLayout(width_layout)
        
        layout.addStretch()
        return widget
    
    def _create_colors_tab(self):
        """Crea la pestaña de configuración de colores."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Paleta predefinida
        palette_layout = QHBoxLayout()
        palette_layout.addWidget(QLabel("Paleta predefinida:"))
        self.combo_palette = QComboBox()
        self.combo_palette.addItems(["Profesional", "Oceánica", "Terrestre", "Personalizada"])
        self.combo_palette.currentTextChanged.connect(self._on_palette_changed)
        palette_layout.addWidget(self.combo_palette)
        palette_layout.addStretch()
        layout.addLayout(palette_layout)
        
        # Colores del encabezado
        header_group = QGroupBox("Colores del Encabezado")
        header_layout = QVBoxLayout()
        
        header_bg_layout = QHBoxLayout()
        self.btn_header_bg = QPushButton("Color de fondo")
        self.btn_header_bg.clicked.connect(lambda: self._on_color_button_clicked("header_bg"))
        header_bg_layout.addWidget(self.btn_header_bg)
        self.lbl_header_bg_preview = QLabel()
        self.lbl_header_bg_preview.setFixedSize(50, 25)
        self.lbl_header_bg_preview.setFrameStyle(QFrame.Box | QFrame.Plain)
        header_bg_layout.addWidget(self.lbl_header_bg_preview)
        header_bg_layout.addStretch()
        header_layout.addLayout(header_bg_layout)
        
        header_text_layout = QHBoxLayout()
        self.btn_header_text = QPushButton("Color de texto")
        self.btn_header_text.clicked.connect(lambda: self._on_color_button_clicked("header_text"))
        header_text_layout.addWidget(self.btn_header_text)
        self.lbl_header_text_preview = QLabel()
        self.lbl_header_text_preview.setFixedSize(50, 25)
        self.lbl_header_text_preview.setFrameStyle(QFrame.Box | QFrame.Plain)
        header_text_layout.addWidget(self.lbl_header_text_preview)
        header_text_layout.addStretch()
        header_layout.addLayout(header_text_layout)
        
        header_group.setLayout(header_layout)
        layout.addWidget(header_group)
        
        # Colores de filas
        rows_group = QGroupBox("Colores de Filas")
        rows_layout = QVBoxLayout()
        
        row1_layout = QHBoxLayout()
        self.btn_row1 = QPushButton("Color fila 1 (alterna)")
        self.btn_row1.clicked.connect(lambda: self._on_color_button_clicked("row_bg1"))
        row1_layout.addWidget(self.btn_row1)
        self.lbl_row1_preview = QLabel()
        self.lbl_row1_preview.setFixedSize(50, 25)
        self.lbl_row1_preview.setFrameStyle(QFrame.Box | QFrame.Plain)
        row1_layout.addWidget(self.lbl_row1_preview)
        row1_layout.addStretch()
        rows_layout.addLayout(row1_layout)
        
        row2_layout = QHBoxLayout()
        self.btn_row2 = QPushButton("Color fila 2 (alterna)")
        self.btn_row2.clicked.connect(lambda: self._on_color_button_clicked("row_bg2"))
        row2_layout.addWidget(self.btn_row2)
        self.lbl_row2_preview = QLabel()
        self.lbl_row2_preview.setFixedSize(50, 25)
        self.lbl_row2_preview.setFrameStyle(QFrame.Box | QFrame.Plain)
        row2_layout.addWidget(self.lbl_row2_preview)
        row2_layout.addStretch()
        rows_layout.addLayout(row2_layout)
        
        cell_text_layout = QHBoxLayout()
        self.btn_cell_text = QPushButton("Color de texto")
        self.btn_cell_text.clicked.connect(lambda: self._on_color_button_clicked("cell_text"))
        cell_text_layout.addWidget(self.btn_cell_text)
        self.lbl_cell_text_preview = QLabel()
        self.lbl_cell_text_preview.setFixedSize(50, 25)
        self.lbl_cell_text_preview.setFrameStyle(QFrame.Box | QFrame.Plain)
        cell_text_layout.addWidget(self.lbl_cell_text_preview)
        cell_text_layout.addStretch()
        rows_layout.addLayout(cell_text_layout)
        
        rows_group.setLayout(rows_layout)
        layout.addWidget(rows_group)
        
        layout.addStretch()
        return widget
    
    def _create_format_tab(self):
        """Crea la pestaña de configuración de formato."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Formato de rumbo
        bearing_layout = QHBoxLayout()
        bearing_layout.addWidget(QLabel("Formato de Rumbo:"))
        self.combo_bearing = QComboBox()
        self.combo_bearing.addItems(["Azimut (0-360°)", "Cuadrante (N 45° E)"])
        self.combo_bearing.currentIndexChanged.connect(self._on_setting_changed)
        bearing_layout.addWidget(self.combo_bearing)
        bearing_layout.addStretch()
        layout.addLayout(bearing_layout)
        
        # Decimales en coordenadas
        coord_dec_layout = QHBoxLayout()
        coord_dec_layout.addWidget(QLabel("Decimales en coordenadas:"))
        self.spin_coord_decimals = QSpinBox()
        self.spin_coord_decimals.setRange(0, 6)
        self.spin_coord_decimals.valueChanged.connect(self._on_setting_changed)
        coord_dec_layout.addWidget(self.spin_coord_decimals)
        coord_dec_layout.addStretch()
        layout.addLayout(coord_dec_layout)
        
        # Decimales en rumbos
        bearing_dec_layout = QHBoxLayout()
        bearing_dec_layout.addWidget(QLabel("Decimales en rumbos:"))
        self.spin_bearing_decimals = QSpinBox()
        self.spin_bearing_decimals.setRange(0, 2)
        self.spin_bearing_decimals.valueChanged.connect(self._on_setting_changed)
        bearing_dec_layout.addWidget(self.spin_bearing_decimals)
        bearing_dec_layout.addStretch()
        layout.addLayout(bearing_dec_layout)
        
        # Separador de miles
        self.chk_thousands = QCheckBox("Usar separador de miles (ej: 500,000)")
        self.chk_thousands.toggled.connect(self._on_setting_changed)
        layout.addWidget(self.chk_thousands)
        
        layout.addStretch()
        return widget
    
    def _load_current_settings(self):
        """Carga la configuración actual en los widgets."""
        # Bordes
        self.chk_all_borders.setChecked(self.settings.show_all_borders)
        self.chk_horizontal.setChecked(self.settings.show_horizontal)
        self.chk_vertical.setChecked(self.settings.show_vertical)
        self.chk_outer.setChecked(self.settings.show_outer)
        self.spin_border_width.setValue(self.settings.border_width)
        
        # Colores
        self.combo_palette.setCurrentText(self.settings.color_palette)
        self._update_color_previews()
        
        # Formato
        if self.settings.bearing_format == "azimuth":
            self.combo_bearing.setCurrentIndex(0)
        else:
            self.combo_bearing.setCurrentIndex(1)
        self.spin_coord_decimals.setValue(self.settings.coord_decimals)
        self.spin_bearing_decimals.setValue(self.settings.bearing_decimals)
        self.chk_thousands.setChecked(self.settings.use_thousands_separator)
    
    def _update_color_previews(self):
        """Actualiza los previews de colores."""
        self.lbl_header_bg_preview.setStyleSheet(f"background-color: {self.settings.header_bg_color};")
        self.lbl_header_text_preview.setStyleSheet(f"background-color: {self.settings.header_text_color};")
        self.lbl_row1_preview.setStyleSheet(f"background-color: {self.settings.row_bg_color1};")
        self.lbl_row2_preview.setStyleSheet(f"background-color: {self.settings.row_bg_color2};")
        self.lbl_cell_text_preview.setStyleSheet(f"background-color: {self.settings.cell_text_color};")
    
    def _on_border_option_changed(self):
        """Maneja cambios en opciones de bordes."""
        sender = self.sender()
        
        if sender == self.chk_all_borders and self.chk_all_borders.isChecked():
            # Si "Todos" se activa, desactivar los demás
            self.chk_horizontal.setChecked(False)
            self.chk_vertical.setChecked(False)
            self.chk_outer.setChecked(False)
        
        self._on_setting_changed()
    
    def _on_palette_changed(self, palette_name):
        """Maneja cambio de paleta."""
        if palette_name != "Personalizada":
            self.settings.apply_palette(palette_name)
            self._update_color_previews()
            self._on_setting_changed()
    
    def _on_color_button_clicked(self, color_type):
        """Abre selector de color."""
        # Cambiar a paleta personalizada
        if self.combo_palette.currentText() != "Personalizada":
            self.combo_palette.setCurrentText("Personalizada")
        
        # Obtener color actual
        current_color_map = {
            "header_bg": self.settings.header_bg_color,
            "header_text": self.settings.header_text_color,
            "row_bg1": self.settings.row_bg_color1,
            "row_bg2": self.settings.row_bg_color2,
            "cell_text": self.settings.cell_text_color
        }
        
        current_color = QColor(current_color_map.get(color_type, "#ffffff"))
        
        # Abrir diálogo de color
        color = QColorDialog.getColor(current_color, self, "Seleccionar Color")
        
        if color.isValid():
            color_hex = color.name()
            
            # Actualizar settings
            if color_type == "header_bg":
                self.settings.header_bg_color = color_hex
            elif color_type == "header_text":
                self.settings.header_text_color = color_hex
            elif color_type == "row_bg1":
                self.settings.row_bg_color1 = color_hex
            elif color_type == "row_bg2":
                self.settings.row_bg_color2 = color_hex
            elif color_type == "cell_text":
                self.settings.cell_text_color = color_hex
            
            self._update_color_previews()
            self._on_setting_changed()
    
    def _on_setting_changed(self):
        """Llamado cuando cualquier configuración cambia."""
        # Actualizar settings desde widgets
        self.settings.show_all_borders = self.chk_all_borders.isChecked()
        self.settings.show_horizontal = self.chk_horizontal.isChecked()
        self.settings.show_vertical = self.chk_vertical.isChecked()
        self.settings.show_outer = self.chk_outer.isChecked()
        self.settings.border_width = self.spin_border_width.value()
        
        self.settings.color_palette = self.combo_palette.currentText()
        
        if self.combo_bearing.currentIndex() == 0:
            self.settings.bearing_format = "azimuth"
        else:
            self.settings.bearing_format = "quadrant"
        
        self.settings.coord_decimals = self.spin_coord_decimals.value()
        self.settings.bearing_decimals = self.spin_bearing_decimals.value()
        self.settings.use_thousands_separator = self.chk_thousands.isChecked()
        
        # Actualizar vista previa si está habilitada
        if self.chk_realtime.isChecked():
            self._update_preview()
    
    def _on_realtime_toggled(self, checked):
        """Maneja activación/desactivación de vista previa en tiempo real."""
        self.preview_browser.setEnabled(checked)
        if checked:
            self._update_preview()
        else:
            self.preview_browser.clear()
    
    def _update_preview(self):
        """Actualiza la vista previa."""
        html = self._generate_example_table()
        self.preview_browser.setHtml(html)
    
    def _generate_example_table(self):
        """Genera tabla HTML de ejemplo."""
        # Datos de ejemplo
        example_data = [
            (1, 45.3, 500000.00, 4000000.00),
            (2, 90.5, 500100.00, 4000050.00),
            (3, 135.2, 500050.00, 4000150.00)
        ]
        
        # Generar HTML con configuración actual
        html = self._build_html_table(example_data)
        return html
    
    def _build_html_table(self, data):
        """Construye tabla HTML con configuración actual."""
        # Determinar estilos de bordes
        if self.settings.show_all_borders:
            border_style = f"border: {self.settings.border_width}px solid #ddd;"
        elif self.settings.show_horizontal:
            border_style = f"border-top: {self.settings.border_width}px solid #ddd; border-bottom: {self.settings.border_width}px solid #ddd;"
        elif self.settings.show_vertical:
            border_style = f"border-left: {self.settings.border_width}px solid #ddd; border-right: {self.settings.border_width}px solid #ddd;"
        elif self.settings.show_outer:
            border_style = f"border: {self.settings.border_width}px solid #ddd;"
        else:
            border_style = "border: none;"
        
        # Construir HTML
        html = f"""
        <table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">
            <thead>
                <tr style="background-color: {self.settings.header_bg_color}; color: {self.settings.header_text_color};">
                    <th style="padding: 8px; {border_style}">ID</th>
                    <th style="padding: 8px; {border_style}">Rumbo (°)</th>
                    <th style="padding: 8px; {border_style}">X (m)</th>
                    <th style="padding: 8px; {border_style}">Y (m)</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for i, (id_val, bearing, x, y) in enumerate(data):
            row_bg = self.settings.row_bg_color1 if i % 2 == 0 else self.settings.row_bg_color2
            bearing_str = f"{bearing:.{self.settings.bearing_decimals}f}" if bearing is not None else "N/A"
            
            # Formatear con o sin separador de miles
            if self.settings.use_thousands_separator:
                x_str = f"{x:,.{self.settings.coord_decimals}f}"
                y_str = f"{y:,.{self.settings.coord_decimals}f}"
            else:
                x_str = f"{x:.{self.settings.coord_decimals}f}"
                y_str = f"{y:.{self.settings.coord_decimals}f}"
            
            html += f"""
                <tr style="background-color: {row_bg}; color: {self.settings.cell_text_color};">
                    <td style="padding: 6px; {border_style} text-align: center;">{id_val}</td>
                    <td style="padding: 6px; {border_style} text-align: right;">{bearing_str}</td>
                    <td style="padding: 6px; {border_style} text-align: right;">{x_str}</td>
                    <td style="padding: 6px; {border_style} text-align: right;">{y_str}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        <p style="text-align: center; margin-top: 10px; font-size: 0.9em; color: #666; font-style: italic;">
            Tabla generada por GeoWizard - Tellus Consultoría
        </p>
        """
        
        return html
    
    def _on_save(self):
        """Guarda la configuración y cierra el diálogo."""
        # Sincronizar todos los valores de los widgets a settings
        self._sync_settings_from_widgets()
        # Guardar en QSettings
        self.settings.save()
        self.settingsChanged.emit(self.settings)
        self.accept()
    
    def _sync_settings_from_widgets(self):
        """Sincroniza todos los valores de los widgets a self.settings."""
        # Bordes
        self.settings.show_all_borders = self.chk_all_borders.isChecked()
        self.settings.show_horizontal = self.chk_horizontal.isChecked()
        self.settings.show_vertical = self.chk_vertical.isChecked()
        self.settings.show_outer = self.chk_outer.isChecked()
        self.settings.border_width = self.spin_border_width.value()
        
        # Colores - ya están en self.settings desde _on_color_button_clicked
        # Pero aseguramos que la paleta esté correcta
        self.settings.color_palette = self.combo_palette.currentText()
        
        # Formato
        if self.combo_bearing.currentIndex() == 0:
            self.settings.bearing_format = "azimuth"
        else:
            self.settings.bearing_format = "quadrant"
        
        self.settings.coord_decimals = self.spin_coord_decimals.value()
        self.settings.bearing_decimals = self.spin_bearing_decimals.value()
        self.settings.use_thousands_separator = self.chk_thousands.isChecked()
    
    def _on_restore_defaults(self):
        """Restaura valores por defecto."""
        self.settings.load_defaults()
        self._load_current_settings()
        self._update_color_previews()
        if self.chk_realtime.isChecked():
            self._update_preview()

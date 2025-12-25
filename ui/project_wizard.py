# ui/project_wizard.py
"""
Project Wizard Dialog for GeoWizard.

This wizard appears at startup and when creating a new project.
It handles project configuration, template fields, and coordinate system selection.
"""

import os
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, Signal, QUrl
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QWidget, QPushButton, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDateEdit, QCheckBox, QFrame, QFileDialog,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout,
    QSplitter, QSizePolicy, QScrollArea
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from ui.custom_titlebar import CustomTitleBar
from utils.logger import get_logger

logger = get_logger(__name__)


class ProjectWizard(QDialog):
    """
    Multi-page project wizard dialog.
    
    Pages:
    1. Welcome - Open/New/Recent files
    2. Project Settings - Template fields and configuration
    """
    
    # Signal emitted when wizard completes with project data
    projectCreated = Signal(dict)
    
    def __init__(self, parent=None, startup: bool = False):
        super().__init__(parent)
        self.startup = startup
        self._project_data = {}
        self._source_file = None
        self._action_type = None  # 'open', 'new_kml', 'new_shp', etc.
        
        self._setup_ui()
        self._load_recent_files()
        self._connect_signals()
        
    def _setup_ui(self):
        """Build the wizard UI."""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setMinimumSize(1000, 700)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom title bar
        self.title_bar = CustomTitleBar("GeoWizard - Asistente de Proyecto", self)
        self.title_bar.closeClicked.connect(self.reject)
        self.title_bar.minimizeClicked.connect(self.showMinimized)
        self.title_bar.maximizeClicked.connect(self._toggle_maximize)
        main_layout.addWidget(self.title_bar)
        
        # Content area
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(content)
        
        # Stacked widget for pages
        self.stack = QStackedWidget()
        
        # Create pages
        self._create_welcome_page()
        self._create_settings_page()
        
        # Initially show welcome page
        self.stack.setCurrentIndex(0)
        
        content_layout.addWidget(self.stack)
        
    def _toggle_maximize(self):
        """Toggle maximize state."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # WELCOME PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _create_welcome_page(self):
        """Create the welcome/start page."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # ═══════════════════════════════════════════════════════════
        # LEFT PANEL - Actions
        # ═══════════════════════════════════════════════════════════
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        
        # Logo/Title
        title_label = QLabel("🗺️ GeoWizard")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        left_layout.addWidget(title_label)
        
        subtitle = QLabel("Asistente de Proyecto")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 20px;")
        left_layout.addWidget(subtitle)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #bdc3c7;")
        left_layout.addWidget(sep)
        
        # Action buttons
        actions_label = QLabel("Comenzar")
        actions_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        actions_label.setStyleSheet("color: #34495e; margin-top: 10px;")
        left_layout.addWidget(actions_label)
        
        # Open existing project
        self.btn_open = self._create_action_button(
            "📂 Abrir Proyecto Existente (.gwz)",
            "Cargar un proyecto GeoWizard guardado",
            "#3498db"
        )
        self.btn_open.clicked.connect(lambda: self._on_action_selected('open'))
        left_layout.addWidget(self.btn_open)
        
        # New from file section
        new_label = QLabel("Nuevo desde archivo:")
        new_label.setFont(QFont("Segoe UI", 10))
        new_label.setStyleSheet("color: #7f8c8d; margin-top: 15px;")
        left_layout.addWidget(new_label)
        
        # New from KML
        self.btn_new_kml = self._create_action_button(
            "📍 Nuevo desde KML/KMZ",
            "Importar geometrías desde Google Earth",
            "#27ae60"
        )
        self.btn_new_kml.clicked.connect(lambda: self._on_action_selected('new_kml'))
        left_layout.addWidget(self.btn_new_kml)
        
        # New from SHP
        self.btn_new_shp = self._create_action_button(
            "🗺️ Nuevo desde Shapefile",
            "Importar geometrías desde archivo SHP",
            "#27ae60"
        )
        self.btn_new_shp.clicked.connect(lambda: self._on_action_selected('new_shp'))
        left_layout.addWidget(self.btn_new_shp)
        
        # New from CSV
        self.btn_new_csv = self._create_action_button(
            "📊 Nuevo desde CSV",
            "Importar coordenadas desde archivo CSV",
            "#27ae60"
        )
        self.btn_new_csv.clicked.connect(lambda: self._on_action_selected('new_csv'))
        left_layout.addWidget(self.btn_new_csv)
        
        # New empty
        self.btn_new_empty = self._create_action_button(
            "✨ Proyecto Vacío",
            "Comenzar desde cero sin importar datos",
            "#9b59b6"
        )
        self.btn_new_empty.clicked.connect(lambda: self._on_action_selected('new_empty'))
        left_layout.addWidget(self.btn_new_empty)
        
        left_layout.addStretch()
        
        # Tellus branding
        branding = QLabel("Powered by Tellus Consultoría")
        branding.setFont(QFont("Segoe UI", 9))
        branding.setStyleSheet("color: #95a5a6;")
        branding.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(branding)
        
        layout.addWidget(left_panel, 1)
        
        # ═══════════════════════════════════════════════════════════
        # RIGHT PANEL - Recent Files
        # ═══════════════════════════════════════════════════════════
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        
        recent_label = QLabel("📋 Archivos Recientes")
        recent_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        recent_label.setStyleSheet("color: #34495e;")
        right_layout.addWidget(recent_label)
        
        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #fafafa;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover {
                background-color: #e8f4fc;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        self.recent_list.itemDoubleClicked.connect(self._on_recent_double_clicked)
        right_layout.addWidget(self.recent_list)
        
        # Open selected recent
        self.btn_open_recent = QPushButton("Abrir Seleccionado")
        self.btn_open_recent.setEnabled(False)
        self.btn_open_recent.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_open_recent.clicked.connect(self._on_open_recent)
        right_layout.addWidget(self.btn_open_recent)
        
        layout.addWidget(right_panel, 1)
        
        self.stack.addWidget(page)
    
    def _create_action_button(self, text: str, tooltip: str, color: str) -> QPushButton:
        """Create a styled action button."""
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 12px 15px;
                border: 2px solid {color};
                border-radius: 8px;
                background-color: white;
                color: #2c3e50;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: white;
            }}
        """)
        return btn
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SETTINGS PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _create_settings_page(self):
        """Create the project settings page with form and preview."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Splitter for form and preview
        splitter = QSplitter(Qt.Horizontal)
        
        # ═══════════════════════════════════════════════════════════
        # LEFT - Form
        # ═══════════════════════════════════════════════════════════
        form_container = QWidget()
        form_container.setStyleSheet("background-color: #f5f6fa;")
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        form_widget = QWidget()
        form_inner = QVBoxLayout(form_widget)
        form_inner.setSpacing(15)
        
        # ─────────────────────────────────────────────────────────
        # Project Info Section
        # ─────────────────────────────────────────────────────────
        project_group = self._create_group("📋 Información del Proyecto")
        project_form = QFormLayout()
        project_form.setSpacing(10)
        
        self.txt_titulo = QLineEdit()
        self.txt_titulo.setPlaceholderText("Ej: Análisis de Riesgo del Sector Hidrocarburos")
        self.txt_titulo.textChanged.connect(self._update_preview)
        self.txt_titulo.textChanged.connect(self._update_output_folder)
        project_form.addRow("Título del Proyecto:", self.txt_titulo)
        
        # Code section (Prefix-Number-Suffix)
        code_layout = QHBoxLayout()
        
        self.txt_code_prefix = QLineEdit("GWZ")
        self.txt_code_prefix.setMaximumWidth(60)
        self.txt_code_prefix.setEnabled(False)  # Blocked in Free version
        self.txt_code_prefix.setStyleSheet("background-color: #ecf0f1; color: #7f8c8d;")
        self.txt_code_prefix.textChanged.connect(self._update_code_preview)
        code_layout.addWidget(self.txt_code_prefix)
        
        code_layout.addWidget(QLabel("-"))
        
        self.spin_code_number = QSpinBox()
        self.spin_code_number.setRange(1, 999)
        self.spin_code_number.setValue(1)
        self.spin_code_number.setMaximumWidth(60)
        self.spin_code_number.valueChanged.connect(self._update_code_preview)
        code_layout.addWidget(self.spin_code_number)
        
        code_layout.addWidget(QLabel("-"))
        
        self.txt_code_suffix = QLineEdit("UBI")
        self.txt_code_suffix.setMaximumWidth(80)
        self.txt_code_suffix.setPlaceholderText("UBI")
        self.txt_code_suffix.textChanged.connect(self._update_code_preview)
        code_layout.addWidget(self.txt_code_suffix)
        
        code_layout.addWidget(QLabel("="))
        
        self.lbl_code_preview = QLabel("GWZ-01-UBI")
        self.lbl_code_preview.setStyleSheet("font-weight: bold; color: #c0392b; font-size: 12pt;")
        code_layout.addWidget(self.lbl_code_preview)
        code_layout.addStretch()
        
        project_form.addRow("Código del Plano:", code_layout)
        
        self.txt_subtitulo = QLineEdit("Ubicación del Proyecto")
        self.txt_subtitulo.textChanged.connect(self._update_preview)
        project_form.addRow("Subtítulo:", self.txt_subtitulo)
        
        project_group.layout().addLayout(project_form)
        form_inner.addWidget(project_group)
        
        # ─────────────────────────────────────────────────────────
        # Client/Promovente Section
        # ─────────────────────────────────────────────────────────
        client_group = self._create_group("🏢 Promovente")
        client_form = QFormLayout()
        client_form.setSpacing(10)
        
        self.txt_promovente = QLineEdit()
        self.txt_promovente.setPlaceholderText("Ej: Servicios Rodríguez Eguía, S.A. de C.V.")
        self.txt_promovente.textChanged.connect(self._update_preview)
        client_form.addRow("Empresa/Promovente:", self.txt_promovente)
        
        self.txt_responsable = QLineEdit()
        self.txt_responsable.setPlaceholderText("Ej: Oscar Omar Contreras Castro")
        self.txt_responsable.textChanged.connect(self._update_preview)
        client_form.addRow("Responsable Técnico:", self.txt_responsable)
        
        client_group.layout().addLayout(client_form)
        form_inner.addWidget(client_group)
        
        # ─────────────────────────────────────────────────────────
        # Revision Section
        # ─────────────────────────────────────────────────────────
        revision_group = self._create_group("📝 Datos de Revisión")
        revision_form = QFormLayout()
        revision_form.setSpacing(10)
        
        self.txt_rev = QLineEdit("00")
        self.txt_rev.setMaximumWidth(60)
        revision_form.addRow("Revisión:", self.txt_rev)
        
        self.txt_descripcion = QLineEdit("Creación del Plano")
        revision_form.addRow("Descripción:", self.txt_descripcion)
        
        self.date_fecha = QDateEdit()
        self.date_fecha.setDate(date.today())
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.dateChanged.connect(self._update_preview)
        revision_form.addRow("Fecha:", self.date_fecha)
        
        # Blocked fields (visible but disabled in Free)
        self.txt_dibujante = QLineEdit("GeoWizard V.1.0")
        self.txt_dibujante.setEnabled(False)
        self.txt_dibujante.setStyleSheet("background-color: #ecf0f1; color: #7f8c8d;")
        revision_form.addRow("Dibujante:", self.txt_dibujante)
        
        self.txt_reviso = QLineEdit("")
        self.txt_reviso.setEnabled(False)
        self.txt_reviso.setStyleSheet("background-color: #ecf0f1; color: #7f8c8d;")
        self.txt_reviso.setPlaceholderText("(Premium)")
        revision_form.addRow("Revisó:", self.txt_reviso)
        
        self.txt_aprobo = QLineEdit("")
        self.txt_aprobo.setEnabled(False)
        self.txt_aprobo.setStyleSheet("background-color: #ecf0f1; color: #7f8c8d;")
        self.txt_aprobo.setPlaceholderText("(Premium)")
        revision_form.addRow("Aprobó:", self.txt_aprobo)
        
        revision_group.layout().addLayout(revision_form)
        form_inner.addWidget(revision_group)
        
        # ─────────────────────────────────────────────────────────
        # Coordinate System Section
        # ─────────────────────────────────────────────────────────
        coords_group = self._create_group("🌐 Sistema de Coordenadas")
        coords_form = QFormLayout()
        coords_form.setSpacing(10)
        
        self.cb_coord_system = QComboBox()
        self.cb_coord_system.addItems([
            "UTM",
            "Geographic (Decimal Degrees)",
            "Geographic (DMS)",
            "Web Mercator"
        ])
        self.cb_coord_system.currentIndexChanged.connect(self._on_coord_system_changed)
        coords_form.addRow("Sistema:", self.cb_coord_system)
        
        # UTM-specific fields
        self.utm_fields_widget = QWidget()
        utm_layout = QHBoxLayout(self.utm_fields_widget)
        utm_layout.setContentsMargins(0, 0, 0, 0)
        
        utm_layout.addWidget(QLabel("Hemisferio:"))
        self.cb_hemisphere = QComboBox()
        self.cb_hemisphere.addItems(["Norte", "Sur"])
        utm_layout.addWidget(self.cb_hemisphere)
        
        utm_layout.addWidget(QLabel("Zona:"))
        self.cb_zone = QComboBox()
        self.cb_zone.addItems([str(i) for i in range(1, 61)])
        self.cb_zone.setCurrentIndex(13)  # Zone 14 default
        utm_layout.addWidget(self.cb_zone)
        utm_layout.addStretch()
        
        coords_form.addRow("", self.utm_fields_widget)
        
        coords_group.layout().addLayout(coords_form)
        form_inner.addWidget(coords_group)
        
        # ─────────────────────────────────────────────────────────
        # Output Section
        # ─────────────────────────────────────────────────────────
        output_group = self._create_group("💾 Guardado")
        output_form = QFormLayout()
        output_form.setSpacing(10)
        
        folder_layout = QHBoxLayout()
        self.txt_output_folder = QLineEdit()
        self.txt_output_folder.setPlaceholderText("Seleccionar carpeta de salida...")
        folder_layout.addWidget(self.txt_output_folder)
        
        self.btn_browse = QPushButton("Examinar...")
        self.btn_browse.clicked.connect(self._browse_output_folder)
        folder_layout.addWidget(self.btn_browse)
        
        output_form.addRow("Carpeta:", folder_layout)
        
        self.cb_format = QComboBox()
        self.cb_format.addItems([".gwz", ".kml", ".kmz", ".shp"])
        output_form.addRow("Formato:", self.cb_format)
        
        output_group.layout().addLayout(output_form)
        form_inner.addWidget(output_group)
        
        # ─────────────────────────────────────────────────────────
        # Branding Section (Blocked)
        # ─────────────────────────────────────────────────────────
        branding_group = self._create_group("🏷️ Marca de Agua")
        branding_form = QFormLayout()
        
        self.chk_powered_by = QCheckBox("Mostrar 'Powered by Tellus Consultoría - GeoWizard V.1.0'")
        self.chk_powered_by.setChecked(True)
        self.chk_powered_by.setEnabled(False)  # Blocked in Free
        self.chk_powered_by.setStyleSheet("color: #7f8c8d;")
        branding_form.addRow(self.chk_powered_by)
        
        branding_group.layout().addLayout(branding_form)
        form_inner.addWidget(branding_group)
        
        form_inner.addStretch()
        
        scroll.setWidget(form_widget)
        form_layout.addWidget(scroll)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.btn_back = QPushButton("← Volver")
        self.btn_back.clicked.connect(self._go_back)
        self.btn_back.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """)
        nav_layout.addWidget(self.btn_back)
        
        nav_layout.addStretch()
        
        self.btn_continue = QPushButton("Continuar →")
        self.btn_continue.clicked.connect(self._on_continue)
        self.btn_continue.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                border: none;
                border-radius: 5px;
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        nav_layout.addWidget(self.btn_continue)
        
        form_layout.addLayout(nav_layout)
        
        splitter.addWidget(form_container)
        
        # ═══════════════════════════════════════════════════════════
        # RIGHT - Preview
        # ═══════════════════════════════════════════════════════════
        preview_container = QWidget()
        preview_container.setStyleSheet("background-color: #ecf0f1;")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.setSpacing(8)
        
        # Preview header with zoom controls
        preview_header = QHBoxLayout()
        
        preview_label = QLabel("Vista Previa")
        preview_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        preview_label.setStyleSheet("color: #34495e;")
        preview_header.addWidget(preview_label)
        
        preview_header.addStretch()
        
        # Zoom controls
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_out.setFixedSize(28, 28)
        self.btn_zoom_out.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover { background-color: #ecf0f1; }
        """)
        self.btn_zoom_out.clicked.connect(self._zoom_out_preview)
        preview_header.addWidget(self.btn_zoom_out)
        
        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setStyleSheet("color: #7f8c8d; min-width: 45px; text-align: center;")
        self.lbl_zoom.setAlignment(Qt.AlignCenter)
        preview_header.addWidget(self.lbl_zoom)
        
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedSize(28, 28)
        self.btn_zoom_in.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover { background-color: #ecf0f1; }
        """)
        self.btn_zoom_in.clicked.connect(self._zoom_in_preview)
        preview_header.addWidget(self.btn_zoom_in)
        
        self.btn_zoom_reset = QPushButton("⟳")
        self.btn_zoom_reset.setFixedSize(28, 28)
        self.btn_zoom_reset.setToolTip("Restablecer zoom")
        self.btn_zoom_reset.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 12pt;
            }
            QPushButton:hover { background-color: #ecf0f1; }
        """)
        self.btn_zoom_reset.clicked.connect(self._reset_zoom_preview)
        preview_header.addWidget(self.btn_zoom_reset)
        
        preview_layout.addLayout(preview_header)
        
        # Preview web view with border
        self.preview_web = QWebEngineView()
        self.preview_web.setMinimumWidth(350)
        self.preview_web.setStyleSheet("border: 1px solid #bdc3c7; border-radius: 4px;")
        self._preview_zoom = 1.0
        preview_layout.addWidget(self.preview_web)
        
        splitter.addWidget(preview_container)
        splitter.setSizes([450, 550])
        
        layout.addWidget(splitter)
        
        self.stack.addWidget(page)
        
        # Load template preview
        self._load_template_preview()
    
    def _create_group(self, title: str) -> QGroupBox:
        """Create a styled group box."""
        group = QGroupBox(title)
        group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2c3e50;
            }
        """)
        group.setLayout(QVBoxLayout())
        return group
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _connect_signals(self):
        """Connect additional signals."""
        self.recent_list.itemSelectionChanged.connect(
            lambda: self.btn_open_recent.setEnabled(len(self.recent_list.selectedItems()) > 0)
        )
    
    def _on_action_selected(self, action: str):
        """Handle action button clicks."""
        self._action_type = action
        
        if action == 'open':
            # Open file dialog for .gwz
            filename, _ = QFileDialog.getOpenFileName(
                self, "Abrir Proyecto GeoWizard",
                str(Path.home() / "Documents"),
                "GeoWizard Project (*.gwz)"
            )
            if filename:
                self._source_file = filename
                self._load_existing_project(filename)
                self.stack.setCurrentIndex(1)
                
        elif action.startswith('new_'):
            # Open file dialog for specific format
            format_map = {
                'new_kml': ("Archivos KML/KMZ (*.kml *.kmz)", "KML"),
                'new_shp': ("Shapefiles (*.shp)", "Shapefile"),
                'new_csv': ("Archivos CSV (*.csv)", "CSV"),
            }
            
            if action in format_map:
                filter_str, format_name = format_map[action]
                filename, _ = QFileDialog.getOpenFileName(
                    self, f"Importar {format_name}",
                    str(Path.home() / "Documents"),
                    filter_str
                )
                if filename:
                    self._source_file = filename
                    self.stack.setCurrentIndex(1)
                    self._set_default_output_folder()
            
            elif action == 'new_empty':
                self._source_file = None
                self.stack.setCurrentIndex(1)
                self._set_default_output_folder()
    
    def _on_recent_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on recent file."""
        filepath = item.data(Qt.UserRole)
        if filepath and os.path.exists(filepath):
            self._source_file = filepath
            self._action_type = 'open'
            self._load_existing_project(filepath)
            self.stack.setCurrentIndex(1)
    
    def _on_open_recent(self):
        """Open selected recent file."""
        items = self.recent_list.selectedItems()
        if items:
            self._on_recent_double_clicked(items[0])
    
    def _go_back(self):
        """Go back to welcome page."""
        self.stack.setCurrentIndex(0)
    
    def _on_continue(self):
        """Handle continue button - finalize and accept."""
        self._collect_project_data()
        self.accept()
    
    def _on_coord_system_changed(self, index: int):
        """Show/hide UTM fields based on coordinate system."""
        is_utm = index == 0
        self.utm_fields_widget.setVisible(is_utm)
        self._update_preview()  # Update preview with new coordinate system
    
    def _update_code_preview(self):
        """Update the code preview label."""
        prefix = self.txt_code_prefix.text() or "GWZ"
        number = f"{self.spin_code_number.value():02d}"
        suffix = self.txt_code_suffix.text() or "UBI"
        self.lbl_code_preview.setText(f"{prefix}-{number}-{suffix}")
        self._update_preview()
    
    def _update_output_folder(self):
        """Update output folder based on project title."""
        title = self.txt_titulo.text().strip()
        if title:
            base = Path.home() / "Documents" / "Proyectos GeoWizard"
            # Sanitize folder name
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
            if safe_title:
                self.txt_output_folder.setText(str(base / safe_title))
    
    def _browse_output_folder(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Salida",
            self.txt_output_folder.text() or str(Path.home() / "Documents")
        )
        if folder:
            self.txt_output_folder.setText(folder)
    
    def _set_default_output_folder(self):
        """Set default output folder."""
        base = Path.home() / "Documents" / "Proyectos GeoWizard"
        self.txt_output_folder.setText(str(base))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DATA MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _load_recent_files(self):
        """Load recent files from settings."""
        settings = QSettings("TellusConsultoria", "GeoWizard")
        recent = settings.value("recent_files", [])
        
        self.recent_list.clear()
        for filepath in recent:
            if os.path.exists(filepath):
                item = QListWidgetItem(os.path.basename(filepath))
                item.setData(Qt.UserRole, filepath)
                item.setToolTip(filepath)
                self.recent_list.addItem(item)
        
        if self.recent_list.count() == 0:
            item = QListWidgetItem("(No hay archivos recientes)")
            item.setFlags(Qt.NoItemFlags)
            self.recent_list.addItem(item)
    
    def _load_existing_project(self, filepath: str):
        """Load project data from existing .gwz file."""
        try:
            from importers.gwz_importer import GWZImporter
            data = GWZImporter.import_file(filepath)
            
            metadata = data.get("metadata", {})
            project = data.get("project_data", {})
            
            # Populate form fields
            self.txt_titulo.setText(project.get("titulo", ""))
            self.txt_subtitulo.setText(project.get("subtitulo", "Ubicación del Proyecto"))
            self.txt_promovente.setText(project.get("promovente", ""))
            self.txt_responsable.setText(project.get("responsable", ""))
            self.txt_rev.setText(project.get("rev", "00"))
            self.txt_descripcion.setText(project.get("descripcion", "Creación del Plano"))
            
            # Code
            code = project.get("codigo", "GWZ-01-UBI")
            parts = code.split("-")
            if len(parts) >= 3:
                self.txt_code_prefix.setText(parts[0])
                try:
                    self.spin_code_number.setValue(int(parts[1]))
                except ValueError:
                    pass
                self.txt_code_suffix.setText("-".join(parts[2:]))
            
            # Coordinate system
            coord_sys = metadata.get("sistema_predeterminado", "UTM")
            index = self.cb_coord_system.findText(coord_sys, Qt.MatchContains)
            if index >= 0:
                self.cb_coord_system.setCurrentIndex(index)
            
            hemisphere = metadata.get("hemisferio", "Norte")
            self.cb_hemisphere.setCurrentText(hemisphere)
            
            zone = metadata.get("zona_utm", 14)
            self.cb_zone.setCurrentText(str(zone))
            
            # Output folder - use original location
            self.txt_output_folder.setText(os.path.dirname(filepath))
            
            logger.info(f"Loaded project from: {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading project: {e}")
    
    def _collect_project_data(self) -> dict:
        """Collect all form data into a dictionary."""
        code = self.lbl_code_preview.text()
        
        self._project_data = {
            # Project info
            "titulo": self.txt_titulo.text(),
            "codigo": code,
            "subtitulo": self.txt_subtitulo.text(),
            
            # Client
            "promovente": self.txt_promovente.text(),
            "responsable": self.txt_responsable.text(),
            
            # Revision
            "rev": self.txt_rev.text(),
            "descripcion": self.txt_descripcion.text(),
            "fecha": self.date_fecha.date().toString("dd/MM/yyyy"),
            "fecha_larga": self.date_fecha.date().toString("dddd, dd 'de' MMMM 'de' yyyy"),
            "dibujante": self.txt_dibujante.text(),
            "reviso": self.txt_reviso.text(),
            "aprobo": self.txt_aprobo.text(),
            
            # Branding
            "powered_by_tellus": self.chk_powered_by.isChecked(),
            
            # Coordinate system
            "coord_system": self.cb_coord_system.currentText(),
            "hemisphere": self.cb_hemisphere.currentText(),
            "zone": int(self.cb_zone.currentText()),
            
            # Output
            "output_folder": self.txt_output_folder.text(),
            "output_format": self.cb_format.currentText(),
            
            # Source
            "source_file": self._source_file,
            "action_type": self._action_type
        }
        
        return self._project_data
    
    def get_project_data(self) -> dict:
        """Get collected project data."""
        return self._project_data
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PREVIEW
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _load_template_preview(self):
        """Load the map template for preview."""
        import sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        template_path = os.path.join(base_path, "templates", "map_report_template.html")
        
        if os.path.exists(template_path):
            self.preview_web.setUrl(QUrl.fromLocalFile(template_path))
        else:
            self.preview_web.setHtml("<html><body><h2>Vista previa no disponible</h2></body></html>")
    
    def _update_preview(self):
        """Update preview with current form values."""
        # Get fecha_larga formatted
        fecha_larga = self.date_fecha.date().toString("dddd, d 'de' MMMM 'de' yyyy")
        coord_system = self.cb_coord_system.currentText()
        
        # Escape quotes in strings for JavaScript
        titulo = self.txt_titulo.text().replace('"', '\\"').replace("'", "\\'")
        codigo = self.lbl_code_preview.text()
        subtitulo = self.txt_subtitulo.text().replace('"', '\\"').replace("'", "\\'")
        promovente = self.txt_promovente.text().replace('"', '\\"').replace("'", "\\'")
        responsable = self.txt_responsable.text().replace('"', '\\"').replace("'", "\\'")
        fecha = self.date_fecha.date().toString('dd/MM/yyyy')
        dibujante = self.txt_dibujante.text()
        reviso = self.txt_reviso.text()  # Will be empty in Free version
        aprobo = self.txt_aprobo.text()  # Will be empty in Free version
        
        # Build JavaScript to update the template
        js = f"""
        if (typeof populateTemplate === 'function') {{
            populateTemplate({{
                proyecto_titulo: "{titulo}",
                codigo: "{codigo}",
                subtitulo: "{subtitulo}",
                promovente: "{promovente}",
                responsable: "{responsable}",
                fecha: "{fecha}",
                fecha_larga: "{fecha_larga}",
                dibujante: "{dibujante}",
                reviso: "{reviso}",
                aprobo: "{aprobo}",
                coord_system: "{coord_system}"
            }});
        }}
        """
        self.preview_web.page().runJavaScript(js)
    
    def _zoom_in_preview(self):
        """Zoom in the preview."""
        self._preview_zoom = min(2.0, self._preview_zoom + 0.1)
        self.preview_web.setZoomFactor(self._preview_zoom)
        self.lbl_zoom.setText(f"{int(self._preview_zoom * 100)}%")
    
    def _zoom_out_preview(self):
        """Zoom out the preview."""
        self._preview_zoom = max(0.25, self._preview_zoom - 0.1)
        self.preview_web.setZoomFactor(self._preview_zoom)
        self.lbl_zoom.setText(f"{int(self._preview_zoom * 100)}%")
    
    def _reset_zoom_preview(self):
        """Reset preview zoom to 100%."""
        self._preview_zoom = 1.0
        self.preview_web.setZoomFactor(1.0)
        self.lbl_zoom.setText("100%")

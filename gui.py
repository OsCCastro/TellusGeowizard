import os
import csv
import json

from PySide6.QtCore import (
    Qt,
    QRegularExpression,
    QSize,
    QItemSelectionModel,
    QEvent,
    QUrl,
    QRectF,
    QPointF,
)
from PySide6.QtGui import (
    QAction,
    QRegularExpressionValidator,
    QBrush,
    QPen,
    QPixmap,
    QColor,
    QPainter,
    QFont,
    QPalette,
    QIcon,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsTextItem, QFileDialog, QMessageBox, QApplication,
    QToolBar, QStyledItemDelegate, QHeaderView, QDialog, QStyleOptionViewItem,
    QStackedLayout
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

from config_dialog import ConfigDialog
from help_dialog import HelpDialog
from core.coordinate_manager import CoordinateManager, GeometryType
from exporters.kml_exporter import KMLExporter
from exporters.kmz_exporter import KMZExporter  # Asumiendo que existe
from exporters.shapefile_exporter import ShapefileExporter  # Asumiendo que existe
from importers.csv_importer import CSVImporter
from importers.kml_importer import KMLImporter
from importers.shapefile_importer import ShapefileImporter
from core.geometry import GeometryBuilder
from pyproj import Transformer

# Import coordinate system utilities
from utils.coordinate_systems import (
    CoordinateSystemType,
    dd_to_dms,
    format_dms,
    parse_dms,
    validate_dms_coordinate,
    get_utm_epsg
)

# Import error handling
from core.exceptions import (
    GeometryBuildError,
    InsufficientDataError,
    FileImportError,
    FileExportError,
    CoordinateConversionError
)
from utils.logger import get_logger
from utils.error_handler import log_and_show_error
from ui.error_dialog import show_error_dialog
from ui.editable_geometry import EditablePoint, EditableGeometry

# Initialize logger for this module
logger = get_logger(__name__)

class UTMDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        # 6-7 dígitos + decimales opcionales
        rx = QRegularExpression(r'^\d{6,7}(\.\d+)?$')
        editor.setValidator(QRegularExpressionValidator(rx, editor))
        editor.installEventFilter(self)
        editor.setProperty("row", index.row())
        editor.setProperty("column", index.column())
        return editor

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            table = obj.parent()
            while table and not isinstance(table, QTableWidget):
                table = table.parent()
            if not table:
                return False
            row = obj.property("row")
            col = obj.property("column")
            if col == 1:
                table.setCurrentCell(row, 2)
                item = table.item(row, 2)
                if item is None:
                    item = QTableWidgetItem("")
                    table.setItem(row, 2, item)
                table.editItem(item)
            elif col == 2:
                next_row = row + 1
                if next_row >= table.rowCount():
                    table.insertRow(next_row)
                    id_it = QTableWidgetItem(str(next_row + 1))
                    id_it.setFlags(Qt.ItemIsEnabled)
                    table.setItem(next_row, 0, id_it)
                table.setCurrentCell(next_row, 1)
                item = table.item(next_row, 1)
                if item is None:
                    item = QTableWidgetItem("")
                    table.setItem(next_row, 1, item)
                table.editItem(item)
            return True
        return super().eventFilter(obj, event)

    def setModelData(self, editor, model, index):
        text = editor.text()
        model.setData(index, text)
        if not (model.flags(index) & Qt.ItemIsSelectable and
                model.data(index, Qt.BackgroundRole)):
            color = Qt.black if editor.hasAcceptableInput() else Qt.red
            model.setData(index, QBrush(color), Qt.ForegroundRole)

class CoordTable(QTableWidget):
    """Extended table widget with support for expandable curve parameters."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track curve data: {main_row_index: {'delta': '...', 'radio': '...', 'centro': '...'}}
        self.curve_data = {}
        # Track which rows are expanded
        self.expanded_rows = set()
        # Track which rows are curve type (even if collapsed)
        self.curve_rows = set()
        # Default number of intermediate points for densification
        self.curve_densification_points = 15  # Default: 10-20 range
        
    def mark_as_curve(self, row):
        """
        Marca una fila como curva y agrega sub-filas para parámetros.
        
        Args:
            row: Índice de la fila a convertir en curva
        """
        if row in self.curve_rows:
            return  # Ya es una curva
        
        # Insertar 3 sub-filas debajo de la fila principal
        for i in range(3):
            self.insertRow(row + i + 1)
        
        # Configurar sub-filas con títulos (sin símbolo →)
        self._setup_subrow(row + 1, "DELTA", "")
        self._setup_subrow(row + 2, "RADIO", "")
        self._setup_subrow(row + 3, "CENTRO", "")
        
        # Agregar botón de expansión en la columna ID
        expand_btn = QPushButton("▼")
        expand_btn.setMaximumWidth(30)
        expand_btn.setStyleSheet("border: none; background: transparent; font-size: 12pt;")
        expand_btn.clicked.connect(lambda: self.toggle_expansion(row))
        
        # Guardar el contenido original del ID
        id_item = self.item(row, 0)
        if id_item:
            expand_btn.setToolTip(f"ID: {id_item.text()}")
            # Reemplazar con botón
            self.setCellWidget(row, 0, expand_btn)
        
        # Marcar como curva y expandida
        self.curve_rows.add(row)
        self.expanded_rows.add(row)
        
        # Cambiar color de fondo de la fila principal
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(220, 240, 255))  # Azul claro
    
    def _setup_subrow(self, row, label, value):
        """
        Configura una sub-fila con título y valor editable.
        
        Args:
            row: Índice de la sub-fila
            label: Etiqueta (DELTA, RADIO, CENTRO)
            value: Valor inicial
        """
        # Columna 0 (ID): Label (no editable)
        label_item = QTableWidgetItem(label)
        label_item.setFlags(Qt.ItemIsEnabled)
        label_item.setBackground(QColor(245, 245, 245))  # Gris claro
        label_item.setFont(QFont("Arial", 9, QFont.Bold))
        self.setItem(row, 0, label_item)
        
        # Columna 1 (X): Valor (editable)
        value_item = QTableWidgetItem(value)
        value_item.setBackground(QColor(245, 245, 245))
        self.setItem(row, 1, value_item)
        
        # Columna 2 (Y): Vacía (no editable)
        empty_item = QTableWidgetItem("")
        empty_item.setFlags(Qt.ItemIsEnabled)
        empty_item.setBackground(QColor(245, 245, 245))
        self.setItem(row, 2, empty_item)
    
    def toggle_expansion(self, row):
        """
        Colapsa/expande las sub-filas de una curva.
        
        Args:
            row: Índice de la fila principal (curva)
        """
        if row not in self.curve_rows:
            return  # No es una curva
        
        btn = self.cellWidget(row, 0)
        if not btn:
            return
        
        if row in self.expanded_rows:
            # Colapsar: ocultar sub-filas
            self.setRowHidden(row + 1, True)
            self.setRowHidden(row + 2, True)
            self.setRowHidden(row + 3, True)
            self.expanded_rows.remove(row)
            btn.setText("►")
        else:
            # Expandir: mostrar sub-filas
            self.setRowHidden(row + 1, False)
            self.setRowHidden(row + 2, False)
            self.setRowHidden(row + 3, False)
            self.expanded_rows.add(row)
            btn.setText("▼")
    
    def convert_to_point(self, row):
        """
        Convierte una fila de curva a punto normal.
        
        Args:
            row: Índice de la fila a convertir
        """
        if row not in self.curve_rows:
            return  # Ya es un punto
        
        # Remover sub-filas
        for i in range(3):
            self.removeRow(row + 1)
        
        # Restaurar celda de ID
        btn = self.cellWidget(row, 0)
        if btn:
            # Obtener ID del tooltip
            id_text = btn.toolTip().replace("ID: ", "")
            self.removeCellWidget(row, 0)
            id_item = QTableWidgetItem(id_text)
            id_item.setFlags(Qt.ItemIsEnabled)
            self.setItem(row, 0, id_item)
        
        # Restaurar color de fondo normal
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(255, 255, 255))  # Blanco
        
        # Remover de conjuntos de seguimiento
        self.curve_rows.discard(row)
        self.expanded_rows.discard(row)
        if row in self.curve_data:
            del self.curve_data[row]
    
    def get_curve_parameters(self, row):
        """
        Obtiene los parámetros de curva de una fila.
        
        Args:
            row: Índice de la fila principal (curva)
        
        Returns:
            dict con keys: 'delta', 'radio', 'centro' (o None si no es curva)
        """
        if row not in self.curve_rows:
            return None
        
        delta_item = self.item(row + 1, 1)
        radio_item = self.item(row + 2, 1)
        centro_item = self.item(row + 3, 1)
        
        return {
            'delta': delta_item.text() if delta_item else "",
            'radio': radio_item.text() if radio_item else "",
            'centro': centro_item.text() if centro_item else ""
        }
    
    def keyPressEvent(self, event):
        # Tab: al salir de Y, saltar a X de la siguiente fila
        if event.key() == Qt.Key_Tab and self.currentColumn() == 2:
            current_row = self.currentRow()
            next_row = current_row + 1
            
            # Si la siguiente fila es una sub-fila de curva, saltarla
            while next_row < self.rowCount() and self.isRowHidden(next_row):
                next_row += 1
            
            if next_row < self.rowCount():
                self.setCurrentCell(next_row, 1)
                # Comenzar edición inmediatamente
                item = self.item(next_row, 1)
                if item is None:
                    item = QTableWidgetItem("")
                    self.setItem(next_row, 1, item)
                self.editItem(item)
            return
        super().keyPressEvent(event)

class CanvasView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zoom_factor = 1.15

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale(self._zoom_factor, self._zoom_factor)
        else:
            self.scale(1 / self._zoom_factor, 1 / self._zoom_factor)
        event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tellus Consultoría - GeoWizard V.1.0 (Beta Tester)")
        
        # Set Tellus Consultoría logo as window icon
        import sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        icon_path = os.path.join(base_path, "icons", "tellus_logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Track zone/hemisphere used for last import
        self._import_zone = None
        self._import_hemisphere = None
        self._has_imported_data = False
        # Track previous coordinate system for conversion
        self._prev_coord_system = "UTM"
        # Cache coordinates for each system to avoid re-conversion
        self._coord_cache = {
            "UTM": [],
            "Geographic (Decimal Degrees)": [],
            "Geographic (DMS)": [],
            "Web Mercator": []
        }
        # Flag to prevent geometry building during conversion
        self._is_converting = False
        
        # Edit mode state
        self._edit_mode = False
        self._editable_geometries = []  # Track editable geometry objects
        
        self._modo_oscuro = False
        self.draw_scale = 0.35
        self.point_size = 6
        self.font_size = 8
        
        self._build_ui()
        self._create_toolbar()
        self._toggle_modo(False)
        
        # Auto-enable basemap checkbox on startup (user can toggle map with checkbox)
        self.chk_mapbase.setChecked(True)
    
    def closeEvent(self, event):
        """Override closeEvent to show thank you message for beta testers."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Gracias por usar GeoWizard")
        msg.setIcon(QMessageBox.Information)
        
        # Message content
        message_text = (
            "<h3>¡Gracias por utilizar GeoWizard V.1.0 (Beta Tester)!</h3>"
            "<p>Tu participación en esta versión beta es muy valiosa para nosotros.</p>"
            "<p><b>Por favor, comparte tu opinión y sugerencias sobre el programa.</b></p>"
            "<hr>"
            "<p><b>Contacto:</b><br>"
            "📧 <a href='mailto:contacto@tellusconsultoria.com'>contacto@tellusconsultoria.com</a></p>"
            "<p><b>Síguenos en redes sociales para recibir actualizaciones:</b><br>"
            "📘 <a href='https://www.facebook.com/TellusConsultoria'>Facebook - Tellus Consultoría</a></p>"
            "<hr>"
            "<p style='color: #666;'><i>Tellus Consultoría - Soluciones Geoespaciales</i></p>"
        )
        
        msg.setText(message_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        
        # Make links clickable
        msg.setTextFormat(Qt.RichText)
        msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
        
        msg.exec()
        event.accept()
    
    def _icono(self, nombre, size=QSize(24, 24)):
        # Get base path - works both in development and PyInstaller executable
        import sys
        if getattr(sys, 'frozen', False):
            # Running in PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # Running in normal Python environment
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        ruta = os.path.join(base_path, "icons", nombre)
        
        # Verify file exists
        if not os.path.exists(ruta):
            print(f"Icon not found: {ruta}")
            return QIcon()  # Return empty icon if not found
        
        renderer = QSvgRenderer(ruta)

        
        # 1. Render SVG to a temporary pixmap (the shape)
        temp_pixmap = QPixmap(size)
        temp_pixmap.fill(Qt.transparent)
        painter = QPainter(temp_pixmap)
        renderer.render(painter)
        painter.end()
        
        # 2. Create the final pixmap filled with the desired color
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        # Use explicit white for dark mode, otherwise palette text color
        if self._modo_oscuro:
            color = QColor("#ffffff")
        else:
            color = QApplication.palette().color(QPalette.Text)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill with color
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(pixmap.rect())
        
        # Apply the SVG shape as a mask (keep destination color where source is opaque)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.drawPixmap(0, 0, temp_pixmap)
        painter.end()

        return QIcon(pixmap)

    def _build_ui(self):
        central = QWidget()
        main_layout = QHBoxLayout(central)

        #######################
        # Panel de controles  #
        #######################
        control = QVBoxLayout()

        # Sistema de Coordenadas (NEW!)
        cs_layout = QHBoxLayout()
        cs_layout.addWidget(QLabel("Sistema de Coordenadas:"))
        self.cb_coord_system = QComboBox()
        self.cb_coord_system.addItems([
            "UTM",
            "Geographic (Decimal Degrees)",
            "Geographic (DMS)",
            "Web Mercator"
        ])
        self.cb_coord_system.currentIndexChanged.connect(self._on_coord_system_changed)
        cs_layout.addWidget(self.cb_coord_system)
        control.addLayout(cs_layout)

        # Hemisferio / Zona (will be shown/hidden based on coordinate system)
        self.hz_layout = QHBoxLayout()
        self.lbl_hemisferio = QLabel("Hemisferio:")
        self.hz_layout.addWidget(self.lbl_hemisferio)
        self.cb_hemisferio = QComboBox()
        self.cb_hemisferio.addItems(["Norte","Sur"])
        # Connect to zone/hemisphere change handler
        self.cb_hemisferio.currentIndexChanged.connect(self._on_zone_hemisphere_changed)
        self.hz_layout.addWidget(self.cb_hemisferio)
        self.lbl_zona = QLabel("Zona UTM:")
        self.hz_layout.addWidget(self.lbl_zona)
        self.cb_zona = QComboBox()
        self.cb_zona.addItems([str(i) for i in range(1,61)])
        # Connect to zone/hemisphere change handler
        self.cb_zona.currentIndexChanged.connect(self._on_zone_hemisphere_changed)
        self.hz_layout.addWidget(self.cb_zona)
        control.addLayout(self.hz_layout)

        # Tabla de coordenadas
        self.table = CoordTable(1,3)
        self.table.setHorizontalHeaderLabels(["ID","X (Este)","Y (Norte)"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        
        # NEW: Use validation delegate for coordinate columns
        from ui.validation_delegate import CoordinateValidationDelegate
        self.coord_validator = CoordinateValidationDelegate(self.table)
        self.coord_validator.set_coordinate_system("UTM", "Norte")  # Initial system
        self.table.setItemDelegateForColumn(1, self.coord_validator)  # X/Longitude column
        self.table.setItemDelegateForColumn(2, self.coord_validator)  # Y/Latitude column
        
        # primer ID
        first = QTableWidgetItem("1")
        first.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(0,0,first)
        # selección y menú contextual
        self.table.setSelectionBehavior(QTableWidget.SelectItems)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.itemChanged.connect(self._on_cell_changed)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_table_menu)
        control.addWidget(self.table)
        
        # NEW: Measurement Panel (Sidebar - Unit Selector only)
        measurements_group = QLabel("📏 Configuración Mediciones")
        measurements_group.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 10px;")
        control.addWidget(measurements_group)
        
        # Unit selector
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Unidades:"))
        self.cb_units = QComboBox()
        self.cb_units.addItems(["Métricas", "Imperiales"])
        self.cb_units.currentIndexChanged.connect(self._on_unit_changed)
        unit_layout.addWidget(self.cb_units)
        control.addLayout(unit_layout)

        # Geometrías
        geo = QHBoxLayout()
        geo.addWidget(QLabel("Geometría:"))
        self.chk_punto     = QCheckBox("Punto")
        self.chk_polilinea = QCheckBox("Polilínea")
        self.chk_poligono  = QCheckBox("Polígono")
        geo.addWidget(self.chk_punto)
        geo.addWidget(self.chk_polilinea)
        geo.addWidget(self.chk_poligono)
        control.addLayout(geo)

        # Mapa base
        self.chk_mapbase = QCheckBox("Usar mapa base (OSM)")
        self.chk_mapbase.toggled.connect(self._toggle_mapbase)
        control.addWidget(self.chk_mapbase)

        # Proyecto / Formato
        ff = QHBoxLayout()
        ff.addWidget(QLabel("Proyecto:"))
        self.le_nombre = QLineEdit()
        ff.addWidget(self.le_nombre)
        ff.addWidget(QLabel("Formato:"))
        self.cb_format = QComboBox()
        self.cb_format.addItems([".kml",".kmz",".shp"])
        ff.addWidget(self.cb_format)
        control.addLayout(ff)

        # Botón seleccionar carpeta
        bl = QHBoxLayout()
        bl.addStretch()
        btn = QPushButton("Seleccionar carpeta")
        btn.clicked.connect(self._on_guardar)
        bl.addWidget(btn)
        control.addLayout(bl)

        ##################
        # Lienzo (canvas)#
        ##################
        self.canvas = CanvasView()
        self.scene  = QGraphicsScene(self.canvas)
        self.canvas.setScene(self.scene)
        self.canvas.setRenderHint(QPainter.Antialiasing)
        
        self.canvas.setMinimumSize(400,300)
        self.canvas.setStyleSheet("background-color:white; border:1px solid #ccc; padding:8px;")
        # Permitir desplazamiento con el cursor en lugar de barras de scroll
        self.canvas.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.canvas.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.canvas.setDragMode(QGraphicsView.ScrollHandDrag)

        # Vista web con Leaflet
        self.web_view = QWebEngineView()
        # Allow local HTML to load remote map tiles (e.g., OpenStreetMap)
        self.web_view.settings().setAttribute(
            QWebEngineSettings.LocalContentCanAccessRemoteUrls, True
        )
        html_path = os.path.join(os.path.dirname(__file__), "map_base.html")
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(html_path)))

        self.stack = QStackedLayout()
        self.stack.addWidget(self.canvas)
        self.stack.addWidget(self.web_view)
        self.stack.setCurrentWidget(self.canvas)
        view_container = QWidget()
        view_container.setLayout(self.stack)

        # ensamblar
        main_layout.addLayout(control,1)
        main_layout.addWidget(view_container,2)
        self.setCentralWidget(central)

    def _create_toolbar(self):
        tb = QToolBar("Principal")
        self.addToolBar(tb)

        # acciones básicas
        for nombre_icono, text, slot in [
            ("file-fill.svg",       "Nuevo",    self._on_new),
            ("folder-open-fill.svg","Abrir",    self._on_open),
            ("save-3-fill.svg",     "Guardar",  self._on_guardar),
            ("import-fill.svg",     "Importar", self._on_import),
            ("export-fill.svg",     "Exportar", self._on_export)
        ]:
            a = QAction(self._icono(nombre_icono), text, self)
            a.svg_filename = nombre_icono  # Store filename for updates
            a.triggered.connect(slot)
            tb.addAction(a)

            if nombre_icono == "save-3-fill.svg":
                csv_action = QAction(
                    self._icono("file-excel-2-fill.svg"),
                    "Exportar CSV",
                    self
                )
                csv_action.svg_filename = "file-excel-2-fill.svg"
                csv_action.setToolTip("Exportar tabla a CSV")
                csv_action.triggered.connect(self._export_csv)
                tb.addAction(csv_action)

        tb.addSeparator()

        for nombre_icono, text, slot in [
            ("arrow-left-box-fill.svg",  "Deshacer", self._on_undo),
            ("arrow-right-box-fill.svg", "Rehacer",  self._on_redo),
        ]:
            a = QAction(self._icono(nombre_icono), text, self)
            a.svg_filename = nombre_icono  # Store filename for updates
            a.triggered.connect(slot)
            tb.addAction(a)

        tb.addSeparator()

        # mostrar/ocultar lienzo
        # mostrar/ocultar lienzo
        tog = QAction(self._icono("edit-box-fill.svg"), "Mostrar/Ocultar lienzo", self)
        tog.svg_filename = "edit-box-fill.svg"
        tog.setCheckable(True); tog.setChecked(True)
        tog.toggled.connect(self.canvas.setVisible)
        tb.addAction(tog)
        btn_html = QAction(self._icono("code-box-fill.svg"), "HTML", self)
        btn_html.svg_filename = "code-box-fill.svg"
        btn_html.setToolTip("Generar resumen HTML con coordenadas, perímetro y área")
        btn_html.triggered.connect(self._on_export_html)
        tb.addAction(btn_html)

        sim_action = QAction("Simular", self)
        sim_action.setToolTip("Recargar vista de geometrías")
        sim_action.triggered.connect(self._on_simular)
        tb.addAction(sim_action)

        zoom_in_action = QAction("Zoom +", self)
        zoom_in_action.triggered.connect(self._on_zoom_in)
        tb.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom -", self)
        zoom_out_action.triggered.connect(self._on_zoom_out)
        tb.addAction(zoom_out_action)

        tb.addSeparator()

        # Edit mode toggle
        self.action_edit = QAction(self._icono("edit-2-fill.svg"), "Editar Geometrías", self)
        self.action_edit.svg_filename = "edit-2-fill.svg"
        self.action_edit.setCheckable(True)
        self.action_edit.setChecked(False)
        self.action_edit.setToolTip("Activar/desactivar modo de edición de geometrías")
        self.action_edit.toggled.connect(self._toggle_edit_mode)
        tb.addAction(self.action_edit)

        tb.addSeparator()

        # modo oscuro
        self.action_modo = QAction(self._icono("sun-fill.svg"), "Modo claro", self)
        self.action_modo.setCheckable(True)
        self.action_modo.setChecked(False)
        self.action_modo.toggled.connect(self._toggle_modo)
        tb.addAction(self.action_modo)

        tb.addSeparator()

        # configuraciones y ayuda
        for nombre_icono, text, slot in [
            ("settings-2-fill.svg", "Configuraciones", self._on_settings),
            ("question-fill.svg",   "Ayuda",           self._on_help),
        ]:
            a = QAction(self._icono(nombre_icono), text, self)
            a.svg_filename = nombre_icono  # Store filename for updates
            a.triggered.connect(slot)
            tb.addAction(a)

    def _export_csv(self):
        """
        Abre un diálogo para guardar un archivo CSV y vuelca en él todas las filas
        de self.table con las columnas: id, x (este), y (norte).
        Sólo escribe aquellas filas cuyo id no esté vacío.
        """
        filtro = "Archivos CSV (*.csv)"
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar tabla a CSV",
            "",
            filtro
        )
        if not ruta:
            return  # El usuario canceló

        if not ruta.lower().endswith(".csv"):
            ruta += ".csv"

        try:
            with open(ruta, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=",")
                # Escribir cabecera
                writer.writerow(["id", "x (este)", "y (norte)"])

                filas = self.table.rowCount()
                for r in range(filas):
                    item_id = self.table.item(r, 0)
                    item_x  = self.table.item(r, 1)
                    item_y  = self.table.item(r, 2)

                    # Tomar el texto o cadena vacía si no existe item
                    id_val = item_id.text().strip() if item_id else ""
                    x_val  = item_x.text().strip()  if item_x  else ""
                    y_val  = item_y.text().strip()  if item_y  else ""

                    # Si el ID está vacío, saltar esta fila
                    if id_val == "":
                        continue

                    # Escribir sólo las filas cuyo ID no esté vacío
                    writer.writerow([id_val, x_val, y_val])

            QMessageBox.information(self, "Exportar CSV", f"CSV guardado correctamente:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar CSV", f"No se pudo escribir el archivo:\n{e}")


    def _toggle_modo(self, activado):
        self._modo_oscuro = activado

        pal = QApplication.palette()

        if activado:
            # ─── MODO OSCURO ───
            pal.setColor(QPalette.Window,    QColor("#2b2b2b"))
            pal.setColor(QPalette.Base,      QColor("#2b2b2b"))
            pal.setColor(QPalette.WindowText, QColor("#ffffff"))
            pal.setColor(QPalette.Text,      QColor("#ffffff"))
            pal.setColor(QPalette.ButtonText, QColor("#ffffff"))
            pal.setColor(QPalette.Button,    QColor("#3b3b3b"))
            pal.setColor(QPalette.Highlight, QColor("#5a90ce"))
            pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))

            QApplication.setPalette(pal)
            
            # Stylesheet para widgets específicos que no respetan la paleta completamente
            dark_stylesheet = """
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QComboBox {
                    background-color: #3b3b3b;
                    color: #ffffff;
                    border: 1px solid #555;
                    padding: 4px;
                    border-radius: 3px;
                }
                QComboBox::drop-down {
                    border: 0px;
                    background: #3b3b3b;
                }
                QComboBox QAbstractItemView {
                    background-color: #3b3b3b;
                    color: #ffffff;
                    selection-background-color: #5a90ce;
                }
                QLineEdit {
                    background-color: #3b3b3b;
                    color: #ffffff;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 4px;
                }
                QTableWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    gridline-color: #444;
                    border: 1px solid #555;
                }
                QHeaderView::section {
                    background-color: #3b3b3b;
                    color: #ffffff;
                    border: 1px solid #444;
                    padding: 4px;
                }
                QPushButton {
                    background-color: #3b3b3b;
                    color: #ffffff;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #4b4b4b;
                }
                QPushButton:pressed {
                    background-color: #2a2a2a;
                }
                QLabel {
                    color: #ffffff;
                }
                QCheckBox {
                    color: #ffffff;
                }
                QGroupBox {
                    border: 1px solid #555;
                    margin-top: 1.1em;
                    color: #ffffff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 3px;
                }
                QScrollBar:vertical {
                    border: none;
                    background: #2b2b2b;
                    width: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #555;
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            """
            QApplication.instance().setStyleSheet(dark_stylesheet)

            self.action_modo.setIcon(self._icono("moon-fill.svg"))
            self.action_modo.setText("Modo oscuro")
        else:
            # ─── MODO CLARO ───
            pal.setColor(QPalette.Window,    QColor("#ffffff"))
            pal.setColor(QPalette.Base,      QColor("#ffffff"))
            pal.setColor(QPalette.WindowText, QColor("#000000"))
            pal.setColor(QPalette.Text,      QColor("#000000"))
            pal.setColor(QPalette.ButtonText, QColor("#000000"))
            pal.setColor(QPalette.Button,    QColor("#f0f0f0"))
            pal.setColor(QPalette.Highlight, QColor("#308cc6"))
            pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))

            QApplication.setPalette(pal)
            QApplication.instance().setStyleSheet("")

            self.action_modo.setIcon(self._icono("sun-fill.svg"))
            self.action_modo.setText("Modo claro")
            
        # Update all icons in the application
        self._update_icons()
        
        # Update validator theme
        if hasattr(self, 'coord_validator'):
            self.coord_validator.set_dark_mode(activado)

    def _update_icons(self):
        """Update all icons based on current theme color."""
        # Update actions in the main window
        for action in self.findChildren(QAction):
            if hasattr(action, 'svg_filename'):
                action.setIcon(self._icono(action.svg_filename))

    def _on_cell_changed(self, item):
        r, c = item.row(), item.column()
        # auto-agregar fila nueva
        if c in (1,2):
            xi = self.table.item(r,1); yi = self.table.item(r,2)
            if xi and yi and xi.text().strip() and yi.text().strip():
                if r == self.table.rowCount()-1:
                    nr = self.table.rowCount()
                    self.table.insertRow(nr)
                    id_it = QTableWidgetItem(str(nr+1))
                    id_it.setFlags(Qt.ItemIsEnabled)
                    self.table.setItem(nr,0,id_it)
        # refresca preview
        try:
            mgr = self._build_manager_from_table()
            self._redraw_scene(mgr)
        except (ValueError, TypeError) as e:
            print(f"Error al construir features para preview: {e}")


    def _on_cell_clicked(self, row, col):
        if col == 0:
            sel = self.table.selectionModel()
            sel.clearSelection()
            for cc in (1,2):
                idx = self.table.model().index(row,cc)
                sel.select(idx, QItemSelectionModel.Select)
            self.table.setCurrentCell(row,1)

    def _show_table_menu(self, pos):
        menu = QMenu()
        menu.addAction("Añadir fila", self._add_row)
        menu.addAction("Eliminar fila", self._delete_row)
        menu.addSeparator()
        menu.addAction("Copiar", self._copy_selection)
        menu.addAction("Pegar", self._paste_to_table)
        menu.addSeparator()
        
        # Nuevo submenú: Tipo de vértice
        vertex_type_menu = menu.addMenu("Tipo de vértice")
        
        current_row = self.table.currentRow()
        is_curve = current_row in self.table.curve_rows
        
        # Opciones con checkmark
        punto_action = vertex_type_menu.addAction("Punto")
        curva_action = vertex_type_menu.addAction("Curva")
        
        # Marcar la opción actual
        if is_curve:
            curva_action.setCheckable(True)
            curva_action.setChecked(True)
        else:
            punto_action.setCheckable(True)
            punto_action.setChecked(True)
        
        # Conectar acciones
        punto_action.triggered.connect(lambda: self._convert_to_point(current_row))
        curva_action.triggered.connect(lambda: self._convert_to_curve(current_row))
        
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _copy_selection(self):
        ranges = self.table.selectedRanges()
        if not ranges:
            return
        text = ""
        for r in ranges:
            for row in range(r.topRow(), r.bottomRow()+1):
                parts = []
                for col in range(r.leftColumn(), r.rightColumn()+1):
                    itm = self.table.item(row,col)
                    parts.append(itm.text() if itm else "")
                text += "\t".join(parts) + "\n"
        QApplication.clipboard().setText(text)

    def _convert_to_curve(self, row):
        """Convierte una fila a tipo curva."""
        if row >= 0:
            self.table.mark_as_curve(row)
            # Refresh preview após conversión
            try:
                mgr = self._build_manager_from_table()
                self._redraw_scene(mgr)
            except (ValueError, TypeError) as e:
                print(f"Error al construir features para preview: {e}")
    
    def _convert_to_point(self, row):
        """Convierte una fila a tipo punto."""
        if row >= 0:
            self.table.convert_to_point(row)
            # Refresh preview after conversion
            try:
                mgr = self._build_manager_from_table()
                self._redraw_scene(mgr)
            except (ValueError, TypeError) as e:
                print(f"Error al construir features para preview: {e}")

    def _add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        id_it = QTableWidgetItem(str(r + 1))
        id_it.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(r, 0, id_it)
        self.table.setCurrentCell(r, 1)
        item = QTableWidgetItem("")
        self.table.setItem(r, 1, item)
        self.table.editItem(item)

    def _delete_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
        try:
            mgr = self._build_manager_from_table()
            self._redraw_scene(mgr)
        except (ValueError, TypeError) as e:
            print(f"Error al construir features para preview tras eliminar fila: {e}")


    def _paste_to_table(self):
        lines = QApplication.clipboard().text().splitlines()
        r = self.table.currentRow()
        if r < 0:
            r = 0
            if self.table.item(r,0) and not (self.table.item(r,0).flags() & Qt.ItemIsEditable):
                pass

        for ln_idx, ln in enumerate(lines):
            if not ln.strip():
                continue

            current_id_item = self.table.item(r, 0)
            is_id_cell_uneditable = current_id_item and not (current_id_item.flags() & Qt.ItemIsEditable)

            if r >= self.table.rowCount():
                self.table.insertRow(r)
                id_it = QTableWidgetItem(str(r+1))
                id_it.setFlags(Qt.ItemIsEnabled)
                self.table.setItem(r,0,id_it)
            elif is_id_cell_uneditable and (self.table.item(r,1) and self.table.item(r,1).text() or \
                                          self.table.item(r,2) and self.table.item(r,2).text()):
                pass

            pts = [p.strip() for p in ln.split(",")]
            if len(pts) < 2:
                pts = [p.strip() for p in ln.split("\t")]

            if len(pts) >= 2:
                try:
                    float(pts[0].replace(',','.'))
                    float(pts[1].replace(',','.'))
                except ValueError:
                    QMessageBox.warning(self, "Error de Pegado", f"Línea '{ln}' no contiene coordenadas X,Y numéricas válidas.")
                    continue

                self.table.setItem(r,1, QTableWidgetItem(pts[0].replace(',','.')))
                self.table.setItem(r,2, QTableWidgetItem(pts[1].replace(',','.')))
                r += 1

        try:
            mgr = self._build_manager_from_table()
            self._redraw_scene(mgr)
        except (ValueError, TypeError) as e:
             print(f"Error al construir features para preview tras pegar: {e}")

    def _toggle_mapbase(self, checked):
        """Toggle basemap tiles visibility via JS, keeping the web view active."""
        # Ensure web view is the current widget
        self.stack.setCurrentWidget(self.web_view)
        
        # Call JS to show/hide tiles (with safety check)
        js_code = f"if (typeof toggleBasemap === 'function') {{ toggleBasemap({'true' if checked else 'false'}); }}"
        self.web_view.page().runJavaScript(js_code)
        
        # If we just enabled it, we might want to refresh features
        if checked:
            try:
                mgr = self._build_manager_from_table()
                self._update_web_features(mgr)
            except Exception as e:
                QMessageBox.warning(self, "Mapa base", f"No se pudo cargar el mapa: {e}")
        else:
            self.stack.setCurrentWidget(self.canvas)


    def _build_manager_from_table(self):
        """
        Build CoordinateManager from table coordinates.
        Handles all coordinate systems: UTM, DD, DMS, Web Mercator.
        Converts non-UTM coordinates to UTM for the manager.
        """
        # Skip geometry building if we're in the middle of coordinate conversion
        if getattr(self, '_is_converting', False):
            # Return empty manager to avoid "Insufficient Data" dialogs during conversion
            zone = int(self.cb_zona.currentText()) if self.cb_zona.currentText() else 14
            hemisphere = self.cb_hemisferio.currentText()
            return CoordinateManager(hemisphere=hemisphere, zone=zone)
        
        coords = []
        cs_text = self.cb_coord_system.currentText()
        
        # Get current zone and hemisphere for UTM conversions
        zone = int(self.cb_zona.currentText()) if self.cb_zona.currentText() else 14
        hemisphere = self.cb_hemisferio.currentText()
        
        for r in range(self.table.rowCount()):
            # Skip hidden rows (curve sub-rows)
            if self.table.isRowHidden(r):
                continue
            
            # Check if this is a curve row
            if r in self.table.curve_rows:
                # Process curve: get main coordinate and curve parameters
                xi = self.table.item(r, 1)
                yi = self.table.item(r, 2)
                
                if xi and yi and xi.text().strip() and yi.text().strip():
                    try:
                        x_str = xi.text().strip()
                        y_str = yi.text().strip()
                        
                        # Convert start point to UTM
                        start_point_utm = None
                        if cs_text == "UTM":
                            start_point_utm = (float(x_str), float(y_str))
                        elif cs_text == "Geographic (Decimal Degrees)":
                            lon, lat = float(x_str), float(y_str)
                            utm_epsg = get_utm_epsg(zone, hemisphere)
                            transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
                            start_point_utm = transformer.transform(lon, lat)
                        elif cs_text == "Geographic (DMS)":
                            is_valid_lon, lon = validate_dms_coordinate(x_str, is_longitude=True)
                            is_valid_lat, lat = validate_dms_coordinate(y_str, is_longitude=False)
                            if is_valid_lon and is_valid_lat:
                                utm_epsg = get_utm_epsg(zone, hemisphere)
                                transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
                                start_point_utm = transformer.transform(lon, lat)
                        elif cs_text == "Web Mercator":
                            x_m, y_m = float(x_str), float(y_str)
                            t1 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
                            lon, lat = t1.transform(x_m, y_m)
                            utm_epsg = get_utm_epsg(zone, hemisphere)
                            t2 = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
                            start_point_utm = t2.transform(lon, lat)
                        
                        if start_point_utm:
                            # Get curve parameters
                            params = self.table.get_curve_parameters(r)
                            if params and params['delta'] and params['radio'] and params['centro']:
                                from core.curve_geometry import CurveSegment
                                
                                # Parse centro (format: "X, Y")
                                centro_str = params['centro'].replace(',', ' ').split()
                                if len(centro_str) >= 2:
                                    centro_utm = (float(centro_str[0]), float(centro_str[1]))
                                    
                                    # Create curve segment
                                    curve = CurveSegment(
                                        start_point=start_point_utm,
                                        center=centro_utm,
                                        delta=params['delta'],
                                        radius=float(params['radio'])
                                    )
                                    
                                    # Validate curve
                                    is_valid, error_msg = curve.validate()
                                    if is_valid:
                                        # Densify curve
                                        num_points = getattr(self.table, 'curve_densification_points', 15)
                                        densified_points = curve.densify(num_points)
                                        # Add densified points to coords
                                        coords.extend(densified_points)
                                    else:
                                        logger.warning(f"Curva en fila {r} inválida: {error_msg}")
                                        # Add just the start point
                                        coords.append(start_point_utm)
                            else:
                                # Curve without complete parameters, add as regular point
                                coords.append(start_point_utm)
                    except Exception as e:
                        logger.warning(f"Error processing curve at row {r}: {e}")
                        continue
            else:
                # Regular point processing
                xi = self.table.item(r, 1)
                yi = self.table.item(r, 2)
                if xi and yi and xi.text().strip() and yi.text().strip():
                    try:
                        x_str = xi.text().strip()
                        y_str = yi.text().strip()
                        
                        # Convert coordinates to UTM based on current system
                        if cs_text == "UTM":
                            # Already in UTM
                            x_val = float(x_str)
                            y_val = float(y_str)
                            coords.append((x_val, y_val))
                            
                        elif cs_text == "Geographic (Decimal Degrees)":
                            # Convert DD to UTM
                            lon = float(x_str)
                            lat = float(y_str)
                            utm_epsg = get_utm_epsg(zone, hemisphere)
                            transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
                            x_utm, y_utm = transformer.transform(lon, lat)
                            coords.append((x_utm, y_utm))
                            
                        elif cs_text == "Geographic (DMS)":
                            # Parse DMS and convert to UTM
                            is_valid_lon, lon = validate_dms_coordinate(x_str, is_longitude=True)
                            is_valid_lat, lat = validate_dms_coordinate(y_str, is_longitude=False)
                            if is_valid_lon and is_valid_lat:
                                utm_epsg = get_utm_epsg(zone, hemisphere)
                                transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
                                x_utm, y_utm = transformer.transform(lon, lat)
                                coords.append((x_utm, y_utm))
                            
                        elif cs_text == "Web Mercator":
                            # Convert Web Mercator to UTM
                            x_mercator = float(x_str)
                            y_mercator = float(y_str)
                            # First to WGS84
                            transformer_to_wgs84 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
                            lon, lat = transformer_to_wgs84.transform(x_mercator, y_mercator)
                            # Then to UTM
                            utm_epsg = get_utm_epsg(zone, hemisphere)
                            transformer_to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
                            x_utm, y_utm = transformer_to_utm.transform(lon, lat)
                            coords.append((x_utm, y_utm))
                            
                    except Exception as e:
                        logger.warning(f"Error parsing coordinate at row {r}: {e}")
                        continue

        mgr = CoordinateManager(
            hemisphere=hemisphere,
            zone=zone
        )
        nid = 1

        if coords:
            if self.chk_punto.isChecked():
                for x, y in coords:
                    try:
                        mgr.add_feature(nid, GeometryType.PUNTO, [(x, y)])
                        nid += 1
                    except Exception as e:
                        error = GeometryBuildError(
                            f"No se pudo crear el punto ID {nid}",
                            details=str(e)
                        )
                        logger.error(f"Error creating point {nid}: {e}")
                        show_error_dialog(self, error)

            if self.chk_polilinea.isChecked():
                if len(coords) >= 2:
                    try:
                        mgr.add_feature(nid, GeometryType.POLILINEA, coords)
                        nid += 1
                    except Exception as e:
                        error = GeometryBuildError(
                            f"No se pudo crear la polilínea ID {nid}",
                            details=str(e)
                        )
                        logger.error(f"Error creating polyline {nid}: {e}")
                        show_error_dialog(self, error)
                elif self.chk_polilinea.isEnabled() and self.chk_polilinea.isChecked():
                    error = InsufficientDataError(
                        "Se necesitan al menos 2 coordenadas para una Polilínea"
                    )
                    logger.warning("Insufficient coordinates for polyline")
                    show_error_dialog(self, error)

            if self.chk_poligono.isChecked():
                if len(coords) >= 3:
                    try:
                        mgr.add_feature(nid, GeometryType.POLIGONO, coords)
                        nid += 1
                    except Exception as e:
                        error = GeometryBuildError(
                            f"No se pudo crear el polígono ID {nid}",
                            details=str(e)
                        )
                        logger.error(f"Error creating polygon {nid}: {e}")
                        show_error_dialog(self, error)
                elif self.chk_poligono.isEnabled() and self.chk_poligono.isChecked():
                    error = InsufficientDataError(
                        "Se necesitan al menos 3 coordenadas para un Polígono"
                    )
                    logger.warning("Insufficient coordinates for polygon")
                    show_error_dialog(self, error)
        return mgr

    def _redraw_scene(self, mgr):
        # Remove old editable geometries BEFORE clearing scene
        # (scene.clear() deletes the C++ objects)
        self._editable_geometries.clear()
        
        # Now clear the scene
        self.scene.clear()
        
        if not mgr:
            return

        features_for_paths = mgr.get_features()
        
        # Draw geometry paths
        for path, pen in GeometryBuilder.paths_from_features(features_for_paths):
            geometry_item = self.scene.addPath(path, pen)
            
            # If in edit mode, create editable points for this geometry
            if self._edit_mode:
                # Get coordinates for this geometry's features
                # We'll create editable points for all coordinates in the table
                points = []
                for r in range(self.table.rowCount()):
                    x_item = self.table.item(r, 1)
                    y_item = self.table.item(r, 2)
                    if x_item and y_item and x_item.text().strip() and y_item.text().strip():
                        try:
                            x = float(x_item.text())
                            y = float(y_item.text())
                            points.append((x, y, r))
                        except ValueError:
                            continue
                
                if points:
                    editable_geom = EditableGeometry(geometry_item, points, self.table)
                    editable_geom.show_points()
                    self._editable_geometries.append(editable_geom)

        if self.chk_punto.isChecked():
            for feat in mgr.get_features():
                if feat["type"] == GeometryType.PUNTO and feat["coords"]:
                    x, y = feat["coords"][0]
                    size = self.point_size * self.draw_scale
                    ellipse = self.scene.addEllipse(
                        x - size / 2,
                        y - size / 2,
                        size,
                        size,
                        QPen(Qt.red),
                        QBrush(Qt.red),
                    )
                    ellipse.setZValue(1)

                    label = QGraphicsTextItem(str(feat.get("id", "")))
                    f = label.font()
                    f.setPointSizeF(self.font_size * self.draw_scale)
                    label.setFont(f)
                    label.setDefaultTextColor(Qt.darkBlue)
                    label.setPos(x + size / 2 + 1, y + size / 2 + 1)
                    label.setZValue(1)
                    self.scene.addItem(label)

        if self.chk_mapbase.isChecked():
            self._update_web_features(mgr)

    def _toggle_edit_mode(self, enabled):
        """Toggle geometry editing mode."""
        self._edit_mode = enabled
        logger.info(f"Edit mode {'enabled' if enabled else 'disabled'}")
        
        # Update button appearance
        if enabled:
            self.action_edit.setText("Editar Geometrías (Activo)")
            # Show status message
            logger.info("Modo de edición activado - Arrastre los puntos para editar")
        else:
            self.action_edit.setText("Editar Geometrías")
            logger.info("Modo de edición desactivado")
        
        # Redraw scene to show/hide editable points
        try:
            mgr = self._build_manager_from_table()
            self._redraw_scene(mgr)
        except Exception as e:
            logger.error(f"Error toggling edit mode: {e}")

    def _update_web_features(self, mgr):
        if not self.chk_mapbase.isChecked() or not mgr:
            return
        hemisphere = self.cb_hemisferio.currentText()
        zone = int(self.cb_zona.currentText())
        epsg = 32600 + zone if hemisphere.lower().startswith("n") else 32700 + zone
        transformer = Transformer.from_crs(f"epsg:{epsg}", "epsg:4326", always_xy=True)
        feats = []
        for feat in mgr.get_features():
            latlon = [transformer.transform(x, y) for x, y in feat["coords"]]
            if feat["type"] == GeometryType.PUNTO:
                geom = {"type": "Point", "coordinates": latlon[0]}
            elif feat["type"] == GeometryType.POLILINEA:
                geom = {"type": "LineString", "coordinates": latlon}
            else:
                geom = {"type": "Polygon", "coordinates": [latlon]}
            feats.append({"type": "Feature", "properties": {"id": feat["id"]}, "geometry": geom})

        geojson = {"type": "FeatureCollection", "features": feats}
        js = (
            "window.clearFeatures && window.clearFeatures();"
            f"window.addFeature && window.addFeature({json.dumps(geojson)})"
        )
        self.web_view.page().runJavaScript(js)

    def _on_guardar(self):
        dirp = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de proyecto")
        if not dirp:
            return
        proj = self.le_nombre.text().strip() or "proyecto"
        full_path_filename = os.path.join(dirp, proj + self.cb_format.currentText())

        try:
            mgr = self._build_manager_from_table()
        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Error en datos de tabla", f"No se pueden generar las geometrías para exportar: {e}")
            return

        selected_format = self.cb_format.currentText()

        features = mgr.get_features()
        if not features:
            QMessageBox.warning(self, "Nada para exportar", "No hay geometrías definidas para exportar.")
            return

        hemisphere = self.cb_hemisferio.currentText()
        zone = self.cb_zona.currentText()

        try:
            export_successful = False
            if selected_format == ".kml":
                KMLExporter.export(features, full_path_filename, hemisphere, zone)
                export_successful = True
            elif selected_format == ".kmz":
                KMZExporter.export(features, full_path_filename, hemisphere, zone)
                export_successful = True
            elif selected_format == ".shp":
                ShapefileExporter.export(features, full_path_filename, hemisphere, zone)
                export_successful = True
            else:
                QMessageBox.warning(self, "Formato no soportado",
                                    f"La exportación al formato '{selected_format}' aún no está implementada.")
                return

            if export_successful:
                QMessageBox.information(self, "Éxito", f"Archivo guardado en:\n{full_path_filename}")

        except ImportError as ie:
            QMessageBox.critical(self, "Error de dependencia",
                                 f"No se pudo exportar a '{selected_format}'. Dependencia faltante: {str(ie)}. Verifique la instalación.")
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar",
                                 f"Ocurrió un error al guardar en formato '{selected_format}':\n{str(e)}")

    def _on_export(self):
        self._on_guardar()

    def _on_new(self):
        self.table.clearContents()
        self.table.setRowCount(1)
        first = QTableWidgetItem("1"); first.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(0,0,first)
        if self.scene:
            self.scene.clear()

        self.chk_punto.setChecked(False)
        self.chk_polilinea.setChecked(False)
        self.chk_poligono.setChecked(False)
        self.le_nombre.clear()
        # Clear import tracking
        self._import_zone = None
        self._import_hemisphere = None
        self._has_imported_data = False

    def _on_zone_hemisphere_changed(self):
        """
        Handler for when zone or hemisphere changes.
        Warns user if they have imported data that will become invalid.
        """
        if not self._has_imported_data:
            return
        
        current_zone = self.cb_zona.currentText()
        current_hemisphere = self.cb_hemisferio.currentText()
        
        # Check if zone/hemisphere changed from import settings
        if (self._import_zone and self._import_hemisphere and
            (str(self._import_zone) != current_zone or 
             self._import_hemisphere != current_hemisphere)):
            
            reply = QMessageBox.warning(
                self,
                "Cambio de Zona/Hemisferio",
                f"Las coordenadas fueron importadas usando Zona {self._import_zone} {self._import_hemisphere}.\\n\\n"
                f"Cambiar a Zona {current_zone} {current_hemisphere} hará que las coordenadas "
                f"se interpreten incorrectamente en el mapa base.\\n\\n"
                f"¿Desea limpiar la tabla y volver a importar con las nuevas configuraciones?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self._on_new()

    def _on_coord_system_changed(self):
        """
        Handler for when coordinate system changes.
        Shows/hides zone and hemisphere selectors based on requirements.
        Updates table column headers.
        Automatically converts existing coordinates to the new system using cache.
        """
        cs_text = self.cb_coord_system.currentText()
        prev_cs = getattr(self, '_prev_coord_system', "UTM")
        
        # If system didn't actually change, just update UI
        if cs_text == prev_cs:
            self._update_ui_for_coordinate_system(cs_text)
            return
        
        # Check if we have cached coordinates for the target system
        cached_coords = self._coord_cache.get(cs_text, [])
        
        print(f"[DEBUG] System change: {prev_cs} -> {cs_text}")
        print(f"[DEBUG] Cache for '{cs_text}': {len(cached_coords)} coordinates")
        
        if cached_coords:
            # Use cached coordinates - instant switch!
            print(f"[DEBUG] Using cached coordinates for '{cs_text}'")
            self._restore_coordinates_from_cache(cs_text)
        else:
            # Check if we have data to convert
            has_data = False
            for row in range(self.table.rowCount()):
                x_item = self.table.item(row, 1)
                y_item = self.table.item(row, 2)
                if x_item and y_item and x_item.text().strip() and y_item.text().strip():
                    has_data = True
                    break
            
            # Convert and cache if we have data
            if has_data:
                print(f"[DEBUG] Converting from '{prev_cs}' to '{cs_text}'")
                # Save current system's coordinates to cache before converting
                self._save_coordinates_to_cache(prev_cs)
                # Convert to new system
                self._convert_table_coordinates(prev_cs, cs_text)
                # Save converted coordinates to cache
                self._save_coordinates_to_cache(cs_text)
        
        # Update UI for the new coordinate system
        self._update_ui_for_coordinate_system(cs_text)
        
        # Update validation delegate with new coordinate system
        hemisphere = self.cb_hemisferio.currentText()
        self.coord_validator.set_coordinate_system(cs_text,hemisphere)
        
        # Store current system for next change
        self._prev_coord_system = cs_text
        
        # Auto-redraw the map with the new coordinates
        try:
            mgr = self._build_manager_from_table()
            self._redraw_scene(mgr)
        except Exception as e:
            print(f"[DEBUG] Auto-redraw failed: {e}")
            # Silent failure - user can manually refresh if needed
    
    def _update_ui_for_coordinate_system(self, cs_text: str):
        """Update UI elements based on selected coordinate system."""
        if cs_text == "UTM":
            self.lbl_hemisferio.setVisible(True)
            self.cb_hemisferio.setVisible(True)
            self.lbl_zona.setVisible(True)
            self.cb_zona.setVisible(True)
            self.table.setHorizontalHeaderLabels(["ID", "Este (X)", "Norte (Y)"])
            
        elif cs_text == "Geographic (Decimal Degrees)":
            self.lbl_hemisferio.setVisible(False)
            self.cb_hemisferio.setVisible(False)
            self.lbl_zona.setVisible(False)
            self.cb_zona.setVisible(False)
            self.table.setHorizontalHeaderLabels(["ID", "Longitud", "Latitud"])
            
        elif cs_text == "Geographic (DMS)":
            self.lbl_hemisferio.setVisible(False)
            self.cb_hemisferio.setVisible(False)
            self.lbl_zona.setVisible(False)
            self.cb_zona.setVisible(False)
            self.table.setHorizontalHeaderLabels(["ID", "Longitud (DMS)", "Latitud (DMS)"])
            
        elif cs_text == "Web Mercator":
            self.lbl_hemisferio.setVisible(False)
            self.cb_hemisferio.setVisible(False)
            self.lbl_zona.setVisible(False)
            self.cb_zona.setVisible(False)
            self.table.setHorizontalHeaderLabels(["ID", "X (metros)", "Y (metros)"])
    
    def _convert_table_coordinates(self, from_system: str, to_system: str):
        """
        Convert all coordinates in the table from one system to another.
        
        Args:
            from_system: Source coordinate system name
            to_system: Target coordinate system name
        """
        # Store checkbox states and disable them during conversion
        punto_checked = self.chk_punto.isChecked()
        polilinea_checked = self.chk_polilinea.isChecked()
        poligono_checked = self.chk_poligono.isChecked()
        
        self.chk_punto.setChecked(False)
        self.chk_polilinea.setChecked(False)
        self.chk_poligono.setChecked(False)
        
        try:
            # Set flag to prevent geometry building during conversion
            self._is_converting = True
            
            # Get current zone and hemisphere for UTM conversions
            zone = int(self.cb_zona.currentText()) if self.cb_zona.currentText() else 14
            hemisphere = self.cb_hemisferio.currentText()
            
            # Create transformers based on systems
            # All conversions go through WGS84 (EPSG:4326) as intermediate
            
            for row in range(self.table.rowCount()):
                x_item = self.table.item(row, 1)
                y_item = self.table.item(row, 2)
                
                if not x_item or not y_item:
                    continue
                    
                x_str = x_item.text().strip()
                y_str = y_item.text().strip()
                
                if not x_str or not y_str:
                    continue
                
                try:
                    # Step 1: Convert FROM source system TO WGS84 (lat/lon)
                    if from_system == "UTM":
                        x_val = float(x_str)
                        y_val = float(y_str)
                        utm_epsg = get_utm_epsg(zone, hemisphere)
                        transformer = Transformer.from_crs(f"EPSG:{utm_epsg}", "EPSG:4326", always_xy=True)
                        lon, lat = transformer.transform(x_val, y_val)
                        
                    elif from_system == "Geographic (Decimal Degrees)":
                        lon = float(x_str)
                        lat = float(y_str)
                        
                    elif from_system == "Geographic (DMS)":
                        # Parse DMS strings
                        is_valid_lon, lon = validate_dms_coordinate(x_str, is_longitude=True)
                        is_valid_lat, lat = validate_dms_coordinate(y_str, is_longitude=False)
                        if not (is_valid_lon and is_valid_lat):
                            continue
                            
                    elif from_system == "Web Mercator":
                        x_val = float(x_str)
                        y_val = float(y_str)
                        transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
                        lon, lat = transformer.transform(x_val, y_val)
                    
                    # Step 2: Convert FROM WGS84 TO target system
                    if to_system == "UTM":
                        utm_epsg = get_utm_epsg(zone, hemisphere)
                        transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
                        x_new, y_new = transformer.transform(lon, lat)
                        x_item.setText(f"{x_new:.2f}")
                        y_item.setText(f"{y_new:.2f}")
                        
                    elif to_system == "Geographic (Decimal Degrees)":
                        x_item.setText(f"{lon:.6f}")
                        y_item.setText(f"{lat:.6f}")
                        
                    elif to_system == "Geographic (DMS)":
                        # Convert to DMS format
                        lon_d, lon_m, lon_s, lon_dir = dd_to_dms(lon, is_longitude=True)
                        lat_d, lat_m, lat_s, lat_dir = dd_to_dms(lat, is_longitude=False)
                        x_item.setText(format_dms(lon_d, lon_m, lon_s, lon_dir))
                        y_item.setText(format_dms(lat_d, lat_m, lat_s, lat_dir))
                        
                    elif to_system == "Web Mercator":
                        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
                        x_new, y_new = transformer.transform(lon, lat)
                        x_item.setText(f"{x_new:.2f}")
                        y_item.setText(f"{y_new:.2f}")
                        
                except (ValueError, Exception) as e:
                    print(f"Error converting row {row}: {e}")
                    continue
            
            # Removed success message to avoid triggering dialogs during conversion
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de Conversión",
                f"Error al convertir coordenadas: {str(e)}"
            )
        finally:
            # Always clear the conversion flag
            self._is_converting = False
            # Restore checkbox states WITHOUT triggering signals
            self.chk_punto.blockSignals(True)
            self.chk_polilinea.blockSignals(True)
            self.chk_poligono.blockSignals(True)
            
            self.chk_punto.setChecked(punto_checked)
            self.chk_polilinea.setChecked(polilinea_checked)
            self.chk_poligono.setChecked(poligono_checked)
            
            self.chk_punto.blockSignals(False)
            self.chk_polilinea.blockSignals(False)
            self.chk_poligono.blockSignals(False)
    
    def _save_coordinates_to_cache(self, system: str):
        """Save current table coordinates to cache for the given system."""
        coords = []
        for row in range(self.table.rowCount()):
            x_item = self.table.item(row, 1)
            y_item = self.table.item(row, 2)
            if x_item and y_item and x_item.text().strip() and y_item.text().strip():
                coords.append({
                    'row': row,
                    'x': x_item.text().strip(),
                    'y': y_item.text().strip()
                })
        self._coord_cache[system] = coords
        print(f"[DEBUG] Saved {len(coords)} coordinates to cache for '{system}'")
    
    def _restore_coordinates_from_cache(self, system: str):
        """Restore table coordinates from cache for the given system."""
        cached = self._coord_cache.get(system, [])
        print(f"[DEBUG] Restoring {len(cached)} coordinates from cache for '{system}'")
        
        # Block table signals to prevent triggering geometry updates during restoration
        self.table.blockSignals(True)
        
        try:
            for coord in cached:
                row = coord['row']
                if row < self.table.rowCount():
                    x_item = self.table.item(row, 1)
                    y_item = self.table.item(row, 2)
                    if x_item:
                        x_item.setText(coord['x'])
                    if y_item:
                        y_item.setText(coord['y'])
        finally:
            # Always unblock signals
            self.table.blockSignals(False)



    def _on_open(self):
        filters = "Archivos de Proyecto SIG (*.kml *.kmz *.shp);;Todos los archivos (*)"
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Proyecto", "", filters
        )
        if path:
            QMessageBox.information(self, "Abrir Proyecto", f"Funcionalidad de abrir proyecto '{path}' aún no implementada.")
            print(f"Abrir proyecto: {path}")

    def _on_import(self):
        filters = "Archivos KML (*.kml);;Archivos Shapefile (*.shp);;Archivos de Coordenadas (*.csv *.txt);;Todos los archivos (*)"
        path, selected_filter = QFileDialog.getOpenFileName(
            self, "Importar Coordenadas o Geometrías", "", filters
        )

        if not path:
            return

        file_ext = os.path.splitext(path)[1].lower()

        if file_ext in ['.csv', '.txt']:
            try:
                # 1) Importamos todos los “features” desde el CSV.
                #    Nuestros CSV exportados usan el orden id,x,y con cabecera.
                imported_features = CSVImporter.import_file(
                    path,
                    x_col_idx=1,
                    y_col_idx=2,
                    id_col_idx=0,
                    skip_header=1,
                )

                # 2) Filtramos solo aquellos que tengan:
                #    a) Un campo "id" no vacío (feat.get("id") != "").
                #    b) Al menos una coordenada válida en feat["coords"][0].
                valid_feats = []
                for feat in imported_features:
                    raw_id = str(feat.get("id", "")).strip()
                    coords_list = feat.get("coords", [])
                    # Comprobamos que el ID no esté vacío y que exista coords_list[0] con 2 valores
                    if raw_id != "" \
                    and coords_list \
                    and isinstance(coords_list[0], (list, tuple)) \
                    and len(coords_list[0]) == 2:
                        x0, y0 = coords_list[0]
                        # Comprobamos también que X y Y no sean None ni cadena vacía
                        if x0 is not None and y0 is not None \
                        and str(x0).strip() != "" and str(y0).strip() != "":
                            valid_feats.append(feat)

                if not valid_feats:
                    QMessageBox.information(
                        self,
                        "Importación CSV",
                        "No se importaron geometrías válidas desde el archivo."
                    )
                    return

                # 3) Limpiamos la tabla y creamos tantas filas como valid_feats haya
                self._on_new()
                self.table.setRowCount(len(valid_feats))

                # 4) Recorremos valid_feats, asignamos ID entero consecutivo y mostramos coords
                for i, feat in enumerate(valid_feats):
                    # Forzar ID entero: 1, 2, 3, ...
                    feat_id = i + 1
                    coords_list = feat.get("coords", [])

                    # Celda ID (solo números enteros, ya que raw_id no se usa)
                    id_item = QTableWidgetItem(str(feat_id))
                    id_item.setFlags(Qt.ItemIsEnabled)
                    self.table.setItem(i, 0, id_item)

                    # Celda X y Y con la primera coordenada válida
                    x_coord, y_coord = coords_list[0]
                    self.table.setItem(i, 1, QTableWidgetItem(str(x_coord)))
                    self.table.setItem(i, 2, QTableWidgetItem(str(y_coord)))

                # 5) Activar solamente el checkbox de Punto (porque importamos coordenadas sueltas)
                self.chk_punto.setChecked(True)
                self.chk_polilinea.setChecked(False)
                self.chk_poligono.setChecked(False)

                # 6) Reconstruir el manager y redibujar la escena
                try:
                    mgr = self._build_manager_from_table()
                    self._redraw_scene(mgr)
                    QMessageBox.information(
                        self,
                        "Importación CSV Exitosa",
                        f"{len(valid_feats)} puntos importados desde {os.path.basename(path)}."
                    )
                except (ValueError, TypeError) as e:
                    QMessageBox.critical(
                        self,
                        "Error al procesar datos importados",
                        f"Los datos CSV importados no pudieron ser procesados: {e}"
                    )

            except FileNotFoundError:
                QMessageBox.critical(self, "Error de Importación", f"Archivo no encontrado: {path}")
            except RuntimeError as e:
                QMessageBox.critical(self, "Error de Importación", f"Error al importar archivo CSV: {e}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Inesperado",
                    f"Ocurrió un error inesperado durante la importación CSV: {e}"
                )


            except FileNotFoundError:
                QMessageBox.critical(self, "Error de Importación", f"Archivo no encontrado: {path}")
            except RuntimeError as e:
                QMessageBox.critical(self, "Error de Importación", f"Error al importar archivo CSV: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error inesperado durante la importación CSV: {e}")

        elif file_ext == '.kml':
            try:
                hemisphere = self.cb_hemisferio.currentText()
                zone_str = self.cb_zona.currentText()
                if not zone_str:
                    QMessageBox.warning(self, "Zona no seleccionada", "Por favor, seleccione una zona UTM antes de importar KML.")
                    return
                zone = int(zone_str)

                imported_features = KMLImporter.import_file(path, hemisphere, zone)

                if not imported_features:
                    QMessageBox.information(self, "Importación KML", "No se importaron geometrías válidas desde el archivo KML.")
                    return

                self._on_new()

                # Track zone/hemisphere used for this import
                self._import_zone = zone
                self._import_hemisphere = hemisphere
                self._has_imported_data = True

                row_index = 0  # fila actual en la tabla

                for feat in imported_features:
                    feat_id = feat.get("id", row_index + 1)
                    coords = feat.get("coords", [])
                    geom_type = feat.get("type", "").lower()
                    if "polígono" in geom_type and len(coords) >= 3:
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])    

                    if not coords:
                        continue

                    for j, (x, y) in enumerate(coords):
                        if row_index >= self.table.rowCount():
                            self.table.insertRow(row_index)
                        id_str = f"{feat_id}.{j+1}" if len(coords) > 1 else str(feat_id)
                        id_item = QTableWidgetItem(id_str)
                        id_item.setFlags(Qt.ItemIsEnabled)
                        self.table.setItem(row_index, 0, id_item)
                        self.table.setItem(row_index, 1, QTableWidgetItem(f"{x:.2f}"))
                        self.table.setItem(row_index, 2, QTableWidgetItem(f"{y:.2f}"))
                        row_index += 1

                    # Activar el checkbox adecuado
                    if "punto" in geom_type:
                        self.chk_punto.setChecked(True)
                    if "polilínea" in geom_type or "linestring" in geom_type:
                        self.chk_polilinea.setChecked(True)
                    if "polígono" in geom_type or "polygon" in geom_type:
                        self.chk_poligono.setChecked(True)


                # No se cambian los checkboxes. El usuario debe seleccionar el tipo apropiado
                # para que _build_manager_from_table construya las geometrías deseadas.
                # Se informa al usuario.

                try:
                    mgr = self._build_manager_from_table()
                    self._redraw_scene(mgr)
                    QMessageBox.information(self, "Importación KML Exitosa",
                                            f"{len(imported_features)} geometrías importadas desde {os.path.basename(path)}.\n"
                                            "Active los checkboxes de tipo de geometría (Punto, Polilínea, Polígono)\n"
                                            "para visualizar y procesar los datos importados.")
                except (ValueError, TypeError) as e:
                     QMessageBox.critical(self, "Error al procesar datos KML importados",
                                          f"Los datos KML importados no pudieron ser procesados: {e}")

            except FileNotFoundError:
                QMessageBox.critical(self, "Error de Importación KML", f"Archivo no encontrado: {path}")
            except (RuntimeError, ValueError) as e:
                QMessageBox.critical(self, "Error de Importación KML", f"Error al importar archivo KML: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error inesperado durante la importación KML: {e}")
        
        elif file_ext == '.shp':
            try:
                logger.info(f"Importing shapefile: {path}")
                
                # Import shapefile with CRS detection
                imported_features, crs_string = ShapefileImporter.import_file(path)
                
                if not imported_features:
                    QMessageBox.information(self, "Importación Shapefile", "No se importaron geometrías válidas desde el shapefile.")
                    return
                
                # Handle CRS conversion if needed
                current_cs = self.cb_coord_system.currentText()
                
                if crs_string:
                    logger.info(f"Shapefile CRS: {crs_string}, Current system: {current_cs}")
                    
                    # Check if CRS conversion is needed
                    needs_conversion = False
                    if crs_string.startswith("EPSG:"):
                        epsg_code = int(crs_string.split(":")[1])
                        
                        # Check if it matches current system
                        if current_cs == "Geographic (Decimal Degrees)" and epsg_code != 4326:
                            needs_conversion = True
                        elif current_cs == "Web Mercator" and epsg_code != 3857:
                            needs_conversion = True
                        elif current_cs == "UTM":
                            # Check if it matches current UTM zone
                            zone = int(self.cb_zona.currentText()) if self.cb_zona.currentText() else 14
                            hemisphere = self.cb_hemisferio.currentText()
                            from utils.coordinate_systems import get_utm_epsg
                            current_utm_epsg = get_utm_epsg(zone, hemisphere)
                            if epsg_code != current_utm_epsg:
                                needs_conversion = True
                    
                    if needs_conversion:
                        # Ask user what to do
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Question)
                        msg.setWindowTitle("Sistema de Coordenadas Diferente")
                        msg.setText(f"El shapefile usa {crs_string}.\n\nSu sistema actual es: {current_cs}")
                        msg.setInformativeText("¿Qué desea hacer?")
                        convert_btn = msg.addButton("Convertir al sistema actual", QMessageBox.AcceptRole)
                        switch_btn = msg.addButton("Cambiar al sistema del shapefile", QMessageBox.RejectRole)
                        cancel_btn = msg.addButton("Cancelar", QMessageBox.RejectRole)
                        msg.exec()
                        
                        if msg.clickedButton() == cancel_btn:
                            return
                        elif msg.clickedButton() == switch_btn:
                            # Switch to shapefile's CRS
                            if epsg_code == 4326:
                                self.cb_coord_system.setCurrentText("Geographic (Decimal Degrees)")
                            elif epsg_code == 3857:
                                self.cb_coord_system.setCurrentText("Web Mercator")
                            # For UTM, would need to extract zone/hemisphere from EPSG
                        # If convert_btn, we'll convert during population
                
                # Clear table
                self._on_new()
                
                # Track that we have imported data
                self._has_imported_data = True
                
                row_index = 0
                
                for feat in imported_features:
                    feat_id = feat.get("id", row_index + 1)
                    coords = feat.get("coords", [])
                    geom_type = feat.get("type", "").lower()
                    
                    # Close polygon if needed
                    if "polígono" in geom_type and len(coords) >= 3:
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                    
                    if not coords:
                        continue
                    
                    # Convert coordinates if needed
                    if crs_string and crs_string.startswith("EPSG:"):
                        epsg_code = int(crs_string.split(":")[1])
                        current_cs = self.cb_coord_system.currentText()
                        
                        # Determine target CRS
                        target_epsg = None
                        if current_cs == "Geographic (Decimal Degrees)":
                            target_epsg = 4326
                        elif current_cs == "Web Mercator":
                            target_epsg = 3857
                        elif current_cs == "UTM":
                            zone = int(self.cb_zona.currentText()) if self.cb_zona.currentText() else 14
                            hemisphere = self.cb_hemisferio.currentText()
                            from utils.coordinate_systems import get_utm_epsg
                            target_epsg = get_utm_epsg(zone, hemisphere)
                        
                        # Convert if different
                        if target_epsg and epsg_code != target_epsg:
                            try:
                                transformer = Transformer.from_crs(f"EPSG:{epsg_code}", f"EPSG:{target_epsg}", always_xy=True)
                                converted_coords = []
                                for x, y in coords:
                                    x_new, y_new = transformer.transform(x, y)
                                    converted_coords.append((x_new, y_new))
                                coords = converted_coords
                            except Exception as e:
                                logger.error(f"Error converting coordinates: {e}")
                                error = CoordinateConversionError(
                                    "No se pudieron convertir las coordenadas del shapefile",
                                    details=str(e)
                                )
                                show_error_dialog(self, error)
                                return
                    
                    # Populate table
                    for j, (x, y) in enumerate(coords):
                        if row_index >= self.table.rowCount():
                            self.table.insertRow(row_index)
                        id_str = f"{feat_id}.{j+1}" if len(coords) > 1 else str(feat_id)
                        id_item = QTableWidgetItem(id_str)
                        id_item.setFlags(Qt.ItemIsEnabled)
                        self.table.setItem(row_index, 0, id_item)
                        self.table.setItem(row_index, 1, QTableWidgetItem(f"{x:.2f}"))
                        self.table.setItem(row_index, 2, QTableWidgetItem(f"{y:.2f}"))
                        row_index += 1
                    
                    # Activate appropriate checkbox
                    if "punto" in geom_type:
                        self.chk_punto.setChecked(True)
                    if "polilínea" in geom_type:
                        self.chk_polilinea.setChecked(True)
                    if "polígono" in geom_type:
                        self.chk_poligono.setChecked(True)
                
                # Redraw scene
                try:
                    mgr = self._build_manager_from_table()
                    self._redraw_scene(mgr)
                    QMessageBox.information(self, "Importación Shapefile Exitosa",
                                            f"{len(imported_features)} geometrías importadas desde {os.path.basename(path)}.\n"
                                            "Los datos se han cargado en la tabla y visualizado en el mapa.")
                except Exception as e:
                    logger.error(f"Error processing imported shapefile data: {e}")
                    error = GeometryBuildError(
                        "Los datos del shapefile no pudieron ser procesados",
                        details=str(e)
                    )
                    show_error_dialog(self, error)
            
            except FileImportError as e:
                logger.error(f"Shapefile import error: {e}")
                show_error_dialog(self, e)
            except Exception as e:
                logger.error(f"Unexpected error importing shapefile: {e}", exc_info=True)
                error = FileImportError(
                    "Error inesperado al importar shapefile",
                    details=str(e)
                )
                show_error_dialog(self, error)
        
        else:
            QMessageBox.warning(self, "Formato no Soportado",
                                f"La importación del formato de archivo '{file_ext}' aún no está implementada.")

    def _on_undo(self):
        QMessageBox.information(self, "Deshacer", "Funcionalidad de Deshacer aún no implementada.")
        print("Deshacer acción")

    def _on_redo(self):
        QMessageBox.information(self, "Rehacer", "Funcionalidad de Rehacer aún no implementada.")
        print("Rehacer acción")

    def _on_settings(self):
        current = {
            "dark_mode": self._modo_oscuro,
            "draw_scale": self.draw_scale,
            "point_size": self.point_size,
            "font_size": self.font_size,
        }
        dialog = ConfigDialog(self, current)
        if dialog.exec():
            vals = dialog.get_values()
            self.draw_scale = vals.get("draw_scale", self.draw_scale)
            self.point_size = vals.get("point_size", self.point_size)
            self.font_size = vals.get("font_size", self.font_size)
            self._toggle_modo(vals.get("dark_mode", self._modo_oscuro))
            try:
                mgr = self._build_manager_from_table()
                self._redraw_scene(mgr)
            except (ValueError, TypeError) as e:
                print(f"Error aplicando configuración: {e}")

    def _on_help(self):
        dialog = HelpDialog(self)
        dialog.exec()

    def _on_export_html(self):
        coords = []
        for r in range(self.table.rowCount()):
            xi = self.table.item(r, 1)
            yi = self.table.item(r, 2)
            if xi and yi:
                try:
                    x = float(xi.text())
                    y = float(yi.text())
                    coords.append((x, y))
                except ValueError:
                    continue

        if len(coords) < 2:
            QMessageBox.warning(self, "Geometría insuficiente", "Se necesitan al menos 2 puntos para calcular perímetro.")
            return

        def distancia(a, b):
            return ((a[0] - b[0])**2 + (a[1] - b[1])**2) ** 0.5

        perimetro = sum(distancia(coords[i], coords[i+1]) for i in range(len(coords)-1))
        if self.chk_poligono.isChecked() and len(coords) >= 3:
            perimetro += distancia(coords[-1], coords[0])

        area = 0
        if self.chk_poligono.isChecked() and len(coords) >= 3:
            area = 0.5 * abs(sum(coords[i][0]*coords[i+1][1] - coords[i+1][0]*coords[i][1] for i in range(-1, len(coords)-1)))

        # HTML visual
        html = "<table border='1' cellpadding='4' cellspacing='0'>"
        html += "<tr><th>ID</th><th>Este (X)</th><th>Norte (Y)</th></tr>"
        for r in range(len(coords)):
            id_val = self.table.item(r, 0).text() if self.table.item(r, 0) else str(r+1)
            html += f"<tr><td>{id_val}</td><td>{coords[r][0]:.2f}</td><td>{coords[r][1]:.2f}</td></tr>"

        # Fila única combinada para Perímetro
        html += f"<tr><td colspan='3'><b>Perímetro:</b> {perimetro:.2f} m</td></tr>"

        # Fila única combinada para Área (si aplica)
        if self.chk_poligono.isChecked() and len(coords) >= 3:
            html += f"<tr><td colspan='3'><b>Área:</b> {area:.2f} m²</td></tr>"

        html += "</table>"



        # Diálogo modal visual
        dlg = QDialog(self)
        dlg.setWindowTitle("Resumen de Coordenadas")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout(dlg)

        view = QTextEdit()
        view.setReadOnly(True)
        view.setHtml(html)

        btn_copiar = QPushButton("Copiar código HTML")
        btn_copiar.clicked.connect(lambda: QApplication.clipboard().setText(html))

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dlg.close)

        layout.addWidget(view)
        layout.addWidget(btn_copiar)
        layout.addWidget(btn_cerrar)

        dlg.setLayout(layout)
        dlg.exec()
    
    def _on_unit_changed(self):
        """Handle unit system change and update measurements display."""
        self._update_measurements_display()
    
    def _update_measurements_display(self):
        """Update measurement labels with current coordinate data."""
        from utils.measurements import (
            calculate_distance_utm, calculate_distance_geographic,
            calculate_area_utm, calculate_area_geographic,
            calculate_perimeter_utm, calculate_perimeter_geographic,
            format_distance, format_area
        )
        
        # Get coordinates from table
        coords = []
        cs_text = self.cb_coord_system.currentText()
        
        for row in range(self.table.rowCount()):
            x_item = self.table.item(row, 1)
            y_item = self.table.item(row, 2)
            if x_item and y_item and x_item.text().strip() and y_item.text().strip():
                try:
                    # For measurements, we need coordinates in appropriate format
                    # UTM: use as-is
                    # Geographic: need lon, lat
                    if cs_text == "UTM":
                        x_val = float(x_item.text())
                        y_val = float(y_item.text())
                        coords.append((x_val, y_val))
                    elif cs_text in ["Geographic (Decimal Degrees)", "Geographic (DMS)", "Web Mercator"]:
                        # Convert to DD for geodesic calculations
                        # For now, assume table has correct format - conversion already done
                        x_val = float(x_item.text()) if cs_text != "Geographic (DMS)" else 0
                        y_val = float(y_item.text()) if cs_text != "Geographic (DMS)" else 0
                        coords.append((x_val, y_val))
                except (ValueError, Exception):
                    continue
        
        # Determine units
        use_metric = (self.cb_units.currentText() == "Métricas")
        distance_unit = "km" if use_metric else "mi"
        area_unit = "ha" if use_metric else "ac"
        
        # Calculate measurements based on coordinate system
        is_geographic = cs_text in ["Geographic (Decimal Degrees)", "Geographic (DMS)"]
        
        if len(coords) < 2:
            self.overlay.update_measurements("Distancia: --", "Área: --", "Perímetro: --")
            return
        
        # IMPORTANT: Remove duplicate closing point if present (for polygons)
        # The table may have the closing point duplicated, but measurement functions
        # expect non-duplicated coordinates
        logger.info(f"Before duplicate check: {len(coords)} points")
        if len(coords) >= 3:
            logger.info(f"First point: {coords[0]}, Last point: {coords[-1]}")
            if coords[0] == coords[-1]:
                logger.info("Removing duplicate closing point")
                coords = coords[:-1]
            else:
                logger.info("No duplicate closing point found")
        logger.info(f"After duplicate check: {len(coords)} points")
        
        # DEBUG: Log coordinate information
        logger.info(f"Measurement calculation - Coordinate system: {cs_text}")
        logger.info(f"Measurement calculation - Number of points: {len(coords)}")
        if len(coords) > 0:
            logger.info(f"Measurement calculation - First point: {coords[0]}")
            if len(coords) > 1:
                logger.info(f"Measurement calculation - Last point: {coords[-1]}")
        
        try:
            # IMPORTANT: For accurate measurements, we should ALWAYS use UTM coordinates
            # regardless of what coordinate system is displayed in the table.
            # We need to convert the displayed coordinates back to UTM for measurement.
            
            utm_coords = []
            zone = int(self.cb_zona.currentText()) if self.cb_zona.currentText() else 14
            hemisphere = self.cb_hemisferio.currentText()
            from utils.coordinate_systems import get_utm_epsg
            utm_epsg = get_utm_epsg(zone, hemisphere)
            
            if cs_text == "UTM":
                # Already in UTM, use as-is
                utm_coords = coords
            elif cs_text == "Geographic (Decimal Degrees)":
                # Convert DD to UTM
                transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
                for lon, lat in coords:
                    x_utm, y_utm = transformer.transform(lon, lat)
                    utm_coords.append((x_utm, y_utm))
            elif cs_text == "Web Mercator":
                # Convert Web Mercator to UTM
                transformer = Transformer.from_crs("EPSG:3857", f"EPSG:{utm_epsg}", always_xy=True)
                for x_merc, y_merc in coords:
                    x_utm, y_utm = transformer.transform(x_merc, y_merc)
                    utm_coords.append((x_utm, y_utm))
            elif cs_text == "Geographic (DMS)":
                # DMS should have been converted to DD in the table, but if not, skip
                # This is why measurements show 0 for DMS
                logger.warning("DMS coordinates cannot be used directly for measurements")
                self.web_view.page().runJavaScript("updateMeasurements('Distancia: --', 'Área: --', 'Perímetro: --');")
                return
            
            # Now calculate measurements using UTM coordinates (planar calculations)
            if len(utm_coords) < 2:
                self.web_view.page().runJavaScript("updateMeasurements('Distancia: --', 'Área: --', 'Perímetro: --');")
                return
            
            # Distance (for points/polylines)
            distance_m = calculate_distance_utm(utm_coords)
            
            distance_str = format_distance(distance_m, distance_unit)
            distance_m_str = format_distance(distance_m, "m")
            dist_text = f"Distancia: {distance_str} ({distance_m_str})"
            
            area_text = "Área: --"
            perim_text = "Perímetro: --"

            # Area and Perimeter (for polygons)
            if len(utm_coords) >= 3:
                # Log UTM coordinates for debugging
                logger.info(f"Calculating area with {len(utm_coords)} UTM points")
                for i, (x, y) in enumerate(utm_coords):
                    logger.info(f"  Point {i+1}: ({x:.2f}, {y:.2f})")
                
                # Always use UTM coordinates for accurate planar calculations
                area_m2 = calculate_area_utm(utm_coords)
                perimeter_m = calculate_perimeter_utm(utm_coords)
                
                logger.info(f"Calculated area: {area_m2:.2f} m²")
                logger.info(f"Calculated perimeter: {perimeter_m:.2f} m")
                
                area_str = format_area(area_m2, area_unit)
                area_m2_str = format_area(area_m2, "m2")
                area_text = f"Área: {area_str} ({area_m2_str})"
                
                perim_str = format_distance(perimeter_m, distance_unit)
                perim_m_str = format_distance(perimeter_m, "m")
                perim_text = f"Perímetro: {perim_str} ({perim_m_str})"
            else:
                area_text = "Área: -- (necesita 3+ puntos)"
                perim_text = "Perímetro: -- (necesita 3+ puntos)"
            
            # Send to HTML overlay via JS
            # Escape strings for JS safety (basic)
            dist_js = dist_text.replace("'", "\\'")
            area_js = area_text.replace("'", "\\'")
            perim_js = perim_text.replace("'", "\\'")
            
            js_code = f"updateMeasurements('{dist_js}', '{area_js}', '{perim_js}');"
            self.web_view.page().runJavaScript(js_code)
        
        except Exception as e:
            print(f"[DEBUG] Measurement error: {e}")
            # Send error to HTML overlay
            js_code = "updateMeasurements('Distancia: Error', 'Área: Error', 'Perímetro: Error');"
            self.web_view.page().runJavaScript(js_code)

    def _on_simular(self):
        try:
            mgr = self._build_manager_from_table()
            self._redraw_scene(mgr)
            self._update_measurements_display()  # NEW: Update measurements
            
            # Always update web features and ensure web view is visible
            self._update_web_features(mgr)
            self.stack.setCurrentWidget(self.web_view)
                
            if self.scene.items():
                self.canvas.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        except (ValueError, TypeError) as e:
            QMessageBox.warning(self, "Error", f"No se pudo simular: {e}")

    def _on_zoom_in(self):
        self.canvas.scale(1.2, 1.2)

    def _on_zoom_out(self):
        self.canvas.scale(0.8, 0.8)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

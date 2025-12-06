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
    QUrlQuery,
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
    QUndoStack,
    QUndoCommand,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsTextItem, QFileDialog, QMessageBox, QApplication,
    QToolBar, QStyledItemDelegate, QHeaderView, QDialog, QStyleOptionViewItem,
    QStackedLayout, QStatusBar, QMenu
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import (
    Qt,
    QRegularExpression,
    QSize,
    QItemSelectionModel,
    QEvent,
    QUrl,
    QUrlQuery,
    QRectF,
    QPointF,
    QThreadPool,
    QRunnable,
    Signal,
    QObject,
    Slot,
)
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
from utils.error_handler import log_and_show_error, handle_errors
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
    def keyPressEvent(self, event):
        # Tab: al salir de Y, saltar a X de la siguiente fila
        if event.key() == Qt.Key_Tab and self.currentColumn() == 2:
            next_row = self.currentRow() + 1
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

class WebBridge(QObject):
    """Bridge object to expose Python methods to JavaScript via QWebChannel."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
    
    @Slot(str, float, float)
    def onDragStart(self, point_id, lat, lon):
        """Called from JavaScript when drag starts."""
        logger.info(f"WebBridge: onDragStart({point_id}, {lat}, {lon})")
        if self.main_window:
            self.main_window._handle_drag_start(point_id, str(lat), str(lon))
    
    @Slot(str, float, float)
    def onDragEnd(self, point_id, lat, lon):
        """Called from JavaScript when drag ends."""
        logger.info(f"WebBridge: onDragEnd({point_id}, {lat}, {lon})")
        if self.main_window:
            # First update the table
            self.main_window._handle_map_point_update_live(point_id, str(lat), str(lon))
            # Then create undo command
            self.main_window._handle_drag_end(point_id, str(lat), str(lon))
    
    @Slot(str, float, float)
    def onDrag(self, point_id, lat, lon):
        """Called from JavaScript during drag for live updates."""
        if self.main_window:
            # Update table in real-time without creating undo commands
            self.main_window._handle_map_point_update_live(point_id, str(lat), str(lon))
    
    @Slot(float, float)
    def onAddVertex(self, lat, lon):
        """Called from JavaScript when adding vertex by click."""
        logger.info(f"WebBridge: onAddVertex({lat}, {lon})")
        if self.main_window:
            self.main_window._handle_add_vertex_at(str(lat), str(lon))

class GeoWizardWebPage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if url.scheme() == "geowizard":
            logger.info(f"WebPage received URL: {url.toString()}")
            
            query = QUrlQuery(url.query())
            point_id = query.queryItemValue("id")
            lat = query.queryItemValue("lat")
            lon = query.queryItemValue("lon")
            
            logger.info(f"Parsed: host={url.host()}, id={point_id}, lat={lat}, lon={lon}")
            
            if self.main_window:
                if url.host() == "update_point_live":
                    logger.info(f"Calling _handle_map_point_update_live for point {point_id}")
                    self.main_window._handle_map_point_update_live(point_id, lat, lon)
                elif url.host() == "drag_start":
                    self.main_window._handle_drag_start(point_id, lat, lon)
                elif url.host() == "drag_end":
                    self.main_window._handle_drag_end(point_id, lat, lon)
                elif url.host() == "add_vertex_at":
                    self.main_window._handle_add_vertex_at(lat, lon)
                elif url.host() == "update_point":
                    # Legacy/Fallback
                    self.main_window._handle_map_point_update(point_id, lat, lon)
            return False
        return True
    
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """Intercept console messages from JavaScript to handle GEOWIZARD commands."""
        # Check if this is a GEOWIZARD command
        if message.startswith('GEOWIZARD:'):
            # Parse the message format: GEOWIZARD:command:id:lat:lng
            # or GEOWIZARD:add_vertex_at::lat:lng (no id)
            parts = message.split(':')
            if len(parts) >= 3:
                command = parts[1]
                
                if command == 'add_vertex_at' and len(parts) >= 5:
                    # Format: GEOWIZARD:add_vertex_at::lat:lng
                    lat = parts[3]
                    lng = parts[4]
                    logger.info(f"Console: add_vertex_at lat={lat}, lng={lng}")
                    if self.main_window:
                        self.main_window._handle_add_vertex_at(lat, lng)
                        
                elif len(parts) >= 5:
                    # Format: GEOWIZARD:command:id:lat:lng
                    point_id = parts[2]
                    lat = parts[3]
                    lng = parts[4]
                    
                    logger.info(f"Console: {command} for point {point_id}, lat={lat}, lng={lng}")
                    
                    if self.main_window:
                        if command == 'update_point_live':
                            self.main_window._handle_map_point_update_live(point_id, lat, lng)
                        elif command == 'drag_start':
                            self.main_window._handle_drag_start(point_id, lat, lng)
                        elif command == 'drag_end':
                            self.main_window._handle_drag_end(point_id, lat, lng)
                    
                    return
        
        # Log normal console messages
        logger.debug(f"JS Console [{level}]: {message} (line {lineNumber})")

class CommandMovePoint(QUndoCommand):
    def __init__(self, main_window, point_id, old_lat, old_lon, new_lat, new_lon):
        super().__init__()
        self.main_window = main_window
        self.point_id = point_id
        self.old_lat = float(old_lat)
        self.old_lon = float(old_lon)
        self.new_lat = float(new_lat)
        self.new_lon = float(new_lon)
        self.setText(f"Mover punto {point_id}")

    def undo(self):
        self.main_window._apply_point_update(self.point_id, self.old_lat, self.old_lon)
        # Force redraw to sync map
        mgr = self.main_window._build_manager_from_table()
        self.main_window._redraw_scene(mgr)
        self.main_window._update_web_features(mgr)

    def redo(self):
        self.main_window._apply_point_update(self.point_id, self.new_lat, self.new_lon)
        # Force redraw to sync map
        mgr = self.main_window._build_manager_from_table()
        self.main_window._redraw_scene(mgr)
        self.main_window._update_web_features(mgr)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tellus Consultoría - GeoWizard V.1.0 (Beta Tester)")
        
        # Set Tellus Consultoría logo as window icon
        import sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(__file__))
        
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
        
        # Staging system for edit mode (Accept/Cancel changes)
        self._original_table_state = None  # Stores table state when entering edit mode
        self._original_coord_system = None  # Stores coord system when entering edit mode
        self._original_zone = None
        self._original_hemisphere = None
        
        # Add vertex by map click mode
        self._add_vertex_mode = False  # Flag for "click to add vertex" mode
        
        self._modo_oscuro = False
        self.draw_scale = 0.35
        self.point_size = 6
        self.font_size = 8
        
        # Undo Stack
        self.undo_stack = QUndoStack(self)
        
        # Drag state for Undo
        self._drag_start_pos = None
        
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
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        ruta = os.path.join(base_path, "icons", nombre)
        
        # Verify file exists
        if not os.path.exists(ruta):
            logger.warning(f"Icon not found: {ruta}")
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
        self.coord_validator.validationChanged.connect(self._on_validation_changed)
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
        
        # Set custom page for web view to intercept navigation requests
        self.web_page = GeoWizardWebPage(self)
        self.web_view.setPage(self.web_page)
        
        # Setup QWebChannel for JS↔Python communication
        self.web_bridge = WebBridge(self)
        self.web_channel = QWebChannel()
        self.web_channel.registerObject("pyBridge", self.web_bridge)
        self.web_page.setWebChannel(self.web_channel)
        logger.info("QWebChannel configured with pyBridge")
        
        # Allow local HTML to load remote map tiles (e.g., OpenStreetMap)
        self.web_view.settings().setAttribute(
            QWebEngineSettings.LocalContentCanAccessRemoteUrls, True
        )
        
        # Get correct path for map_base.html (works in development and PyInstaller)
        import sys
        if getattr(sys, 'frozen', False):
            # PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # Development: map_base.html is in the root directory, go up one level from ui/
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        html_path = os.path.join(base_path, "map_base.html")
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))

        
        # Inject Python bridge after page loads
        self.web_view.loadFinished.connect(self._on_webpage_loaded)

        self.stack = QStackedLayout()
        self.stack.addWidget(self.canvas)
        self.stack.addWidget(self.web_view)
        self.stack.setCurrentWidget(self.canvas)
        view_container = QWidget()
        view_container.setLayout(self.stack)

        # ensamblar
        main_layout.addLayout(control,1)
        main_layout.addWidget(view_container,2)
        main_layout.addWidget(view_container,2)
        self.setCentralWidget(central)
        
        # Status Bar
        self.setStatusBar(QStatusBar(self))

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

        # ═══════════════════════════════════════════════════════
        # EDIT SECTION - Botones de edición
        # ═══════════════════════════════════════════════════════
        
        # Edit mode toggle
        self.action_edit = QAction(self._icono("edit-2-fill.svg"), "Editar Geometrías", self)
        self.action_edit.svg_filename = "edit-2-fill.svg"
        self.action_edit.setCheckable(True)
        self.action_edit.setChecked(False)
        self.action_edit.setToolTip("Activar/desactivar modo de edición de geometrías")
        self.action_edit.toggled.connect(self._toggle_edit_mode)
        tb.addAction(self.action_edit)
        
        # Undo button (starts disabled)
        self.action_undo = QAction(self._icono("undo.svg"), "Deshacer", self)
        self.action_undo.svg_filename = "undo.svg"
        self.action_undo.setEnabled(False)
        self.action_undo.setToolTip("Presione el botón de edición para habilitar")
        self.action_undo.triggered.connect(self.undo_stack.undo)
        tb.addAction(self.action_undo)
        
        # Redo button (starts disabled)
        self.action_redo = QAction(self._icono("redo.svg"), "Rehacer", self)
        self.action_redo.svg_filename = "redo.svg"
        self.action_redo.setEnabled(False)
        self.action_redo.setToolTip("Presione el botón de edición para habilitar")
        self.action_redo.triggered.connect(self.undo_stack.redo)
        tb.addAction(self.action_redo)
        
        # Add vertex button (starts disabled)
        self.action_add_vertex = QAction(self._icono("geo-fill.svg"), "Añadir Vértice", self)
        self.action_add_vertex.svg_filename = "geo-fill.svg"
        self.action_add_vertex.setEnabled(False)
        self.action_add_vertex.setCheckable(True)  # Make it toggleable for "click mode"
        self.action_add_vertex.setToolTip("Presione el botón de edición para habilitar")
        self.action_add_vertex.triggered.connect(self._on_add_vertex)
        tb.addAction(self.action_add_vertex)
        
        # Accept changes button (starts disabled)
        self.action_accept = QAction(self._icono("check-square.svg"), "Aceptar Cambios", self)
        self.action_accept.svg_filename = "check-square.svg"
        self.action_accept.setEnabled(False)
        self.action_accept.setToolTip("Presione el botón de edición para habilitar")
        self.action_accept.triggered.connect(self._on_accept_changes)
        tb.addAction(self.action_accept)
        
        # Cancel changes button (starts disabled)
        self.action_cancel = QAction(self._icono("cross-square.svg"), "Cancelar Cambios", self)
        self.action_cancel.svg_filename = "cross-square.svg"
        self.action_cancel.setEnabled(False)
        self.action_cancel.setToolTip("Presione el botón de edición para habilitar")
        self.action_cancel.triggered.connect(self._on_cancel_changes)
        tb.addAction(self.action_cancel)

        tb.addSeparator()
        
        # ═══════════════════════════════════════════════════════
        # UTILITIES SECTION
        # ═══════════════════════════════════════════════════════
        
        # Google Maps button
        self.action_google_maps = QAction(self._icono("map-location.svg"), "Abrir en Google Maps", self)
        self.action_google_maps.svg_filename = "map-location.svg"
        self.action_google_maps.setToolTip("Abrir primera coordenada en Google Maps")
        self.action_google_maps.triggered.connect(self._on_open_google_maps)
        tb.addAction(self.action_google_maps)

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

    @handle_errors(user_message="Error al exportar CSV", log_level="ERROR")
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
        
        # Skip automatic redraw if in edit mode - editable points handle their own updates
        if self._edit_mode:
            return
        
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
            
            # NOTA: Edición deshabilitada en canvas
            # La edición solo funciona en el mapa web para mejor sincronización
            # if self._edit_mode:
            #     # Get coordinates for this geometry's features
            #     # We'll create editable points for all coordinates in the table
            #     points = []
            #     for r in range(self.table.rowCount()):
            #         x_item = self.table.item(r, 1)
            #         y_item = self.table.item(r, 2)
            #         if x_item and y_item and x_item.text().strip() and y_item.text().strip():
            #             try:
            #                 x = float(x_item.text())
            #                 y = float(y_item.text())
            #                 points.append((x, y, r))
            #             except ValueError:
            #                 continue
            #     
            #     if points:
            #         editable_geom = EditableGeometry(geometry_item, points, self.table)
            #         editable_geom.show_points()
            #         self._editable_geometries.append(editable_geom)

        # Draw points and labels
        feats = mgr.get_features()
        for feat in feats:
            gt = feat.get("geometry_type")
            if gt == GeometryType.PUNTO and feat["coords"] and self.chk_punto.isChecked():
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
            logger.info("Modo de edición activado - Arrastre los puntos para editar")
            
            # Save original state for cancel functionality
            self._save_table_state()
            
            # Clear undo stack when entering edit mode
            self.undo_stack.clear()
            
            # Enable edit-related buttons
            self.action_undo.setEnabled(True)
            self.action_undo.setToolTip("Deshacer último cambio")
            
            self.action_redo.setEnabled(True)
            self.action_redo.setToolTip("Rehacer último cambio")
            
            self.action_add_vertex.setEnabled(True)
            self.action_add_vertex.setToolTip("Click para activar modo añadir vértice por clic en mapa")
            
            self.action_accept.setEnabled(True)
            self.action_accept.setToolTip("Aceptar todos los cambios realizados")
            
            self.action_cancel.setEnabled(True)
            self.action_cancel.setToolTip("Cancelar todos los cambios y restaurar estado original")
        else:
            self.action_edit.setText("Editar Geometrías")
            logger.info("Modo de edición desactivado")
            
            # Disable edit-related buttons
            self.action_undo.setEnabled(False)
            self.action_undo.setToolTip("Presione el botón de edición para habilitar")
            
            self.action_redo.setEnabled(False)
            self.action_redo.setToolTip("Presione el botón de edición para habilitar")
            
            self.action_add_vertex.setEnabled(False)
            self.action_add_vertex.setChecked(False)
            self.action_add_vertex.setToolTip("Presione el botón de edición para habilitar")
            self._add_vertex_mode = False
            
            self.action_accept.setEnabled(False)
            self.action_accept.setToolTip("Presione el botón de edición para habilitar")
            
            self.action_cancel.setEnabled(False)
            self.action_cancel.setToolTip("Presione el botón de edición para habilitar")
            
            # Clear original state
            self._original_table_state = None
        
        # Redraw scene to show/hide editable points on canvas
        try:
            mgr = self._build_manager_from_table()
            self._redraw_scene(mgr)
            # Also update web map to reflect current table state
            if self.chk_mapbase.isChecked():
                self._update_web_features(mgr)
        except Exception as e:
            logger.error(f"Error toggling edit mode: {e}")

        # Enable/Disable editing on web map
        js_code = f"if (typeof setEditable === 'function') {{ setEditable({'true' if enabled else 'false'}); }}"
        self.web_view.page().runJavaScript(js_code)

    def _handle_drag_start(self, point_id, lat_str, lon_str):
        """Store initial position for Undo command."""
        try:
            self._drag_start_pos = (float(lat_str), float(lon_str))
        except ValueError:
            self._drag_start_pos = None

    def _handle_drag_end(self, point_id, lat_str, lon_str):
        """Create Undo command after drag completes."""
        if not self._drag_start_pos:
            return
            
        try:
            old_lat, old_lon = self._drag_start_pos
            new_lat = float(lat_str)
            new_lon = float(lon_str)
            
            # Only push command if position actually changed
            if old_lat != new_lat or old_lon != new_lon:
                cmd = CommandMovePoint(self, point_id, old_lat, old_lon, new_lat, new_lon)
                self.undo_stack.push(cmd)
                
        except ValueError:
            pass
        finally:
            self._drag_start_pos = None

    def _handle_map_point_update_live(self, point_id, lat_str, lon_str):
        """
        Handle real-time point update from map drag.
        Updates table and measurements WITHOUT full scene redraw.
        Throttled to max 60 FPS to avoid excessive updates.
        """
        import time
        
        # Throttle updates to max 60 FPS (16.67ms between updates)
        current_time = time.time()
        last_update = getattr(self, '_last_live_update_time', 0)
        
        if current_time - last_update < 0.0167:  # ~60 FPS
            # Skip this update, too soon
            return
        
        self._last_live_update_time = current_time
        
        try:
            self._apply_point_update(point_id, float(lat_str), float(lon_str))
            # Update measurements immediately
            self._update_measurements_display()
        except Exception as e:
            logger.error(f"Error in live update: {e}")

    def _apply_point_update(self, point_id, lat, lon):
        """
        Helper to update table coordinates from WGS84 lat/lon.
        Does NOT trigger signals or redraws.
        """
        pid = str(point_id)
        target_row = -1
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.text() == pid:
                target_row = r
                break
        
        if target_row == -1:
            return

        # Convert WGS84 (lat/lon) to current system
        current_cs = self.cb_coord_system.currentText()
        x_new_str = ""
        y_new_str = ""

        if current_cs == "UTM":
            zone = int(self.cb_zona.currentText())
            hemisphere = self.cb_hemisferio.currentText()
            utm_epsg = get_utm_epsg(zone, hemisphere)
            transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
            x_utm, y_utm = transformer.transform(lon, lat)
            x_new_str = f"{x_utm:.2f}"
            y_new_str = f"{y_utm:.2f}"
            
        elif current_cs == "Geographic (Decimal Degrees)":
            x_new_str = f"{lon:.6f}"
            y_new_str = f"{lat:.6f}"
            
        elif current_cs == "Geographic (DMS)":
            lon_d, lon_m, lon_s, lon_dir = dd_to_dms(lon, is_longitude=True)
            lat_d, lat_m, lat_s, lat_dir = dd_to_dms(lat, is_longitude=False)
            x_new_str = format_dms(lon_d, lon_m, lon_s, lon_dir)
            y_new_str = format_dms(lat_d, lat_m, lat_s, lat_dir)
            
        elif current_cs == "Web Mercator":
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
            x_merc, y_merc = transformer.transform(lon, lat)
            x_new_str = f"{x_merc:.2f}"
            y_new_str = f"{y_merc:.2f}"

        # Update table silently
        self.table.blockSignals(True)
        try:
            old_x = self.table.item(target_row, 1).text()
            old_y = self.table.item(target_row, 2).text()
            
            self.table.item(target_row, 1).setText(x_new_str)
            self.table.item(target_row, 2).setText(y_new_str)
            
            logger.debug(f"Updated point {point_id} in table row {target_row}: ({old_x}, {old_y}) → ({x_new_str}, {y_new_str})")
        finally:
            self.table.blockSignals(False)

    def _handle_map_point_update(self, point_id, lat_str, lon_str):
        """Legacy handler - redirects to live update but might trigger final redraw if needed"""
        self._handle_map_point_update_live(point_id, lat_str, lon_str)

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

    @handle_errors(user_message="Error al guardar el proyecto", log_level="ERROR")
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

        # try:  <-- Removed outer try
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
            # Raise exception instead of showing message manually
            raise FileExportError(f"La exportación al formato '{selected_format}' aún no está implementada.")

        if export_successful:
            QMessageBox.information(self, "Éxito", f"Archivo guardado en:\n{full_path_filename}")

        # except ImportError as ie: ... <-- Handled by decorator (or let it bubble up)
        # except Exception as e: ... <-- Handled by decorator

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

    @handle_errors(user_message="Error durante la importación", log_level="ERROR")
    def _on_import(self):
        filters = "Archivos KML (*.kml);;Archivos Shapefile (*.shp);;Archivos de Coordenadas (*.csv *.txt);;Todos los archivos (*)"
        path, selected_filter = QFileDialog.getOpenFileName(
            self, "Importar Coordenadas o Geometrías", "", filters
        )

        if not path:
            return

        file_ext = os.path.splitext(path)[1].lower()

        if file_ext in ['.csv', '.txt']:
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
                raise InsufficientDataError("No se importaron geometrías válidas desde el archivo.")

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
            mgr = self._build_manager_from_table()
            self._redraw_scene(mgr)
            QMessageBox.information(
                self,
                "Importación CSV Exitosa",
                f"{len(valid_feats)} puntos importados desde {os.path.basename(path)}."
            )

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

                # --- DEDUPLICATION LOGIC START ---
                # Filter out Point features that are exact duplicates of Polygon/Polyline vertices.
                # This prevents "ghost points" and duplicate table rows when the KML contains both.
                
                # 1. Collect all vertex coordinates from Polygons and Polylines
                complex_geom_coords = set()
                for feat in imported_features:
                    if feat.get('type') in ['Polígono', 'Polilínea']:
                        for coord in feat.get('coords', []):
                            complex_geom_coords.add(coord)
                            
                # 2. Filter out Points that duplicate these coordinates
                unique_features = []
                duplicates_removed = 0
                for feat in imported_features:
                    if feat.get('type') == 'Punto':
                        # Check if point coord is in complex_geom_coords
                        coords = feat.get('coords', [])
                        if coords and coords[0] in complex_geom_coords:
                            duplicates_removed += 1
                            continue # Skip this duplicate point
                        unique_features.append(feat)
                    else:
                        unique_features.append(feat)
                
                if duplicates_removed > 0:
                    print(f"Removed {duplicates_removed} duplicate points that coincided with polygon vertices.")
                    imported_features = unique_features
                # --- DEDUPLICATION LOGIC END ---

                row_index = 0  # fila actual en la tabla

                for feat in imported_features:
                    feat_id = feat.get("id", row_index + 1)
                    coords = feat.get("coords", [])
                    geom_type = feat.get("type", "").lower()
                    if "polígono" in geom_type and len(coords) >= 3:
                        # Ensure we DO NOT have a duplicate closing point in the table
                        # The table should only hold unique vertices.
                        # Geometry builders will handle closure.
                        if coords[0] == coords[-1]:
                            coords.pop() # Remove the closing point

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

    def _on_validation_changed(self, is_valid):
        """Handle validation status changes."""
        if is_valid:
            self.statusBar().showMessage("Datos válidos", 3000)
            self.statusBar().setStyleSheet("color: green")
        else:
            self.statusBar().showMessage("Hay celdas con datos inválidos", 0) # 0 = permanent until cleared
            self.statusBar().setStyleSheet("color: red")
    
    def _on_webpage_loaded(self, ok):
        """Inject Python bridge into JavaScript after page loads."""
        if not ok:
            logger.error("Failed to load web page")
            return
        
        logger.info("Web page loaded, injecting Python bridge")
        
        # Inject global pyBridge object into JavaScript
        js_code = """
        window.pyBridge = {
            onDragStart: function(id, lat, lng) {
                console.log('pyBridge.onDragStart called:', id, lat, lng);
                // Will be overridden by Python
            },
            onDragEnd: function(id, lat, lng) {
                console.log('pyBridge.onDragEnd called:', id, lat, lng);
                // Will be overridden by Python
            },
            onAddVertex: function(lat, lng) {
                console.log('pyBridge.onAddVertex called:', lat, lng);
                // Will be overridden by Python
            }
        };
        console.log('Python bridge injected successfully');
        """
        
        self.web_view.page().runJavaScript(js_code, lambda result: logger.info("Bridge injection complete"))
        
        # Override the bridge functions with Python callbacks
        # Note: Since we can't directly expose Python functions to JS in Qt WebEngine without QWebChannel,
        # we'll use a hybrid approach: inject a bridge that calls console.log, then we intercept in javaScriptConsoleMessage
        pass

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
            self.web_view.page().runJavaScript("updateMeasurements('Distancia: --', 'Área: --', 'Perímetro: --');")
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

    def _save_table_state(self):
        """
        Save the current table state to allow canceling changes.
        Called when entering edit mode.
        """
        # Store table data
        table_data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            table_data.append(row_data)
        
        self._original_table_state = table_data
        
        # Store coordinate system settings
        self._original_coord_system = self.cb_coord_system.currentText()
        self._original_zone = self.cb_zona.currentText()
        self._original_hemisphere = self.cb_hemisferio.currentText()
        
        logger.info(f"Saved table state: {len(table_data)} rows, system={self._original_coord_system}")

    def _restore_table_state(self):
        """
        Restore the table to its saved state.
        Called when canceling edit mode changes.
        """
        if not self._original_table_state:
            logger.warning("No saved state to restore")
            return
        
        # Block signals to prevent triggering updates during restoration
        self.table.blockSignals(True)
        try:
            # Clear current table
            self.table.setRowCount(0)
            
            # Restore rows
            for row_idx, row_data in enumerate(self._original_table_state):
                self.table.insertRow(row_idx)
                for col_idx, cell_text in enumerate(row_data):
                    item = QTableWidgetItem(cell_text)
                    if col_idx == 0:  # ID column
                        item.setFlags(Qt.ItemIsEnabled)
                    self.table.setItem(row_idx, col_idx, item)
            
            # Restore coordinate system settings
            if self._original_coord_system:
                index = self.cb_coord_system.findText(self._original_coord_system)
                if index >= 0:
                    self.cb_coord_system.setCurrentIndex(index)
            
            if self._original_zone:
                index = self.cb_zona.findText(self._original_zone)
                if index >= 0:
                    self.cb_zona.setCurrentIndex(index)
            
            if self._original_hemisphere:
                index = self.cb_hemisferio.findText(self._original_hemisphere)
                if index >= 0:
                    self.cb_hemisferio.setCurrentIndex(index)
            
            logger.info(f"Restored table state: {len(self._original_table_state)} rows")
            
        finally:
            self.table.blockSignals(False)
        
        # Redraw to reflect restored state
        try:
            mgr = self._build_manager_from_table()
            self._redraw_scene(mgr)
            self._update_web_features(mgr)
        except Exception as e:
            logger.error(f"Error redrawing after restore: {e}")

    def _on_accept_changes(self):
        """
        Accept all changes made in edit mode and exit edit mode.
        Clears the undo stack and saved state.
        """
        if not self._edit_mode:
            return
        
        reply = QMessageBox.question(
            self,
            "Aceptar Cambios",
            "¿Confirmar todos los cambios realizados?\n\n"
            "Esto saldrá del modo de edición y guardará los cambios permanentemente.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # CRITICAL: Build manager with current table state BEFORE clearing original state
            # This ensures we have the edited geometry to display
            try:
                mgr = self._build_manager_from_table()
            except Exception as e:
                logger.error(f"Error building manager before accepting changes: {e}")
                mgr = None
            
            # IMPORTANT: Clear original state BEFORE exiting edit mode
            # so that _toggle_edit_mode doesn't try to restore it
            self._original_table_state = None
            self._original_coord_system = None
            self._original_zone = None
            self._original_hemisphere = None
            
            # Clear undo stack
            self.undo_stack.clear()
            
            # Redraw scene and map with current (edited) state
            if mgr:
                try:
                    self._redraw_scene(mgr)
                    if self.chk_mapbase.isChecked():
                        self._update_web_features(mgr)
                    logger.info("Redrawn scene and map with accepted changes")
                except Exception as e:
                    logger.error(f"Error redrawing after accepting changes: {e}")
            
            # Exit edit mode (this will disable dragging)
            self.action_edit.setChecked(False)
            
            logger.info("Changes accepted and saved, exited edit mode")
            self.statusBar().showMessage("Cambios aceptados y guardados exitosamente", 3000)

    def _on_cancel_changes(self):
        """
        Cancel all changes made in edit mode and restore original state.
        Exits edit mode after restoring.
        """
        if not self._edit_mode:
            return
        
        reply = QMessageBox.warning(
            self,
            "Cancelar Cambios",
            "¿Descartar todos los cambios realizados en modo edición?\n\n"
            "Esto restaurará el estado original de la tabla.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Restore original state
            self._restore_table_state()
            
            # Clear undo stack
            self.undo_stack.clear()
            
            # Exit edit mode
            self.action_edit.setChecked(False)
            # This will trigger _toggle_edit_mode(False)
            
            logger.info("Changes canceled, restored original state")
            self.statusBar().showMessage("Cambios cancelados, estado restaurado", 3000)


    def _on_add_vertex(self, checked):
        """
        Toggle "add vertex by click" mode.
        When activated, user can click on the map to add a new vertex.
        """
        if not self._edit_mode:
            QMessageBox.warning(
                self,
                "Modo de edición desactivado",
                "Active el modo de edición para añadir vértices."
            )
            self.action_add_vertex.setChecked(False)
            return
        
        # Toggle add vertex mode (no longer check geometry type)
        self._add_vertex_mode = checked
        
        if checked:
            # Entering add vertex mode
            self.statusBar().showMessage("Modo Añadir Vértice: Haga clic en el mapa para añadir un nuevo punto. Seleccione una fila para insertar después de ella.", 5000)
            self.action_add_vertex.setToolTip("Click para desactivar modo añadir vértice")
            
            # Enable map click handler via JavaScript
            js_code = """
            if (typeof enableAddVertexMode === 'function') {
                enableAddVertexMode(true);
            }
            """
            self.web_view.page().runJavaScript(js_code)
            
            logger.info("Add vertex mode activated - Click on map to add vertex")
        else:
            # Exiting add vertex mode
            self.statusBar().showMessage("Modo Añadir Vértice desactivado", 2000)
            self.action_add_vertex.setToolTip("Click para activar modo añadir vértice por clic en mapa")
            
            # Disable map click handler
            js_code = """
            if (typeof enableAddVertexMode === 'function') {
                enableAddVertexMode(false);
            }
            """
            self.web_view.page().runJavaScript(js_code)
            
            logger.info("Add vertex mode deactivated")

    def _handle_add_vertex_at(self, lat_str, lon_str):
        """
        Handle click on map to add vertex.
        Receives WGS84 coordinates, converts to current system, and adds to table.
        Inserts after the currently selected row, or at the end if no selection.
        """
        if not self._add_vertex_mode:
            logger.warning("Received add_vertex_at but mode is not active")
            return
        
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            
            # Convert from WGS84 to current coordinate system
            cs_text = self.cb_coord_system.currentText()
            x_str = ""
            y_str = ""
            
            if cs_text == "UTM":
                # Convert to UTM
                zone = int(self.cb_zona.currentText())
                hemisphere = self.cb_hemisferio.currentText()
                utm_epsg = get_utm_epsg(zone, hemisphere)
                transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
                x_utm, y_utm = transformer.transform(lon, lat)
                x_str = f"{x_utm:.2f}"
                y_str = f"{y_utm:.2f}"
                
            elif cs_text == "Geographic (Decimal Degrees)":
                # Already in correct format
                x_str = f"{lon:.6f}"
                y_str = f"{lat:.6f}"
                
            elif cs_text == "Geographic (DMS)":
                # Convert to DMS
                lon_d, lon_m, lon_s, lon_dir = dd_to_dms(lon, is_longitude=True)
                lat_d, lat_m, lat_s, lat_dir = dd_to_dms(lat, is_longitude=False)
                x_str = format_dms(lon_d, lon_m, lon_s, lon_dir)
                y_str = format_dms(lat_d, lat_m, lat_s, lat_dir)
                
            elif cs_text == "Web Mercator":
                # Convert to Web Mercator
                transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
                x_merc, y_merc = transformer.transform(lon, lat)
                x_str = f"{x_merc:.2f}"
                y_str = f"{y_merc:.2f}"
            
            # Determine insertion position
            current_row = self.table.currentRow()
            if current_row >= 0:
                # Insert after the selected row
                insert_row = current_row + 1
            else:
                # No selection, insert at end
                insert_row = self.table.rowCount()
            
            # Block signals to prevent auto-creating empty rows
            self.table.blockSignals(True)
            try:
                # Insert new row
                self.table.insertRow(insert_row)
                
                # Set coordinates
                self.table.setItem(insert_row, 1, QTableWidgetItem(x_str))
                self.table.setItem(insert_row, 2, QTableWidgetItem(y_str))
                
                # Renumber all IDs sequentially
                for row in range(self.table.rowCount()):
                    id_item = QTableWidgetItem(str(row + 1))
                    id_item.setFlags(Qt.ItemIsEnabled)
                    self.table.setItem(row, 0, id_item)
                    
            finally:
                self.table.blockSignals(False)
            
            logger.info(f"Added vertex at row {insert_row + 1}: ({x_str}, {y_str})")
            self.statusBar().showMessage(f"Vértice añadido en fila {insert_row + 1}", 2000)
            
            # Select the newly added row for next insertion
            self.table.setCurrentCell(insert_row, 1)
            
            # Redraw to show the new vertex
            try:
                mgr = self._build_manager_from_table()
                self._redraw_scene(mgr)
                self._update_web_features(mgr)
            except Exception as e:
                # Don't show error dialog in add vertex mode - user is still building geometry
                logger.warning(f"Geometry not yet complete: {e}")
            
        except Exception as e:
            logger.error(f"Error adding vertex from map click: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo añadir el vértice:\n{e}"
            )


    def _on_open_google_maps(self):
        """
        Open the centroid (geometric center) of all coordinates in Google Maps.
        Converts from current coordinate system to WGS84 (lat/lon) if necessary.
        """
        # Check if there's at least one coordinate
        if self.table.rowCount() == 0:
            QMessageBox.warning(
                self,
                "Sin Coordenadas",
                "No hay coordenadas en la tabla para abrir en Google Maps."
            )
            return
        
        try:
            # Collect all valid coordinates
            coords_lat_lon = []
            cs_text = self.cb_coord_system.currentText()
            
            for row in range(self.table.rowCount()):
                x_item = self.table.item(row, 1)
                y_item = self.table.item(row, 2)
                
                if not x_item or not y_item or not x_item.text().strip() or not y_item.text().strip():
                    continue  # Skip empty rows
                
                x_str = x_item.text().strip()
                y_str = y_item.text().strip()
                
                lat = None
                lon = None
                
                if cs_text == "UTM":
                    # Convert UTM to WGS84
                    zone = int(self.cb_zona.currentText())
                    hemisphere = self.cb_hemisferio.currentText()
                    utm_epsg = get_utm_epsg(zone, hemisphere)
                    
                    x_utm = float(x_str)
                    y_utm = float(y_str)
                    
                    transformer = Transformer.from_crs(f"EPSG:{utm_epsg}", "EPSG:4326", always_xy=True)
                    lon, lat = transformer.transform(x_utm, y_utm)
                    
                elif cs_text == "Geographic (Decimal Degrees)":
                    # Already in WGS84
                    lon = float(x_str)
                    lat = float(y_str)
                    
                elif cs_text == "Geographic (DMS)":
                    # Parse DMS and convert to decimal degrees
                    is_valid_lon, lon = validate_dms_coordinate(x_str, is_longitude=True)
                    is_valid_lat, lat = validate_dms_coordinate(y_str, is_longitude=False)
                    
                    if not (is_valid_lon and is_valid_lat):
                        continue  # Skip invalid DMS
                        
                elif cs_text == "Web Mercator":
                    # Convert Web Mercator to WGS84
                    x_mercator = float(x_str)
                    y_mercator = float(y_str)
                    
                    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
                    lon, lat = transformer.transform(x_mercator, y_mercator)
                
                if lat is not None and lon is not None:
                    coords_lat_lon.append((lat, lon))
            
            if len(coords_lat_lon) == 0:
                QMessageBox.warning(
                    self,
                    "Sin Coordenadas Válidas",
                    "No se encontraron coordenadas válidas para abrir en Google Maps."
                )
                return
            
            # Calculate centroid (average of all coordinates)
            avg_lat = sum(coord[0] for coord in coords_lat_lon) / len(coords_lat_lon)
            avg_lon = sum(coord[1] for coord in coords_lat_lon) / len(coords_lat_lon)
            
            # Construct Google Maps URL with centroid
            google_maps_url = f"https://www.google.com/maps?q={avg_lat},{avg_lon}"
            
            # Open in default browser
            import webbrowser
            webbrowser.open(google_maps_url)
            
            logger.info(f"Opened Google Maps at centroid: lat={avg_lat:.6f}, lon={avg_lon:.6f} (from {len(coords_lat_lon)} points)")
            self.statusBar().showMessage(f"Abriendo centroid en Google Maps ({len(coords_lat_lon)} puntos)", 3000)
            
        except Exception as e:
            logger.error(f"Error opening Google Maps: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir Google Maps.\n\n"
                f"Asegúrese de que las coordenadas sean válidas.\n\n"
                f"Error: {e}"
            )


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

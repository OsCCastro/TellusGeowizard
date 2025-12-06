# constants.py
"""
Application-wide constants for GeoWizard.
Centralizes configuration values, color schemes, and default settings.
"""

# Application Information
APP_NAME = "GeoWizard"
APP_VERSION = "1.0.0"
ORGANIZATION = "GeoWizard"
ORGANIZATION_DOMAIN = "geowizard.local"

# File Extensions and Filters
PROJECT_FILE_EXTENSION = ".gwp"
PROJECT_FILE_FILTER = "GeoWizard Project (*.gwp)"
KML_FILE_FILTER = "KML Files (*.kml)"
KMZ_FILE_FILTER = "KMZ Files (*.kmz)"
SHAPEFILE_FILTER = "Shapefile (*.shp)"
CSV_FILE_FILTER = "CSV Files (*.csv *.txt)"
ALL_IMPORT_FILTERS = "Archivos KML (*.kml);;Archivos de Coordenadas (*.csv *.txt);;Todos los archivos (*)"
ALL_PROJECT_FILTERS = "Archivos de Proyecto SIG (*.kml *.kmz *.shp);;Todos los archivos (*)"

# Default Values
DEFAULT_ZONE = 18
DEFAULT_HEMISPHERE = "Norte"
DEFAULT_PRECISION = 2
DEFAULT_DRAW_SCALE = 0.35
DEFAULT_POINT_SIZE = 6
DEFAULT_FONT_SIZE = 8
MAX_RECENT_FILES = 10

# Table Configuration
TABLE_COLUMNS = 3
TABLE_HEADER_LABELS = ["ID", "Este (X)", "Norte (Y)"]
TABLE_INITIAL_ROWS = 50

# Canvas Configuration
CANVAS_ZOOM_FACTOR = 1.15
CANVAS_MIN_ZOOM = 0.1
CANVAS_MAX_ZOOM = 50.0

# Color Schemes
class Colors:
    """Color definitions for light and dark themes"""
    
    # Light Mode Colors
    LIGHT_BACKGROUND = "#FFFFFF"
    LIGHT_TEXT = "#000000"
    LIGHT_TABLE_BACKGROUND = "#FFFFFF"
    LIGHT_TABLE_ALTERNATE = "#F5F5F5"
    LIGHT_BORDER = "#CCCCCC"
    LIGHT_ACCENT = "#0078D4"
    
    # Dark Mode Colors
    DARK_BACKGROUND = "#1E1E1E"
    DARK_TEXT = "#FFFFFF"
    DARK_TABLE_BACKGROUND = "#2D2D30"
    DARK_TABLE_ALTERNATE = "#252526"
    DARK_BORDER = "#3F3F46"
    DARK_ACCENT = "#0E639C"
    
    # Geometry Colors (theme-independent)
    POINT_COLOR = "#FF0000"  # Red
    LINESTRING_COLOR = "#0000FF"  # Blue
    POLYGON_COLOR = "#00FF00"  # Green
    POLYGON_FILL = "#00FF0040"  # Green with transparency
    SELECTION_COLOR = "#FFFF00"  # Yellow
    GRID_COLOR = "#CCCCCC"

# UTM Configuration
UTM_ZONES = list(range(1, 61))  # 1 to 60
HEMISPHERES = ["Norte", "Sur"]
DEFAULT_EPSG_NORTH_BASE = 32600
DEFAULT_EPSG_SOUTH_BASE = 32700
WGS84_EPSG = 4326

# Validation Patterns
COORDINATE_PATTERN = r"^-?\d+(\.\d+)?$"  # Matches integers or decimals
ID_PATTERN = r"^\d+$"  # Matches positive integers

# UI Messages
MSG_NO_DATA = "No hay datos para exportar"
MSG_EXPORT_SUCCESS = "Exportación exitosa"
MSG_IMPORT_SUCCESS = "Importación exitosa"
MSG_SAVE_SUCCESS = "Proyecto guardado exitosamente"
MSG_LOAD_SUCCESS = "Proyecto cargado exitosamente"
MSG_ERROR = "Error"
MSG_WARNING = "Advertencia"
MSG_INFO = "Información"

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE_NAME = "geowizard.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 3

# Keyboard Shortcuts (Qt Key Sequences)
# These will be used with QKeySequence.StandardKey or custom combinations
SHORTCUT_NEW = "Ctrl+N"
SHORTCUT_OPEN = "Ctrl+O"
SHORTCUT_SAVE = "Ctrl+S"
SHORTCUT_SAVE_AS = "Ctrl+Shift+S"
SHORTCUT_IMPORT = "Ctrl+I"
SHORTCUT_EXPORT = "Ctrl+E"
SHORTCUT_UNDO = "Ctrl+Z"
SHORTCUT_REDO = "Ctrl+Y"
SHORTCUT_DELETE = "Delete"
SHORTCUT_COPY = "Ctrl+C"
SHORTCUT_PASTE = "Ctrl+V"
SHORTCUT_SETTINGS = "Ctrl+,"
SHORTCUT_QUIT = "Ctrl+Q"
SHORTCUT_ZOOM_IN = "Ctrl++"
SHORTCUT_ZOOM_OUT = "Ctrl+-"
SHORTCUT_ZOOM_FIT = "Ctrl+0"

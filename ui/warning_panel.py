# ui/warning_panel.py
"""
Panel de advertencias y log para GeoWizard.
Muestra errores, advertencias y mensajes de información en la parte inferior de la UI.
Se integra con el sistema de logging existente.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtGui import QTextCursor, QColor, QFont

from utils.logger import get_logger

logger = get_logger(__name__)


class WarningEntry:
    """Representa una entrada de advertencia/error."""
    
    ERROR = "error"
    WARNING = "warning"
    SUCCESS = "success"
    INFO = "info"
    DEBUG = "debug"
    
    def __init__(self, entry_type: str, code: str, message: str, 
                 solution: str = None, timestamp: datetime = None):
        self.entry_type = entry_type
        self.code = code
        self.message = message
        self.solution = solution
        self.timestamp = timestamp or datetime.now()
    
    def to_display_text(self) -> str:
        """Formatea la entrada para mostrar en el panel."""
        type_label = {
            self.ERROR: "❌ Error",
            self.WARNING: "⚠️ Advertencia",
            self.SUCCESS: "✅ Éxito",
            self.INFO: "ℹ️ Info",
            self.DEBUG: "🔍 Debug"
        }.get(self.entry_type, "📝 Mensaje")
        
        time_str = self.timestamp.strftime("%H:%M:%S")
        text = f"[{time_str}] {type_label} {self.code}: {self.message}"
        if self.solution:
            text += f"\n    💡 Solución: {self.solution}"
        text += " (ver log)"
        return text


class LogHandler(logging.Handler):
    """Handler de logging que envía mensajes al WarningPanel."""
    
    def __init__(self, warning_panel: 'WarningPanel'):
        super().__init__()
        self.warning_panel = warning_panel
        self.setFormatter(logging.Formatter('%(message)s'))
    
    def emit(self, record: logging.LogRecord):
        """Emite un registro de log al panel."""
        try:
            # Determinar tipo de entrada
            if record.levelno >= logging.ERROR:
                entry_type = WarningEntry.ERROR
            elif record.levelno >= logging.WARNING:
                entry_type = WarningEntry.WARNING
            elif record.levelno >= logging.INFO:
                entry_type = WarningEntry.INFO
            else:
                entry_type = WarningEntry.DEBUG
            
            # Crear código único
            code = f"{record.levelname[0]}{len(self.warning_panel.entries) + 1:03d}"
            
            # Crear entrada
            entry = WarningEntry(
                entry_type=entry_type,
                code=code,
                message=self.format(record),
                solution=getattr(record, 'solution', None),
                timestamp=datetime.fromtimestamp(record.created)
            )
            
            # Añadir al panel (thread-safe via signal)
            QTimer.singleShot(0, lambda: self.warning_panel.add_entry(entry))
            
        except Exception:
            self.handleError(record)


class WarningPanel(QFrame):
    """
    Panel de advertencias que muestra errores, advertencias y logs.
    Se ubica en la parte inferior de la ventana principal.
    """
    
    # Señales
    entryAdded = Signal(WarningEntry)
    panelCleared = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries: List[WarningEntry] = []
        self._error_count = 0
        self._warning_count = 0
        self._success_count = 0
        self._info_count = 0
        self._is_expanded = True
        self._max_entries = 500  # Limitar entradas para no consumir mucha memoria
        
        self._setup_ui()
        self._setup_log_handler()
    
    def _setup_ui(self):
        """Configura la interfaz del panel."""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setMinimumHeight(100)
        self.setMaximumHeight(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # ─── Header ───
        header = QHBoxLayout()
        
        self.lbl_title = QLabel("📋 Panel de Advertencias y Log")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 10pt;")
        header.addWidget(self.lbl_title)
        
        header.addStretch()
        
        # Contadores
        self.lbl_errors = QLabel("❌ 0")
        self.lbl_errors.setStyleSheet("color: #dc3545; font-weight: bold;")
        self.lbl_errors.setToolTip("Número de errores")
        header.addWidget(self.lbl_errors)
        
        self.lbl_warnings = QLabel("⚠️ 0")
        self.lbl_warnings.setStyleSheet("color: #ffc107; font-weight: bold;")
        self.lbl_warnings.setToolTip("Número de advertencias")
        header.addWidget(self.lbl_warnings)
        
        self.lbl_success = QLabel("✅ 0")
        self.lbl_success.setStyleSheet("color: #28a745; font-weight: bold;")
        self.lbl_success.setToolTip("Operaciones exitosas")
        header.addWidget(self.lbl_success)
        
        self.lbl_info = QLabel("ℹ️ 0")
        self.lbl_info.setStyleSheet("color: #17a2b8; font-weight: bold;")
        self.lbl_info.setToolTip("Número de mensajes informativos")
        header.addWidget(self.lbl_info)
        
        # Botones
        self.btn_clear = QPushButton("🗑️ Limpiar")
        self.btn_clear.setMaximumWidth(80)
        self.btn_clear.setToolTip("Limpiar todos los mensajes")
        self.btn_clear.clicked.connect(self.clear_entries)
        header.addWidget(self.btn_clear)
        
        self.btn_toggle = QPushButton("▼")
        self.btn_toggle.setMaximumWidth(30)
        self.btn_toggle.setToolTip("Expandir/Contraer panel")
        self.btn_toggle.clicked.connect(self._toggle_expand)
        header.addWidget(self.btn_toggle)
        
        layout.addLayout(header)
        
        # ─── Content Area ───
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Consolas", 9))
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        self.text_area.setPlaceholderText("Los mensajes, advertencias y errores aparecerán aquí...")
        layout.addWidget(self.text_area)
    
    def _setup_log_handler(self):
        """Configura el handler para capturar mensajes del logger."""
        self.log_handler = LogHandler(self)
        self.log_handler.setLevel(logging.INFO)  # Capturar INFO y superiores
        
        # Añadir al logger raíz
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        
        logger.info("Panel de advertencias inicializado")
    
    def _toggle_expand(self):
        """Alterna entre expandido y contraído."""
        self._is_expanded = not self._is_expanded
        self.text_area.setVisible(self._is_expanded)
        self.btn_toggle.setText("▼" if self._is_expanded else "▶")
        
        if self._is_expanded:
            self.setMaximumHeight(200)
            self.setMinimumHeight(100)
        else:
            self.setMaximumHeight(30)
            self.setMinimumHeight(30)
    
    def _update_counters(self):
        """Actualiza los contadores de errores/advertencias/success/info."""
        self.lbl_errors.setText(f"❌ {self._error_count}")
        self.lbl_warnings.setText(f"⚠️ {self._warning_count}")
        self.lbl_success.setText(f"✅ {self._success_count}")
        self.lbl_info.setText(f"ℹ️ {self._info_count}")
    
    def _get_color_for_type(self, entry_type: str) -> str:
        """Obtiene el color HTML para el tipo de entrada."""
        colors = {
            WarningEntry.ERROR: "#ff6b6b",
            WarningEntry.WARNING: "#ffd93d",
            WarningEntry.SUCCESS: "#4caf50",
            WarningEntry.INFO: "#6bcbff",
            WarningEntry.DEBUG: "#888888"
        }
        return colors.get(entry_type, "#d4d4d4")
    
    @Slot(WarningEntry)
    def add_entry(self, entry: WarningEntry):
        """Añade una nueva entrada al panel."""
        # Limitar número de entradas
        if len(self.entries) >= self._max_entries:
            self.entries.pop(0)
        
        self.entries.append(entry)
        
        # Actualizar contadores
        if entry.entry_type == WarningEntry.ERROR:
            self._error_count += 1
        elif entry.entry_type == WarningEntry.WARNING:
            self._warning_count += 1
        elif entry.entry_type == WarningEntry.SUCCESS:
            self._success_count += 1
        elif entry.entry_type == WarningEntry.INFO:
            self._info_count += 1
        
        self._update_counters()
        
        # Añadir texto con color
        color = self._get_color_for_type(entry.entry_type)
        html = f'<span style="color: {color};">{entry.to_display_text()}</span><br>'
        
        cursor = self.text_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(html)
        
        # Auto-scroll al final
        self.text_area.verticalScrollBar().setValue(
            self.text_area.verticalScrollBar().maximum()
        )
        
        self.entryAdded.emit(entry)
    
    def add_error(self, code: str, message: str, solution: str = None):
        """Atajo para añadir un error."""
        entry = WarningEntry(
            entry_type=WarningEntry.ERROR,
            code=code,
            message=message,
            solution=solution
        )
        self.add_entry(entry)
        logger.error(f"{code}: {message}")
    
    def add_warning(self, code: str, message: str, solution: str = None):
        """Atajo para añadir una advertencia."""
        entry = WarningEntry(
            entry_type=WarningEntry.WARNING,
            code=code,
            message=message,
            solution=solution
        )
        self.add_entry(entry)
        logger.warning(f"{code}: {message}")
    
    def add_info(self, code: str, message: str):
        """Atajo para añadir información."""
        entry = WarningEntry(
            entry_type=WarningEntry.INFO,
            code=code,
            message=message
        )
        self.add_entry(entry)
    
    def add_success(self, code: str, message: str):
        """
        Añade un mensaje de éxito al panel.
        Reemplaza CustomMessageBox.information para operaciones exitosas.
        """
        entry = WarningEntry(
            entry_type=WarningEntry.SUCCESS,
            code=code,
            message=message
        )
        self.add_entry(entry)
        logger.info(f"✅ {code}: {message}")
    
    def clear_entries(self):
        """Limpia todas las entradas."""
        self.entries.clear()
        self._error_count = 0
        self._warning_count = 0
        self._success_count = 0
        self._info_count = 0
        self._update_counters()
        self.text_area.clear()
        self.panelCleared.emit()
        logger.info("Panel de advertencias limpiado")
    
    def get_error_count(self) -> int:
        """Retorna el número de errores."""
        return self._error_count
    
    def get_warning_count(self) -> int:
        """Retorna el número de advertencias."""
        return self._warning_count
    
    def has_errors(self) -> bool:
        """Indica si hay errores."""
        return self._error_count > 0
    
    def cleanup(self):
        """Limpia recursos al cerrar."""
        # Remover handler del logger
        root_logger = logging.getLogger()
        if self.log_handler in root_logger.handlers:
            root_logger.removeHandler(self.log_handler)


# ═══════════════════════════════════════════════════════════════════════════
# Diccionario de errores conocidos con soluciones
# ═══════════════════════════════════════════════════════════════════════════

KNOWN_ERRORS = {
    "COORD_001": {
        "message": "Coordenada inválida",
        "solution": "Verifique que el valor sea numérico. Para UTM use valores como 500000.00"
    },
    "COORD_002": {
        "message": "Coordenada fuera de rango",
        "solution": "Para latitud: -90 a 90. Para longitud: -180 a 180. Para UTM: valores positivos típicos"
    },
    "CURVE_001": {
        "message": "Parámetros de curva inválidos",
        "solution": "Verifique que DELTA esté en formato DMS (ej: 10°15'30\") y RADIO sea positivo"
    },
    "CURVE_002": {
        "message": "Punto no coincide con radio",
        "solution": "El punto inicial debe estar a la distancia del radio desde el centro"
    },
    "IMPORT_001": {
        "message": "Error al importar archivo",
        "solution": "Verifique que el archivo existe y tiene formato válido (KML, CSV, SHP)"
    },
    "IMPORT_002": {
        "message": "Sistema de coordenadas no detectado",
        "solution": "Seleccione manualmente el sistema de coordenadas antes de importar"
    },
    "EXPORT_001": {
        "message": "Error al exportar archivo",
        "solution": "Verifique permisos de escritura en la carpeta de destino"
    },
    "GEOM_001": {
        "message": "Polígono no cerrado",
        "solution": "El primer y último punto deben ser iguales para cerrar el polígono"
    },
    "GEOM_002": {
        "message": "Puntos insuficientes",
        "solution": "Polígono requiere mín. 3 puntos, Polilínea mín. 2 puntos"
    },
    "MAP_001": {
        "message": "Error de comunicación con el mapa",
        "solution": "Recargue la aplicación o verifique la conexión a internet"
    },
}


def get_error_solution(code: str) -> Optional[str]:
    """Obtiene la solución para un código de error conocido."""
    if code in KNOWN_ERRORS:
        return KNOWN_ERRORS[code]["solution"]
    return None


def get_error_message(code: str) -> Optional[str]:
    """Obtiene el mensaje para un código de error conocido."""
    if code in KNOWN_ERRORS:
        return KNOWN_ERRORS[code]["message"]
    return None

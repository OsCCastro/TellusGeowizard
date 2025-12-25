# ui/coordinate_table.py
"""
Custom table widget for coordinate input with UTM validation.
"""

from PySide6.QtCore import Qt, QRegularExpression, QEvent
from PySide6.QtGui import QRegularExpressionValidator, QBrush
from PySide6.QtWidgets import QStyledItemDelegate, QTableWidget, QTableWidgetItem

from utils.logger import get_logger

logger = get_logger(__name__)


class UTMDelegate(QStyledItemDelegate):
    """
    Custom delegate for UTM coordinate validation in table cells.
    Provides real-time validation and tab navigation between cells.
    """
    
    def createEditor(self, parent, option, index):
        """Create editor widget with UTM coordinate validation."""
        editor = super().createEditor(parent, option, index)
        
        # 6-7 digits + optional decimals for UTM coordinates
        rx = QRegularExpression(r'^\d{6,7}(\.\d+)?$')
        editor.setValidator(QRegularExpressionValidator(rx, editor))
        editor.installEventFilter(self)
        editor.setProperty("row", index.row())
        editor.setProperty("column", index.column())
        
        return editor

    def eventFilter(self, obj, event):
        """
        Handle Tab key navigation between coordinate cells.
        Tab from X column -> Y column
        Tab from Y column -> X column of next row (auto-creates row if needed)
        """
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            table = obj.parent()
            while table and not isinstance(table, QTableWidget):
                table = table.parent()
            
            if not table:
                return False
            
            row = obj.property("row")
            col = obj.property("column")
            
            if col == 1:  # X (Este) column
                # Move to Y (Norte) column
                table.setCurrentCell(row, 2)
                item = table.item(row, 2)
                if item is None:
                    item = QTableWidgetItem("")
                    table.setItem(row, 2, item)
                table.editItem(item)
                
            elif col == 2:  # Y (Norte) column
                # Move to next row's X column, skipping hidden curve sub-rows
                next_row = row + 1
                
                # Skip hidden rows (curve sub-rows)
                while next_row < table.rowCount() and table.isRowHidden(next_row):
                    next_row += 1
                
                if next_row >= table.rowCount():
                    # Auto-create new row
                    table.insertRow(next_row)
                    id_item = QTableWidgetItem(str(next_row + 1))
                    id_item.setFlags(Qt.ItemIsEnabled)
                    table.setItem(next_row, 0, id_item)
                
                table.setCurrentCell(next_row, 1)
                item = table.item(next_row, 1)
                if item is None:
                    item = QTableWidgetItem("")
                    table.setItem(next_row, 1, item)
                table.editItem(item)
            
            return True
        
        return super().eventFilter(obj, event)

    def setModelData(self, editor, model, index):
        """Set model data and apply color based on validation."""
        text = editor.text()
        model.setData(index, text)
        
        # Color text based on validation
        if not (model.flags(index) & Qt.ItemIsSelectable and
                model.data(index, Qt.BackgroundRole)):
            color = Qt.black if editor.hasAcceptableInput() else Qt.red
            model.setData(index, QBrush(color), Qt.ForegroundRole)


class CoordTable(QTableWidget):
    """
    Extended table widget with support for expandable curve parameters.
    Handles Tab key navigation and coordinate/curve input functionality.
    """
    
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
        Incluye indicador visual con icono y colores distintivos.
        
        Args:
            row: Índice de la fila a convertir en curva
        """
        from PySide6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QLabel
        from PySide6.QtGui import QColor, QFont
        
        if row in self.curve_rows:
            return  # Ya es una curva
        
        # Insertar 6 sub-filas debajo de la fila principal 
        # (DELTA, RADIO, CENTRO_X, CENTRO_Y, LONG.CURVA, SUB.TAN)
        for i in range(6):
            self.insertRow(row + i + 1)
        
        # Configurar sub-filas con títulos en columna X, valores en columna Y
        self._setup_subrow(row + 1, "DELTA", "")
        self._setup_subrow(row + 2, "RADIO", "")
        self._setup_subrow(row + 3, "CENTRO_X", "")  # Este (X)
        self._setup_subrow(row + 4, "CENTRO_Y", "")  # Norte (Y)
        self._setup_subrow(row + 5, "LONG.CURVA", "")
        self._setup_subrow(row + 6, "SUB.TAN", "")
        
        # Guardar el contenido original del ID antes de reemplazar
        id_item = self.item(row, 0)
        original_id = id_item.text() if id_item else str(row + 1)
        
        # Crear widget contenedor con icono de curva + botón expandir
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(2)
        
        # Icono de curva (emoji)
        curve_icon = QLabel("📐")
        curve_icon.setStyleSheet("font-size: 14px;")
        curve_icon.setToolTip("Curva")
        layout.addWidget(curve_icon)
        
        # ID text
        id_label = QLabel(original_id)
        id_label.setStyleSheet("font-weight: bold; color: #1565C0;")
        layout.addWidget(id_label)
        
        layout.addStretch()
        
        # Botón expandir/colapsar
        expand_btn = QPushButton("▼")
        expand_btn.setFixedSize(20, 20)
        expand_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 10px;
                color: #666;
            }
            QPushButton:hover {
                background: #E3F2FD;
                border-radius: 3px;
            }
        """)
        expand_btn.setToolTip("Expandir/Colapsar parámetros de curva")
        expand_btn.clicked.connect(lambda: self.toggle_expansion(row))
        layout.addWidget(expand_btn)
        
        # Guardar referencia para toggle
        container.setProperty("expand_btn", expand_btn)
        container.setProperty("original_id", original_id)
        
        self.setCellWidget(row, 0, container)
        
        # Marcar como curva y expandida
        self.curve_rows.add(row)
        self.expanded_rows.add(row)
        
        # Cambiar color de fondo de la fila principal con estilo distintivo
        curve_bg_color = QColor(227, 242, 253)  # Azul muy claro (#E3F2FD)
        curve_text_color = QColor(21, 101, 192)  # Azul Material (#1565C0)
        
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(curve_bg_color)
                if col > 0:  # No cambiar color de texto en columna ID (es un widget)
                    item.setForeground(curve_text_color)
        
        logger.info(f"Fila {row} (ID: {original_id}) marcada como curva con indicador visual")
    
    def _setup_subrow(self, row, label, value):
        """
        Configura una sub-fila con título en X y valor editable en Y.
        
        Args:
            row: Índice de la sub-fila
            label: Etiqueta (DELTA, RADIO, CENTRO, etc.)
            value: Valor inicial
        """
        from PySide6.QtGui import QColor, QFont
        
        # Columna 0 (ID): Vacía y no editable
        empty_id = QTableWidgetItem("")
        empty_id.setFlags(Qt.ItemIsEnabled)
        empty_id.setBackground(QColor(245, 245, 245))  # Gris claro
        self.setItem(row, 0, empty_id)
        
        # Columna 1 (X): Título (no editable, negrita)
        label_item = QTableWidgetItem(label)
        label_item.setFlags(Qt.ItemIsEnabled)
        label_item.setBackground(QColor(245, 245, 245))  # Gris claro
        label_item.setFont(QFont("Arial", 9, QFont.Bold))
        label_item.setForeground(QColor(60, 60, 60))  # Gris oscuro para texto
        self.setItem(row, 1, label_item)
        
        # Columna 2 (Y): Valor editable SIN validación
        value_item = QTableWidgetItem(value)
        value_item.setBackground(QColor(255, 255, 255))  # Blanco (editable)
        # IMPORTANTE: Hacer editable y NO aplicar delegado de validación
        value_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.setItem(row, 2, value_item)
    
    def toggle_expansion(self, row):
        """
        Colapsa/expande las sub-filas de una curva.
        
        Args:
            row: Índice de la fila principal (curva)
        """
        if row not in self.curve_rows:
            return  # No es una curva
        
        container = self.cellWidget(row, 0)
        if not container:
            return
        
        # Get expand button from container's property
        expand_btn = container.property("expand_btn")
        if not expand_btn:
            return
        
        if row in self.expanded_rows:
            # Colapsar: ocultar sub-filas (6 sub-filas)
            for i in range(1, 7):
                self.setRowHidden(row + i, True)
            self.expanded_rows.remove(row)
            expand_btn.setText("►")
            expand_btn.setToolTip("Expandir parámetros de curva")
        else:
            # Expandir: mostrar sub-filas (6 sub-filas)
            for i in range(1, 7):
                self.setRowHidden(row + i, False)
            self.expanded_rows.add(row)
            expand_btn.setText("▼")
            expand_btn.setToolTip("Colapsar parámetros de curva")
    
    def convert_to_point(self, row):
        """
        Convierte una fila de curva a punto normal.
        Restaura el aspecto visual de punto (sin indicador de curva).
        
        Args:
            row: Índice de la fila a convertir
        """
        from PySide6.QtGui import QColor
        
        if row not in self.curve_rows:
            return  # Ya es un punto
        
        # Remover 6 sub-filas
        for i in range(6):
            self.removeRow(row + 1)
        
        # Restaurar celda de ID desde el container widget
        container = self.cellWidget(row, 0)
        if container:
            # Obtener ID original del property
            original_id = container.property("original_id")
            if not original_id:
                original_id = str(row + 1)  # Fallback
            self.removeCellWidget(row, 0)
            id_item = QTableWidgetItem(original_id)
            id_item.setFlags(Qt.ItemIsEnabled)
            self.setItem(row, 0, id_item)
        
        # Restaurar color de fondo normal
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(255, 255, 255))  # Blanco
                item.setForeground(QColor(0, 0, 0))  # Negro (texto normal)
        
        # Remover de conjuntos de seguimiento
        self.curve_rows.discard(row)
        self.expanded_rows.discard(row)
        if row in self.curve_data:
            del self.curve_data[row]
        
        logger.info(f"Fila {row} convertida de curva a punto")
    
    def get_curve_parameters(self, row):
        """
        Obtiene los parámetros de curva de una fila.
        
        Args:
            row: Índice de la fila principal (curva)
        
        Returns:
            dict con keys: 'delta', 'radio', 'centro_x', 'centro_y', 'long_curva', 'sub_tan'
            (o None si no es curva)
        """
        if row not in self.curve_rows:
            return None
        
        # Leer valores de columna 2 (Y) para cada sub-fila
        delta_item = self.item(row + 1, 2)
        radio_item = self.item(row + 2, 2)
        centro_x_item = self.item(row + 3, 2)  # Este (X)
        centro_y_item = self.item(row + 4, 2)  # Norte (Y)
        long_curva_item = self.item(row + 5, 2)
        sub_tan_item = self.item(row + 6, 2)
        
        # Get individual values
        centro_x = centro_x_item.text() if centro_x_item else ""
        centro_y = centro_y_item.text() if centro_y_item else ""
        
        return {
            'delta': delta_item.text() if delta_item else "",
            'radio': radio_item.text() if radio_item else "",
            'centro_x': centro_x,
            'centro_y': centro_y,
            # Keep combined 'centro' for backward compatibility (Y, X format)
            'centro': f"{centro_y}, {centro_x}" if centro_x and centro_y else "",
            'long_curva': long_curva_item.text() if long_curva_item else "",
            'sub_tan': sub_tan_item.text() if sub_tan_item else ""
        }
    
    def keyPressEvent(self, event):
        """
        Handle keyboard events.
        Tab from Y column: move to X column of next row and start editing.
        Skips hidden curve sub-rows.
        """
        if event.key() == Qt.Key_Tab and self.currentColumn() == 2:
            current_row = self.currentRow()
            next_row = current_row + 1
            
            # Si la siguiente fila es una sub-fila de curva, saltarla
            while next_row < self.rowCount() and self.isRowHidden(next_row):
                next_row += 1
            
            if next_row < self.rowCount():
                self.setCurrentCell(next_row, 1)
                # Start editing immediately
                item = self.item(next_row, 1)
                if item is None:
                    item = QTableWidgetItem("")
                    self.setItem(next_row, 1, item)
                self.editItem(item)
            return
        
        super().keyPressEvent(event)


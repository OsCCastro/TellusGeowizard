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
                # Move to next row's X column
                next_row = row + 1
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
        
        Args:
            row: Índice de la fila a convertir en curva
        """
        from PySide6.QtWidgets import QPushButton
        from PySide6.QtGui import QColor, QFont
        
        if row in self.curve_rows:
            return  # Ya es una curva
        
        # Insertar 5 sub-filas debajo de la fila principal (DELTA, RADIO, CENTRO, LONG.CURVA, SUB.TAN)
        for i in range(5):
            self.insertRow(row + i + 1)
        
        # Configurar sub-filas con títulos en columna X, valores en columna Y
        self._setup_subrow(row + 1, "DELTA", "")
        self._setup_subrow(row + 2, "RADIO", "")
        self._setup_subrow(row + 3, "CENTRO", "")
        self._setup_subrow(row + 4, "LONG.CURVA", "")
        self._setup_subrow(row + 5, "SUB.TAN", "")
        
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
        
        btn = self.cellWidget(row, 0)
        if not btn:
            return
        
        if row in self.expanded_rows:
            # Colapsar: ocultar sub-filas (ahora son 5)
            for i in range(1, 6):
                self.setRowHidden(row + i, True)
            self.expanded_rows.remove(row)
            btn.setText("►")
        else:
            # Expandir: mostrar sub-filas
            for i in range(1, 6):
                self.setRowHidden(row + i, False)
            self.expanded_rows.add(row)
            btn.setText("▼")
    
    def convert_to_point(self, row):
        """
        Convierte una fila de curva a punto normal.
        
        Args:
            row: Índice de la fila a convertir
        """
        from PySide6.QtGui import QColor
        
        if row not in self.curve_rows:
            return  # Ya es un punto
        
        # Remover 5 sub-filas
        for i in range(5):
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
            dict con keys: 'delta', 'radio', 'centro', 'long_curva', 'sub_tan' (o None si no es curva)
        """
        if row not in self.curve_rows:
            return None
        
        # Leer valores de columna 2 (Y)
        delta_item = self.item(row + 1, 2)
        radio_item = self.item(row + 2, 2)
        centro_item = self.item(row + 3, 2)
        long_curva_item = self.item(row + 4, 2)
        sub_tan_item = self.item(row + 5, 2)
        
        return {
            'delta': delta_item.text() if delta_item else "",
            'radio': radio_item.text() if radio_item else "",
            'centro': centro_item.text() if centro_item else "",
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


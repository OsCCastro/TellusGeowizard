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
    Custom table widget for coordinate input.
    Handles Tab key navigation and provides coordinate input functionality.
    """
    
    def keyPressEvent(self, event):
        """
        Handle keyboard events.
        Tab from Y column: move to X column of next row and start editing.
        """
        if event.key() == Qt.Key_Tab and self.currentColumn() == 2:
            next_row = self.currentRow() + 1
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

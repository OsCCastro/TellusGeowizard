"""
Validation delegate for coordinate table with real-time validation and visual feedback.
"""

from PySide6.QtWidgets import QStyledItemDelegate, QLineEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen

from utils.coordinate_systems import validate_dms_coordinate


class CoordinateValidationDelegate(QStyledItemDelegate):
    """
    Custom delegate that validates coordinate input in real-time.
    Shows red border and tooltip for invalid coordinates.
    """
    
    validationChanged = Signal(bool)  # Emitted when validity changes (True=valid, False=invalid)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_coord_system = "UTM"
        self.current_hemisphere = "Norte"
        self.invalid_cells = set()  # Track (row, col) of invalid cells
        self.is_dark_mode = False   # Track theme state
        
    def set_dark_mode(self, is_dark: bool):
        """Update dark mode state."""
        self.is_dark_mode = is_dark
    
    def set_coordinate_system(self, coord_system: str, hemisphere: str = "Norte"):
        """Update validation rules when coordinate system changes."""
        self.current_coord_system = coord_system
        self.current_hemisphere = hemisphere
        self.invalid_cells.clear()
    
    def createEditor(self, parent, option, index):
        """Create editor with validation."""
        editor = QLineEdit(parent)
        editor.setFrame(False)
        
        # Set initial style based on validity (assume valid initially or check?)
        # We'll let textChanged handle it, but set initial base style
        if self.is_dark_mode:
            editor.setStyleSheet("background-color: #3b3b3b; color: #ffffff; border: 1px solid #555;")
        else:
            editor.setStyleSheet("background-color: white; color: black; border: 1px solid #cccccc;")
        
        # Connect to validation on text change
        editor.textChanged.connect(lambda text: self._validate_cell(editor, index, text))
        
        return editor
    
    def _validate_cell(self, editor, index, text):
        """Validate input and update visual feedback."""
        if not text.strip():
            self._mark_valid(editor, index)
            return
        
        column = index.column()
        is_valid = False
        tooltip_msg = ""
        
        # Skip ID column (column 0)
        if column == 0:
            self._mark_valid(editor, index)
            return
        
        # Validate based on current coordinate system
        try:
            if self.current_coord_system == "UTM":
                is_longitude = (column == 1)  # X column
                # Simple range check for UTM
                try:
                    value = float(text)
                    if is_longitude:
                        is_valid = 160000 <= value <= 840000
                        if not is_valid:
                            tooltip_msg = "UTM Este (X): Rango válido 160,000 - 840,000"
                    else:
                        is_valid = 0 <= value <= 10000000
                        if not is_valid:
                            tooltip_msg = "UTM Norte (Y): Rango válido 0 - 10,000,000"
                except ValueError:
                    is_valid = False
                    tooltip_msg = "Debe ser un número válido"
            
            elif self.current_coord_system == "Geographic (Decimal Degrees)":
                is_longitude = (column == 1)  # Longitude column
                try:
                    value = float(text)
                    if is_longitude:
                        is_valid = -180 <= value <= 180
                        if not is_valid:
                            tooltip_msg = "Longitud: Rango válido -180 a 180\nEjemplo: -99.133200"
                    else:
                        is_valid = -90 <= value <= 90
                        if not is_valid:
                            tooltip_msg = "Latitud: Rango válido -90 a 90\nEjemplo: 19.432600"
                except ValueError:
                    is_valid = False
                    tooltip_msg = "Debe ser un número decimal válido"
            
            elif self.current_coord_system == "Geographic (DMS)":
                is_longitude = (column == 1)  # Longitude column
                is_valid, value = validate_dms_coordinate(text, is_longitude=is_longitude)
                if not is_valid:
                    tooltip_msg = "Formato DMS inválido.\nEjemplos válidos:\n• 19°25'57.36\"N\n• 19 25 57.36 N\n• 19d 25m 57.36s N"
            
            elif self.current_coord_system == "Web Mercator":
                try:
                    value = float(text)
                    # Web Mercator bounds
                    is_valid = -20037508 <= value <= 20037508
                    if not is_valid:
                        tooltip_msg = "Web Mercator: Rango válido -20,037,508 a 20,037,508"
                except ValueError:
                    is_valid = False
                    tooltip_msg = "Debe ser un número válido"
        
        except Exception as e:
            is_valid = False
            tooltip_msg = f"Error de validación: {str(e)}"
        
        # Update visual feedback
        if is_valid:
            self._mark_valid(editor, index)
        else:
            self._mark_invalid(editor, index, tooltip_msg)
    
    def _mark_valid(self, editor, index):
        """Mark cell as valid - normal styling."""
        if self.is_dark_mode:
            editor.setStyleSheet("border: 1px solid #555; background-color: #3b3b3b; color: #ffffff;")
        else:
            editor.setStyleSheet("border: 1px solid #cccccc; background-color: white; color: black;")
            
        cell_key = (index.row(), index.column())
        if cell_key in self.invalid_cells:
            self.invalid_cells.remove(cell_key)
            self.validationChanged.emit(len(self.invalid_cells) == 0)
            # Force table to repaint
            if hasattr(editor, 'parent') and editor.parent():
                table = editor.parent()
                while table and not hasattr(table, 'viewport'):
                    table = table.parent() if hasattr(table, 'parent') else None
                if table and hasattr(table, 'viewport'):
                    table.viewport().update()
        editor.setToolTip("")
    
    def _mark_invalid(self, editor, index, tooltip_msg):
        """Mark cell as invalid - red border and tooltip."""
        if self.is_dark_mode:
            editor.setStyleSheet("border: 2px solid #ff4444; background-color: #4a2a2a; color: #ffffff;")
        else:
            editor.setStyleSheet("border: 2px solid #ff4444; background-color: #fff5f5; color: black;")
            
        editor.setToolTip(tooltip_msg)
        cell_key = (index.row(), index.column())
        if cell_key not in self.invalid_cells:
            self.invalid_cells.add(cell_key)
            self.validationChanged.emit(False)
        # Force table to repaint
        if hasattr(editor, 'parent') and editor.parent():
            table = editor.parent()
            while table and not hasattr(table, 'viewport'):
                table = table.parent() if hasattr(table, 'parent') else None
            if table and hasattr(table, 'viewport'):
                table.viewport().update()
    
    def paint(self, painter, option, index):
        """Custom paint to show red border for invalid cells."""
        # Call parent paint first for text
        super().paint(painter, option, index)
        
        # Then overlay red border if invalid
        cell_key = (index.row(), index.column())
        if cell_key in self.invalid_cells:
            # Draw red background
            painter.save()
            painter.fillRect(option.rect, QColor(255, 245, 245, 100))  # Semi-transparent red
            painter.restore()
            
            # Draw red border
            painter.save()
            pen = QPen(QColor("#ff4444"), 2)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
            painter.restore()

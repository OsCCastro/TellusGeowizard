# ui/table_manager.py
"""
TableManager - Manages coordinate table operations for GeoWizard.
Extracted from main_window.py to improve separation of concerns.
"""

from typing import TYPE_CHECKING, Optional, List, Dict, Any

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
    QTableWidgetItem, QMenu, QApplication
)

from utils.logger import get_logger

if TYPE_CHECKING:
    from ui.coordinate_table import CoordTable
    from ui.main_window import MainWindow

logger = get_logger(__name__)


class TableManager(QObject):
    """
    Manages coordinate table operations including:
    - Row add/delete
    - Copy/paste operations
    - State save/restore for edit mode
    - Coordinate caching for system conversion
    """
    
    # Signal emitted when table needs redraw
    tableModified = Signal()
    
    def __init__(self, table: 'CoordTable', main_window: 'MainWindow'):
        """
        Initialize TableManager.
        
        Args:
            table: The CoordTable widget to manage
            main_window: Reference to MainWindow for callbacks
        """
        super().__init__()
        self.table = table
        self.main_window = main_window
        
        # State storage for edit mode
        self._original_table_state: Optional[List[List[str]]] = None
        self._original_coord_system: Optional[str] = None
        self._original_zone: Optional[str] = None
        self._original_hemisphere: Optional[str] = None
        
        # Coordinate cache for system conversion
        self._coord_cache: Dict[str, List[Dict[str, Any]]] = {
            "UTM": [],
            "Geographic (Decimal Degrees)": [],
            "Geographic (DMS)": [],
            "Web Mercator": []
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ROW OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def add_row(self) -> int:
        """
        Add a new row at the end of the table.
        
        Returns:
            Index of the new row
        """
        r = self.table.rowCount()
        self.table.insertRow(r)
        
        # Set ID (read-only)
        id_item = QTableWidgetItem(str(r + 1))
        id_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(r, 0, id_item)
        
        # Set focus to X column
        self.table.setCurrentCell(r, 1)
        item = QTableWidgetItem("")
        self.table.setItem(r, 1, item)
        self.table.editItem(item)
        
        logger.debug(f"Added row {r + 1}")
        return r
    
    def delete_current_row(self) -> bool:
        """
        Delete the currently selected row.
        
        Returns:
            True if a row was deleted, False otherwise
        """
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            logger.debug(f"Deleted row {r}")
            self.tableModified.emit()
            return True
        return False
    
    def copy_selection(self) -> str:
        """
        Copy selected cells to clipboard in tab-separated format.
        
        Returns:
            The copied text
        """
        ranges = self.table.selectedRanges()
        if not ranges:
            return ""
        
        text = ""
        for r in ranges:
            for row in range(r.topRow(), r.bottomRow() + 1):
                parts = []
                for col in range(r.leftColumn(), r.rightColumn() + 1):
                    item = self.table.item(row, col)
                    parts.append(item.text() if item else "")
                text += "\t".join(parts) + "\n"
        
        QApplication.clipboard().setText(text)
        logger.debug(f"Copied {len(text)} characters to clipboard")
        return text
    
    def paste_from_clipboard(self) -> int:
        """
        Paste coordinates from clipboard into table.
        Supports comma or tab-separated values.
        
        Returns:
            Number of rows pasted
        """
        from ui.custom_message_box import CustomMessageBox
        
        lines = QApplication.clipboard().text().splitlines()
        r = self.table.currentRow()
        if r < 0:
            r = 0
        
        rows_pasted = 0
        for ln in lines:
            if not ln.strip():
                continue
            
            # Ensure row exists
            if r >= self.table.rowCount():
                self.table.insertRow(r)
                id_item = QTableWidgetItem(str(r + 1))
                id_item.setFlags(Qt.ItemIsEnabled)
                self.table.setItem(r, 0, id_item)
            
            # Parse coordinates (comma or tab separated)
            pts = [p.strip() for p in ln.split(",")]
            if len(pts) < 2:
                pts = [p.strip() for p in ln.split("\t")]
            
            if len(pts) >= 2:
                try:
                    float(pts[0].replace(',', '.'))
                    float(pts[1].replace(',', '.'))
                except ValueError:
                    CustomMessageBox.warning(
                        self.main_window,
                        "Error de Pegado",
                        f"Línea '{ln}' no contiene coordenadas numéricas válidas."
                    )
                    continue
                
                self.table.setItem(r, 1, QTableWidgetItem(pts[0].replace(',', '.')))
                self.table.setItem(r, 2, QTableWidgetItem(pts[1].replace(',', '.')))
                r += 1
                rows_pasted += 1
        
        if rows_pasted > 0:
            self.tableModified.emit()
            logger.debug(f"Pasted {rows_pasted} rows")
        
        return rows_pasted
    
    # ═══════════════════════════════════════════════════════════════════════════
    # VERTEX TYPE CONVERSION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def convert_to_curve(self, row: int) -> bool:
        """
        Convert a row to curve type.
        
        Args:
            row: Row index to convert
            
        Returns:
            True if converted successfully
        """
        if row >= 0 and hasattr(self.table, 'mark_as_curve'):
            self.table.mark_as_curve(row)
            self.tableModified.emit()
            logger.debug(f"Row {row} converted to curve")
            return True
        return False
    
    def convert_to_point(self, row: int) -> bool:
        """
        Convert a row to point type (remove curve parameters).
        
        Args:
            row: Row index to convert
            
        Returns:
            True if converted successfully
        """
        if row >= 0 and hasattr(self.table, 'convert_to_point'):
            self.table.convert_to_point(row)
            self.tableModified.emit()
            logger.debug(f"Row {row} converted to point")
            return True
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STATE MANAGEMENT (for edit mode)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def save_state(self) -> Dict[str, Any]:
        """
        Save current table state for later restoration.
        
        Returns:
            Dictionary with saved state
        """
        table_data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            table_data.append(row_data)
        
        self._original_table_state = table_data
        self._original_coord_system = self.main_window.cb_coord_system.currentText()
        self._original_zone = self.main_window.cb_zona.currentText()
        self._original_hemisphere = self.main_window.cb_hemisferio.currentText()
        
        logger.info(f"Saved table state: {len(table_data)} rows")
        
        return {
            'table_data': table_data,
            'coord_system': self._original_coord_system,
            'zone': self._original_zone,
            'hemisphere': self._original_hemisphere
        }
    
    def restore_state(self) -> bool:
        """
        Restore table to previously saved state.
        
        Returns:
            True if state was restored, False if no saved state
        """
        if not self._original_table_state:
            logger.warning("No saved state to restore")
            return False
        
        # Block signals during restoration
        self.table.blockSignals(True)
        try:
            # Clear and restore table
            self.table.setRowCount(0)
            
            for row_idx, row_data in enumerate(self._original_table_state):
                self.table.insertRow(row_idx)
                for col_idx, cell_text in enumerate(row_data):
                    item = QTableWidgetItem(cell_text)
                    if col_idx == 0:  # ID column
                        item.setFlags(Qt.ItemIsEnabled)
                    self.table.setItem(row_idx, col_idx, item)
            
            # Restore coordinate system settings
            if self._original_coord_system:
                index = self.main_window.cb_coord_system.findText(self._original_coord_system)
                if index >= 0:
                    self.main_window.cb_coord_system.setCurrentIndex(index)
            
            if self._original_zone:
                index = self.main_window.cb_zona.findText(self._original_zone)
                if index >= 0:
                    self.main_window.cb_zona.setCurrentIndex(index)
            
            if self._original_hemisphere:
                index = self.main_window.cb_hemisferio.findText(self._original_hemisphere)
                if index >= 0:
                    self.main_window.cb_hemisferio.setCurrentIndex(index)
            
            logger.info(f"Restored table state: {len(self._original_table_state)} rows")
            
        finally:
            self.table.blockSignals(False)
        
        self.tableModified.emit()
        return True
    
    def clear_saved_state(self):
        """Clear any saved state."""
        self._original_table_state = None
        self._original_coord_system = None
        self._original_zone = None
        self._original_hemisphere = None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COORDINATE CACHING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def save_to_cache(self, system: str):
        """
        Save current table coordinates to cache for the given system.
        
        Args:
            system: Coordinate system name
        """
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
        logger.debug(f"Saved {len(coords)} coordinates to cache for '{system}'")
    
    def restore_from_cache(self, system: str) -> bool:
        """
        Restore table coordinates from cache for the given system.
        
        Args:
            system: Coordinate system name
            
        Returns:
            True if coordinates were restored
        """
        cached = self._coord_cache.get(system, [])
        if not cached:
            return False
        
        logger.debug(f"Restoring {len(cached)} coordinates from cache for '{system}'")
        
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
            self.table.blockSignals(False)
        
        return True
    
    def get_cache(self, system: str) -> List[Dict[str, Any]]:
        """Get cached coordinates for a system."""
        return self._coord_cache.get(system, [])
    
    def has_cached_coords(self, system: str) -> bool:
        """Check if system has cached coordinates."""
        return bool(self._coord_cache.get(system, []))

# tests/test_table_manager.py
"""
Unit tests for TableManager class.
Tests table operations without requiring Qt application.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestTableManagerBasic(unittest.TestCase):
    """Basic tests for TableManager that don't require Qt."""
    
    def test_import_table_manager(self):
        """Test that TableManager can be imported."""
        # This tests the module structure without requiring Qt
        try:
            # Import should work without Qt being initialized
            import ui.table_manager as tm
            self.assertTrue(hasattr(tm, 'TableManager'))
        except ImportError as e:
            self.skipTest(f"Cannot import module: {e}")
    
    def test_logger_exists(self):
        """Test that module has logger configured."""
        try:
            from ui.table_manager import logger
            self.assertIsNotNone(logger)
        except ImportError:
            self.skipTest("Cannot import module")


class TestTableManagerWithMocks(unittest.TestCase):
    """Tests using mocked Qt widgets."""
    
    @classmethod
    def setUpClass(cls):
        """Check if Qt is available."""
        try:
            from PySide6.QtWidgets import QApplication
            # Only create app if not exists
            if not QApplication.instance():
                cls.app = QApplication([])
            else:
                cls.app = QApplication.instance()
            cls.qt_available = True
        except ImportError:
            cls.qt_available = False
    
    def setUp(self):
        if not self.qt_available:
            self.skipTest("Qt not available")
        
        from PySide6.QtWidgets import QTableWidget, QComboBox
        from ui.table_manager import TableManager
        
        # Create real QTableWidget
        self.table = QTableWidget(3, 3)  # 3 rows, 3 columns
        
        # Create mock main_window with required attributes
        self.main_window = MagicMock()
        self.main_window.cb_coord_system = MagicMock()
        self.main_window.cb_zona = MagicMock()
        self.main_window.cb_hemisferio = MagicMock()
        
        # Create TableManager
        self.manager = TableManager(self.table, self.main_window)
    
    def test_add_row(self):
        """Test adding a row to empty table."""
        initial_count = self.table.rowCount()
        new_row = self.manager.add_row()
        
        # Should have added one row
        self.assertEqual(self.table.rowCount(), initial_count + 1)
        self.assertEqual(new_row, initial_count)
    
    def test_delete_current_row(self):
        """Test deleting a selected row."""
        # Add some rows first
        self.manager.add_row()
        self.manager.add_row()
        initial_count = self.table.rowCount()
        
        # Select first row
        self.table.setCurrentCell(0, 0)
        
        # Delete it
        result = self.manager.delete_current_row()
        
        self.assertTrue(result)
        self.assertEqual(self.table.rowCount(), initial_count - 1)
    
    def test_delete_no_selection(self):
        """Test delete when nothing is selected."""
        # Clear selection
        self.table.setCurrentCell(-1, -1)
        
        result = self.manager.delete_current_row()
        
        # Should return False when no row is selected
        # Note: -1 means no selection, but removeRow(-1) does nothing
        self.assertFalse(result)
    
    def test_save_state(self):
        """Test saving table state."""
        from PySide6.QtWidgets import QTableWidgetItem
        
        # Populate table
        self.table.setItem(0, 0, QTableWidgetItem("1"))
        self.table.setItem(0, 1, QTableWidgetItem("100.0"))
        self.table.setItem(0, 2, QTableWidgetItem("200.0"))
        
        # Configure mock returns
        self.main_window.cb_coord_system.currentText.return_value = "UTM"
        self.main_window.cb_zona.currentText.return_value = "14"
        self.main_window.cb_hemisferio.currentText.return_value = "Norte"
        
        # Save state
        state = self.manager.save_state()
        
        # Verify state contains expected data
        self.assertIn('table_data', state)
        self.assertIn('coord_system', state)
        self.assertEqual(state['coord_system'], "UTM")
    
    def test_has_cached_coords_empty(self):
        """Test has_cached_coords when cache is empty."""
        result = self.manager.has_cached_coords("UTM")
        self.assertFalse(result)
    
    def test_save_to_cache(self):
        """Test saving coordinates to cache."""
        from PySide6.QtWidgets import QTableWidgetItem
        
        # Populate table
        self.table.setItem(0, 1, QTableWidgetItem("100.0"))
        self.table.setItem(0, 2, QTableWidgetItem("200.0"))
        
        # Save to cache
        self.manager.save_to_cache("UTM")
        
        # Verify cache
        self.assertTrue(self.manager.has_cached_coords("UTM"))
        cached = self.manager.get_cache("UTM")
        self.assertEqual(len(cached), 1)
        self.assertEqual(cached[0]['x'], "100.0")
        self.assertEqual(cached[0]['y'], "200.0")


class TestCoordinateCaching(unittest.TestCase):
    """Tests specifically for coordinate caching functionality."""
    
    @classmethod
    def setUpClass(cls):
        try:
            from PySide6.QtWidgets import QApplication
            if not QApplication.instance():
                cls.app = QApplication([])
            cls.qt_available = True
        except ImportError:
            cls.qt_available = False
    
    def setUp(self):
        if not self.qt_available:
            self.skipTest("Qt not available")
        
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
        from ui.table_manager import TableManager
        
        self.table = QTableWidget(5, 3)
        self.main_window = MagicMock()
        self.main_window.cb_coord_system = MagicMock()
        self.main_window.cb_zona = MagicMock()
        self.main_window.cb_hemisferio = MagicMock()
        
        self.manager = TableManager(self.table, self.main_window)
        
        # Populate with test data
        for i in range(5):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(f"{100.0 + i}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{200.0 + i}"))
    
    def test_cache_and_restore(self):
        """Test full cache and restore cycle."""
        # Save to cache
        self.manager.save_to_cache("TestSystem")
        
        # Modify table
        from PySide6.QtWidgets import QTableWidgetItem
        self.table.setItem(0, 1, QTableWidgetItem("999.0"))
        
        # Restore from cache
        result = self.manager.restore_from_cache("TestSystem")
        
        self.assertTrue(result)
        self.assertEqual(self.table.item(0, 1).text(), "100.0")
    
    def test_restore_nonexistent_cache(self):
        """Test restoring from non-existent cache."""
        result = self.manager.restore_from_cache("NonExistentSystem")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()

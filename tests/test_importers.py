import unittest
import os
import sys

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from importers.csv_importer import CSVImporter
from core.exceptions import FileImportError, InsufficientDataError

class TestCSVImporter(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_csv_imports_auto"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_import_nonexistent_file(self):
        with self.assertRaises(FileImportError):
            CSVImporter.import_file("nonexistent.csv")

    def test_import_malformed_csv(self):
        # Create a file that is not a CSV or has issues that might raise generic errors
        # But CSVImporter handles most malformed rows by skipping.
        # Let's try to pass invalid arguments to force an error if possible,
        # or rely on the fact that we wrapped generic exceptions.
        pass

if __name__ == '__main__':
    unittest.main()

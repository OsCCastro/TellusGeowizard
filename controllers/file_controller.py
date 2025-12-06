# controllers/file_controller.py
"""
Controller for file operations (export/import).
"""

from typing import Dict, Optional
from pathlib import Path

from exporters.kml_exporter import KMLExporter
from exporters.kmz_exporter import KMZExporter
from exporters.shapefile_exporter import ShapefileExporter
from importers.csv_importer import CSVImporter
from importers.kml_importer import KMLImporter

from utils.logger import get_logger
from utils.exceptions import FileOperationError
from utils.validators import validate_file_extension

logger = get_logger(__name__)


class FileController:
    """
    Handles file import and export operations.
    """
    
    @staticmethod
    def export_kml(features: list, filename: str, hemisphere: str, zone: str,
                   html_dict: Dict[int, str] = None) -> None:
        """
        Export features to KML format.
        
        Args:
            features: List of feature dictionaries
            filename: Output filename
            hemisphere: "Norte" or "Sur"
            zone: UTM zone
            html_dict: Optional HTML descriptions for features
        
        Raises:
            FileOperationError: If export fails
        """
        try:
            if not validate_file_extension(filename, '.kml'):
                filename += '.kml'
            
            KMLExporter.export(features, filename, hemisphere, zone, html_dict)
            logger.info(f"Successfully exported KML to {filename}")
        
        except Exception as e:
            logger.error(f"KML export failed: {e}")
            raise FileOperationError("exportación KML", filename, str(e))
    
    @staticmethod
    def export_kmz(features: list, filename: str, hemisphere: str, zone: str) -> None:
        """
        Export features to KMZ format.
        
        Args:
            features: List of feature dictionaries
            filename: Output filename
            hemisphere: "Norte" or "Sur"
            zone: UTM zone
        
        Raises:
            FileOperationError: If export fails
        """
        try:
            if not validate_file_extension(filename, '.kmz'):
                filename += '.kmz'
            
            KMZExporter.export(features, filename, hemisphere, zone)
            logger.info(f"Successfully exported KMZ to {filename}")
        
        except Exception as e:
            logger.error(f"KMZ export failed: {e}")
            raise FileOperationError("exportación KMZ", filename, str(e))
    
    @staticmethod
    def export_shapefile(features: list, filename: str, hemisphere: str, zone: str) -> None:
        """
        Export features to Shapefile format.
        
        Args:
            features: List of feature dictionaries
            filename: Output filename (base name)
            hemisphere: "Norte" or "Sur"
            zone: UTM zone
        
        Raises:
            FileOperationError: If export fails
        """
        try:
            # Shapefile exporter creates multiple files with different geometry types
            # Remove extension if provided, as exporter adds suffixes
            filename = str(Path(filename).with_suffix(''))
            
            ShapefileExporter.export(features, filename, hemisphere, zone)
            logger.info(f"Successfully exported Shapefile to {filename}")
        
        except Exception as e:
            logger.error(f"Shapefile export failed: {e}")
            raise FileOperationError("exportación Shapefile", filename, str(e))
    
    @staticmethod
    def import_csv(filepath: str, x_col_idx: int = 0, y_col_idx: int = 1,
                   id_col_idx: Optional[int] = None, delimiter: str = ',',
                   skip_header: int = 0) -> list:
        """
        Import coordinates from CSV file.
        
        Args:
            filepath: Path to CSV file
            x_col_idx: Column index for X coordinate (0-based)
            y_col_idx: Column index for Y coordinate (0-based)
            id_col_idx: Optional column index for feature ID
            delimiter: CSV delimiter
            skip_header: Number of header rows to skip
        
        Returns:
            List of imported feature dictionaries
        
        Raises:
            FileOperationError: If import fails
        """
        try:
            features = CSVImporter.import_file(
                filepath,
                x_col_idx=x_col_idx,
                y_col_idx=y_col_idx,
                id_col_idx=id_col_idx,
                delimiter=delimiter,
                skip_header=skip_header
            )
            logger.info(f"Successfully imported {len(features)} features from CSV: {filepath}")
            return features
        
        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            raise FileOperationError("importación CSV", filepath, str(e))
    
    @staticmethod
    def import_kml(filepath: str) -> list:
        """
        Import features from KML file.
        
        Args:
            filepath: Path to KML file
        
        Returns:
            List of imported feature dictionaries
        
        Raises:
            FileOperationError: If import fails
        """
        try:
            features = KMLImporter.import_file(filepath)
            logger.info(f"Successfully imported {len(features)} features from KML: {filepath}")
            return features
        
        except Exception as e:
            logger.error(f"KML import failed: {e}")
            raise FileOperationError("importación KML", filepath, str(e))
    
    @staticmethod
    def get_export_function(format_str: str):
        """
        Get the appropriate export function for the given format.
        
        Args:
            format_str: Format string (.kml, .kmz, .shp)
        
        Returns:
            Export function
        
        Raises:
            ValueError: If format is not supported
        """
        format_map = {
            '.kml': FileController.export_kml,
            '.kmz': FileController.export_kmz,
            '.shp': FileController.export_shapefile
        }
        
        format_lower = format_str.lower()
        if format_lower not in format_map:
            raise ValueError(f"Formato no soportado: {format_str}")
        
        return format_map[format_lower]

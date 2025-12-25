# importers/base_importer.py
"""
Base class for file importers.
Provides common interface and validation for all importer implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pathlib import Path

from utils.logger import get_logger
from utils.exceptions import FileOperationError

logger = get_logger(__name__)


class BaseImporter(ABC):
    """
    Abstract base class for file importers.
    
    All import implementations should inherit from this class
    and implement the required methods.
    """
    
    # Supported file extensions (override in subclass)
    SUPPORTED_EXTENSIONS: List[str] = []
    
    @classmethod
    def validate_file(cls, filepath: str) -> bool:
        """
        Validate that the file exists and has a supported extension.
        
        Args:
            filepath: Path to file to validate
            
        Returns:
            True if file is valid
            
        Raises:
            FileOperationError: If validation fails
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileOperationError(
                "importación", 
                filepath,
                "El archivo especificado no existe"
            )
        
        if not path.is_file():
            raise FileOperationError(
                "importación",
                filepath,
                "La ruta especificada no es un archivo válido"
            )
        
        if cls.SUPPORTED_EXTENSIONS:
            ext = path.suffix.lower()
            if ext not in cls.SUPPORTED_EXTENSIONS:
                raise FileOperationError(
                    "importación",
                    filepath,
                    f"Extensiones soportadas: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
                )
        
        return True
    
    @classmethod
    @abstractmethod
    def import_file(cls, filepath: str, **kwargs) -> List[Dict]:
        """
        Import features from file.
        
        Args:
            filepath: Path to file to import
            **kwargs: Importer-specific options
            
        Returns:
            List of feature dictionaries with {id, type, coords}
        """
        pass
    
    @staticmethod
    def normalize_feature(
        feature_id: any,
        geom_type: str,
        coords: List[tuple],
        properties: Optional[Dict] = None
    ) -> Dict:
        """
        Normalize a feature to standard format.
        
        Args:
            feature_id: Feature identifier
            geom_type: Geometry type (punto, polilínea, polígono)
            coords: List of (x, y) coordinate tuples
            properties: Optional additional properties
            
        Returns:
            Normalized feature dictionary
        """
        # Normalize geometry type
        type_map = {
            "point": "Punto",
            "punto": "Punto",
            "linestring": "Polilínea",
            "polilinea": "Polilínea",
            "polilínea": "Polilínea",
            "polygon": "Polígono",
            "poligono": "Polígono",
            "polígono": "Polígono"
        }
        
        normalized_type = type_map.get(geom_type.lower(), geom_type)
        
        feature = {
            "id": feature_id,
            "type": normalized_type,
            "coords": coords
        }
        
        if properties:
            feature["properties"] = properties
        
        return feature
    
    @staticmethod
    def remove_duplicate_closing_point(coords: List[tuple]) -> List[tuple]:
        """
        Remove duplicate closing point from polygon coordinates.
        
        Args:
            coords: List of coordinate tuples
            
        Returns:
            Coordinates without duplicate closing point
        """
        if len(coords) > 1 and coords[0] == coords[-1]:
            return coords[:-1]
        return coords


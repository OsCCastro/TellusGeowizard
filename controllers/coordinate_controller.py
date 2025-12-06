# controllers/coordinate_controller.py
"""
Controller for coordinate operations and transformations.
"""

from typing import List, Tuple, Optional
from pyproj import Transformer

from core.coordinate_manager import CoordinateManager, GeometryType
from utils.logger import get_logger
from utils.validators import validate_coordinate, get_epsg_code
from utils.exceptions import InvalidCoordinateError, CoordinateTransformError

logger = get_logger(__name__)


class CoordinateController:
    """
    Handles coordinate operations, validation, and transformations.
    """
    
    def __init__(self, hemisphere: str, zone: int):
        """
        Initialize the coordinate controller.
        
        Args:
            hemisphere: "Norte" or "Sur"
            zone: UTM zone number (1-60)
        """
        self.hemisphere = hemisphere
        self.zone = zone
        self.manager = CoordinateManager(hemisphere, zone)
        logger.info(f"CoordinateController initialized: Zone {zone}, Hemisphere {hemisphere}")
    
    def add_coordinates(self, feature_id: int, geom_type: str, coords: List[Tuple[float, float]]) -> None:
        """
        Add coordinates as a feature.
        
        Args:
            feature_id: Feature ID
            geom_type: Geometry type ("Punto", "Polilínea", "Polígono")
            coords: List of (x, y) coordinate tuples
        
        Raises:
            InvalidCoordinateError: If coordinates are invalid
        """
        try:
            self.manager.add_feature(feature_id, geom_type, coords)
            logger.debug(f"Added feature {feature_id} of type {geom_type} with {len(coords)} coordinates")
        except Exception as e:
            logger.error(f"Failed to add feature {feature_id}: {e}")
            raise
    
    def get_features(self) -> list:
        """Get all features from the manager."""
        return self.manager.get_features()
    
    def clear(self) -> None:
        """Clear all features."""
        self.manager.clear()
        logger.debug("Cleared all features")
    
    def update_zone_hemisphere(self, hemisphere: str, zone: int) -> None:
        """
        Update the UTM zone and hemisphere.
        
        Args:
            hemisphere: "Norte" or "Sur"
            zone: UTM zone number (1-60)
        """
        self.hemisphere = hemisphere
        self.zone = zone
        # Recreate manager with new settings
        features_backup = self.manager.get_features()
        self.manager = CoordinateManager(hemisphere, zone)
        
        # Re-add features
        for feat in features_backup:
            self.manager.add_feature(feat["id"], feat["type"], feat["coords"])
        
        logger.info(f"Updated zone/hemisphere: Zone {zone}, Hemisphere {hemisphere}")
    
    def transform_to_wgs84(self, coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Transform UTM coordinates to WGS84 (lat/lon).
        
        Args:
            coords: List of (x, y) UTM coordinates
        
        Returns:
            List of (lon, lat) coordinates in WGS84
        
        Raises:
            CoordinateTransformError: If transformation fails
        """
        try:
            epsg_code = get_epsg_code(self.zone, self.hemisphere)
            transformer = Transformer.from_crs(
                f"EPSG:{epsg_code}",
                "EPSG:4326",
                always_xy=True
            )
            
            transformed = []
            for x, y in coords:
                lon, lat = transformer.transform(x, y)
                transformed.append((lon, lat))
            
            logger.debug(f"Transformed {len(coords)} coordinates from UTM to WGS84")
            return transformed
        
        except Exception as e:
            logger.error(f"Coordinate transformation failed: {e}")
            raise CoordinateTransformError(
                f"EPSG:{epsg_code}",
                "EPSG:4326",
                str(e)
            )
    
    def parse_coordinate_value(self, value: str) -> Optional[float]:
        """
        Parse and validate a coordinate value string.
        
        Args:
            value: String value to parse
        
        Returns:
            Parsed float value, or None if invalid
        """
        is_valid, parsed = validate_coordinate(value, allow_empty=True)
        if is_valid:
            return parsed
        return None
    
    def validate_geometry_coordinates(self, coords: List[Tuple[float, float]], geom_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that coordinates are appropriate for the geometry type.
        
        Args:
            coords: List of coordinate tuples
            geom_type: Geometry type
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        from utils.validators import validate_coordinates_for_geometry
        return validate_coordinates_for_geometry(coords, geom_type)

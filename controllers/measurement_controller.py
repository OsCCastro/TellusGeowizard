# controllers/measurement_controller.py
"""
Controller for measurement calculations.
Handles distance, area, and perimeter calculations with unit conversions.
"""

from typing import List, Tuple, Dict, Optional

from utils.measurements import (
    calculate_distance_utm,
    calculate_distance_geographic,
    calculate_distance_with_curves,
    calculate_area_utm,
    calculate_area_geographic,
    calculate_perimeter_utm,
    calculate_perimeter_geographic,
    format_distance,
    format_area
)
from utils.logger import get_logger

logger = get_logger(__name__)


class MeasurementController:
    """
    Controller for geometry measurements.
    
    Provides a unified interface for calculating distances, areas, and perimeters
    with support for different coordinate systems and curved segments.
    """
    
    def __init__(self, use_metric: bool = True):
        """
        Initialize measurement controller.
        
        Args:
            use_metric: True for metric units, False for imperial
        """
        self.use_metric = use_metric
    
    def set_units(self, use_metric: bool):
        """Set unit preference."""
        self.use_metric = use_metric
    
    def calculate_distance(
        self, 
        coords: List[Tuple[float, float]], 
        is_geographic: bool = False,
        curves: Optional[List[Dict]] = None
    ) -> float:
        """
        Calculate total distance along a path.
        
        Args:
            coords: List of (x, y) or (lon, lat) tuples
            is_geographic: True if coords are geographic (lon, lat)
            curves: Optional list of curve segments for arc-aware calculation
            
        Returns:
            Distance in meters
        """
        if len(coords) < 2:
            return 0.0
        
        if curves and not is_geographic:
            return calculate_distance_with_curves(coords, curves)
        elif is_geographic:
            return calculate_distance_geographic(coords)
        else:
            return calculate_distance_utm(coords)
    
    def calculate_area(
        self, 
        coords: List[Tuple[float, float]], 
        is_geographic: bool = False
    ) -> float:
        """
        Calculate area of a polygon.
        
        Args:
            coords: List of (x, y) or (lon, lat) tuples
            is_geographic: True if coords are geographic (lon, lat)
            
        Returns:
            Area in square meters
        """
        if len(coords) < 3:
            return 0.0
        
        if is_geographic:
            return calculate_area_geographic(coords)
        else:
            return calculate_area_utm(coords)
    
    def calculate_perimeter(
        self, 
        coords: List[Tuple[float, float]], 
        is_geographic: bool = False,
        curves: Optional[List[Dict]] = None
    ) -> float:
        """
        Calculate perimeter of a polygon.
        
        Args:
            coords: List of (x, y) or (lon, lat) tuples
            is_geographic: True if coords are geographic (lon, lat)
            curves: Optional list of curve segments
            
        Returns:
            Perimeter in meters
        """
        if len(coords) < 3:
            return 0.0
        
        # For arc-aware perimeter, close the ring and use distance calculation
        if curves and not is_geographic:
            closed_coords = coords + [coords[0]]
            return calculate_distance_with_curves(closed_coords, curves)
        elif is_geographic:
            return calculate_perimeter_geographic(coords)
        else:
            return calculate_perimeter_utm(coords)
    
    def get_formatted_measurements(
        self, 
        coords: List[Tuple[float, float]], 
        is_polygon: bool = False,
        is_geographic: bool = False,
        curves: Optional[List[Dict]] = None
    ) -> Dict[str, str]:
        """
        Get all measurements formatted with units.
        
        Args:
            coords: List of coordinates
            is_polygon: True if geometry is a polygon
            is_geographic: True if geographic coordinates
            curves: Optional curve segments
            
        Returns:
            Dict with 'distance', 'area', 'perimeter' keys
        """
        distance_unit = "km" if self.use_metric else "mi"
        area_unit = "ha" if self.use_metric else "ac"
        
        distance = self.calculate_distance(coords, is_geographic, curves)
        
        result = {
            "distance": format_distance(distance, distance_unit),
            "area": "--",
            "perimeter": "--"
        }
        
        if is_polygon and len(coords) >= 3:
            area = self.calculate_area(coords, is_geographic)
            perimeter = self.calculate_perimeter(coords, is_geographic, curves)
            
            result["area"] = format_area(area, area_unit)
            result["perimeter"] = format_distance(perimeter, distance_unit)
        
        return result


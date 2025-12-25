# controllers/map_controller.py
"""
Controller for map-related operations.
Handles web map updates, feature synchronization, and coordinate transformations.
"""

import json
from typing import List, Dict, Optional, Tuple

from pyproj import Transformer

from core.coordinate_manager import CoordinateManager, GeometryType
from utils.logger import get_logger
from utils.coordinate_systems import get_utm_epsg

logger = get_logger(__name__)


class MapController:
    """
    Controller for managing web map operations.
    
    Responsibilities:
    - Convert features between coordinate systems for map display
    - Build GeoJSON from table data
    - Sync map markers with table coordinates
    """
    
    def __init__(self, hemisphere: str = "Norte", zone: int = 14):
        """
        Initialize map controller.
        
        Args:
            hemisphere: "Norte" or "Sur"
            zone: UTM zone number
        """
        self.hemisphere = hemisphere
        self.zone = zone
        self._transformer_cache = {}
    
    def set_projection(self, hemisphere: str, zone: int):
        """Update projection settings and clear transformer cache."""
        self.hemisphere = hemisphere
        self.zone = zone
        self._transformer_cache.clear()
    
    def _get_transformer(self, from_epsg: str, to_epsg: str) -> Transformer:
        """Get or create cached transformer."""
        key = (from_epsg, to_epsg)
        if key not in self._transformer_cache:
            self._transformer_cache[key] = Transformer.from_crs(
                from_epsg, to_epsg, always_xy=True
            )
        return self._transformer_cache[key]
    
    def utm_to_wgs84(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert UTM coordinates to WGS84 (lon, lat).
        
        Args:
            x: UTM Easting
            y: UTM Northing
            
        Returns:
            Tuple of (longitude, latitude)
        """
        epsg = get_utm_epsg(self.zone, self.hemisphere)
        transformer = self._get_transformer(f"EPSG:{epsg}", "EPSG:4326")
        return transformer.transform(x, y)
    
    def wgs84_to_utm(self, lon: float, lat: float) -> Tuple[float, float]:
        """
        Convert WGS84 (lon, lat) to UTM coordinates.
        
        Args:
            lon: Longitude
            lat: Latitude
            
        Returns:
            Tuple of (Easting, Northing)
        """
        epsg = get_utm_epsg(self.zone, self.hemisphere)
        transformer = self._get_transformer("EPSG:4326", f"EPSG:{epsg}")
        return transformer.transform(lon, lat)
    
    def build_geojson_from_table(self, table_data: List[Dict]) -> Dict:
        """
        Build GeoJSON FeatureCollection from table data.
        
        Args:
            table_data: List of dicts with {id, x, y} for each row
            
        Returns:
            GeoJSON FeatureCollection dict
        """
        features = []
        
        for row in table_data:
            row_id = row.get('id', '')
            x = row.get('x')
            y = row.get('y')
            
            if x is None or y is None:
                continue
            
            try:
                lon, lat = self.utm_to_wgs84(float(x), float(y))
                
                feature = {
                    "type": "Feature",
                    "properties": {"id": row_id},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    }
                }
                features.append(feature)
                
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping row {row_id}: {e}")
                continue
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    def build_geojson_from_manager(self, mgr: CoordinateManager) -> Dict:
        """
        Build GeoJSON FeatureCollection from CoordinateManager.
        
        Args:
            mgr: CoordinateManager with features
            
        Returns:
            GeoJSON FeatureCollection dict
        """
        features = []
        
        for feat in mgr.get_features():
            coords = feat["coords"]
            feat_type = feat["type"]
            feat_id = feat["id"]
            
            # Convert coordinates to WGS84
            wgs84_coords = [self.utm_to_wgs84(x, y) for x, y in coords]
            
            if feat_type == GeometryType.PUNTO:
                geom = {"type": "Point", "coordinates": wgs84_coords[0]}
            elif feat_type == GeometryType.POLILINEA:
                geom = {"type": "LineString", "coordinates": wgs84_coords}
            elif feat_type == GeometryType.POLIGONO:
                geom = {"type": "Polygon", "coordinates": [wgs84_coords]}
            else:
                continue
            
            features.append({
                "type": "Feature", 
                "properties": {"id": feat_id},
                "geometry": geom
            })
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    def generate_update_js(self, geojson: Dict) -> str:
        """
        Generate JavaScript code to update map features.
        
        Args:
            geojson: GeoJSON FeatureCollection
            
        Returns:
            JavaScript code string
        """
        return (
            "window.clearFeatures && window.clearFeatures();"
            f"window.addFeature && window.addFeature({json.dumps(geojson)})"
        )
    
    def generate_center_js(self, lat: float, lon: float, zoom: int = 15) -> str:
        """
        Generate JavaScript code to center map on coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            zoom: Zoom level (default 15)
            
        Returns:
            JavaScript code string
        """
        return f"if (typeof centerMap === 'function') {{ centerMap({lat}, {lon}, {zoom}); }}"
    
    def generate_edit_mode_js(self, enabled: bool) -> str:
        """
        Generate JavaScript to enable/disable edit mode.
        
        Args:
            enabled: True to enable editing
            
        Returns:
            JavaScript code string
        """
        return f"if (typeof setEditable === 'function') {{ setEditable({'true' if enabled else 'false'}); }}"


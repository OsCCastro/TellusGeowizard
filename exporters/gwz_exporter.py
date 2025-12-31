# exporters/gwz_exporter.py
"""
GeoWizard Native Format (.gwz) Exporter

The .gwz format is a JSON-based project file that stores:
- Project metadata (zone, hemisphere, coordinate system)
- All vertices with multiple coordinate representations (UTM, DD, DMS, Web Mercator)
- Curve parameters for curved segments
- Calculated measurements
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pyproj import Transformer
import logging

logger = logging.getLogger(__name__)

# Version of the GWZ format
GWZ_VERSION = "1.0"


class GWZExporter:
    """
    Exports GeoWizard project data to .gwz native format.
    
    The format includes all coordinate conversions pre-calculated for
    fast loading and offline use.
    """
    
    @staticmethod
    def utm_to_geographic(x: float, y: float, zone: int, hemisphere: str) -> Tuple[float, float]:
        """Convert UTM coordinates to Geographic (lon, lat)."""
        try:
            epsg_code = 32600 + zone if hemisphere.upper().startswith('N') else 32700 + zone
            transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(x, y)
            return lon, lat
        except Exception as e:
            logger.warning(f"Error converting UTM to Geographic: {e}")
            return None, None
    
    @staticmethod  
    def utm_to_web_mercator(x: float, y: float, zone: int, hemisphere: str) -> Tuple[float, float]:
        """Convert UTM coordinates to Web Mercator (EPSG:3857)."""
        try:
            epsg_code = 32600 + zone if hemisphere.upper().startswith('N') else 32700 + zone
            transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:3857", always_xy=True)
            wm_x, wm_y = transformer.transform(x, y)
            return wm_x, wm_y
        except Exception as e:
            logger.warning(f"Error converting UTM to Web Mercator: {e}")
            return None, None
    
    @staticmethod
    def decimal_to_dms(decimal_degrees: float, is_longitude: bool) -> str:
        """Convert decimal degrees to DMS string format."""
        if decimal_degrees is None:
            return ""
        
        direction = ""
        if is_longitude:
            direction = "W" if decimal_degrees < 0 else "E"
        else:
            direction = "S" if decimal_degrees < 0 else "N"
        
        decimal_degrees = abs(decimal_degrees)
        degrees = int(decimal_degrees)
        minutes_decimal = (decimal_degrees - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        
        return f"{degrees}°{minutes}'{seconds:.2f}\"{direction}"
    
    @staticmethod
    def export(
        table,  # CoordTable instance
        filename: str,
        zone: int,
        hemisphere: str,
        coord_system: str,
        measurements: Optional[Dict[str, float]] = None,
        project_data: Optional[Dict[str, Any]] = None,
        selected_geometries: Optional[List[str]] = None,
        map_preview_base64: Optional[str] = None
    ) -> bool:
        """
        Export table data to GWZ format.
        
        Args:
            table: CoordTable instance with coordinate data
            filename: Output file path (.gwz)
            zone: UTM zone number
            hemisphere: 'Norte' or 'Sur'
            coord_system: Current coordinate system in use
            measurements: Optional dict with area, perimeter, distance values
            project_data: Optional dict with wizard project data (titulo, codigo, etc.)
            selected_geometries: Optional list of selected geometry IDs
            map_preview_base64: Optional base64-encoded map preview image
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Build the GWZ data structure
            gwz_data = {
                "version": GWZ_VERSION,
                "metadata": {
                    "zona_utm": zone,
                    "hemisferio": hemisphere,
                    "sistema_predeterminado": "UTM",
                    "fecha_creacion": datetime.now().isoformat(),
                    "software": "GeoWizard V.1.0"
                },
                "project_data": project_data or {},
                "vertices": [],
                "mediciones": measurements or {},
                "selected_geometries": selected_geometries or [],
                "map_preview": map_preview_base64
            }
            
            # Get curve rows set
            curve_rows = getattr(table, 'curve_rows', set())
            
            # Process each row
            row = 0
            while row < table.rowCount():
                # Skip hidden rows
                if table.isRowHidden(row):
                    row += 1
                    continue
                
                # Get ID
                id_item = table.item(row, 0)
                if not id_item or not id_item.text().strip():
                    row += 1
                    continue
                
                vertex_id = id_item.text().strip()
                
                # Check if this is a curve sub-row (skip these, they're part of curve data)
                x_item = table.item(row, 1)
                if x_item:
                    x_text = x_item.text().strip().upper()
                    if x_text in ('DELTA', 'RADIO', 'CENTRO', 'CENTRO_X', 'CENTRO_Y', 'LONG.CURVA', 'SUB.TAN'):
                        row += 1
                        continue
                
                # Get coordinates
                y_item = table.item(row, 2)
                if not x_item or not y_item:
                    row += 1
                    continue
                
                x_text = x_item.text().strip()
                y_text = y_item.text().strip()
                
                if not x_text or not y_text:
                    row += 1
                    continue
                
                try:
                    x_val = float(x_text)
                    y_val = float(y_text)
                except ValueError:
                    row += 1
                    continue
                
                # Determine if this is a curve row
                is_curve = row in curve_rows
                
                # Convert coordinates (assuming input is UTM)
                # If coord_system is not UTM, we'd need to convert to UTM first
                utm_x, utm_y = x_val, y_val
                
                # Get all coordinate representations
                lon, lat = GWZExporter.utm_to_geographic(utm_x, utm_y, zone, hemisphere)
                wm_x, wm_y = GWZExporter.utm_to_web_mercator(utm_x, utm_y, zone, hemisphere)
                
                # Create vertex entry
                vertex = {
                    "id": vertex_id,
                    "tipo": "curva" if is_curve else "punto",
                    "coordenadas": {
                        "utm": {"x": utm_x, "y": utm_y},
                        "geograficas_dd": {"lon": lon, "lat": lat} if lon is not None else None,
                        "geograficas_dms": {
                            "lon": GWZExporter.decimal_to_dms(lon, True),
                            "lat": GWZExporter.decimal_to_dms(lat, False)
                        } if lon is not None else None,
                        "web_mercator": {"x": wm_x, "y": wm_y} if wm_x is not None else None
                    }
                }
                
                # If curve, get curve parameters
                if is_curve:
                    params = table.get_curve_parameters(row)
                    if params:
                        vertex["parametros_curva"] = {
                            "delta": params.get('delta', ''),
                            "radio": params.get('radio', ''),
                            "centro_x": params.get('centro_x', ''),
                            "centro_y": params.get('centro_y', ''),
                            "long_curva": params.get('long_curva', ''),
                            "sub_tan": params.get('sub_tan', '')
                        }
                    
                    # Skip the 6 sub-rows after a curve row
                    row += 7
                else:
                    row += 1
                
                gwz_data["vertices"].append(vertex)
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(gwz_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"GWZ file exported successfully: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting GWZ file: {e}")
            raise RuntimeError(f"Error al exportar archivo GWZ: {e}")

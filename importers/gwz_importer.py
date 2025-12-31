# importers/gwz_importer.py
"""
GeoWizard Native Format (.gwz) Importer

Imports .gwz project files and populates the coordinate table with
all data including curve parameters.
"""

import json
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class GWZImporter:
    """
    Imports GeoWizard project data from .gwz native format.
    
    The .gwz format stores complete project data including:
    - Multiple coordinate representations
    - Curve parameters
    - Project metadata
    """
    
    @staticmethod
    def validate_gwz_data(data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate the structure of GWZ data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "El archivo no contiene un objeto JSON válido"
        
        if "version" not in data:
            return False, "Falta el campo 'version' en el archivo GWZ"
        
        if "vertices" not in data:
            return False, "Falta el campo 'vertices' en el archivo GWZ"
        
        if not isinstance(data["vertices"], list):
            return False, "El campo 'vertices' debe ser una lista"
        
        return True, ""
    
    @staticmethod
    def import_file(filename: str) -> Dict[str, Any]:
        """
        Import a GWZ file and return its contents.
        
        Args:
            filename: Path to the .gwz file
            
        Returns:
            Dictionary with the parsed GWZ data including:
            - metadata: zone, hemisphere, etc.
            - vertices: list of vertex dictionaries
            - measurements: area, perimeter, distance
            
        Raises:
            RuntimeError: If file cannot be read or parsed
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            is_valid, error_msg = GWZImporter.validate_gwz_data(data)
            if not is_valid:
                raise ValueError(error_msg)
            
            logger.info(f"GWZ file imported: {filename} (version {data.get('version', 'unknown')})")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing GWZ file: {e}")
            raise RuntimeError(f"Error al parsear archivo GWZ: {e}")
        except FileNotFoundError:
            logger.error(f"GWZ file not found: {filename}")
            raise RuntimeError(f"Archivo GWZ no encontrado: {filename}")
        except Exception as e:
            logger.error(f"Error importing GWZ file: {e}")
            raise RuntimeError(f"Error al importar archivo GWZ: {e}")
    
    @staticmethod
    def populate_table(table, gwz_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Populate a CoordTable with data from imported GWZ.
        
        Args:
            table: CoordTable instance to populate
            gwz_data: Parsed GWZ data dictionary
            
        Returns:
            Dictionary with metadata for UI updates (zone, hemisphere, etc.)
        """
        from PySide6.QtWidgets import QTableWidgetItem
        
        # Block signals to prevent itemChanged from triggering auto-row-addition
        table.blockSignals(True)
        
        try:
            # Clear existing data
            table.setRowCount(0)
            table.curve_rows = set()
            
            metadata = gwz_data.get("metadata", {})
            vertices = gwz_data.get("vertices", [])
        
            for vertex in vertices:
                vertex_id = vertex.get("id", "")
                vertex_type = vertex.get("tipo", "punto")
                coords = vertex.get("coordenadas", {})
                
                # Get UTM coordinates (default)
                utm = coords.get("utm", {})
                x = utm.get("x", "")
                y = utm.get("y", "")
                
                # Add row to table - get the current count BEFORE inserting
                current_row = table.rowCount()
                table.insertRow(current_row)
                
                # Set ID
                table.setItem(current_row, 0, QTableWidgetItem(str(vertex_id)))
                
                # Set coordinates
                table.setItem(current_row, 1, QTableWidgetItem(str(x) if x != "" else ""))
                table.setItem(current_row, 2, QTableWidgetItem(str(y) if y != "" else ""))
                
                # If it's a curve, mark it and add curve parameters
                if vertex_type == "curva":
                    curve_params = vertex.get("parametros_curva", {})
                    
                    # Mark as curve (this adds 6 sub-rows automatically)
                    table.mark_as_curve(current_row)
                    
                    # NOTE: After mark_as_curve, 6 sub-rows were inserted after current_row
                    # The sub-rows are at current_row + 1 through current_row + 6
                    # Order: DELTA, RADIO, CENTRO_X, CENTRO_Y, LONG.CURVA, SUB.TAN
                    
                    # DELTA (row + 1, column 2)
                    delta_item = table.item(current_row + 1, 2)
                    if delta_item:
                        delta_item.setText(str(curve_params.get('delta', '')))
                    
                    # RADIO (row + 2, column 2)
                    radio_item = table.item(current_row + 2, 2)
                    if radio_item:
                        radio_item.setText(str(curve_params.get('radio', '')))
                    
                    # CENTRO_X (row + 3, column 2)
                    centro_x_item = table.item(current_row + 3, 2)
                    if centro_x_item:
                        centro_x_item.setText(str(curve_params.get('centro_x', '')))
                    
                    # CENTRO_Y (row + 4, column 2)
                    centro_y_item = table.item(current_row + 4, 2)
                    if centro_y_item:
                        centro_y_item.setText(str(curve_params.get('centro_y', '')))
                    
                    # LONG.CURVA (row + 5, column 2)
                    long_curva_item = table.item(current_row + 5, 2)
                    if long_curva_item:
                        long_curva_item.setText(str(curve_params.get('long_curva', '')))
                    
                    # SUB.TAN (row + 6, column 2)
                    sub_tan_item = table.item(current_row + 6, 2)
                    if sub_tan_item:
                        sub_tan_item.setText(str(curve_params.get('sub_tan', '')))
        
            logger.info(f"Populated table with {len(vertices)} vertices from GWZ")
        
        finally:
            # Restore signals so normal editing works
            table.blockSignals(False)
        
        return {
            "zone": metadata.get("zona_utm", 14),
            "hemisphere": metadata.get("hemisferio", "Norte"),
            "coord_system": metadata.get("sistema_predeterminado", "UTM"),
            "measurements": gwz_data.get("mediciones", {}),
            "selected_geometries": gwz_data.get("selected_geometries", []),
            "map_preview": gwz_data.get("map_preview", None)
        }

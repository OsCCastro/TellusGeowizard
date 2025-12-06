"""
Shapefile importer for GeoWizard application.

Imports ESRI Shapefiles (.shp) and converts them to GeoWizard's internal format.
Supports Point, Polyline, and Polygon geometries with coordinate system conversion.
"""

import shapefile
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from pyproj import Transformer, CRS
from core.exceptions import FileImportError
from utils.logger import get_logger

logger = get_logger(__name__)


class ShapefileImporter:
    """Import ESRI Shapefiles and convert to GeoWizard format."""
    
    # Shapefile geometry type mapping
    GEOMETRY_TYPE_MAP = {
        1: "punto",           # Point
        3: "polilínea",       # Polyline
        5: "polígono",        # Polygon
        8: "punto",           # MultiPoint (treat as points)
        11: "punto",          # PointZ
        13: "polilínea",      # PolylineZ
        15: "polígono",       # PolygonZ
        21: "punto",          # PointM
        23: "polilínea",      # PolylineM
        25: "polígono",       # PolygonM
    }
    
    @staticmethod
    def import_file(filepath: str) -> Tuple[List[Dict], Optional[str]]:
        """
        Import shapefile and return list of features with CRS info.
        
        Args:
            filepath: Path to .shp file
        
        Returns:
            Tuple of (features_list, crs_string)
            - features_list: List of dicts with id, type, coords, attributes
            - crs_string: CRS description (e.g., "EPSG:4326") or None
        
        Raises:
            FileImportError: If file cannot be read or is invalid
        """
        try:
            logger.info(f"Importing shapefile: {filepath}")
            
            # Validate file exists
            shp_path = Path(filepath)
            if not shp_path.exists():
                raise FileImportError(
                    f"Archivo no encontrado: {filepath}",
                    details="El archivo .shp no existe"
                )
            
            # Check for required companion files
            dbf_path = shp_path.with_suffix('.dbf')
            shx_path = shp_path.with_suffix('.shx')
            
            if not dbf_path.exists():
                logger.warning(f"Missing .dbf file: {dbf_path}")
            if not shx_path.exists():
                logger.warning(f"Missing .shx file: {shx_path}")
            
            # Read shapefile
            try:
                sf = shapefile.Reader(str(shp_path))
            except Exception as e:
                raise FileImportError(
                    "No se pudo leer el archivo shapefile",
                    details=f"Error al abrir: {str(e)}"
                )
            
            # Detect CRS from .prj file
            crs_string = ShapefileImporter._detect_crs(shp_path)
            
            # Get geometry type
            shape_type = sf.shapeType
            geom_type = ShapefileImporter.GEOMETRY_TYPE_MAP.get(shape_type)
            
            if geom_type is None:
                raise FileImportError(
                    f"Tipo de geometría no soportado: {shape_type}",
                    details=f"El shapefile contiene geometrías de tipo {shape_type} que no son compatibles"
                )
            
            logger.info(f"Shapefile geometry type: {geom_type} (type code: {shape_type})")
            
            # Extract features
            features = []
            shapes = sf.shapes()
            records = sf.records() if dbf_path.exists() else []
            
            for idx, shape in enumerate(shapes):
                try:
                    # Get coordinates based on geometry type
                    coords = ShapefileImporter._extract_coordinates(shape, geom_type)
                    
                    if not coords:
                        logger.warning(f"Skipping feature {idx}: no valid coordinates")
                        continue
                    
                    # Get attributes if available
                    attributes = {}
                    if idx < len(records):
                        try:
                            record = records[idx]
                            # Convert record to dict using field names
                            field_names = [field[0] for field in sf.fields[1:]]  # Skip DeletionFlag
                            attributes = dict(zip(field_names, record))
                        except Exception as e:
                            logger.warning(f"Error reading attributes for feature {idx}: {e}")
                    
                    feature = {
                        "id": idx + 1,
                        "type": geom_type,
                        "coords": coords,
                        "attributes": attributes
                    }
                    features.append(feature)
                    
                except Exception as e:
                    logger.warning(f"Error processing feature {idx}: {e}")
                    continue
            
            sf.close()
            
            if not features:
                raise FileImportError(
                    "No se encontraron geometrías válidas en el shapefile",
                    details="El archivo no contiene datos que puedan ser importados"
                )
            
            logger.info(f"Successfully imported {len(features)} features from shapefile")
            return features, crs_string
            
        except FileImportError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error importing shapefile: {e}", exc_info=True)
            raise FileImportError(
                "Error inesperado al importar shapefile",
                details=str(e)
            )
    
    @staticmethod
    def _detect_crs(shp_path: Path) -> Optional[str]:
        """
        Detect CRS from .prj file.
        
        Args:
            shp_path: Path to .shp file
        
        Returns:
            CRS string (e.g., "EPSG:4326") or None if not found
        """
        prj_path = shp_path.with_suffix('.prj')
        
        if not prj_path.exists():
            logger.warning(f"No .prj file found: {prj_path}")
            return None
        
        try:
            with open(prj_path, 'r') as f:
                prj_text = f.read()
            
            # Try to parse WKT to CRS
            crs = CRS.from_wkt(prj_text)
            
            # Try to get EPSG code
            if crs.to_epsg():
                crs_string = f"EPSG:{crs.to_epsg()}"
                logger.info(f"Detected CRS: {crs_string}")
                return crs_string
            else:
                # Return WKT if no EPSG code
                logger.info(f"CRS detected but no EPSG code available")
                return prj_text
                
        except Exception as e:
            logger.warning(f"Error reading .prj file: {e}")
            return None
    
    @staticmethod
    def _extract_coordinates(shape, geom_type: str) -> List[Tuple[float, float]]:
        """
        Extract coordinates from shapefile shape.
        
        Args:
            shape: Shapefile shape object
            geom_type: Geometry type (punto, polilínea, polígono)
        
        Returns:
            List of (x, y) coordinate tuples
        """
        coords = []
        
        try:
            if geom_type == "punto":
                # Point geometry
                if hasattr(shape, 'points') and shape.points:
                    # MultiPoint
                    for point in shape.points:
                        coords.append((point[0], point[1]))
                elif hasattr(shape, 'point'):
                    # Single point
                    coords.append((shape.point[0], shape.point[1]))
                    
            elif geom_type in ["polilínea", "polígono"]:
                # Polyline or Polygon
                if hasattr(shape, 'points') and shape.points:
                    # Handle multi-part geometries
                    if hasattr(shape, 'parts') and len(shape.parts) > 1:
                        # Multi-part: use first part only
                        logger.warning("Multi-part geometry detected, using first part only")
                        start_idx = shape.parts[0]
                        end_idx = shape.parts[1] if len(shape.parts) > 1 else len(shape.points)
                        points = shape.points[start_idx:end_idx]
                    else:
                        # Single part
                        points = shape.points
                    
                    for point in points:
                        coords.append((point[0], point[1]))
            
        except Exception as e:
            logger.error(f"Error extracting coordinates: {e}")
        
        return coords

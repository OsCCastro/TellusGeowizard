# utils/validators.py
"""
Validation utilities for GeoWizard application.
Provides functions to validate user input and data integrity.
"""

import re
from typing import Tuple, Optional
from constants import (
    COORDINATE_PATTERN,
    ID_PATTERN,
    UTM_ZONES,
    HEMISPHERES,
    DEFAULT_EPSG_NORTH_BASE,
    DEFAULT_EPSG_SOUTH_BASE
)
from core.coordinate_manager import GeometryType
from .exceptions import InvalidCoordinateError, ValidationError


def validate_coordinate(value: str, allow_empty: bool = False) -> Tuple[bool, Optional[float]]:
    """
    Validate a coordinate value string.
    
    Args:
        value: String value to validate
        allow_empty: Whether to allow empty strings
    
    Returns:
        Tuple of (is_valid, parsed_value)
        - is_valid: True if the value is valid
        - parsed_value: Float value if valid, None otherwise
    """
    if not value or not value.strip():
        if allow_empty:
            return True, None
        return False, None
    
    value = value.strip()
    
    # Try to match the pattern
    if not re.match(COORDINATE_PATTERN, value):
        return False, None
    
    try:
        parsed = float(value)
        return True, parsed
    except ValueError:
        return False, None


def validate_numeric(value: str, min_val: float = None, max_val: float = None) -> Tuple[bool, Optional[float]]:
    """
    Validate a numeric value with optional range checking.
    
    Args:
        value: String value to validate
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
    
    Returns:
        Tuple of (is_valid, parsed_value)
    """
    is_valid, parsed = validate_coordinate(value, allow_empty=False)
    
    if not is_valid:
        return False, None
    
    if min_val is not None and parsed < min_val:
        return False, None
    
    if max_val is not None and parsed > max_val:
        return False, None
    
    return True, parsed


def validate_utm_zone(zone) -> Tuple[bool, Optional[int]]:
    """
    Validate UTM zone number.
    
    Args:
        zone: Zone value (string or int)
    
    Returns:
        Tuple of (is_valid, zone_int)
    """
    try:
        zone_int = int(zone)
        if zone_int in UTM_ZONES:
            return True, zone_int
        return False, None
    except (ValueError, TypeError):
        return False, None


def validate_hemisphere(hemisphere: str) -> Tuple[bool, Optional[str]]:
    """
    Validate hemisphere value.
    
    Args:
        hemisphere: Hemisphere string
    
    Returns:
        Tuple of (is_valid, normalized_hemisphere)
    """
    if not hemisphere:
        return False, None
    
    hemisphere = hemisphere.strip().capitalize()
    
    if hemisphere in HEMISPHERES:
        return True, hemisphere
    
    # Try to match partial input
    for valid_hemi in HEMISPHERES:
        if valid_hemi.lower().startswith(hemisphere.lower()):
            return True, valid_hemi
    
    return False, None


def validate_geometry_type(geom_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate geometry type.
    
    Args:
        geom_type: Geometry type string
    
    Returns:
        Tuple of (is_valid, normalized_type)
    """
    if not geom_type:
        return False, None
    
    geom_type = geom_type.strip()
    
    if geom_type in GeometryType.VALID_TYPES:
        return True, geom_type
    
    return False, None


def validate_id(value: str) -> Tuple[bool, Optional[int]]:
    """
    Validate an ID value.
    
    Args:
        value: String value to validate
    
    Returns:
        Tuple of (is_valid, id_int)
    """
    if not value or not value.strip():
        return False, None
    
    value = value.strip()
    
    if not re.match(ID_PATTERN, value):
        return False, None
    
    try:
        id_int = int(value)
        if id_int > 0:
            return True, id_int
        return False, None
    except ValueError:
        return False, None


def get_epsg_code(zone: int, hemisphere: str) -> int:
    """
    Get EPSG code for UTM zone and hemisphere.
    
    Args:
        zone: UTM zone number (1-60)
        hemisphere: "Norte" or "Sur"
    
    Returns:
        EPSG code
    
    Raises:
        ValidationError: If zone or hemisphere is invalid
    """
    is_valid_zone, zone_int = validate_utm_zone(zone)
    if not is_valid_zone:
        raise ValidationError("zona", zone, "Zona UTM debe estar entre 1 y 60")
    
    is_valid_hemi, hemi = validate_hemisphere(hemisphere)
    if not is_valid_hemi:
        raise ValidationError("hemisferio", hemisphere, "Debe ser 'Norte' o 'Sur'")
    
    if hemi.lower() == "norte":
        return DEFAULT_EPSG_NORTH_BASE + zone_int
    else:
        return DEFAULT_EPSG_SOUTH_BASE + zone_int


def validate_file_extension(filename: str, expected_extension: str) -> bool:
    """
    Validate that a filename has the expected extension.
    
    Args:
        filename: Filename to check
        expected_extension: Expected extension (with or without leading dot)
    
    Returns:
        True if extension matches
    """
    if not filename:
        return False
    
    if not expected_extension.startswith('.'):
        expected_extension = '.' + expected_extension
    
    return filename.lower().endswith(expected_extension.lower())


def validate_coordinates_for_geometry(coords: list, geom_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that coordinates list is appropriate for the geometry type.
    
    Args:
        coords: List of coordinate tuples
        geom_type: Geometry type string
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if valid
        - error_message: Error description if invalid, None otherwise
    """
    if not coords:
        return False, "Lista de coordenadas vacía"
    
    is_valid_type, normalized_type = validate_geometry_type(geom_type)
    if not is_valid_type:
        return False, f"Tipo de geometría inválido: {geom_type}"
    
    if normalized_type == GeometryType.PUNTO:
        if len(coords) != 1:
            return False, f"Punto debe tener exactamente 1 coordenada, tiene {len(coords)}"
    
    elif normalized_type == GeometryType.POLILINEA:
        if len(coords) < 2:
            return False, f"Polilínea debe tener al menos 2 coordenadas, tiene {len(coords)}"
    
    elif normalized_type == GeometryType.POLIGONO:
        if len(coords) < 3:
            return False, f"Polígono debe tener al menos 3 coordenadas, tiene {len(coords)}"
    
    return True, None


def validate_decimal_degrees(value: str, is_longitude: bool = False) -> Tuple[bool, Optional[float]]:
    """
    Validate decimal degrees coordinate.
    
    Args:
        value: String value to validate
        is_longitude: True if this is longitude (-180 to 180), False for latitude (-90 to 90)
    
    Returns:
        Tuple of (is_valid, parsed_value)
    """
    if not value or not value.strip():
        return False, None
    
    try:
        parsed = float(value.strip())
        
        if is_longitude:
            if -180 <= parsed <= 180:
                return True, parsed
        else:  # latitude
            if -90 <= parsed <= 90:
                return True, parsed
        
        return False, None
    except ValueError:
        return False, None


def validate_web_mercator(value: str) -> Tuple[bool, Optional[float]]:
    """
    Validate Web Mercator coordinate.
    Web Mercator coordinates are in meters and can be quite large.
    
    Args:
        value: String value to validate
    
    Returns:
        Tuple of (is_valid, parsed_value)
    """
    if not value or not value.strip():
        return False, None
    
    try:
        parsed = float(value.strip())
        # Web Mercator range is approximately ±20,037,508 meters
        if -20037509 <= parsed <= 20037509:
            return True, parsed
        return False, None
    except ValueError:
        return False, None


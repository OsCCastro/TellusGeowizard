# utils/coordinate_systems.py
"""
Coordinate system definitions and conversion utilities.
Supports UTM, Geographic (Decimal Degrees and DMS), and Web Mercator.
"""

import re
from typing import Tuple, Optional
from enum import Enum

from utils.logger import get_logger
from utils.exceptions import CoordinateTransformError, ValidationError

logger = get_logger(__name__)


class CoordinateSystemType(Enum):
    """Supported coordinate system types."""
    UTM = "UTM"
    GEOGRAPHIC_DD = "Geographic (Decimal Degrees)"
    GEOGRAPHIC_DMS = "Geographic (DMS)"
    WEB_MERCATOR = "Web Mercator"


class CoordinateSystem:
    """Base class for coordinate system definitions."""
    
    def __init__(self, name: str, epsg: Optional[int], requires_zone: bool, 
                 requires_hemisphere: bool, x_label: str, y_label: str):
        self.name = name
        self.epsg = epsg
        self.requires_zone = requires_zone
        self.requires_hemisphere = requires_hemisphere
        self.x_label = x_label
        self.y_label = y_label


# Coordinate System Definitions
COORDINATE_SYSTEMS = {
    CoordinateSystemType.UTM: CoordinateSystem(
        name="UTM",
        epsg=None,  # Dynamic based on zone/hemisphere
        requires_zone=True,
        requires_hemisphere=True,
        x_label="Este (X)",
        y_label="Norte (Y)"
    ),
    CoordinateSystemType.GEOGRAPHIC_DD: CoordinateSystem(
        name="Geographic (Decimal Degrees)",
        epsg=4326,  # WGS84
        requires_zone=False,
        requires_hemisphere=False,
        x_label="Longitud",
        y_label="Latitud"
    ),
    CoordinateSystemType.GEOGRAPHIC_DMS: CoordinateSystem(
        name="Geographic (DMS)",
        epsg=4326,  # WGS84
        requires_zone=False,
        requires_hemisphere=False,
        x_label="Longitud (DMS)",
        y_label="Latitud (DMS)"
    ),
    CoordinateSystemType.WEB_MERCATOR: CoordinateSystem(
        name="Web Mercator",
        epsg=3857,
        requires_zone=False,
        requires_hemisphere=False,
        x_label="X (metros)",
        y_label="Y (metros)"
    ),
}


def dms_to_dd(degrees: float, minutes: float, seconds: float, direction: str) -> float:
    """
    Convert Degrees, Minutes, Seconds to Decimal Degrees.
    
    Args:
        degrees: Degrees component
        minutes: Minutes component (0-59)
        seconds: Seconds component (0-59.999...)
        direction: Direction ('N', 'S', 'E', 'W')
    
    Returns:
        Decimal degrees value
    
    Raises:
        ValidationError: If components are out of range
    """
    if not (0 <= minutes < 60):
        raise ValidationError("minutes", minutes, "Minutos deben estar entre 0 y 59")
    
    if not (0 <= seconds < 60):
        raise ValidationError("seconds", seconds, "Segundos deben estar entre 0 y 59.999")
    
    direction = direction.upper()
    if direction not in ['N', 'S', 'E', 'W']:
        raise ValidationError("direction", direction, "Dirección debe ser N, S, E, o W")
    
    dd = abs(degrees) + (minutes / 60.0) + (seconds / 3600.0)
    
    # Make negative for South and West
    if direction in ['S', 'W']:
        dd = -dd
    
    return dd


def dd_to_dms(dd: float, is_longitude: bool = False) -> Tuple[int, int, float, str]:
    """
    Convert Decimal Degrees to Degrees, Minutes, Seconds.
    
    Args:
        dd: Decimal degrees value
        is_longitude: True if this is longitude (E/W), False for latitude (N/S)
    
    Returns:
        Tuple of (degrees, minutes, seconds, direction)
    """
    # Determine direction
    if is_longitude:
        direction = 'E' if dd >= 0 else 'W'
    else:
        direction = 'N' if dd >= 0 else 'S'
    
    # Work with absolute value
    dd_abs = abs(dd)
    
    # Extract components
    degrees = int(dd_abs)
    minutes_decimal = (dd_abs - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    return degrees, minutes, seconds, direction


def parse_dms(dms_str: str) -> Tuple[float, float, float, str]:
    """
    Parse a DMS string into components.
    
    Supported formats:
    - 19°25'57.36"N
    - 19° 25' 57.36" N
    - 19 25 57.36 N
    - 19d 25m 57.36s N
    
    Args:
        dms_str: DMS string to parse
    
    Returns:
        Tuple of (degrees, minutes, seconds, direction)
    
    Raises:
        ValidationError: If format is invalid
    """
    dms_str = dms_str.strip()
    
    # Pattern to match various DMS formats
    # Captures: degrees, minutes, seconds, direction
    patterns = [
        r'(\d+)[°d]\s*(\d+)[\'m]\s*([\d.]+)[\"s]?\s*([NSEWnsew])',  # 19°25'57.36"N
        r'(\d+)\s+(\d+)\s+([\d.]+)\s+([NSEWnsew])',  # 19 25 57.36 N
        r'(\d+)[°d]\s*(\d+)[\'m]\s*([NSEWnsew])',  # 19°25'N (no seconds)
    ]
    
    for pattern in patterns:
        match = re.match(pattern, dms_str)
        if match:
            groups = match.groups()
            degrees = float(groups[0])
            minutes = float(groups[1])
            
            if len(groups) == 4:
                seconds = float(groups[2])
                direction = groups[3].upper()
            else:  # No seconds
                seconds = 0.0
                direction = groups[2].upper()
            
            return degrees, minutes, seconds, direction
    
    raise ValidationError("DMS format", dms_str, 
                         "Formato debe ser como: 19°25'57.36\"N o 19 25 57.36 N")


def format_dms(degrees: int, minutes: int, seconds: float, direction: str) -> str:
    """
    Format DMS components into a readable string.
    
    Args:
        degrees: Degrees component
        minutes: Minutes component
        seconds: Seconds component
        direction: Direction letter
    
    Returns:
        Formatted DMS string
    """
    return f"{degrees}°{minutes:02d}'{seconds:05.2f}\"{direction}"


def validate_dms_coordinate(dms_str: str, is_longitude: bool = False) -> Tuple[bool, Optional[float]]:
    """
    Validate a DMS coordinate string and convert to decimal degrees.
    
    Args:
        dms_str: DMS string to validate
        is_longitude: True if this should be longitude, False for latitude
    
    Returns:
        Tuple of (is_valid, decimal_degrees_value)
    """
    try:
        degrees, minutes, seconds, direction = parse_dms(dms_str)
        
        # Validate direction matches coordinate type
        if is_longitude and direction not in ['E', 'W']:
            return False, None
        if not is_longitude and direction not in ['N', 'S']:
            return False, None
        
        # Validate degree range
        if is_longitude and not (0 <= degrees <= 180):
            return False, None
        if not is_longitude and not (0 <= degrees <= 90):
            return False, None
        
        # Convert to decimal degrees
        dd = dms_to_dd(degrees, minutes, seconds, direction)
        
        return True, dd
    
    except (ValidationError, ValueError, AttributeError):
        return False, None


def get_utm_epsg(zone: int, hemisphere: str) -> int:
    """
    Get EPSG code for a UTM zone and hemisphere.
    
    Args:
        zone: UTM zone (1-60)
        hemisphere: "Norte" or "Sur"
    
    Returns:
        EPSG code
    """
    if hemisphere.lower() in ['norte', 'north', 'n']:
        return 32600 + zone
    else:
        return 32700 + zone


def get_coordinate_system_info(cs_type: CoordinateSystemType) -> CoordinateSystem:
    """
    Get coordinate system information.
    
    Args:
        cs_type: Coordinate system type
    
    Returns:
        CoordinateSystem object
    """
    return COORDINATE_SYSTEMS[cs_type]

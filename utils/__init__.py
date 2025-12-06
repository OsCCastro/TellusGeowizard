# utils/__init__.py
"""
Utility modules for GeoWizard application.
"""

from .logger import get_logger, setup_logging
from .validators import (
    validate_coordinate,
    validate_utm_zone,
    validate_hemisphere,
    validate_geometry_type
)
from .exceptions import (
    GeoWizardError,
    InvalidCoordinateError,
    InvalidGeometryError,
    FileOperationError,
    ValidationError
)

# Export coordinate system utilities
from .coordinate_systems import (
    CoordinateSystem,
    dd_to_dms,
    dms_to_dd,
    format_dms,
    parse_dms,
    validate_dms_coordinate,
    get_utm_epsg
)

# Export measurement utilities
from .measurements import (
    calculate_distance_utm,
    calculate_distance_geographic,
    calculate_area_utm,
    calculate_area_geographic,
    calculate_perimeter_utm,
    calculate_perimeter_geographic,
    convert_distance,
    convert_area,
    format_distance,
    format_area
)

__all__ = [
    # Logger
    'get_logger',
    'setup_logging',
    # Validators
    'validate_coordinate',
    'validate_utm_zone',
    'validate_hemisphere',
    'validate_geometry_type',
    # Exceptions
    'GeoWizardError',
    'InvalidCoordinateError',
    'InvalidGeometryError',
    'FileOperationError',
    'ValidationError',
    # Coordinate systems
    'CoordinateSystem',
    'dd_to_dms',
    'dms_to_dd',
    'format_dms',
    'parse_dms',
    'validate_dms_coordinate',
    'get_utm_epsg',
    # Measurements
    'calculate_distance_utm',
    'calculate_distance_geographic',
    'calculate_area_utm',
    'calculate_area_geographic',
    'calculate_perimeter_utm',
    'calculate_perimeter_geographic',
    'convert_distance',
    'convert_area',
    'format_distance',
    'format_area'
]

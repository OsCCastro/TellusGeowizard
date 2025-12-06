"""
Measurement utilities for calculating distances, areas, and perimeters.
Supports both planar (UTM) and geodesic (geographic) calculations.
"""

from math import sqrt
from pyproj import Geod

# Initialize WGS84 ellipsoid for geodesic calculations
geod = Geod(ellps='WGS84')


def calculate_distance_utm(coords):
    """
    Calculate distance for UTM coordinates (planar).
    
    Args:
        coords: List of (x, y) tuples in UTM meters
        
    Returns:
        float: Total distance in meters
    """
    if len(coords) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        distance = sqrt((x2 - x1)**2 + (y2 - y1)**2)
        total_distance += distance
    
    return total_distance


def calculate_distance_geographic(coords):
    """
    Calculate geodesic distance for geographic coordinates.
    
    Args:
        coords: List of (lon, lat) tuples in decimal degrees
        
    Returns:
        float: Total distance in meters
    """
    if len(coords) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i + 1]
        # geod.inv returns (forward_azimuth, back_azimuth, distance)
        _, _, distance = geod.inv(lon1, lat1, lon2, lat2)
        total_distance += distance
    
    return total_distance


def calculate_area_utm(coords):
    """
    Calculate area for UTM coordinates using Shoelace formula (planar).
    
    Args:
        coords: List of (x, y) tuples in UTM meters
        
    Returns:
        float: Area in square meters
    """
    if len(coords) < 3:
        return 0.0
    
    # Remove duplicate closing point if it exists (first == last)
    # The Shoelace formula works on a non-closed polygon
    working_coords = coords[:]  # Make a copy
    if len(working_coords) >= 3 and working_coords[0] == working_coords[-1]:
        working_coords = working_coords[:-1]
    
    # Shoelace formula
    area = 0.0
    n = len(working_coords)
    for i in range(n):
        j = (i + 1) % n
        area += working_coords[i][0] * working_coords[j][1]
        area -= working_coords[j][0] * working_coords[i][1]
    
    return abs(area) / 2.0



def calculate_area_geographic(coords):
    """
    Calculate geodesic area for geographic coordinates.
    
    Args:
        coords: List of (lon, lat) tuples in decimal degrees
        
    Returns:
        float: Area in square meters
    """
    if len(coords) < 3:
        return 0.0
    
    # Remove duplicate closing point if it exists (first == last)
    # The geodesic calculation handles polygon closure automatically
    working_coords = coords[:]  # Make a copy
    if len(working_coords) >= 3 and working_coords[0] == working_coords[-1]:
        working_coords = working_coords[:-1]
    
    # Extract lons and lats
    lons = [coord[0] for coord in working_coords]
    lats = [coord[1] for coord in working_coords]
    
    # polygon_area_perimeter returns (area, perimeter)
    area, _ = geod.polygon_area_perimeter(lons, lats)
    
    return abs(area)



def calculate_perimeter_utm(coords):
    """
    Calculate perimeter for UTM polygon (planar).
    
    Args:
        coords: List of (x, y) tuples in UTM meters
        
    Returns:
        float: Perimeter in meters
    """
    if len(coords) < 3:
        return 0.0
    
    # Remove duplicate closing point if it exists (first == last)
    # This prevents double-counting when we add our own closing point
    working_coords = coords[:]  # Make a copy
    if len(working_coords) >= 3 and working_coords[0] == working_coords[-1]:
        working_coords = working_coords[:-1]
    
    # Now close the ring
    closed_coords = working_coords + [working_coords[0]]
    return calculate_distance_utm(closed_coords)



def calculate_perimeter_geographic(coords):
    """
    Calculate geodesic perimeter for geographic polygon.
    
    Args:
        coords: List of (lon, lat) tuples in decimal degrees
        
    Returns:
        float: Perimeter in meters
    """
    if len(coords) < 3:
        return 0.0
    
    # Remove duplicate closing point if it exists (first == last)
    # This prevents double-counting in the geodesic calculation
    working_coords = coords[:]  # Make a copy
    if len(working_coords) >= 3 and working_coords[0] == working_coords[-1]:
        working_coords = working_coords[:-1]
    
    # Extract lons and lats
    lons = [coord[0] for coord in working_coords]
    lats = [coord[1] for coord in working_coords]
    
    # polygon_area_perimeter returns (area, perimeter)
    # It automatically closes the polygon, so we don't need to add the first point
    _, perimeter = geod.polygon_area_perimeter(lons, lats)
    
    return abs(perimeter)



# Unit conversion functions

def convert_distance(value_meters, to_unit="m"):
    """
    Convert distance from meters to specified unit.
    
    Args:
        value_meters: Distance in meters
        to_unit: Target unit ('m', 'km', 'ft', 'mi')
        
    Returns:
        float: Converted distance
    """
    conversions = {
        "m": 1.0,
        "km": 0.001,
        "ft": 3.28084,
        "mi": 0.000621371
    }
    
    return value_meters * conversions.get(to_unit, 1.0)


def convert_area(value_m2, to_unit="m2"):
    """
    Convert area from square meters to specified unit.
    
    Args:
        value_m2: Area in square meters
        to_unit: Target unit ('m2', 'km2', 'ha', 'ft2', 'ac')
        
    Returns:
        float: Converted area
    """
    conversions = {
        "m2": 1.0,
        "km2": 0.000001,
        "ha": 0.0001,  # hectares
        "ft2": 10.7639,
        "ac": 0.000247105  # acres
    }
    
    return value_m2 * conversions.get(to_unit, 1.0)


def format_distance(value_meters, unit="m"):
    """
    Format distance with appropriate precision and unit label.
    
    Args:
        value_meters: Distance in meters
        unit: Preferred display unit
        
    Returns:
        str: Formatted distance string
    """
    value = convert_distance(value_meters, unit)
    
    if value < 1:
        return f"{value * 1000:.2f} m" if unit == "km" else f"{value:.4f} {unit}"
    elif value < 1000:
        return f"{value:.2f} {unit}"
    else:
        return f"{value:,.2f} {unit}"


def format_area(value_m2, unit="m2"):
    """
    Format area with appropriate precision and unit label.
    
    Args:
        value_m2: Area in square meters
        unit: Preferred display unit
        
    Returns:
        str: Formatted area string
    """
    value = convert_area(value_m2, unit)
    
    unit_labels = {
        "m2": "m²",
        "km2": "km²",
        "ha": "ha",
        "ft2": "ft²",
        "ac": "acres"
    }
    
    label = unit_labels.get(unit, unit)
    
    if value < 1:
        return f"{value:.4f} {label}"
    elif value < 1000:
        return f"{value:.2f} {label}"
    else:
        return f"{value:,.2f} {label}"

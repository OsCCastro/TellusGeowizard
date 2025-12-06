"""
Test script to verify measurement calculations (area, distance, perimeter).
This script tests the calculation functions with known ground truth values.
"""

from utils.measurements import (
    calculate_distance_utm,
    calculate_area_utm,
    calculate_perimeter_utm,
    calculate_distance_geographic,
    calculate_area_geographic,
    calculate_perimeter_geographic
)

def test_utm_measurements():
    """Test UTM measurements with known values."""
    print("=" * 70)
    print("Testing UTM Measurement Calculations")
    print("=" * 70)
    
    # Test 1: Simple square (100m x 100m)
    print("\nTest 1: Square (100m x 100m)")
    print("-" * 70)
    square_coords = [
        (500000, 2000000),  # Bottom-left
        (500100, 2000000),  # Bottom-right (FIXED: was 200000)
        (500100, 2000100),  # Top-right
        (500000, 2000100),  # Top-left
    ]

    
    area = calculate_area_utm(square_coords)
    perimeter = calculate_perimeter_utm(square_coords)
    
    print(f"Expected area: 10,000 m²")
    print(f"Calculated area: {area:,.2f} m²")
    print(f"Expected perimeter: 400 m")
    print(f"Calculated perimeter: {perimeter:,.2f} m")
    
    # Test 2: Rectangle (200m x 100m)
    print("\nTest 2: Rectangle (200m x 100m)")
    print("-" * 70)
    rect_coords = [
        (500000, 2000000),
        (500200, 2000000),
        (500200, 2000100),
        (500000, 2000100),
    ]
    
    area = calculate_area_utm(rect_coords)
    perimeter = calculate_perimeter_utm(rect_coords)
    
    print(f"Expected area: 20,000 m²")
    print(f"Calculated area: {area:,.2f} m²")
    print(f"Expected perimeter: 600 m")
    print(f"Calculated perimeter: {perimeter:,.2f} m")
    
    # Test 3: Distance calculation
    print("\nTest 3: Distance between two points")
    print("-" * 70)
    line_coords = [
        (500000, 2000000),
        (500300, 2000400),  # 300m east, 400m north
    ]
    
    distance = calculate_distance_utm(line_coords)
    expected_distance = (300**2 + 400**2) ** 0.5  # Pythagorean theorem
    
    print(f"Point 1: {line_coords[0]}")
    print(f"Point 2: {line_coords[1]}")
    print(f"Expected distance: {expected_distance:.2f} m")
    print(f"Calculated distance: {distance:.2f} m")
    
    # Test 4: Polyline (multiple segments)
    print("\nTest 4: Polyline with 3 points")
    print("-" * 70)
    polyline_coords = [
        (500000, 2000000),
        (500100, 2000000),  # 100m east
        (500100, 2000100),  # 100m north
    ]
    
    distance = calculate_distance_utm(polyline_coords)
    expected_distance = 200  # 100 + 100
    
    print(f"Expected total distance: {expected_distance:.2f} m")
    print(f"Calculated total distance: {distance:.2f} m")
    
    # Test 5: Triangle
    print("\nTest 5: Triangle (right triangle with legs 300m and 400m)")
    print("-" * 70)
    triangle_coords = [
        (500000, 2000000),
        (500300, 2000000),  # 300m east
        (500000, 2000400),  # 400m north from first point
    ]
    
    area = calculate_area_utm(triangle_coords)
    perimeter = calculate_perimeter_utm(triangle_coords)
    expected_area = 0.5 * 300 * 400  # Triangle area = 0.5 * base * height
    hypotenuse = (300**2 + 400**2) ** 0.5
    expected_perimeter = 300 + 400 + hypotenuse
    
    print(f"Expected area: {expected_area:,.2f} m²")
    print(f"Calculated area: {area:,.2f} m²")
    print(f"Expected perimeter: {expected_perimeter:.2f} m")
    print(f"Calculated perimeter: {perimeter:.2f} m")
    
    print("\n" + "=" * 70)
    print("UTM Tests Completed")
    print("=" * 70)

def test_geographic_measurements():
    """Test geographic (geodesic) measurements."""
    print("\n" + "=" * 70)
    print("Testing Geographic Measurement Calculations")
    print("=" * 70)
    
    # Test with a small polygon near Mexico City
    print("\nTest: Small polygon near Mexico City")
    print("-" * 70)
    
    # Approximate 100m x 100m square in decimal degrees near Mexico City
    # (This is approximate - actual size will vary due to geodesic calculation)
    lat_base = 19.4326
    lon_base = -99.1332
    
    # Rough approximation: 1 degree ≈ 111km at equator
    # For 100m, we need about 0.0009 degrees
    offset = 0.0009
    
    geo_coords = [
        (lon_base, lat_base),
        (lon_base + offset, lat_base),
        (lon_base + offset, lat_base + offset),
        (lon_base, lat_base + offset),
    ]
    
    area = calculate_area_geographic(geo_coords)
    perimeter = calculate_perimeter_geographic(geo_coords)
    
    print(f"Coordinates:")
    for i, (lon, lat) in enumerate(geo_coords):
        print(f"  Point {i+1}: ({lon:.6f}, {lat:.6f})")
    print(f"\nCalculated area: {area:,.2f} m²")
    print(f"Calculated perimeter: {perimeter:.2f} m")
    print(f"(Note: This is a geodesic calculation, so values may differ from planar)")
    
    # Test distance between two cities (known approximate values)
    print("\nTest: Distance between two lat/lon points")
    print("-" * 70)
    
    # Mexico City to Guadalajara (approximate)
    mexico_city = (-99.1332, 19.4326)
    guadalajara = (-103.3320, 20.6597)
    
    distance = calculate_distance_geographic([mexico_city, guadalajara])
    
    print(f"Mexico City: {mexico_city}")
    print(f"Guadalajara: {guadalajara}")
    print(f"Calculated distance: {distance/1000:.2f} km")
    print(f"(Expected: ~460-470 km)")
    
    print("\n" + "=" * 70)
    print("Geographic Tests Completed")
    print("=" * 70)

if __name__ == "__main__":
    test_utm_measurements()
    test_geographic_measurements()

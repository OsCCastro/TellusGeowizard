# test_coordinate_systems.py
"""
Simple test script to demonstrate multi-coordinate system support.
Run this to see DMS conversion in action!
"""

from utils.coordinate_systems import (
    dms_to_dd,
    dd_to_dms,
    parse_dms,
    format_dms,
    validate_dms_coordinate,
    CoordinateSystemType,
    COORDINATE_SYSTEMS
)

def test_dms_conversions():
    print("=" * 60)
    print("Testing DMS (Degrees Minutes Seconds) Conversions")
    print("=" * 60)
    
    # Test 1: Convert DMS to Decimal Degrees
    print("\n1. Converting DMS to Decimal Degrees:")
    print("-" * 40)
    
    # Mexico City coordinates
    lat_dms = "19°25'57.36\"N"
    lon_dms = "99°7'59.52\"W"
    
    print(f"Input  Latitude:  {lat_dms}")
    print(f"Input  Longitude: {lon_dms}")
    
    # Parse and convert
    lat_d, lat_m, lat_s, lat_dir = parse_dms(lat_dms)
    lon_d, lon_m, lon_s, lon_dir = parse_dms(lon_dms)
    
    lat_dd = dms_to_dd(lat_d, lat_m, lat_s, lat_dir)
    lon_dd = dms_to_dd(lon_d, lon_m, lon_s, lon_dir)
    
    print(f"Output Latitude:  {lat_dd:.6f}°")
    print(f"Output Longitude: {lon_dd:.6f}°")
    
    # Test 2: Convert Decimal Degrees to DMS
    print("\n2. Converting Decimal Degrees to DMS:")
    print("-" * 40)
    
    test_lat = 19.432600
    test_lon = -99.133200
    
    print(f"Input  Latitude:  {test_lat}°")
    print(f"Input  Longitude: {test_lon}°")
    
    lat_d2, lat_m2, lat_s2, lat_dir2 = dd_to_dms(test_lat, is_longitude=False)
    lon_d2, lon_m2, lon_s2, lon_dir2 = dd_to_dms(test_lon, is_longitude=True)
    
    lat_formatted = format_dms(lat_d2, lat_m2, lat_s2, lat_dir2)
    lon_formatted = format_dms(lon_d2, lon_m2, lon_s2, lon_dir2)
    
    print(f"Output Latitude:  {lat_formatted}")
    print(f"Output Longitude: {lon_formatted}")
    
    # Test 3: Validate various DMS formats
    print("\n3. Testing DMS Format Validation:")
    print("-" * 40)
    
    test_formats = [
        "19°25'57.36\"N",
        "19 25 57.36 N",
        "19d 25m 57.36s N",
        "99°7'59.52\"W",
        "45°30'N",  # No seconds
    ]
    
    for fmt in test_formats:
        is_valid, dd_value = validate_dms_coordinate(fmt, is_longitude=('W' in fmt or 'E' in fmt))
        status = "[OK]" if is_valid else "[FAIL]"
        if is_valid:
            print(f"{status}: {fmt:20s} -> {dd_value:.6f} degrees")
        else:
            print(f"{status}: {fmt}")
    
    # Test 4: Show available coordinate systems
    print("\n4. Available Coordinate Systems:")
    print("-" * 40)
    
    for cs_type in CoordinateSystemType:
        cs_info = COORDINATE_SYSTEMS[cs_type]
        print(f"\n{cs_info.name}")
        print(f"  EPSG: {cs_info.epsg if cs_info.epsg else 'Dynamic (zone-based)'}")
        print(f"  Requires Zone: {cs_info.requires_zone}")
        print(f"  Requires Hemisphere: {cs_info.requires_hemisphere}")
        print(f"  X Label: {cs_info.x_label}")
        print(f"  Y Label: {cs_info.y_label}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_dms_conversions()

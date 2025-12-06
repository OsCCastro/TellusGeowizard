"""
Test script to verify measurement calculations work correctly with closed polygons.
This tests the fix for duplicate closing points.
"""

from utils.measurements import (
    calculate_distance_utm,
    calculate_area_utm,
    calculate_perimeter_utm,
)

def test_closed_polygon_fix():
    """Test that closed polygons (with duplicate first/last point) calculate correctly."""
    print("=" * 70)
    print("Testing Closed Polygon Fix")
    print("=" * 70)
    
    # Test 1: Square WITHOUT duplicate closing point
    print("\nTest 1: Square WITHOUT duplicate closing point (100m x 100m)")
    print("-" * 70)
    square_open = [
        (500000, 2000000),  # Bottom-left
        (500100, 2000000),  # Bottom-right
        (500100, 2000100),  # Top-right
        (500000, 2000100),  # Top-left
        # NO duplicate of first point
    ]
    
    area_open = calculate_area_utm(square_open)
    perim_open = calculate_perimeter_utm(square_open)
    
    print(f"Coordinates: {len(square_open)} points (open polygon)")
    print(f"Calculated area: {area_open:,.2f} m²")
    print(f"Calculated perimeter: {perim_open:,.2f} m")
    print(f"Expected: 10,000 m² area, 400 m perimeter")
    
    # Test 2: Same square WITH duplicate closing point
    print("\nTest 2: Same square WITH duplicate closing point")
    print("-" * 70)
    square_closed = [
        (500000, 2000000),  # Bottom-left
        (500100, 2000000),  # Bottom-right
        (500100, 2000100),  # Top-right
        (500000, 2000100),  # Top-left
        (500000, 2000000),  # DUPLICATE of first point (closing)
    ]
    
    area_closed = calculate_area_utm(square_closed)
    perim_closed = calculate_perimeter_utm(square_closed)
    
    print(f"Coordinates: {len(square_closed)} points (closed polygon)")
    print(f"Calculated area: {area_closed:,.2f} m²")
    print(f"Calculated perimeter: {perim_closed:,.2f} m")
    print(f"Expected: 10,000 m² area, 400 m perimeter (SAME AS OPEN)")
    
    # Test 3: Verify they match
    print("\n" + "=" * 70)
    print("Verification:")
    print("=" * 70)
    
    area_match = abs(area_open - area_closed) < 0.01
    perim_match = abs(perim_open - perim_closed) < 0.01
    
    print(f"Area matches: {area_match} {'[OK]' if area_match else '[FAIL]'}")
    print(f"  Open:   {area_open:,.2f} m²")
    print(f"  Closed: {area_closed:,.2f} m²")
    print(f"\nPerimeter matches: {perim_match} {'[OK]' if perim_match else '[FAIL]'}")
    print(f"  Open:   {perim_open:,.2f} m")
    print(f"  Closed: {perim_closed:,.2f} m")
    
    if area_match and perim_match:
        print("\n*** SUCCESS! Open and closed polygons now calculate identically!")
    else:
        print("\n*** FAIL! There's still a difference between open and closed polygons.")

    
    # Test 4: User's actual coordinates (Web Mercator)
    print("\n" + "=" * 70)
    print("Test 4: User's actual polygon from screenshot")
    print("=" * 70)
    
    user_coords_closed = [
        (9510915.49, 7192020.34),
        (9511397.85, 7192284.40),
        (9511536.87, 7192119.00),
        (9511133.88, 7191775.31),
        (9510915.49, 7192020.34),  # Duplicate closing point
    ]
    
    # Note: These are Web Mercator, not UTM, so the calculation won't match
    # Google Earth exactly, but we're testing that the duplicate doesn't cause issues
    area_user = calculate_area_utm(user_coords_closed)
    perim_user = calculate_perimeter_utm(user_coords_closed)
    
    print(f"Number of points: {len(user_coords_closed)} (with closing duplicate)")
    print(f"Calculated area: {area_user:,.2f} m²")
    print(f"Calculated perimeter: {perim_user:,.2f} m")
    print(f"\nNote: These are Web Mercator coords, not UTM.")
    print(f"Google Earth shows: ~12,432 m² area, ~598 m perimeter")
    print(f"The values won't match exactly because coords need to be converted to UTM first.")
    
    print("\n" + "=" * 70)
    print("Tests Completed!")
    print("=" * 70)

if __name__ == "__main__":
    test_closed_polygon_fix()

"""
Quick diagnostic script to verify the measurement fix is working.
Run this BEFORE starting the GUI to confirm the fix is loaded.
"""

import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)

# Force import fresh modules
if 'utils.measurements' in sys.modules:
    del sys.modules['utils.measurements']

from utils.measurements import calculate_area_utm, calculate_perimeter_utm

# Test with YOUR actual scenario: polygon with duplicate closing point
coords_with_duplicate = [
    (500000, 2000000),  # Point 1  
    (500100, 2000000),  # Point 2
    (500100, 2000100),  # Point 3
    (500000, 2000100),  # Point 4
    (500000, 2000000),  # Point 5 (DUPLICATE of Point 1)
]

area = calculate_area_utm(coords_with_duplicate)
perimeter = calculate_perimeter_utm(coords_with_duplicate)

print("\n" + "="*70)
print("DIAGNOSTIC TEST - 100m x 100m Square with Duplicate Closing Point")
print("="*70)
print(f"Input: {len(coords_with_duplicate)} points (last = first)")
print(f"Calculated Area: {area:,.2f} m²")
print(f"Calculated Perimeter: {perimeter:,.2f} m")
print(f"\nExpected: 10,000 m² area, 400 m perimeter")
print("="*70)

if abs(area - 10000) < 1 and abs(perimeter - 400) < 1:
    print("✓ FIX IS WORKING! The measurements are correct.")
    print("✓ Safe to start the GUI - the fix is loaded.")
else:
    print("✗ FIX NOT WORKING! Still getting wrong values:")
    print(f"  Area error: {area - 10000:,.2f} m²")
    print(f"  Perimeter error: {perimeter - 400:,.2f} m")
    print("\n✗ DO NOT start the GUI yet. Debug needed.")
    
print("="*70)

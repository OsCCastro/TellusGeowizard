# tests/test_coordinate_systems.py
"""
Unit tests for coordinate_systems module.
Tests UTM zone detection, DMS conversion, and coordinate validation.
"""

import unittest
import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.coordinate_systems import (
    detect_utm_zone,
    detect_hemisphere,
    detect_utm_from_coords,
    dd_to_dms,
    dms_to_dd,
    validate_dms_coordinate,
    get_utm_epsg
)


class TestDetectUTMZone(unittest.TestCase):
    """Tests for detect_utm_zone function."""
    
    def test_mexico_city(self):
        """Mexico City (-99.13) should be in zone 14."""
        self.assertEqual(detect_utm_zone(-99.13), 14)
    
    def test_madrid(self):
        """Madrid (-3.7) should be in zone 30."""
        self.assertEqual(detect_utm_zone(-3.7), 30)
    
    def test_london(self):
        """London (0.0) should be in zone 31."""
        self.assertEqual(detect_utm_zone(0.0), 31)
    
    def test_tokyo(self):
        """Tokyo (139.7) should be in zone 54."""
        self.assertEqual(detect_utm_zone(139.7), 54)
    
    def test_new_york(self):
        """New York (-74.0) should be in zone 18."""
        self.assertEqual(detect_utm_zone(-74.0), 18)
    
    def test_sydney(self):
        """Sydney (151.2) should be in zone 56."""
        self.assertEqual(detect_utm_zone(151.2), 56)
    
    def test_boundary_west(self):
        """Test western boundary (-180)."""
        self.assertEqual(detect_utm_zone(-180), 1)
    
    def test_boundary_east(self):
        """Test eastern boundary (180) - wraps to zone 1."""
        result = detect_utm_zone(180)
        self.assertIn(result, [1, 60])  # Either boundary is acceptable
    
    def test_normalized_longitude(self):
        """Test longitude normalization for values > 180."""
        # 190 degrees should normalize to -170, which is zone 1
        self.assertEqual(detect_utm_zone(190), 2)


class TestDetectHemisphere(unittest.TestCase):
    """Tests for detect_hemisphere function."""
    
    def test_north(self):
        """Positive latitude should return 'Norte'."""
        self.assertEqual(detect_hemisphere(19.43), "Norte")
    
    def test_south(self):
        """Negative latitude should return 'Sur'."""
        self.assertEqual(detect_hemisphere(-33.87), "Sur")
    
    def test_equator(self):
        """Equator (0.0) should return 'Norte'."""
        self.assertEqual(detect_hemisphere(0.0), "Norte")


class TestDetectUTMFromCoords(unittest.TestCase):
    """Tests for detect_utm_from_coords function."""
    
    def test_cdmx(self):
        """CDMX should be zone 14 Norte."""
        zone, hemisphere = detect_utm_from_coords(-99.13, 19.43)
        self.assertEqual(zone, 14)
        self.assertEqual(hemisphere, "Norte")
    
    def test_buenos_aires(self):
        """Buenos Aires should be zone 21 Sur."""
        zone, hemisphere = detect_utm_from_coords(-58.38, -34.60)
        self.assertEqual(zone, 21)
        self.assertEqual(hemisphere, "Sur")
    
    def test_santiago(self):
        """Santiago should be zone 19 Sur."""
        zone, hemisphere = detect_utm_from_coords(-70.65, -33.45)
        self.assertEqual(zone, 19)
        self.assertEqual(hemisphere, "Sur")


class TestDMSConversion(unittest.TestCase):
    """Tests for DMS conversion functions."""
    
    def test_dd_to_dms_positive_lat(self):
        """Convert positive latitude to DMS."""
        d, m, s, direction = dd_to_dms(19.4326, is_longitude=False)
        self.assertEqual(d, 19)
        self.assertEqual(m, 25)
        self.assertAlmostEqual(s, 57.36, places=1)
        self.assertEqual(direction, 'N')
    
    def test_dd_to_dms_negative_lat(self):
        """Convert negative latitude to DMS."""
        d, m, s, direction = dd_to_dms(-33.4489, is_longitude=False)
        self.assertEqual(d, 33)
        self.assertEqual(m, 26)
        self.assertAlmostEqual(s, 56.04, places=1)
        self.assertEqual(direction, 'S')
    
    def test_dd_to_dms_positive_lon(self):
        """Convert positive longitude to DMS."""
        d, m, s, direction = dd_to_dms(139.6917, is_longitude=True)
        self.assertEqual(d, 139)
        self.assertEqual(m, 41)
        self.assertEqual(direction, 'E')
    
    def test_dd_to_dms_negative_lon(self):
        """Convert negative longitude to DMS."""
        d, m, s, direction = dd_to_dms(-99.1332, is_longitude=True)
        self.assertEqual(d, 99)
        self.assertEqual(m, 7)
        self.assertEqual(direction, 'W')
    
    def test_dms_to_dd_north(self):
        """Convert DMS North to DD."""
        dd = dms_to_dd(19, 25, 57.36, 'N')
        self.assertAlmostEqual(dd, 19.4326, places=4)
    
    def test_dms_to_dd_south(self):
        """Convert DMS South to DD."""
        dd = dms_to_dd(33, 26, 56.04, 'S')
        self.assertAlmostEqual(dd, -33.4489, places=4)
    
    def test_dms_to_dd_west(self):
        """Convert DMS West to DD."""
        dd = dms_to_dd(99, 7, 59.52, 'W')
        self.assertAlmostEqual(dd, -99.1332, places=4)


class TestValidateDMSCoordinate(unittest.TestCase):
    """Tests for validate_dms_coordinate function."""
    
    def test_valid_latitude(self):
        """Test valid DMS latitude string."""
        is_valid, dd = validate_dms_coordinate("19°25'57.36\"N", is_longitude=False)
        self.assertTrue(is_valid)
        self.assertAlmostEqual(dd, 19.4326, places=4)
    
    def test_valid_longitude(self):
        """Test valid DMS longitude string."""
        is_valid, dd = validate_dms_coordinate("99°07'59.52\"W", is_longitude=True)
        self.assertTrue(is_valid)
        self.assertAlmostEqual(dd, -99.1332, places=4)
    
    def test_invalid_format(self):
        """Test invalid DMS format."""
        is_valid, dd = validate_dms_coordinate("not a coordinate", is_longitude=False)
        self.assertFalse(is_valid)


class TestGetUTMEPSG(unittest.TestCase):
    """Tests for get_utm_epsg function."""
    
    def test_zone_14_north(self):
        """Zone 14 North should be EPSG:32614."""
        self.assertEqual(get_utm_epsg(14, "Norte"), 32614)
    
    def test_zone_14_south(self):
        """Zone 14 South should be EPSG:32714."""
        self.assertEqual(get_utm_epsg(14, "Sur"), 32714)
    
    def test_zone_1_north(self):
        """Zone 1 North should be EPSG:32601."""
        self.assertEqual(get_utm_epsg(1, "Norte"), 32601)
    
    def test_zone_60_south(self):
        """Zone 60 South should be EPSG:32760."""
        self.assertEqual(get_utm_epsg(60, "Sur"), 32760)


if __name__ == '__main__':
    unittest.main()

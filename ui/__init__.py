# ui/__init__.py
"""
UI components for GeoWizard application.
"""

from .coordinate_table import CoordTable, UTMDelegate
from .map_canvas import CanvasView

__all__ = [
    'CoordTable',
    'UTMDelegate',
    'CanvasView'
]

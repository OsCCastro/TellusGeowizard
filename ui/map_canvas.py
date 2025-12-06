# ui/map_canvas.py
"""
Custom graphics view for map canvas with zoom capabilities.
"""

from PySide6.QtWidgets import QGraphicsView
from constants import CANVAS_ZOOM_FACTOR

from utils.logger import get_logger

logger = get_logger(__name__)


class CanvasView(QGraphicsView):
    """
    Custom graphics view with mouse wheel zoom functionality.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zoom_factor = CANVAS_ZOOM_FACTOR
    
    def wheelEvent(self, event):
        """
        Handle mouse wheel events for zooming.
        Scroll up: zoom in
        Scroll down: zoom out
        """
        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale(self._zoom_factor, self._zoom_factor)
        else:
            # Zoom out
            self.scale(1 / self._zoom_factor, 1 / self._zoom_factor)
        
        event.accept()
    
    def zoom_in(self):
        """Programmatically zoom in."""
        self.scale(self._zoom_factor, self._zoom_factor)
    
    def zoom_out(self):
        """Programmatically zoom out."""
        self.scale(1 / self._zoom_factor, 1 / self._zoom_factor)
    
    def reset_zoom(self):
        """Reset zoom to default (1:1)."""
        self.resetTransform()

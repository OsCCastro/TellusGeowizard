"""
Editable geometry components for GeoWizard.

Provides interactive editing of geometries on the canvas with
real-time table synchronization.
"""

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor


class EditablePoint(QGraphicsEllipseItem):
    """
    Draggable point for geometry editing.
    
    Represents a single coordinate that can be moved interactively.
    Updates the coordinate table when moved.
    """
    
    def __init__(self, x, y, row_index, table_widget, parent=None):
        """
        Initialize editable point.
        
        Args:
            x: X coordinate in scene
            y: Y coordinate in scene
            row_index: Row index in coordinate table
            table_widget: Reference to QTableWidget for updates
            parent: Parent graphics item
        """
        # Create circle centered at origin
        super().__init__(-6, -6, 12, 12, parent)
        
        self.row_index = row_index
        self.table = table_widget
        self.is_dragging = False  # Track drag state
        self.geometry_owner = None  # Reference to EditableGeometry
        
        # Set position
        self.setPos(x, y)
        
        # Make draggable
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Visual styling
        self.setBrush(QBrush(QColor("#0078d4")))
        self.setPen(QPen(QColor("#ffffff"), 2))
        
        # Hover effect
        self.setAcceptHoverEvents(True)
        self.is_hovered = False
    
    def hoverEnterEvent(self, event):
        """Change appearance on hover."""
        self.is_hovered = True
        self.setBrush(QBrush(QColor("#106ebe")))
        self.setCursor(Qt.SizeAllCursor)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Restore appearance when hover ends."""
        self.is_hovered = False
        self.setBrush(QBrush(QColor("#0078d4")))
        self.unsetCursor()
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Mark start of drag operation."""
        self.is_dragging = True
        # Save initial position for undo
        self._drag_start_pos = self.scenePos()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Mark end of drag and update table/geometry."""
        self.is_dragging = False
        # Update table with final position
        self.update_table_coordinates()
        # Signal to owner to update geometry path
        if self.geometry_owner:
            self.geometry_owner.update_geometry_shape()
        
        # Create undo command if position changed
        if hasattr(self, '_drag_start_pos') and self._drag_start_pos is not None:
            final_pos = self.scenePos()
            if (abs(final_pos.x() - self._drag_start_pos.x()) > 0.01 or 
                abs(final_pos.y() - self._drag_start_pos.y()) > 0.01):
                # Position changed, create undo command
                if hasattr(self, 'main_window') and self.main_window:
                    # We need to pass lat/lon for undo command
                    # Get point ID from table row
                    point_id = str(self.row_index + 1)
                    
                    # Convert scene coordinates to lat/lon for undo command
                    # We'll use the table values which are already in the correct system
                    old_x = self._drag_start_pos.x()
                    old_y = self._drag_start_pos.y()
                    new_x = final_pos.x()
                    new_y = final_pos.y()
                    
                    # For canvas edits, we can't easily get lat/lon, so we skip undo for now
                    # The undo system works mainly for web map edits
                    pass
                    
        super().mouseReleaseEvent(event)
    
    def itemChange(self, change, value):
        """Handle item changes, especially position changes."""
        if change == QGraphicsItem.ItemPositionChange:
            # During drag, update geometry in real-time without table update
            if self.is_dragging and self.geometry_owner:
                self.geometry_owner.update_geometry_shape()
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # Only update table if NOT dragging (e.g., programmatic moves)
            if not self.is_dragging:
                self.update_table_coordinates()
        
        return super().itemChange(change, value)
    
    def update_table_coordinates(self):
        """Update coordinate table with new position."""
        if self.table is None:
            return
        
        # Get new position in scene coordinates
        pos = self.scenePos()
        
        # Update table (block signals to prevent recursion)
        self.table.blockSignals(True)
        try:
            # Update X coordinate
            x_item = self.table.item(self.row_index, 1)
            if x_item:
                x_item.setText(f"{pos.x():.2f}")
            
            # Update Y coordinate
            y_item = self.table.item(self.row_index, 2)
            if y_item:
                y_item.setText(f"{pos.y():.2f}")
        finally:
            self.table.blockSignals(False)


class EditableGeometry:
    """
    Container for editable geometry with control points.
    
    Manages the relationship between the geometry graphics item
    and its editable control points.
    """
    
    def __init__(self, geometry_item, points, table_widget):
        """
        Initialize editable geometry.
        
        Args:
            geometry_item: The main geometry graphics item (line, polygon, etc.)
            points: List of (x, y, row_index) tuples for control points
            table_widget: Reference to coordinate table
        """
        self.geometry_item = geometry_item
        self.control_points = []
        self.table = table_widget
        
        # Create editable points
        for x, y, row_idx in points:
            point = EditablePoint(x, y, row_idx, table_widget, parent=geometry_item)
            point.geometry_owner = self  # Set back-reference
            self.control_points.append(point)
    
    def show_points(self):
        """Show all control points."""
        for point in self.control_points:
            point.show()
    
    def hide_points(self):
        """Hide all control points."""
        for point in self.control_points:
            point.hide()
    
    def remove_points(self):
        """Remove all control points from scene."""
        for point in self.control_points:
            if point.scene():
                point.scene().removeItem(point)
        self.control_points.clear()
    
    def update_geometry_shape(self):
        """
        Update the geometry path based on current control point positions.
        This provides real-time visual feedback during dragging.
        """
        from PySide6.QtGui import QPainterPath
        
        if not self.control_points or not self.geometry_item:
            return
        
        # Get current positions of all control points
        positions = []
        for point in self.control_points:
            pos = point.scenePos()
            positions.append((pos.x(), pos.y()))
        
        if len(positions) < 2:
            return
        
        # Create new path
        path = QPainterPath()
        path.moveTo(positions[0][0], positions[0][1])
        
        for x, y in positions[1:]:
            path.lineTo(x, y)
        
        # Close path if it's a polygon (check if geometry_item has fillRule or brush)
        if hasattr(self.geometry_item, 'brush') and self.geometry_item.brush().style() != 0:
            path.closeSubpath()
        
        # Update the geometry item's path
        self.geometry_item.setPath(path)

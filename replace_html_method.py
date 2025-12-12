# Script to replace old _on_export_html method and add new methods to main_window.py
import re

# Read the file
with open(r'a:\Windows\Usuarios\ContrerasO\Escritorio\GeoWizard\ui\main_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and read lines between line 2315 and 2382 (the old method)
lines = content.split('\n')

# Remove old method (lines 2315-2382, but in 0-indexed that's 2314-2381)
new_lines = lines[:2314] + lines[2382:]

# The new methods to insert
new_methods = '''    def _on_export_html(self):
        """Export coordinates as HTML table with preview dialog."""
        try:
            # Validate that we have coordinates
            has_coords = False
            for r in range(self.table.rowCount()):
                xi = self.table.item(r, 1)
                yi = self.table.item(r, 2)
                if xi and yi and xi.text().strip() and yi.text().strip():
                    has_coords = True
                    break
            
            if not has_coords:
                QMessageBox.warning(
                    self,
                    "Sin coordenadas",
                    "No hay coordenadas para exportar. Por favor, ingrese al menos un punto."
                )
                return
            
            # Open preview dialog
            preview_dialog = HTMLPreviewDialog(self, self)
            preview_dialog.exec()
            
        except Exception as e:
            logger.error(f"Error al exportar HTML: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error al exportar HTML",
                f"No se pudo generar la tabla HTML:\\n{str(e)}"
            )
    
    def _generate_coordinates_html_table(self, settings=None):
        """
        Generate HTML table of coordinates with bearings.
        
        Args:
            settings: HTMLTableSettings instance. If None, loads defaults.
            
        Returns:
            str: Complete HTML table string
        """
        if settings is None:
            settings = HTMLTableSettings.load()
        
        # Get current coordinate system
        coord_system = self.cb_coord_system.currentText()
        
        # Extract coordinates from table
        coords_data = []
        for r in range(self.table.rowCount()):
            id_item = self.table.item(r, 0)
            x_item = self.table.item(r, 1)
            y_item = self.table.item(r, 2)
            
            if not (x_item and y_item):
                continue
            
            x_text = x_item.text().strip()
            y_text = y_item.text().strip()
            
            if not (x_text and y_text):
                continue
            
            try:
                id_val = id_item.text() if id_item else str(r + 1)
                x = float(x_text.replace(',', '.'))
                y = float(y_text.replace(',', '.'))
                coords_data.append((id_val, x, y))
            except ValueError:
                continue
        
        if not coords_data:
            raise ValueError("No hay coordenadas válidas para exportar")
        
        # Convert all coordinates to WGS84 for bearing calculation
        wgs84_coords = []
        for id_val, x, y in coords_data:
            lon, lat = self._coord_to_wgs84(x, y, coord_system)
            wgs84_coords.append((lon, lat))
        
        # Calculate bearings
        bearings = []
        for i in range(len(wgs84_coords)):
            if i < len(wgs84_coords) - 1:
                # Normal case: bearing to next point
                bearing = self._calculate_bearing(
                    wgs84_coords[i],
                    wgs84_coords[i + 1],
                    settings.bearing_format
                )
                bearings.append(bearing)
            else:
                # Last point
                if self.chk_poligono.isChecked() and len(wgs84_coords) >= 3:
                    # For polygons, bearing from last to first
                    bearing = self._calculate_bearing(
                        wgs84_coords[i],
                        wgs84_coords[0],
                        settings.bearing_format
                    )
                    bearings.append(bearing)
                else:
                    # For lines/points, no bearing for last point
                    bearings.append(None)
        
        # Build HTML table
        html = self._build_html_table_from_data(
            coords_data,
            bearings,
            settings,
            coord_system
        )
        
        return html
    
    def _coord_to_wgs84(self, x, y, coord_system):
        """
        Convert coordinates to WGS84 (lon, lat).
        
        Args:
            x: X coordinate
            y: Y coordinate
            coord_system: Current coordinate system name
            
        Returns:
            tuple: (longitude, latitude) in WGS84
        """
        if coord_system == "UTM":
            # Get zone and hemisphere
            hemisphere = self.cb_hemisferio.currentText()
            zone = int(self.cb_zona.currentText())
            epsg_code = get_utm_epsg(zone, hemisphere)
            transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(x, y)
            return lon, lat
        
        elif coord_system == "Geographic (Decimal Degrees)":
            # Already in lon, lat
            return x, y
        
        elif coord_system == "Geographic (DMS)":
            # DMS is stored as decimal degrees in the table after validation
            return x, y
        
        elif coord_system == "Web Mercator":
            # Convert from Web Mercator (EPSG:3857) to WGS84 (EPSG:4326)
            transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(x, y)
            return lon, lat
        
        else:
            # Default: assume already in lon, lat
            return x, y
    
    def _calculate_bearing(self, coord1_wgs84, coord2_wgs84, format_type):
        """
        Calculate bearing between two WGS84 coordinates.
        
        Args:
            coord1_wgs84: Tuple (lon, lat) in degrees
            coord2_wgs84: Tuple (lon, lat) in degrees
            format_type: "azimuth" or "quadrant"
            
        Returns:
            str: Formatted bearing string
        """
        geod = Geod(ellps='WGS84')
        lon1, lat1 = coord1_wgs84
        lon2, lat2 = coord2_wgs84
        
        try:
            az_forward, az_back, distance = geod.inv(lon1, lat1, lon2, lat2)
            
            if format_type == "azimuth":
                # Normalize to 0-360°
                azimuth = az_forward if az_forward >= 0 else az_forward + 360
                return f"{azimuth:.1f}"
            else:  # quadrant
                return self._azimuth_to_quadrant(az_forward)
        except Exception as e:
            logger.warning(f"Error calculating bearing: {e}")
            return "N/A"
    
    def _azimuth_to_quadrant(self, azimuth):
        """
        Convert azimuth to quadrant format (e.g., "N 45° E").
        
        Args:
            azimuth: Azimuth in degrees (-180 to 180 or 0 to 360)
            
        Returns:
            str: Quadrant format string
        """
        # Normalize to 0-360
        if azimuth < 0:
            azimuth += 360
        
        if azimuth <= 90:
            # NE quadrant
            return f"N {azimuth:.1f}° E"
        elif azimuth <= 180:
            # SE quadrant
            angle = 180 - azimuth
            return f"S {angle:.1f}° E"
        elif azimuth <= 270:
            # SW quadrant
            angle = azimuth - 180
            return f"S {angle:.1f}° W"
        else:
            # NW quadrant
            angle = 360 - azimuth
            return f"N {angle:.1f}° W"
    
    def _build_html_table_from_data(self, coords_data, bearings, settings, coord_system):
        """
        Build HTML table with styling from settings.
        
        Args:
            coords_data: List of (id, x, y) tuples
            bearings: List of bearing strings (or None)
            settings: HTMLTableSettings instance
            coord_system: Current coordinate system name
            
        Returns:
            str: Complete HTML string
        """
        # Determine border style
        if settings.show_all_borders:
            border_style = f"border: {settings.border_width}px solid #ddd;"
        elif settings.show_horizontal:
            border_style = f"border-top: {settings.border_width}px solid #ddd; border-bottom: {settings.border_width}px solid #ddd;"
        elif settings.show_vertical:
            border_style = f"border-left: {settings.border_width}px solid #ddd; border-right: {settings.border_width}px solid #ddd;"
        elif settings.show_outer:
            border_style = f"border: {settings.border_width}px solid #ddd;"
        else:
            border_style = "border: none;"
        
        # Determine coordinate units
        if coord_system == "UTM":
            x_label = "X (m)"
            y_label = "Y (m)"
        elif coord_system == "Web Mercator":
            x_label = "X (m)"
            y_label = "Y (m)"
        elif "Geographic" in coord_system:
            x_label = "Longitud (°)"
            y_label = "Latitud (°)"
        else:
            x_label = "X"
            y_label = "Y"
        
        # Build HTML
        html = f"""
<table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">
    <thead>
        <tr style="background-color: {settings.header_bg_color}; color: {settings.header_text_color};">
            <th style="padding: 8px; {border_style}">ID</th>
            <th style="padding: 8px; {border_style}">Rumbo (°)</th>
            <th style="padding: 8px; {border_style}">{x_label}</th>
            <th style="padding: 8px; {border_style}">{y_label}</th>
        </tr>
    </thead>
    <tbody>
"""
        
        # Add data rows
        for i, ((id_val, x, y), bearing) in enumerate(zip(coords_data, bearings)):
            row_bg = settings.row_bg_color1 if i % 2 == 0 else settings.row_bg_color2
            bearing_str = bearing if bearing is not None else "N/A"
            x_str = f"{x:.{settings.coord_decimals}f}"
            y_str = f"{y:.{settings.coord_decimals}f}"
            
            html += f"""        <tr style="background-color: {row_bg}; color: {settings.cell_text_color};">
            <td style="padding: 6px; {border_style} text-align: center;">{id_val}</td>
            <td style="padding: 6px; {border_style} text-align: right;">{bearing_str}</td>
            <td style="padding: 6px; {border_style} text-align: right;">{x_str}</td>
            <td style="padding: 6px; {border_style} text-align: right;">{y_str}</td>
        </tr>
"""
        
        html += """    </tbody>
</table>
<p style="text-align: center; margin-top: 10px; font-size: 0.9em; color: #666; font-style: italic;">
    Tabla generada por GeoWizard - Tellus Consultoría
</p>
"""
        
        return html
'''

# Insert new methods at line 2314 (0-indexed)
new_lines.insert(2314, new_methods)

# Write back
with open(r'a:\Windows\Usuarios\ContrerasO\Escritorio\GeoWizard\ui\main_window.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("Successfully replaced _on_export_html and added new methods!")

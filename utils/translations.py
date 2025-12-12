# utils/translations.py
"""
Internationalization (i18n) system for GeoWizard.
Provides translations for Spanish and English.
"""

TRANSLATIONS = {
    "es": {
        # Main Window
        "app_title": "Tellus Consultoría - GeoWizard V.1.0 (Beta Tester)",
        
        # Menu & Toolbar
        "new": "Nuevo",
        "open": "Abrir",
        "save": "Guardar",
        "import": "Importar",
        "export": "Exportar",
        "settings": "Configuración",
        "help": "Ayuda",
        
        # Coordinate Systems
        "coord_system": "Sistema de Coordenadas:",
        "hemisphere": "Hemisferio:",
        "utm_zone": "Zona UTM:",
        "north": "Norte",
        "south": "Sur",
        
        # Table Headers
        "id": "ID",
        "x_east": "X (Este)",
        "y_north": "Y (Norte)",
        "longitude": "Longitud",
        "latitude": "Latitud",
        
        # Measurement Config
        "measurement_config": "📏 Configuración Mediciones",
        "units": "Unidades:",
        "metric": "Métricas",
        "imperial": "Imperiales",
        
        # Geometry
        "geometry": "Geometría:",
        "point": "Punto",
        "polyline": "Polilínea",
        "polygon": "Polígono",
        
        # Map
        "use_basemap": "Usar mapa base (OSM)",
        
        # Project
        "project": "Proyecto:",
        "format": "Formato:",
        "select_folder": "Seleccionar carpeta",
        
        # Measurements
        "measurements": "Mediciones",
        "distance": "Distancia:",
        "area": "Área:",
        "perimeter": "Perímetro:",
        
        # Messages
        "no_coordinates": "Sin coordenadas",
        "no_coordinates_msg": "No hay coordenadas para exportar. Por favor, ingrese al menos un punto.",
        "export_success": "Éxito",
        "export_success_msg": "Archivo guardado en:",
        "export_error": "Error al exportar",
        "import_success": "Importación Exitosa",
        "import_error": "Error de Importación",
        
        # Dialog buttons
        "ok": "Aceptar",
        "cancel": "Cancelar",
        "close": "Cerrar",
        "yes": "Sí",
        "no": "No",
        "save_btn": "Guardar",
        
        # Close message
        "thanks_title": "Gracias por usar GeoWizard",
        "thanks_msg": """<h3>¡Gracias por utilizar GeoWizard V.1.0 (Beta Tester)!</h3>
<p>Tu participación en esta versión beta es muy valiosa para nosotros.</p>
<p><b>Por favor, comparte tu opinión y sugerencias sobre el programa.</b></p>
<hr>
<p><b>Contacto:</b><br>
📧 <a href='mailto:contacto@tellusconsultoria.com'>contacto@tellusconsultoria.com</a></p>
<p><b>Síguenos en redes sociales para recibir actualizaciones:</b><br>
📸 <a href='https://www.facebook.com/TellusConsultoria'>Facebook - Tellus Consultoría</a></p>
<hr>
<p style='color: #666;'><i>Tellus Consultoría - Soluciones Geoespaciales</i></p>""",
        
        # Config Dialog
        "config_title": "Configuración",
        "appearance": "Apariencia",
        "dark_mode": "Modo oscuro",
        "general": "General",
        "language": "Idioma:",
        "spanish": "Español",
        "english": "English",
        "autosave": "Guardar automáticamente",
        
        # Help Dialog
        "help_title": "Ayuda - GeoWizard",
        "help_subtitle": "GeoWizard V.1.0 (Beta Tester)",
        "help_description": "Herramienta profesional para gestión y visualización de datos geoespaciales",
        "developed_by": "Desarrollado por:",
        "tellus_name": "Tellus Consultoría - Soluciones Geoespaciales",
        "main_features": "Características principales:",
        "contact_support": "Contacto y Soporte:",
        "about_version": "Acerca de esta versión:",
        "beta_message": "Esta es una versión beta para pruebas. Tu feedback es muy valioso para mejorar la aplicación. Por favor, reporta cualquier problema o sugerencia.",
        "copyright": "© 2024 Tellus Consultoría. Todos los derechos reservados.",
    },
    
    "en": {
        # Main Window
        "app_title": "Tellus Consulting - GeoWizard V.1.0 (Beta Tester)",
        
        # Menu & Toolbar
        "new": "New",
        "open": "Open",
        "save": "Save",
        "import": "Import",
        "export": "Export",
        "settings": "Settings",
        "help": "Help",
        
        # Coordinate Systems
        "coord_system": "Coordinate System:",
        "hemisphere": "Hemisphere:",
        "utm_zone": "UTM Zone:",
        "north": "North",
        "south": "South",
        
        # Table Headers
        "id": "ID",
        "x_east": "X (East)",
        "y_north": "Y (North)",
        "longitude": "Longitude",
        "latitude": "Latitude",
        
        # Measurement Config
        "measurement_config": "📏 Measurement Settings",
        "units": "Units:",
        "metric": "Metric",
        "imperial": "Imperial",
        
        # Geometry
        "geometry": "Geometry:",
        "point": "Point",
        "polyline": "Polyline",
        "polygon": "Polygon",
        
        # Map
        "use_basemap": "Use basemap (OSM)",
        
        # Project
        "project": "Project:",
        "format": "Format:",
        "select_folder": "Select folder",
        
        # Measurements
        "measurements": "Measurements",
        "distance": "Distance:",
        "area": "Area:",
        "perimeter": "Perimeter:",
        
        # Messages
        "no_coordinates": "No coordinates",
        "no_coordinates_msg": "No coordinates to export. Please enter at least one point.",
        "export_success": "Success",
        "export_success_msg": "File saved at:",
        "export_error": "Export Error",
        "import_success": "Import Successful",
        "import_error": "Import Error",
        
        # Dialog buttons
        "ok": "OK",
        "cancel": "Cancel",
        "close": "Close", 
        "yes": "Yes",
        "no": "No",
        "save_btn": "Save",
        
        # Close message
        "thanks_title": "Thanks for using GeoWizard",
        "thanks_msg": """<h3>Thank you for using GeoWizard V.1.0 (Beta Tester)!</h3>
<p>Your participation in this beta version is very valuable to us.</p>
<p><b>Please share your opinions and suggestions about the program.</b></p>
<hr>
<p><b>Contact:</b><br>
📧 <a href='mailto:contacto@tellusconsultoria.com'>contacto@tellusconsultoria.com</a></p>
<p><b>Follow us on social media for updates:</b><br>
📸 <a href='https://www.facebook.com/TellusConsultoria'>Facebook - Tellus Consulting</a></p>
<hr>
<p style='color: #666;'><i>Tellus Consulting - Geospatial Solutions</i></p>""",
        
        # Config Dialog
        "config_title": "Settings",
        "appearance": "Appearance",
        "dark_mode": "Dark mode",
        "general": "General",
        "language": "Language:",
        "spanish": "Español",
        "english": "English",
        "autosave": "Auto-save",
        
        # Help Dialog
        "help_title": "Help - GeoWizard",
        "help_subtitle": "GeoWizard V.1.0 (Beta Tester)",
        "help_description": "Professional tool for geospatial data management and visualization",
        "developed_by": "Developed by:",
        "tellus_name": "Tellus Consulting - Geospatial Solutions",
        "main_features": "Main Features:",
        "contact_support": "Contact & Support:",
        "about_version": "About this version:",
        "beta_message": "This is a beta version for testing. Your feedback is very valuable to improve the application. Please report any issues or suggestions.",
        "copyright": "© 2024 Tellus Consulting. All rights reserved.",
    }
}


class Translator:
    """Simple translation manager."""
    
    def __init__(self, language="es"):
        self.language = language
    
    def set_language(self, language):
        """Change the active language."""
        if language in TRANSLATIONS:
            self.language = language
        elif language == "Español":
            self.language = "es"
        elif language == "English":
            self.language = "en"
    
    def tr(self, key):
        """Translate a key."""
        return TRANSLATIONS.get(self.language, TRANSLATIONS["es"]).get(key, key)


# Global translator instance
_translator = Translator()

def tr(key):
    """Get translation for key."""
    return _translator.tr(key)

def set_language(language):
    """Set the global language."""
    _translator.set_language(language)

def get_current_language():
    """Get current language code."""
    return _translator.language

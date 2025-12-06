"""
Custom exception classes for GeoWizard application.

These exceptions provide better error categorization and enable
more specific error handling throughout the application.
"""


class GeoWizardError(Exception):
    """Base exception for all GeoWizard errors."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message}\nDetalles: {self.details}"
        return self.message


class CoordinateValidationError(GeoWizardError):
    """Raised when coordinate validation fails."""
    pass


class CoordinateConversionError(GeoWizardError):
    """Raised when coordinate system conversion fails."""
    pass


class GeometryBuildError(GeoWizardError):
    """Raised when geometry construction fails."""
    pass


class FileImportError(GeoWizardError):
    """Raised when file import fails."""
    pass


class FileExportError(GeoWizardError):
    """Raised when file export fails."""
    pass


class InsufficientDataError(GeoWizardError):
    """Raised when insufficient data for operation."""
    pass


class InvalidCoordinateSystemError(GeoWizardError):
    """Raised when an invalid coordinate system is specified."""
    pass


class ZoneHemisphereError(GeoWizardError):
    """Raised when UTM zone or hemisphere is invalid."""
    pass

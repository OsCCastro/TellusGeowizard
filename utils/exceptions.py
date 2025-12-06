# utils/exceptions.py
"""
Custom exception classes for GeoWizard application.
Provides specific exception types for better error handling and user feedback.
"""


class GeoWizardError(Exception):
    """Base exception class for all GeoWizard-specific exceptions."""
    
    def __init__(self, message: str, details: str = None):
        """
        Initialize the exception.
        
        Args:
            message: User-friendly error message
            details: Technical details for logging (optional)
        """
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} (Detalles: {self.details})"
        return self.message


class InvalidCoordinateError(GeoWizardError):
    """Raised when coordinate values are invalid."""
    
    def __init__(self, coordinate_value, reason: str = None):
        message = f"Coordenada inválida: {coordinate_value}"
        if reason:
            message += f". {reason}"
        super().__init__(message, details=str(coordinate_value))


class InvalidGeometryError(GeoWizardError):
    """Raised when geometry data is invalid or inconsistent."""
    
    def __init__(self, geometry_type: str = None, reason: str = None):
        if geometry_type:
            message = f"Geometría '{geometry_type}' inválida"
        else:
            message = "Geometría inválida"
        
        if reason:
            message += f": {reason}"
        
        super().__init__(message, details=geometry_type)


class FileOperationError(GeoWizardError):
    """Raised when file operations (read/write/import/export) fail."""
    
    def __init__(self, operation: str, filename: str, reason: str = None):
        message = f"Error en {operation}: {filename}"
        if reason:
            message += f". {reason}"
        super().__init__(message, details=f"{operation} - {filename}")


class ValidationError(GeoWizardError):
    """Raised when input validation fails."""
    
    def __init__(self, field_name: str, value, reason: str = None):
        message = f"Validación fallida para '{field_name}': {value}"
        if reason:
            message += f". {reason}"
        super().__init__(message, details=f"{field_name}={value}")


class ProjectError(GeoWizardError):
    """Raised when project operations fail."""
    
    def __init__(self, operation: str, reason: str = None):
        message = f"Error en operación de proyecto: {operation}"
        if reason:
            message += f". {reason}"
        super().__init__(message, details=operation)


class CoordinateTransformError(GeoWizardError):
    """Raised when coordinate transformation fails."""
    
    def __init__(self, from_crs: str, to_crs: str, reason: str = None):
        message = f"Error transformando coordenadas de {from_crs} a {to_crs}"
        if reason:
            message += f": {reason}"
        super().__init__(message, details=f"{from_crs} -> {to_crs}")

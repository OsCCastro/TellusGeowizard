"""
User-friendly error messages for GeoWizard application.

Maps exception types to localized, helpful error messages in Spanish.
"""

from core.exceptions import (
    GeoWizardError,
    CoordinateValidationError,
    CoordinateConversionError,
    GeometryBuildError,
    FileImportError,
    FileExportError,
    InsufficientDataError,
    InvalidCoordinateSystemError,
    ZoneHemisphereError
)


# Error message templates
ERROR_MESSAGES = {
    CoordinateValidationError: {
        "title": "Error de Validación de Coordenadas",
        "message": "Las coordenadas ingresadas no son válidas.",
        "suggestions": [
            "Verifique el formato de las coordenadas",
            "Asegúrese de que los valores estén dentro del rango permitido",
            "Consulte la ayuda para ver ejemplos de formatos válidos"
        ]
    },
    
    CoordinateConversionError: {
        "title": "Error de Conversión de Coordenadas",
        "message": "No se pudieron convertir las coordenadas al sistema seleccionado.",
        "suggestions": [
            "Verifique que las coordenadas de origen sean válidas",
            "Asegúrese de que la zona UTM y hemisferio sean correctos",
            "Intente con un sistema de coordenadas diferente"
        ]
    },
    
    GeometryBuildError: {
        "title": "Error al Construir Geometría",
        "message": "No se pudo construir la geometría con los datos proporcionados.",
        "suggestions": [
            "Verifique que haya suficientes puntos para el tipo de geometría",
            "Los polígonos requieren al menos 3 puntos",
            "Las polilíneas requieren al menos 2 puntos",
            "Asegúrese de que las coordenadas sean válidas"
        ]
    },
    
    FileImportError: {
        "title": "Error al Importar Archivo",
        "message": "No se pudo importar el archivo seleccionado.",
        "suggestions": [
            "Verifique que el archivo exista y no esté corrupto",
            "Asegúrese de que el formato del archivo sea compatible",
            "Intente abrir el archivo con otra aplicación para verificar su validez"
        ]
    },
    
    FileExportError: {
        "title": "Error al Exportar Archivo",
        "message": "No se pudo exportar el archivo.",
        "suggestions": [
            "Verifique que tenga permisos de escritura en la carpeta destino",
            "Asegúrese de que haya espacio suficiente en el disco",
            "Intente exportar a una ubicación diferente"
        ]
    },
    
    InsufficientDataError: {
        "title": "Datos Insuficientes",
        "message": "No hay suficientes datos para realizar esta operación.",
        "suggestions": [
            "Agregue más puntos a la tabla de coordenadas",
            "Verifique que los datos ingresados sean válidos",
            "Consulte la documentación para los requisitos mínimos"
        ]
    },
    
    InvalidCoordinateSystemError: {
        "title": "Sistema de Coordenadas Inválido",
        "message": "El sistema de coordenadas especificado no es válido.",
        "suggestions": [
            "Seleccione un sistema de coordenadas de la lista",
            "Sistemas soportados: UTM, Geographic (DD), Geographic (DMS), Web Mercator"
        ]
    },
    
    ZoneHemisphereError: {
        "title": "Error de Zona/Hemisferio",
        "message": "La zona UTM o hemisferio especificado no es válido.",
        "suggestions": [
            "La zona UTM debe estar entre 1 y 60",
            "El hemisferio debe ser Norte o Sur",
            "Verifique la ubicación geográfica de sus coordenadas"
        ]
    },
    
    # Generic fallback
    Exception: {
        "title": "Error Inesperado",
        "message": "Ocurrió un error inesperado.",
        "suggestions": [
            "Intente la operación nuevamente",
            "Si el problema persiste, consulte los registros de la aplicación",
            "Contacte al soporte técnico si necesita ayuda"
        ]
    }
}


def get_error_message(exception: Exception) -> dict:
    """
    Get user-friendly error message for an exception.
    
    Args:
        exception: The exception that occurred
    
    Returns:
        Dictionary with title, message, and suggestions
    """
    exc_type = type(exception)
    
    # Try to find exact match
    if exc_type in ERROR_MESSAGES:
        error_info = ERROR_MESSAGES[exc_type].copy()
    else:
        # Try parent classes
        for exc_class in exc_type.__mro__:
            if exc_class in ERROR_MESSAGES:
                error_info = ERROR_MESSAGES[exc_class].copy()
                break
        else:
            # Fallback to generic error
            error_info = ERROR_MESSAGES[Exception].copy()
    
    # Add exception details if available
    if hasattr(exception, 'details') and exception.details:
        error_info['details'] = exception.details
    elif str(exception):
        error_info['details'] = str(exception)
    
    return error_info


def format_error_message(exception: Exception) -> str:
    """
    Format error message as a string for display.
    
    Args:
        exception: The exception that occurred
    
    Returns:
        Formatted error message string
    """
    error_info = get_error_message(exception)
    
    message = f"{error_info['message']}\n"
    
    if 'details' in error_info:
        message += f"\nDetalles: {error_info['details']}\n"
    
    if error_info['suggestions']:
        message += "\nSugerencias:\n"
        for suggestion in error_info['suggestions']:
            message += f"• {suggestion}\n"
    
    return message.strip()

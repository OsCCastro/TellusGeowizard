"""
Error handling utilities for GeoWizard application.

Provides decorators and functions for consistent error handling,
logging, and user feedback.
"""

import functools
import traceback
from typing import Callable, Type, Optional
from utils.logger import get_logger
from utils.error_messages import get_error_message, format_error_message
from core.exceptions import GeoWizardError


logger = get_logger(__name__)


def handle_errors(
    error_type: Type[Exception] = Exception,
    user_message: str = None,
    log_level: str = "ERROR",
    reraise: bool = False,
    default_return=None
):
    """
    Decorator for consistent error handling.
    
    Args:
        error_type: Type of exception to catch (default: Exception for all)
        user_message: Custom user message (overrides default)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        reraise: Whether to re-raise the exception after handling
        default_return: Value to return if exception occurs and not reraising
    
    Example:
        @handle_errors(
            error_type=CoordinateConversionError,
            user_message="No se pudo convertir las coordenadas",
            log_level="ERROR"
        )
        def convert_coordinates(...):
            # function code
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                # Log the error
                log_func = getattr(logger, log_level.lower(), logger.error)
                log_func(
                    f"Error in {func.__name__}: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                
                # Store error info for potential UI display
                error_info = get_error_message(e)
                if user_message:
                    error_info['message'] = user_message
                
                # Attach error info to exception for UI to use
                if isinstance(e, GeoWizardError):
                    e.user_message = error_info['message']
                    e.suggestions = error_info.get('suggestions', [])
                
                if reraise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


def log_and_show_error(exception: Exception, context: str = None, show_ui: bool = True) -> dict:
    """
    Log an error and prepare it for UI display.
    
    Args:
        exception: The exception that occurred
        context: Additional context about where the error occurred
        show_ui: Whether to prepare for UI display
    
    Returns:
        Dictionary with error information for UI
    """
    # Log the error
    if context:
        logger.error(f"Error in {context}: {type(exception).__name__}: {str(exception)}")
    else:
        logger.error(f"{type(exception).__name__}: {str(exception)}")
    
    logger.debug(traceback.format_exc())
    
    # Get user-friendly message
    error_info = get_error_message(exception)
    
    if show_ui:
        return error_info
    
    return None


def safe_execute(func: Callable, *args, **kwargs) -> tuple:
    """
    Safely execute a function and return (success, result_or_error).
    
    Args:
        func: Function to execute
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function
    
    Returns:
        Tuple of (success: bool, result or exception)
    
    Example:
        success, result = safe_execute(risky_function, arg1, arg2)
        if success:
            print(f"Result: {result}")
        else:
            print(f"Error: {result}")
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {str(e)}", exc_info=True)
        return False, e

from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first to get a standard response.
    response = exception_handler(exc, context)
    
    errors = []
    
    if response is not None:
        # Handled exceptions (4xx)
        if isinstance(exc, ValidationError):
            if isinstance(response.data, dict):
                for field, val in response.data.items():
                    # val can be a list of errors
                    if isinstance(val, list):
                        for v in val:
                            errors.append({
                                "code": "VALIDATION_ERROR",
                                "field": field,
                                "message": str(v)
                            })
                    else:
                        errors.append({
                            "code": "VALIDATION_ERROR",
                            "field": field,
                            "message": str(val)
                        })
            elif isinstance(response.data, list):
                for val in response.data:
                    errors.append({
                        "code": "VALIDATION_ERROR",
                        "field": "non_field_errors",
                        "message": str(val)
                    })
        else:
            # Other DRF exceptions
            msg = str(exc)
            if isinstance(response.data, dict):
                msg = response.data.get('detail', response.data.get('message', msg))
            code = exc.__class__.__name__
            # Convert CamelCase to SNAKE_CASE_UPPER
            import re
            code_snake = re.sub(r'(?<!^)(?=[A-Z])', '_', code).upper()
            errors.append({
                "code": code_snake,
                "field": None,
                "message": msg
            })
            
        response.data = {
            "errors": errors,
            "data": None
        }
    else:
        # Unhandled exceptions (500)
        logger.exception("Unhandled server error: %s", str(exc))
        errors.append({
            "code": "INTERNAL_SERVER_ERROR",
            "field": None,
            "message": "An unexpected error occurred on the server."
        })
        return JsonResponse({
            "errors": errors,
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    return response

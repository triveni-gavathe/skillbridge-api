from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # Foreign key / DoesNotExist → 404
    if isinstance(exc, ObjectDoesNotExist):
        return Response({'error': str(exc)}, status=404)

    # Database integrity (duplicate keys etc.) → 400
    if isinstance(exc, IntegrityError):
        return Response({'error': 'Database integrity error. Check your input.'}, status=400)

    return response
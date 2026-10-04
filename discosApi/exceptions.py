from django.core.exceptions import ValidationError as ValidacionModelo
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.http import Http404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def excepcion_api(error, context):
    """Nunca devolver SQL, objetos protegidos ni los valores de una validación."""
    if isinstance(error, ProtectedError):
        return Response({"detail": "No se puede eliminar un registro con ventas asociadas."}, status=400)
    if isinstance(error, ValidacionModelo):
        return Response({"detail": "No se pudo guardar. Revisa la cantidad, el stock y los datos."}, status=400)
    if isinstance(error, (ValidationError, IntegrityError)):
        return Response({"detail": "Datos no válidos. Revisa los campos y las relaciones."}, status=400)
    if isinstance(error, Http404):
        return Response({"detail": "Registro no encontrado."}, status=404)
    respuesta = exception_handler(error, context)
    if respuesta is not None:
        return respuesta
    return Response({"detail": "No se pudo completar la operación."}, status=500)

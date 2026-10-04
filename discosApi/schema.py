from drf_spectacular.serializers import PolymorphicProxySerializerExtension
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, PolymorphicProxySerializer

from .serializers import (
    ClienteAdminEntradaSerializer, ClienteAdminSerializer, ClienteEntradaSerializer, ClientePublicoSerializer,
    CompraEntradaSerializer, DiscoAdminSerializer, DiscoCatalogoSerializer, ErrorRespuestaSerializer,
    VentaAdminSerializer, VentaEntradaSerializer, VentaPublicaSerializer,
)


class UnionSinDiscriminador(PolymorphicProxySerializerExtension):
    # Las formas pública/admin comparten campos: anyOf admite ese solapamiento.
    priority = 1

    def map_serializer(self, auto_schema, direction):
        resultado = super().map_serializer(auto_schema, direction)
        if self.target.resource_type_field_name is None:
            resultado["anyOf"] = resultado.pop("oneOf")
        return resultado


ROLES = (
    "JWT obligatorio. Precedencia: superusuario/Administrador > Operador > Consulta > Cliente. "
    "Administrador: CRUD completo. Operador: GET, POST y PUT. Consulta: GET. "
    "Cliente: GET catálogo y sus propios clientes/ventas; POST compra propia. "
    "Sin grupo válido o sólo is_staff: sin acceso."
)

CLIENTE_RESPUESTA = PolymorphicProxySerializer(
    component_name="ClienteRespuesta", serializers=[ClientePublicoSerializer, ClienteAdminSerializer],
    resource_type_field_name=None,
)
DISCO_RESPUESTA = PolymorphicProxySerializer(
    component_name="DiscoRespuesta", serializers=[DiscoCatalogoSerializer, DiscoAdminSerializer],
    resource_type_field_name=None,
)
VENTA_RESPUESTA = PolymorphicProxySerializer(
    component_name="VentaRespuesta", serializers=[VentaPublicaSerializer, VentaAdminSerializer],
    resource_type_field_name=None,
)
CLIENTE_ENTRADA = PolymorphicProxySerializer(
    component_name="ClienteEscritura", serializers=[ClienteEntradaSerializer, ClienteAdminEntradaSerializer],
    resource_type_field_name=None,
)
VENTA_ENTRADA = PolymorphicProxySerializer(
    component_name="VentaEscritura", serializers=[CompraEntradaSerializer, VentaEntradaSerializer],
    resource_type_field_name=None,
)


def respuestas(serializer=None, estado=200, lista=False, detalle=False):
    errores = {
        400: OpenApiResponse(ErrorRespuestaSerializer, description="Datos inválidos, stock insuficiente o relación protegida."),
        401: OpenApiResponse(ErrorRespuestaSerializer, description="JWT ausente, inválido o caducado."),
        403: OpenApiResponse(ErrorRespuestaSerializer, description="Perfil sin permiso para esta operación."),
        405: OpenApiResponse(ErrorRespuestaSerializer, description="Método no admitido."),
        500: OpenApiResponse(ErrorRespuestaSerializer, description="Error genérico sin información privada."),
    }
    if detalle:
        errores[404] = OpenApiResponse(ErrorRespuestaSerializer, description="ID inexistente o ajeno al cliente.")
    if estado == 204:
        errores[204] = OpenApiResponse(description="Registro eliminado; sin cuerpo.")
    else:
        if lista:
            serializer = PolymorphicProxySerializer(
                component_name=serializer.component_name, serializers=serializer.serializers,
                resource_type_field_name=None, many=True,
            )
        errores[estado] = serializer
    return errores


CLIENTE_EJEMPLOS = [
    OpenApiExample("Crear cliente de prueba", value={"nombre": "Cliente de prueba", "correo": "prueba@example.test", "telefono": "123"}, request_only=True),
    OpenApiExample("Cliente público", value={"id": 1, "nombre": "Cliente de prueba"}, response_only=True, status_codes=["200", "201"]),
    OpenApiExample("Cliente administrador", value={"id": 1, "nombre": "Cliente de prueba", "correo": "prueba@example.test", "telefono": "123", "usuario": None}, response_only=True, status_codes=["200", "201"]),
]
DISCO_EJEMPLOS = [
    OpenApiExample("Crear disco de prueba", value={"titulo": "Disco de prueba", "artista": 1, "genero": "Rock", "anio": 2020, "formato": "CD", "precio": "12000", "stock": 8}, request_only=True),
    OpenApiExample("Disco público", value={"id": 1, "titulo": "Disco de prueba", "artista": 1, "genero": "Rock", "anio": 2020, "formato": "CD", "precio": "12000", "stock": 8, "descripcion": "", "imagen": None}, response_only=True, status_codes=["200", "201"]),
]
VENTA_EJEMPLOS = [
    OpenApiExample("Compra de cliente", value={"disco": 1, "cantidad": 2}, description="Cliente y fecha los asigna el servidor; se ignoran extras.", request_only=True),
    OpenApiExample("Venta de administrador u operador", value={"cliente": 1, "disco": 1, "fecha": "2026-10-04", "cantidad": 2}, description="El servidor siempre fija el precio.", request_only=True),
    OpenApiExample("Venta pública", value={"id": 1, "cliente": 1, "disco": 1, "fecha": "2026-10-04", "cantidad": 2}, response_only=True, status_codes=["200", "201"]),
    OpenApiExample("Venta administrador", value={"id": 1, "cliente": 1, "disco": 1, "fecha": "2026-10-04", "cantidad": 2, "precio_unitario": "12000", "total": "24000"}, response_only=True, status_codes=["200", "201"]),
]

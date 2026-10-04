from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from discosApp.models import Disco
from ventasApp.models import Cliente, Venta
from .schema import (
    CLIENTE_EJEMPLOS, CLIENTE_ENTRADA, CLIENTE_RESPUESTA, DISCO_EJEMPLOS, DISCO_RESPUESTA,
    ROLES, VENTA_EJEMPLOS, VENTA_ENTRADA, VENTA_RESPUESTA, respuestas,
)
from .serializers import (
    ClienteAdminEntradaSerializer, ClienteAdminSerializer, ClienteEntradaSerializer, ClientePublicoSerializer,
    CompraEntradaSerializer, DiscoAdminSerializer, DiscoCatalogoSerializer, DiscoEntradaSerializer,
    VentaAdminSerializer, VentaEntradaSerializer, VentaPublicaSerializer,
)


def clientes_visibles(request):
    clientes = Cliente.objects.all()
    if request.rol_api == "Cliente":
        clientes = clientes.filter(usuario=request.user)
    return clientes


def ventas_visibles(request):
    ventas = Venta.objects.all()
    if request.rol_api == "Cliente":
        ventas = ventas.filter(cliente__usuario=request.user)
    return ventas


def respuesta_cliente(request, objeto, many=False, estado=200):
    serializer = ClienteAdminSerializer if request.rol_api == "Administrador" else ClientePublicoSerializer
    return Response(serializer(objeto, many=many).data, status=estado)


def respuesta_disco(request, objeto, many=False, estado=200):
    serializer = DiscoAdminSerializer if request.rol_api == "Administrador" else DiscoCatalogoSerializer
    return Response(serializer(objeto, many=many, context={"request": request}).data, status=estado)


def respuesta_venta(request, objeto, many=False, estado=200):
    serializer = VentaAdminSerializer if request.rol_api == "Administrador" else VentaPublicaSerializer
    return Response(serializer(objeto, many=many).data, status=estado)


@extend_schema(methods=["GET"], tags=["Clientes"], description=ROLES + " Respuesta noadministrador: id y nombre. Administrador añade correo, teléfono y usuario.", responses=respuestas(CLIENTE_RESPUESTA, lista=True), examples=CLIENTE_EJEMPLOS)
@extend_schema(methods=["POST"], tags=["Clientes"], description=ROLES + " Sólo administrador y operador; sólo administrador escribe vínculo usuario. Extras se ignoran.", request=CLIENTE_ENTRADA, responses=respuestas(CLIENTE_RESPUESTA, estado=201), examples=CLIENTE_EJEMPLOS)
@api_view(["GET", "POST"])
def clientes_lista(request):
    if request.method == "GET":
        return respuesta_cliente(request, clientes_visibles(request), many=True)
    entrada = ClienteAdminEntradaSerializer if request.rol_api == "Administrador" else ClienteEntradaSerializer
    serializer = entrada(data=request.data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        cliente = serializer.save()
        return respuesta_cliente(request, cliente, estado=201)


@extend_schema(methods=["GET"], tags=["Clientes"], description=ROLES + " Cliente: sólo su propia ficha; ID ajeno devuelve 404.", responses=respuestas(CLIENTE_RESPUESTA, detalle=True), examples=CLIENTE_EJEMPLOS)
@extend_schema(methods=["PUT"], tags=["Clientes"], description=ROLES + " Actualización completa: nombre y correo obligatorios. Sólo administrador escribe usuario.", request=CLIENTE_ENTRADA, responses=respuestas(CLIENTE_RESPUESTA, detalle=True), examples=CLIENTE_EJEMPLOS)
@extend_schema(methods=["DELETE"], tags=["Clientes"], description=ROLES + " Sólo administrador. Cliente con ventas no se elimina.", responses=respuestas(estado=204, detalle=True))
@api_view(["GET", "PUT", "DELETE"])
def clientes_detalle(request, pk):
    with transaction.atomic():
        clientes = clientes_visibles(request)
        if request.method != "GET":
            clientes = clientes.select_for_update()
        cliente = get_object_or_404(clientes, pk=pk)
        if request.method == "GET":
            return respuesta_cliente(request, cliente)
        if request.method == "DELETE":
            cliente.delete()
            return Response(status=204)
        entrada = ClienteAdminEntradaSerializer if request.rol_api == "Administrador" else ClienteEntradaSerializer
        serializer = entrada(cliente, data=request.data)
        serializer.is_valid(raise_exception=True)
        return respuesta_cliente(request, serializer.save())


@extend_schema(methods=["GET"], tags=["Discos"], description=ROLES + " Precio de catálogo visible. Documento privado: sólo nombre base para administrador.", responses=respuestas(DISCO_RESPUESTA, lista=True), examples=DISCO_EJEMPLOS)
@extend_schema(methods=["POST"], tags=["Discos"], description=ROLES + " JSON o multipart con imagen JPG/PNG/WebP (5 MB) y PDF (10 MB). Operador puede subir PDF sin recibir sus metadatos.", request=DiscoEntradaSerializer, responses=respuestas(DISCO_RESPUESTA, estado=201), examples=DISCO_EJEMPLOS)
@api_view(["GET", "POST"])
def discos_lista(request):
    if request.method == "GET":
        return respuesta_disco(request, Disco.objects.all(), many=True)
    serializer = DiscoEntradaSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        return respuesta_disco(request, serializer.save(), estado=201)


@extend_schema(methods=["GET"], tags=["Discos"], description=ROLES + " Documento privado nunca devuelve URL ni ruta; sólo nombre para administrador.", responses=respuestas(DISCO_RESPUESTA, detalle=True), examples=DISCO_EJEMPLOS)
@extend_schema(methods=["PUT"], tags=["Discos"], description=ROLES + " Actualización completa. Archivos omitidos se conservan. Imagen pública y PDF privado usan validadores existentes.", request=DiscoEntradaSerializer, responses=respuestas(DISCO_RESPUESTA, detalle=True), examples=DISCO_EJEMPLOS)
@extend_schema(methods=["DELETE"], tags=["Discos"], description=ROLES + " Sólo administrador. Disco con ventas no se elimina.", responses=respuestas(estado=204, detalle=True))
@api_view(["GET", "PUT", "DELETE"])
def discos_detalle(request, pk):
    with transaction.atomic():
        discos = Disco.objects.all()
        if request.method != "GET":
            discos = discos.select_for_update()
        disco = get_object_or_404(discos, pk=pk)
        if request.method == "GET":
            return respuesta_disco(request, disco)
        if request.method == "DELETE":
            disco.delete()
            return Response(status=204)
        serializer = DiscoEntradaSerializer(disco, data=request.data)
        serializer.is_valid(raise_exception=True)
        return respuesta_disco(request, serializer.save())


def guardar_venta(request, venta=None):
    """Se llama dentro de atomic; bloquea discos antes de tomar su precio."""
    entrada = CompraEntradaSerializer if request.rol_api == "Cliente" else VentaEntradaSerializer
    serializer = entrada(venta, data=request.data)
    serializer.is_valid(raise_exception=True)
    datos_servidor = {}
    if request.rol_api == "Cliente":
        cliente = clientes_visibles(request).first()
        if cliente is None:
            raise ValidationError("No hay ficha de cliente.")
        datos_servidor = {"cliente": cliente, "fecha": timezone.localdate()}
    disco_id = serializer.validated_data["disco"].pk
    ids = {disco_id}
    if venta:
        ids.add(venta.disco_id)
    discos = {disco.pk: disco for disco in Disco.objects.select_for_update().filter(pk__in=ids).order_by("pk")}
    disco = get_object_or_404(Disco, pk=disco_id) if disco_id not in discos else discos[disco_id]
    precio = venta.precio_unitario if venta and venta.disco_id == disco_id else disco.precio
    return serializer.save(disco=disco, precio_unitario=precio, **datos_servidor)


@extend_schema(methods=["GET"], tags=["Ventas"], description=ROLES + " Cliente ve sólo compras propias. Sólo administrador recibe precio_unitario y total.", responses=respuestas(VENTA_RESPUESTA, lista=True), examples=VENTA_EJEMPLOS)
@extend_schema(methods=["POST"], tags=["Ventas"], description=ROLES + " Cliente sólo envía disco y cantidad; extras cliente/fecha/precio/total se ignoran antes de validar. Fecha actual y cliente propio. Administrador/operador envían cliente/disco/cantidad y fecha opcional. Precio de catálogo fijado por servidor; descuento de stock atómico.", request=VENTA_ENTRADA, responses=respuestas(VENTA_RESPUESTA, estado=201), examples=VENTA_EJEMPLOS)
@api_view(["GET", "POST"])
def ventas_lista(request):
    if request.method == "GET":
        return respuesta_venta(request, ventas_visibles(request), many=True)
    with transaction.atomic():
        return respuesta_venta(request, guardar_venta(request), estado=201)


@extend_schema(methods=["GET"], tags=["Ventas"], description=ROLES + " Propiedad se filtra antes de buscar ID; venta ajena a Cliente devuelve 404. Importes sólo administrador.", responses=respuestas(VENTA_RESPUESTA, detalle=True), examples=VENTA_EJEMPLOS)
@extend_schema(methods=["PUT"], tags=["Ventas"], description=ROLES + " Sólo administrador/operador. Cliente, disco y cantidad obligatorios. Conserva precio histórico si mantiene disco; cambiar disco toma nuevo precio. Ignora precios enviados. Stock atómico.", request=VentaEntradaSerializer, responses=respuestas(VENTA_RESPUESTA, detalle=True), examples=VENTA_EJEMPLOS[1:])
@extend_schema(methods=["DELETE"], tags=["Ventas"], description=ROLES + " Sólo administrador. Borrado individual devuelve unidades al stock.", responses=respuestas(estado=204, detalle=True))
@api_view(["GET", "PUT", "DELETE"])
def ventas_detalle(request, pk):
    with transaction.atomic():
        ventas = ventas_visibles(request)
        if request.method != "GET":
            ventas = ventas.select_for_update()
        venta = get_object_or_404(ventas, pk=pk)
        if request.method == "GET":
            return respuesta_venta(request, venta)
        if request.method == "DELETE":
            venta.delete()
            return Response(status=204)
        return respuesta_venta(request, guardar_venta(request, venta))

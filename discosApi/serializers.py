from pathlib import Path

from rest_framework import serializers

from discosApp.models import Disco
from ventasApp.models import Cliente, Venta


class ClientePublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ("id", "nombre")
        read_only_fields = fields


class ClienteAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ("id", "nombre", "correo", "telefono", "usuario")
        read_only_fields = fields


class ClienteEntradaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ("nombre", "correo", "telefono")


class ClienteAdminEntradaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ("nombre", "correo", "telefono", "usuario")


class DiscoCatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disco
        fields = ("id", "titulo", "artista", "genero", "anio", "formato", "precio", "stock", "descripcion", "imagen")
        read_only_fields = fields


class DiscoAdminSerializer(DiscoCatalogoSerializer):
    documento = serializers.SerializerMethodField()

    def get_documento(self, disco) -> str:
        return Path(disco.documento.name).name if disco.documento else ""

    class Meta(DiscoCatalogoSerializer.Meta):
        fields = DiscoCatalogoSerializer.Meta.fields + ("documento",)
        read_only_fields = fields


class DiscoEntradaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disco
        fields = ("titulo", "artista", "genero", "anio", "formato", "precio", "stock", "descripcion", "imagen", "documento")
        extra_kwargs = {"documento": {"write_only": True}}


class VentaPublicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = ("id", "cliente", "disco", "fecha", "cantidad")
        read_only_fields = fields


class VentaAdminSerializer(VentaPublicaSerializer):
    total = serializers.DecimalField(max_digits=20, decimal_places=0, read_only=True)

    class Meta(VentaPublicaSerializer.Meta):
        fields = VentaPublicaSerializer.Meta.fields + ("precio_unitario", "total")
        read_only_fields = fields


class VentaEntradaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = ("cliente", "disco", "fecha", "cantidad")


class CompraEntradaSerializer(serializers.ModelSerializer):
    # Campos ajenos se descartan antes de convertir cualquier FK o fecha.
    class Meta:
        model = Venta
        fields = ("disco", "cantidad")


class ErrorRespuestaSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True)

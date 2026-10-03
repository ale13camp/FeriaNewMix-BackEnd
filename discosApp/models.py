from django.core.validators import MinValueValidator
from django.db import models

from discosApp.storage import DocumentosPrivadosStorage
from discosApp.validators import validar_documento, validar_imagen


class Disco(models.Model):
    titulo = models.CharField("título", max_length=200)
    artista = models.ForeignKey("artistasApp.Artista", on_delete=models.PROTECT, related_name="discos")
    genero = models.CharField("género", max_length=100)
    anio = models.PositiveIntegerField("año", validators=[MinValueValidator(1)])
    formato = models.CharField(max_length=30, choices=[("Vinilo", "Vinilo"), ("CD", "CD"), ("Cassette", "Cassette")])
    precio = models.DecimalField("precio (CLP)", max_digits=10, decimal_places=0, validators=[MinValueValidator(1)])
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    descripcion = models.TextField("descripción", blank=True)
    imagen = models.ImageField(upload_to="discos/", blank=True, validators=[validar_imagen])
    documento = models.FileField(upload_to="documentos/", storage=DocumentosPrivadosStorage(), blank=True, validators=[validar_documento])

    class Meta:
        ordering = ["titulo", "id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(precio__gte=1), name="disco_precio_positivo"),
            models.CheckConstraint(condition=models.Q(stock__gte=0), name="disco_stock_no_negativo"),
        ]

    def __str__(self):
        return f"{self.titulo} — {self.artista}"

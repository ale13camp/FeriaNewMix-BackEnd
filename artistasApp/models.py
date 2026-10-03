from django.core.validators import MinValueValidator
from django.db import models

from discosApp.validators import validar_imagen


class Artista(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    genero = models.CharField("género", max_length=100)
    pais = models.CharField("país", max_length=100)
    anio_formacion = models.PositiveIntegerField("año de formación", validators=[MinValueValidator(1)])
    integrantes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    bio = models.TextField("biografía")
    imagen = models.ImageField(upload_to="artistas/", blank=True, validators=[validar_imagen])

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "artistas"

    def __str__(self):
        return self.nombre

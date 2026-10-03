from django.contrib import admin

from artistasApp.forms import ArtistaForm
from artistasApp.models import Artista


@admin.register(Artista)
class ArtistaAdmin(admin.ModelAdmin):
    form = ArtistaForm
    list_display = ["nombre", "genero", "pais", "anio_formacion", "integrantes"]
    search_fields = ["nombre", "genero", "pais"]
    list_filter = ["genero", "pais"]

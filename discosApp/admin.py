from django.contrib import admin

from discosApp.forms import DiscoForm
from discosApp.models import Disco


@admin.register(Disco)
class DiscoAdmin(admin.ModelAdmin):
    form = DiscoForm
    list_display = ["titulo", "artista", "formato", "precio", "stock"]
    search_fields = ["titulo", "artista__nombre", "genero"]
    list_filter = ["formato", "genero", "artista"]
    list_select_related = ["artista"]

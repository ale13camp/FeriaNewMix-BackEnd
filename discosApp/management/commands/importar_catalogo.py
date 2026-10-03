import json
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, transaction

from artistasApp.models import Artista
from discosApp.models import Disco


class Command(BaseCommand):
    help = "Importa el catálogo original una vez y conserva las ediciones posteriores."

    @transaction.atomic
    def handle(self, *args, **options):
        base = settings.BASE_DIR
        artistas = json.loads((base / "artistasApp/data/artistas.json").read_text(encoding="utf-8"))
        discos = json.loads((base / "discosApp/data/discos.json").read_text(encoding="utf-8"))
        creados_artistas = 0
        creados_discos = 0
        # Se valida la existencia de los originales antes de insertar registros.
        for carpeta, datos in [("artistas", artistas), ("discos", discos)]:
            for dato in datos:
                if not (base / "static/img" / carpeta / dato["imagen"]).is_file():
                    raise CommandError(f"Falta la imagen original {carpeta}/{dato['imagen']}.")
        artistas_por_nombre = {}
        for dato in artistas:
            campos = {clave: valor for clave, valor in dato.items() if clave not in ["id", "imagen"]}
            artista, creado = Artista.objects.get_or_create(pk=dato["id"], defaults=campos)
            artistas_por_nombre[dato["nombre"]] = artista
            if creado:
                self.copiar_imagen(artista, "artistas", dato["imagen"])
                creados_artistas += 1
        for dato in discos:
            campos = {clave: valor for clave, valor in dato.items() if clave not in ["id", "imagen", "artista"]}
            campos["artista"] = artistas_por_nombre[dato["artista"]]
            disco, creado = Disco.objects.get_or_create(pk=dato["id"], defaults=campos)
            if creado:
                self.copiar_imagen(disco, "discos", dato["imagen"])
                creados_discos += 1
        # Mantiene correctos los siguientes IDs también en bases distintas de SQLite.
        with connection.cursor() as cursor:
            for sql in connection.ops.sequence_reset_sql(no_style(), [Artista, Disco]):
                cursor.execute(sql)
        self.stdout.write(self.style.SUCCESS(f"Importados: {creados_artistas} artistas y {creados_discos} discos nuevos."))

    def copiar_imagen(self, objeto, carpeta, nombre):
        ruta = Path(settings.BASE_DIR) / "static/img" / carpeta / nombre
        with ruta.open("rb") as archivo:
            objeto.imagen.save(nombre, File(archivo), save=True)

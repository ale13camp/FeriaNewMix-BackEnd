"""Comprueba rutas, catálogo y archivos después de preparar la base local."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.test import Client, override_settings
from artistasApp.models import Artista
from discosApp.models import Disco


def comprobar(condicion, texto):
    if not condicion:
        raise AssertionError(texto)
    print("OK:", texto)


with override_settings(ALLOWED_HOSTS=["localhost", "testserver"]):
    cliente = Client()
    comprobar(cliente.get("/").status_code == 302, "El acceso anónimo solicita iniciar sesión")
    usuario = next((u for u in User.objects.filter(is_active=True, is_staff=True)
                    if u.has_perms(["artistasApp.view_artista", "discosApp.view_disco", "ventasApp.view_cliente", "ventasApp.view_venta"])), None)
    if usuario is None:
        raise SystemExit("Crea un administrador con manage.py createsuperuser antes de esta comprobación.")
    cliente.force_login(usuario)
    for url in ["/", "/artistas/", "/artistas/catalogo/", "/artistas/lista/", "/discos/", "/discos/catalogo/", "/discos/lista/", "/ventas/clientes/", "/ventas/"]:
        comprobar(cliente.get(url).status_code == 200, url)
    for modelo, prefijo in [(Artista, "artistas"), (Disco, "discos")]:
        registro = modelo.objects.first()
        comprobar(registro is not None, f"Hay registros de {prefijo}")
        comprobar(cliente.get(f"/{prefijo}/detalle/{registro.pk}/").status_code == 200, f"Detalle de {prefijo}")
        for objeto in modelo.objects.all():
            if objeto.imagen:
                comprobar(objeto.imagen.storage.exists(objeto.imagen.name), f"Imagen {objeto.imagen.name}")
    # Client no sirve static: se usan los buscadores de archivos Django.
    for archivo in ["css/bootstrap.min.css", "css/estilo.css", "js/bootstrap.bundle.min.js"]:
        comprobar(bool(finders.find(archivo)), f"Archivo estático {archivo}")
    cliente.logout()
print("Comprobación rápida terminada.")

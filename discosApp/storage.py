from django.conf import settings
from django.core.files.storage import FileSystemStorage


class DocumentosPrivadosStorage(FileSystemStorage):
    # Los documentos quedan fuera de MEDIA_ROOT y sólo se descargan desde una vista con permiso.
    @property
    def base_location(self):
        return getattr(settings, "PRIVATE_MEDIA_ROOT", settings.BASE_DIR / "privados")

    def url(self, name):
        raise ValueError("El documento se descarga desde la vista protegida.")

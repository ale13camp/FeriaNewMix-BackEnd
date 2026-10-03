from pathlib import Path

from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError


def validar_imagen(archivo):
    if Path(archivo.name).suffix.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise ValidationError("La imagen debe ser JPG, PNG o WebP.")
    if archivo.size > 5 * 1024 * 1024:
        raise ValidationError("La imagen no puede superar 5 MB.")
    posicion = archivo.tell()
    try:
        archivo.seek(0)
        imagen = Image.open(archivo)
        if imagen.format not in ["JPEG", "PNG", "WEBP"]:
            raise ValidationError("El contenido debe ser una imagen JPG, PNG o WebP.")
        imagen.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ValidationError("El archivo no contiene una imagen válida.")
    finally:
        archivo.seek(posicion)


def validar_documento(archivo):
    if Path(archivo.name).suffix.lower() != ".pdf":
        raise ValidationError("El documento debe tener extensión PDF.")
    if archivo.size > 10 * 1024 * 1024:
        raise ValidationError("El PDF no puede superar 10 MB.")
    posicion = archivo.tell()
    try:
        archivo.seek(0)
        if archivo.read(5) != b"%PDF-":
            raise ValidationError("El archivo no tiene una firma PDF válida.")
    finally:
        archivo.seek(posicion)

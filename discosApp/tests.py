import io
import tempfile

from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from discosApp import models


def imagen_prueba(nombre="portada.png"):
    from PIL import Image
    contenido = io.BytesIO()
    Image.new("RGB", (2, 2), "white").save(contenido, format="PNG")
    return SimpleUploadedFile(nombre, contenido.getvalue(), content_type="image/png")


class DiscosTests(TestCase):
    def datos(self):
        self.assertTrue(hasattr(models, "Disco"), "Falta el modelo ORM Disco")
        from artistasApp.models import Artista
        artista = Artista.objects.create(nombre="Prueba", genero="Rock", pais="Chile", anio_formacion=2000, integrantes=1, bio="Prueba")
        return dict(titulo="Prueba", artista=artista, genero="Rock", anio=2020, formato="CD", precio=1000, stock=1)

    def test_modelo_rechaza_precio_cero_y_stock_negativo(self):
        datos = self.datos()
        disco = models.Disco(**datos, imagen=imagen_prueba())
        disco.full_clean()
        disco.precio = 0
        disco.stock = -1
        with self.assertRaises(ValidationError) as error:
            disco.full_clean()
        self.assertIn("precio", error.exception.message_dict)
        self.assertIn("stock", error.exception.message_dict)

    def test_formulario_valida_imagen_y_documento(self):
        datos = self.datos()
        from discosApp.forms import DiscoForm
        datos["artista"] = datos["artista"].pk
        formulario = DiscoForm(datos, files={"imagen": imagen_prueba(), "documento": SimpleUploadedFile("ficha.pdf", b"%PDF-1.4\nprueba")})
        self.assertTrue(formulario.is_valid(), formulario.errors)
        for nombre, contenido in [("ficha.pdf", b"texto"), ("ficha.txt", b"%PDF-1.4\n")]:
            formulario = DiscoForm(datos, files={"imagen": imagen_prueba(), "documento": SimpleUploadedFile(nombre, contenido)})
            self.assertFalse(formulario.is_valid())
            self.assertIn("documento", formulario.errors)
        formulario = DiscoForm(datos, files={"imagen": imagen_prueba("portada.gif")})
        self.assertFalse(formulario.is_valid())
        self.assertIn("imagen", formulario.errors)

    def test_validadores_limite_y_modelo_para_admin(self):
        datos = self.datos()
        disco = models.Disco(**datos, imagen=imagen_prueba(), documento=SimpleUploadedFile("mal.pdf", b"texto"))
        with self.assertRaises(ValidationError) as error:
            disco.full_clean()
        self.assertIn("documento", error.exception.message_dict)
        from discosApp.validators import validar_documento, validar_imagen
        imagen = imagen_prueba()
        imagen.size = 5 * 1024 * 1024 + 1
        with self.assertRaises(ValidationError):
            validar_imagen(imagen)
        pdf = SimpleUploadedFile("ficha.pdf", b"%PDF-1.4")
        pdf.size = 10 * 1024 * 1024 + 1
        with self.assertRaises(ValidationError):
            validar_documento(pdf)

    def test_documento_privado_y_permiso(self):
        datos = self.datos()
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media, PRIVATE_MEDIA_ROOT=media):
                disco = models.Disco.objects.create(**datos, documento=SimpleUploadedFile("ficha.pdf", b"%PDF-1.4\n"))
                url = reverse("discos_documento", args=[disco.pk])
                self.assertEqual(self.client.get(url).status_code, 302)
                usuario = User.objects.create_user("lector")
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(url).status_code, 403)
                usuario.user_permissions.add(Permission.objects.get(codename="view_disco"))
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(b"".join(respuesta.streaming_content), b"%PDF-1.4\n")
                self.assertIn("attachment", respuesta["Content-Disposition"])

    def test_busqueda_filtra_en_orm_y_permiso_escritura(self):
        datos = self.datos()
        models.Disco.objects.create(**datos)
        usuario = User.objects.create_user("lector")
        usuario.user_permissions.add(Permission.objects.get(codename="view_disco"))
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("discos_lista"), {"q": "Prueba", "formato": "CD"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.context["discos"]), 1)
        self.assertEqual(len(self.client.get(reverse("discos_lista"), {"q": "inexistente"}).context["discos"]), 0)
        self.assertEqual(self.client.post(reverse("discos_crear"), {}).status_code, 403)

    def test_origen_y_listas_sin_discos(self):
        self.datos()
        usuario = User.objects.create_user("consulta")
        usuario.user_permissions.add(Permission.objects.get(codename="view_disco"))
        self.client.force_login(usuario)
        for nombre in ["discos_inicio", "discos_catalogo", "discos_lista"]:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)
        self.assertEqual(self.client.get(reverse("discos_detalle", args=[999])).status_code, 404)

    def test_alta_edicion_con_upload_y_documento_conservado(self):
        datos = self.datos()
        usuario = User.objects.create_user("admin", "admin@example.test", "Prueba123!", is_staff=True)
        usuario.user_permissions.add(*Permission.objects.filter(content_type__app_label="discosApp"))
        self.client.force_login(usuario)
        respuesta = self.client.post(reverse("discos_crear"), {})
        self.assertTrue(respuesta.context["form"].is_bound)
        self.assertIn("titulo", respuesta.context["form"].errors)
        datos["artista"] = datos["artista"].pk
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media, PRIVATE_MEDIA_ROOT=media):
                datos["imagen"] = imagen_prueba()
                datos["documento"] = SimpleUploadedFile("ficha.pdf", b"%PDF-1.4\n")
                self.assertEqual(self.client.post(reverse("discos_crear"), datos).status_code, 302)
                disco = models.Disco.objects.get(titulo="Prueba")
                documento_original = disco.documento.name
                imagen_original = disco.imagen.name
                url = reverse("discos_editar", args=[disco.pk])
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.context["form"].initial["stock"], 1)
                datos.pop("imagen")
                datos.pop("documento")
                datos["titulo"] = "Editado"
                self.assertEqual(self.client.post(url, datos).status_code, 302)
                disco.refresh_from_db()
                self.assertEqual(disco.titulo, "Editado")
                self.assertEqual(disco.documento.name, documento_original)
                self.assertEqual(disco.imagen.name, imagen_original)
                self.assertEqual(disco.documento.read(), b"%PDF-1.4\n")
                disco.documento.close()
                self.assertEqual(self.client.get(reverse("discos_detalle", args=[disco.pk])).status_code, 200)
                self.assertEqual(self.client.get(reverse("admin:discosApp_disco_change", args=[disco.pk])).status_code, 200)

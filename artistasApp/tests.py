import io
import tempfile
from pathlib import Path

from django.contrib.auth.models import Permission, User
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse

from artistasApp import models


class CatalogoTests(TestCase):
    def modelo_artista(self):
        self.assertTrue(hasattr(models, "Artista"), "Falta el modelo ORM Artista")
        return models.Artista

    def test_nombre_unico_y_relacion_protegida(self):
        Artista = self.modelo_artista()
        from discosApp.models import Disco
        artista = Artista.objects.create(nombre="Prueba", genero="Rock", pais="Chile", anio_formacion=2000, integrantes=3, bio="Biografía")
        Disco.objects.create(titulo="Uno", artista=artista, genero="Rock", anio=2020, formato="CD", precio=1000, stock=2)
        with self.assertRaises(ProtectedError):
            artista.delete()
        self.assertEqual(Artista.objects.count(), 1)
        repetido = Artista(nombre="Prueba", genero="Rock", pais="Chile", anio_formacion=2000, integrantes=1, bio="Prueba")
        with self.assertRaises(ValidationError) as error:
            repetido.full_clean()
        self.assertIn("nombre", error.exception.message_dict)

    def test_importar_conserva_datos_imagenes_y_ediciones(self):
        Artista = self.modelo_artista()
        from discosApp.models import Disco
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media):
                call_command("importar_catalogo", stdout=io.StringIO())
                self.assertEqual(Artista.objects.count(), 13)
                self.assertEqual(Disco.objects.count(), 37)
                artista = Artista.objects.get(pk=1)
                self.assertEqual(artista.nombre, "System of a Down")
                self.assertEqual(Disco.objects.get(pk=1).titulo, "Toxicity")
                imagen_original = Path("static/img/artistas/system.jpg").read_bytes()
                self.assertEqual(Path(artista.imagen.path).read_bytes(), imagen_original)
                artista.bio = "Cambio conservado"
                artista.save()
                disco = Disco.objects.get(pk=1)
                disco.stock = 1
                disco.save()
                call_command("importar_catalogo", stdout=io.StringIO())
                artista.refresh_from_db()
                disco.refresh_from_db()
                self.assertEqual(artista.bio, "Cambio conservado")
                self.assertEqual(disco.stock, 1)
                self.assertEqual(len(list(Path(media).rglob("*.jpg"))), 50)

    def test_paginas_vacias_y_permiso_lectura(self):
        self.modelo_artista()
        usuario = User.objects.create_user("consulta", password="Prueba123!")
        usuario.user_permissions.add(*Permission.objects.filter(codename__in=["view_artista", "view_disco"]))
        for nombre in ["home", "artistas_inicio", "artistas_catalogo", "artistas_lista"]:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 302)
        self.client.force_login(usuario)
        for nombre in ["home", "artistas_inicio", "artistas_catalogo", "artistas_lista"]:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)
        self.assertEqual(self.client.get(reverse("artistas_crear")).status_code, 403)

    def test_alta_edicion_y_post_vacio_muestra_errores(self):
        Artista = self.modelo_artista()
        usuario = User.objects.create_user("admin", "admin@example.test", "Prueba123!", is_staff=True)
        usuario.user_permissions.add(*Permission.objects.filter(content_type__app_label="artistasApp"))
        self.client.force_login(usuario)
        respuesta = self.client.post(reverse("artistas_crear"), {})
        self.assertTrue(respuesta.context["form"].is_bound)
        self.assertIn("nombre", respuesta.context["form"].errors)
        datos = {"nombre": "Nuevo", "genero": "Rock", "pais": "Chile", "anio_formacion": 2000, "integrantes": 2, "bio": "Biografía"}
        self.assertEqual(self.client.post(reverse("artistas_crear"), datos).status_code, 302)
        artista = Artista.objects.get(nombre="Nuevo")
        respuesta = self.client.get(reverse("artistas_editar", args=[artista.pk]))
        self.assertEqual(respuesta.context["form"].initial["nombre"], "Nuevo")
        datos["nombre"] = "Editado"
        self.assertEqual(self.client.post(reverse("artistas_editar", args=[artista.pk]), datos).status_code, 302)
        artista.refresh_from_db()
        self.assertEqual(artista.nombre, "Editado")

    def test_eliminar_get_no_borra_y_post_respeta_protect(self):
        Artista = self.modelo_artista()
        from discosApp.models import Disco
        artista = Artista.objects.create(nombre="Protegido", genero="Rock", pais="Chile", anio_formacion=2000, integrantes=1, bio="Prueba")
        Disco.objects.create(titulo="Álbum", artista=artista, genero="Rock", anio=2020, formato="CD", precio=1000, stock=0)
        usuario = User.objects.create_user("admin", "admin@example.test", "Prueba123!", is_staff=True)
        usuario.user_permissions.add(*Permission.objects.filter(content_type__app_label="artistasApp"))
        self.client.force_login(usuario)
        url = reverse("artistas_eliminar", args=[artista.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Artista.objects.filter(pk=artista.pk).exists())
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertTrue(Artista.objects.filter(pk=artista.pk).exists())

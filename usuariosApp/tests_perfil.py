from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import IntegrityError
from django.test import Client as ClienteWeb, TestCase
from django.urls import reverse

from ventasApp.models import Cliente


class PerfilClienteTests(TestCase):
    perfil_url = "/cuentas/perfil/"
    password_url = "/cuentas/cambiar-contrasena/"
    clave_actual = "ClaveClienteActual_842"
    clave_nueva = "ClaveClienteActualizada_943"

    @classmethod
    def setUpTestData(cls):
        call_command("crear_perfiles", verbosity=0)
        cls.usuario = User.objects.create_user(
            username="cliente_perfil", password=cls.clave_actual,
            first_name="Cliente de prueba", email="cliente@example.com",
        )
        cls.usuario.groups.add(Group.objects.get(name="Cliente"))
        cls.cliente = Cliente.objects.create(
            usuario=cls.usuario, nombre="Cliente de prueba",
            correo="cliente@example.com", telefono="123456789",
        )
        cls.otro_usuario = User.objects.create_user(username="otro_cliente", password=cls.clave_actual)
        cls.otro_cliente = Cliente.objects.create(
            usuario=cls.otro_usuario, nombre="Otro cliente",
            correo="otro@example.com", telefono="987654321",
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def datos_perfil(self, **cambios):
        datos = {"nombre": "Cliente actualizado", "correo": "actualizado@example.com", "telefono": ""}
        datos.update(cambios)
        return datos

    def datos_password(self, **cambios):
        datos = {
            "old_password": self.clave_actual,
            "new_password1": self.clave_nueva,
            "new_password2": self.clave_nueva,
        }
        datos.update(cambios)
        return datos

    def test_perfil_muestra_solo_los_datos_del_cliente_actual(self):
        respuesta = self.client.get(self.perfil_url, {"cliente": self.otro_cliente.pk})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "cliente_perfil")
        self.assertContains(respuesta, 'value="Cliente de prueba"')
        self.assertContains(respuesta, 'value="cliente@example.com"')
        self.assertNotContains(respuesta, "otro@example.com")
        self.assertContains(respuesta, self.password_url)

    def test_perfil_actualiza_cliente_y_usuario_sin_aceptar_privilegios_ni_otro_id(self):
        datos = self.datos_perfil(
            usuario=self.otro_usuario.pk, cliente=self.otro_cliente.pk, username="nombre_alterado",
            is_staff="true", is_superuser="true", groups="Administrador",
        )
        respuesta = self.client.post(self.perfil_url + f"?cliente={self.otro_cliente.pk}", datos)
        self.assertRedirects(respuesta, self.perfil_url)
        self.cliente.refresh_from_db()
        self.usuario.refresh_from_db()
        self.otro_cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, "Cliente actualizado")
        self.assertEqual(self.cliente.correo, "actualizado@example.com")
        self.assertEqual(self.cliente.telefono, "")
        self.assertEqual(self.cliente.usuario_id, self.usuario.pk)
        self.assertEqual(self.usuario.first_name, self.cliente.nombre)
        self.assertEqual(self.usuario.email, self.cliente.correo)
        self.assertEqual(self.usuario.username, "cliente_perfil")
        self.assertFalse(self.usuario.is_staff)
        self.assertFalse(self.usuario.is_superuser)
        self.assertEqual(list(self.usuario.groups.values_list("name", flat=True)), ["Cliente"])
        usuario_actualizado = User.objects.get(pk=self.usuario.pk)
        self.assertEqual(usuario_actualizado.get_all_permissions(), {
            "artistasApp.view_artista", "discosApp.view_disco",
        })
        self.assertEqual(self.otro_cliente.correo, "otro@example.com")

    def test_correo_invalido_no_actualiza_ninguno_de_los_dos_registros(self):
        respuesta = self.client.post(self.perfil_url, self.datos_perfil(correo="correo-invalido"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("correo", respuesta.context["form"].errors)
        self.cliente.refresh_from_db()
        self.usuario.refresh_from_db()
        self.assertEqual(self.cliente.nombre, "Cliente de prueba")
        self.assertEqual(self.cliente.correo, "cliente@example.com")
        self.assertEqual(self.usuario.first_name, "Cliente de prueba")
        self.assertEqual(self.usuario.email, "cliente@example.com")

    def test_error_al_guardar_usuario_revierte_los_cambios_del_cliente(self):
        with patch.object(User, "save", side_effect=IntegrityError("Fallo de prueba")):
            with self.assertRaises(IntegrityError):
                self.client.post(self.perfil_url, self.datos_perfil())
        self.cliente.refresh_from_db()
        self.usuario.refresh_from_db()
        self.assertEqual(self.cliente.correo, "cliente@example.com")
        self.assertEqual(self.usuario.email, "cliente@example.com")

    def test_anonimo_debe_iniciar_sesion(self):
        self.client.logout()
        for ruta in [self.perfil_url, self.password_url]:
            with self.subTest(ruta=ruta):
                self.assertRedirects(self.client.get(ruta), reverse("login") + "?next=" + ruta)

    def test_otros_perfiles_sin_cliente_vinculado_no_entran(self):
        for perfil in ["Administrador", "Operador", "Consulta", "Cliente"]:
            with self.subTest(perfil=perfil):
                usuario = User.objects.create_user(username=f"sin_cliente_{perfil}")
                usuario.groups.add(Group.objects.get(name=perfil))
                self.client.force_login(usuario)
                for ruta in [self.perfil_url, self.password_url]:
                    self.assertEqual(self.client.get(ruta).status_code, 403)
                    self.assertEqual(self.client.post(ruta, {}).status_code, 403)

    def test_formulario_de_contrasena_y_cambio_valido_conservan_sesion(self):
        respuesta = self.client.get(self.password_url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'name="old_password"')
        self.assertContains(respuesta, 'name="new_password1"')
        self.assertContains(respuesta, self.perfil_url)
        respuesta = self.client.post(self.password_url, self.datos_password())
        self.assertRedirects(respuesta, self.perfil_url)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(self.clave_nueva))
        self.assertFalse(self.usuario.check_password(self.clave_actual))
        self.assertEqual(self.client.session["_auth_user_id"], str(self.usuario.pk))
        self.assertEqual(self.client.session["_auth_user_hash"], self.usuario.get_session_auth_hash())
        self.assertEqual(self.client.get(self.perfil_url).status_code, 200)
        self.assertFalse(self.client.login(username="cliente_perfil", password=self.clave_actual))
        self.assertTrue(self.client.login(username="cliente_perfil", password=self.clave_nueva))

    def test_contrasena_actual_erronea_no_cambia_la_clave(self):
        respuesta = self.client.post(self.password_url, self.datos_password(old_password="OtraClave_943"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("old_password", respuesta.context["form"].errors)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(self.clave_actual))

    def test_contrasenas_distintas_no_cambian_la_clave(self):
        respuesta = self.client.post(self.password_url, self.datos_password(new_password2="OtraNuevaClave_944"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("new_password2", respuesta.context["form"].errors)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(self.clave_actual))

    def test_contrasena_debil_no_cambia_la_clave(self):
        respuesta = self.client.post(self.password_url, self.datos_password(new_password1="123", new_password2="123"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("new_password2", respuesta.context["form"].errors)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(self.clave_actual))

    def test_post_sin_csrf_no_puede_actualizar_perfil_ni_contrasena(self):
        cliente_web = ClienteWeb(enforce_csrf_checks=True)
        cliente_web.force_login(self.usuario)
        self.assertEqual(cliente_web.post(self.perfil_url, self.datos_perfil()).status_code, 403)
        self.assertEqual(cliente_web.post(self.password_url, self.datos_password()).status_code, 403)
        respuesta = cliente_web.get(self.perfil_url)
        self.assertEqual(respuesta.status_code, 200)
        datos = self.datos_perfil(csrfmiddlewaretoken=cliente_web.cookies["csrftoken"].value)
        self.assertEqual(cliente_web.post(self.perfil_url, datos).status_code, 302)

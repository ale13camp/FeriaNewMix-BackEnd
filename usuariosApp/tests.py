from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch

from ventasApp.models import Cliente


class PerfilesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("crear_perfiles", verbosity=0)

    def test_crear_perfiles_se_puede_repetir(self):
        permisos = {g.name: set(g.permissions.values_list("pk", flat=True)) for g in Group.objects.all()}
        call_command("crear_perfiles", verbosity=0)
        self.assertEqual(Group.objects.count(), 4)
        for grupo in Group.objects.all():
            self.assertEqual(set(grupo.permissions.values_list("pk", flat=True)), permisos[grupo.name])

    def test_permisos_de_los_tres_perfiles(self):
        for nombre, acciones in {
            "Administrador": {"add", "change", "delete", "view"},
            "Operador": {"add", "change", "view"},
            "Consulta": {"view"},
        }.items():
            usuario = User.objects.create_user(username=nombre)
            usuario.groups.add(Group.objects.get(name=nombre))
            for app, modelo in [("artistasApp", "artista"), ("discosApp", "disco"), ("ventasApp", "cliente"), ("ventasApp", "venta")]:
                for accion in ["add", "change", "delete", "view"]:
                    self.assertEqual(usuario.has_perm(f"{app}.{accion}_{modelo}"), accion in acciones)
            self.assertEqual(usuario.has_perm("auth.change_user"), nombre == "Administrador")

    def test_inicio_de_sesion_y_logout_por_post_con_csrf(self):
        usuario = User.objects.create_user(username="sesion", password="ClaveSoloParaPrueba_48")
        usuario.groups.add(Group.objects.get(name="Consulta"))
        cliente = Client(enforce_csrf_checks=True)
        respuesta = cliente.get(reverse("login"))
        self.assertEqual(respuesta.status_code, 200)
        token = cliente.cookies["csrftoken"].value
        self.assertEqual(cliente.post(reverse("login"), {"username": "sesion", "password": "ClaveSoloParaPrueba_48", "csrfmiddlewaretoken": token}).status_code, 302)
        self.assertEqual(cliente.get(reverse("home")).status_code, 200)
        self.assertEqual(cliente.get(reverse("logout")).status_code, 405)
        self.assertEqual(cliente.post(reverse("logout")).status_code, 403)
        token = cliente.cookies["csrftoken"].value
        self.assertEqual(cliente.post(reverse("logout"), {"csrfmiddlewaretoken": token}).status_code, 302)
        respuesta = cliente.get(reverse("home"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Registrarme como cliente")

    def test_consulta_no_ve_botones_para_escribir(self):
        usuario = User.objects.create_user(username="lector")
        usuario.groups.add(Group.objects.get(name="Consulta"))
        self.client.force_login(usuario)
        for listado, alta in [("artistas_lista", "artistas_crear"), ("discos_lista", "discos_crear"), ("clientes_lista", "clientes_crear"), ("ventas_lista", "ventas_crear")]:
            respuesta = self.client.get(reverse(listado))
            self.assertEqual(respuesta.status_code, 200)
            self.assertNotContains(respuesta, 'href="' + reverse(alta) + '"')
            self.assertEqual(self.client.post(reverse(alta), {}).status_code, 403)

    def test_operador_no_entra_a_gestion_de_usuarios(self):
        usuario = User.objects.create_user(username="operador")
        usuario.groups.add(Group.objects.get(name="Operador"))
        self.client.force_login(usuario)
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 302)


class RegistroClienteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("crear_perfiles", verbosity=0)

    def datos_registro(self, **cambios):
        datos = {
            "username": "cliente_nuevo",
            "nombre": "Cliente de prueba",
            "correo": "cliente@example.com",
            "telefono": "",
            "password1": "ClaveRegistroParaPrueba_842",
            "password2": "ClaveRegistroParaPrueba_842",
        }
        datos.update(cambios)
        return datos

    def test_registro_publico_muestra_formulario(self):
        respuesta = self.client.get(reverse("registro"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'name="username"')
        self.assertContains(respuesta, 'name="correo"')

    def test_registro_crea_cliente_e_inicia_sesion_sin_permisos_de_gestion(self):
        respuesta = self.client.post(reverse("registro"), self.datos_registro(
            is_staff="true", is_superuser="true", groups="Administrador"
        ))
        self.assertRedirects(respuesta, reverse("home"))
        usuario = User.objects.get(username="cliente_nuevo")
        cliente = Cliente.objects.get(usuario=usuario)
        self.assertEqual(cliente.nombre, "Cliente de prueba")
        self.assertEqual(cliente.correo, "cliente@example.com")
        self.assertEqual(cliente.telefono, "")
        self.assertEqual(usuario.email, cliente.correo)
        self.assertTrue(usuario.check_password("ClaveRegistroParaPrueba_842"))
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(list(usuario.groups.values_list("name", flat=True)), ["Cliente"])
        self.assertEqual(usuario.get_all_permissions(), {
            "artistasApp.view_artista", "discosApp.view_disco",
        })
        self.assertEqual(self.client.session["_auth_user_id"], str(usuario.pk))
        self.assertEqual(self.client.get(reverse("ventas_lista")).status_code, 403)
        self.assertEqual(self.client.get(reverse("clientes_lista")).status_code, 403)

    def test_contrasenas_distintas_no_crean_usuario_ni_cliente(self):
        respuesta = self.client.post(reverse("registro"), self.datos_registro(password2="OtraClave_843"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("password2", respuesta.context["form"].errors)
        self.assertFalse(User.objects.filter(username="cliente_nuevo").exists())
        self.assertEqual(Cliente.objects.count(), 0)

    def test_contrasena_debil_no_crea_usuario(self):
        respuesta = self.client.post(reverse("registro"), self.datos_registro(password1="123", password2="123"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("password2", respuesta.context["form"].errors)
        self.assertFalse(User.objects.filter(username="cliente_nuevo").exists())
        self.assertEqual(Cliente.objects.count(), 0)

    def test_usuario_repetido_no_crea_otro_cliente(self):
        User.objects.create_user(username="cliente_nuevo")
        respuesta = self.client.post(reverse("registro"), self.datos_registro())
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("username", respuesta.context["form"].errors)
        self.assertEqual(User.objects.filter(username="cliente_nuevo").count(), 1)
        self.assertEqual(Cliente.objects.count(), 0)

    def test_cliente_existente_puede_seguir_sin_cuenta(self):
        cliente = Cliente.objects.create(nombre="Cliente anterior", correo="anterior@example.com")
        self.assertIsNone(cliente.usuario)
        usuario = User.objects.create_user(username="cuenta_borrada")
        cliente.usuario = usuario
        cliente.save()
        usuario.delete()
        cliente.refresh_from_db()
        self.assertIsNone(cliente.usuario)

    def test_usuario_autenticado_regresa_al_inicio(self):
        usuario = User.objects.create_user(username="sesion_cliente")
        self.client.force_login(usuario)
        self.assertRedirects(self.client.get(reverse("registro")), reverse("home"))

    def test_error_al_crear_cliente_no_deja_una_cuenta_huerfana(self):
        with patch("usuariosApp.views.Cliente.objects.create", side_effect=IntegrityError("Fallo de prueba")):
            with self.assertRaises(IntegrityError):
                self.client.post(reverse("registro"), self.datos_registro())
        self.assertFalse(User.objects.filter(username="cliente_nuevo").exists())
        self.assertEqual(Cliente.objects.count(), 0)

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse


class PerfilesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("crear_perfiles", verbosity=0)

    def test_crear_perfiles_se_puede_repetir(self):
        permisos = {g.name: set(g.permissions.values_list("pk", flat=True)) for g in Group.objects.all()}
        call_command("crear_perfiles", verbosity=0)
        self.assertEqual(Group.objects.count(), 3)
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
        self.assertRedirects(cliente.get(reverse("home")), reverse("login") + "?next=/")

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

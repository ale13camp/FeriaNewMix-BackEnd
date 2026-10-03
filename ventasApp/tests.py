from decimal import Decimal
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from artistasApp.models import Artista
from discosApp.models import Disco
from .admin import VentaAdmin
from .forms import ClienteForm, VentaForm
from .models import Cliente, Venta


class DatosVentas(TestCase):
    def setUp(self):
        self.artista = Artista.objects.create(nombre="Artista de prueba", genero="Rock", pais="Chile",
                                              anio_formacion=2000, integrantes=1, bio="Prueba")
        self.disco = Disco.objects.create(
            artista=self.artista, titulo="Álbum de prueba", genero="Rock", anio=2020,
            formato="CD", precio=12000, stock=8
        )
        self.otro = Disco.objects.create(
            artista=self.artista, titulo="Otro álbum", genero="Rock", anio=2020,
            formato="CD", precio=15000, stock=3
        )
        self.comprador = Cliente.objects.create(nombre="Cliente de prueba", correo="prueba@example.com")

    def venta(self, cantidad=2, disco=None):
        return Venta.objects.create(
            cliente=self.comprador, disco=disco or self.disco,
            cantidad=cantidad, precio_unitario=12000, fecha="2026-10-02"
        )

    def stock(self, disco):
        disco.refresh_from_db()
        return disco.stock


class StockTests(DatosVentas):
    def test_crear_descuenta_stock_y_conserva_precio_historico(self):
        venta = self.venta(3)
        self.assertEqual(self.stock(self.disco), 5)
        self.assertEqual(venta.total, Decimal("36000"))
        self.disco.precio = 17000
        self.disco.save()
        venta.refresh_from_db()
        self.assertEqual(venta.precio_unitario, Decimal("12000"))

    def test_editar_cantidad_aplica_solo_diferencia(self):
        venta = self.venta(3)
        venta.cantidad = 5
        venta.save()
        self.assertEqual(self.stock(self.disco), 3)
        venta.cantidad = 1
        venta.save()
        self.assertEqual(self.stock(self.disco), 7)

    def test_editar_cambia_disco_y_devuelve_stock_anterior(self):
        venta = self.venta(3)
        venta.disco = self.otro
        venta.cantidad = 2
        venta.save()
        self.assertEqual(self.stock(self.disco), 8)
        self.assertEqual(self.stock(self.otro), 1)

    def test_stock_insuficiente_no_crea_venta(self):
        with self.assertRaises(ValidationError):
            self.venta(9)
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(self.stock(self.disco), 8)

    def test_edicion_insuficiente_no_devuelve_stock_parcial(self):
        venta = self.venta(3)
        venta.disco = self.otro
        venta.cantidad = 4
        with self.assertRaises(ValidationError):
            venta.save()
        venta.refresh_from_db()
        self.assertEqual(venta.disco_id, self.disco.pk)
        self.assertEqual(venta.cantidad, 3)
        self.assertEqual(self.stock(self.disco), 5)
        self.assertEqual(self.stock(self.otro), 3)

    def test_guardar_objeto_antiguo_usa_cantidad_actual_de_bd(self):
        venta = self.venta(2)
        antigua = Venta.objects.get(pk=venta.pk)
        venta.cantidad = 4
        venta.save()
        antigua.cantidad = 3
        antigua.save()
        self.assertEqual(self.stock(self.disco), 5)

    def test_eliminar_devuelve_stock_y_objeto_antiguo_no_duplica(self):
        venta = self.venta(2)
        antigua = Venta.objects.get(pk=venta.pk)
        venta.delete()
        antigua.delete()
        self.assertEqual(self.stock(self.disco), 8)

    def test_admin_guardado_y_borrado_individual_ajustan_stock(self):
        administrador = VentaAdmin(Venta, AdminSite())
        request = RequestFactory().get("/admin/")
        venta = Venta(cliente=self.comprador, disco=self.disco, cantidad=2, precio_unitario=12000)
        administrador.save_model(request, venta, None, False)
        self.assertEqual(self.stock(self.disco), 6)
        self.assertEqual(administrador.get_actions(request), {})
        administrador.delete_model(request, venta)
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(self.stock(self.disco), 8)

    def test_cliente_y_disco_con_ventas_estan_protegidos(self):
        self.venta()
        with self.assertRaises(ProtectedError):
            self.comprador.delete()
        with self.assertRaises(ProtectedError):
            self.disco.delete()

    def test_no_permite_cantidad_o_precio_cero(self):
        for campo in ("cantidad", "precio_unitario"):
            venta = Venta(cliente=self.comprador, disco=self.disco, cantidad=1, precio_unitario=12000)
            setattr(venta, campo, 0)
            with self.assertRaises(ValidationError):
                venta.save()
        self.assertEqual(self.stock(self.disco), 8)

    def test_guardado_parcial_se_rechaza_para_evitar_desajuste(self):
        venta = self.venta(2)
        venta.cantidad = 4
        with self.assertRaises(ValidationError):
            venta.save(update_fields=["precio_unitario"])
        venta.refresh_from_db()
        self.assertEqual(venta.cantidad, 2)
        self.assertEqual(self.stock(self.disco), 6)


class FormulariosTests(DatosVentas):
    def datos(self, cantidad=2):
        return {"cliente": self.comprador.pk, "disco": self.disco.pk,
                "fecha": "2026-10-02", "cantidad": cantidad, "precio_unitario": "12000"}

    def test_stock_insuficiente_aparece_como_error_de_cantidad(self):
        formulario = VentaForm(self.datos(9))
        self.assertFalse(formulario.is_valid())
        self.assertIn("cantidad", formulario.errors)
        self.assertEqual(Venta.objects.count(), 0)

    def test_formulario_editar_incluye_unidades_ya_vendidas(self):
        venta = self.venta(7)
        formulario = VentaForm(self.datos(8), instance=venta)
        self.assertTrue(formulario.is_valid(), formulario.errors)
        formulario.save()
        self.assertEqual(self.stock(self.disco), 0)

    def test_correo_invalido_y_telefono_opcional(self):
        self.assertFalse(ClienteForm({"nombre": "Cliente", "correo": "incorrecto"}).is_valid())
        self.assertTrue(ClienteForm({"nombre": "Cliente", "correo": "a@example.com"}).is_valid())

    def test_fecha_y_cantidad_son_obligatorios_y_cantidad_entera(self):
        for campo, valor in (("fecha", ""), ("cantidad", ""), ("cantidad", "1.5")):
            datos = self.datos()
            datos[campo] = valor
            formulario = VentaForm(datos)
            self.assertFalse(formulario.is_valid())
            self.assertIn(campo, formulario.errors)

    def test_precio_inicial_corresponde_al_disco_seleccionado(self):
        formulario = VentaForm(initial={"disco": self.otro.pk})
        self.assertEqual(formulario["precio_unitario"].value(), Decimal("15000"))

    def test_precio_se_obtiene_del_catalogo_sin_confiar_en_el_post(self):
        for precio_enviado in (None, "1", "incorrecto"):
            with self.subTest(precio=precio_enviado):
                datos = self.datos(1)
                datos.pop("precio_unitario")
                if precio_enviado is not None:
                    datos["precio_unitario"] = precio_enviado
                formulario = VentaForm(datos)
                self.assertTrue(formulario.is_valid(), formulario.errors)
                venta = formulario.save()
                self.assertEqual(venta.precio_unitario, Decimal("12000"))

    def test_editar_mismo_disco_conserva_precio_historico(self):
        venta = self.venta()
        self.disco.precio = 17000
        self.disco.save()
        datos = self.datos(3)
        datos["precio_unitario"] = "1"
        formulario = VentaForm(datos, instance=venta)
        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertEqual(formulario.save().precio_unitario, Decimal("12000"))

    def test_editar_otro_disco_toma_su_precio_y_ajusta_stock(self):
        venta = self.venta()
        datos = self.datos(1)
        datos["disco"] = self.otro.pk
        formulario = VentaForm(datos, instance=venta)
        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertEqual(formulario.save().precio_unitario, Decimal("15000"))
        self.assertEqual(self.stock(self.disco), 8)
        self.assertEqual(self.stock(self.otro), 2)

    def test_disco_invalido_muestra_error_sin_crear_venta(self):
        datos = self.datos()
        datos["disco"] = "no-existe"
        formulario = VentaForm(datos)
        self.assertFalse(formulario.is_valid())
        self.assertIn("disco", formulario.errors)
        self.assertEqual(Venta.objects.count(), 0)


class AdminTests(DatosVentas):
    def setUp(self):
        super().setUp()
        self.usuario = User.objects.create_superuser("supervisor", "supervisor@example.com", "clave-de-prueba")
        self.client.force_login(self.usuario)

    def datos(self, cantidad):
        return {"cliente": self.comprador.pk, "disco": self.disco.pk,
                "fecha": "2026-10-02", "cantidad": cantidad, "precio_unitario": "12000", "_save": "Guardar"}

    def test_admin_formulario_rechaza_stock_insuficiente(self):
        respuesta = self.client.post(reverse("admin:ventasApp_venta_add"), self.datos(9))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("cantidad", respuesta.context["adminform"].form.errors)
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(self.stock(self.disco), 8)

    def test_admin_crea_venta_con_precio_del_disco_sin_precio_manual(self):
        datos = self.datos(1)
        datos.pop("precio_unitario")
        respuesta = self.client.post(reverse("admin:ventasApp_venta_add"), datos)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Venta.objects.get().precio_unitario, Decimal("12000"))

    def test_admin_error_tardio_da_mensaje_y_no_error_500(self):
        # Inyecta el error que puede llegar al guardar tras otra venta concurrente.
        self.client.raise_request_exception = False
        with patch.object(Venta, "save", side_effect=ValidationError({"cantidad": "Stock insuficiente."})):
            respuesta = self.client.post(reverse("admin:ventasApp_venta_add"), self.datos(2))
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(self.stock(self.disco), 8)
        respuesta = self.client.get(respuesta.url)
        self.assertContains(respuesta, "Stock insuficiente")


class VistasTests(DatosVentas):
    def setUp(self):
        super().setUp()
        self.consulta = self.usuario("Consulta", ("view",))
        self.operador = self.usuario("Operador", ("view", "add", "change"))
        self.administrador = self.usuario("Administrador", ("view", "add", "change", "delete"))

    def usuario(self, nombre, acciones):
        grupo = Group.objects.create(name=nombre)
        grupo.permissions.set(Permission.objects.filter(
            content_type__app_label="ventasApp",
            codename__in=[f"{accion}_{modelo}" for accion in acciones for modelo in ("cliente", "venta")],
        ))
        usuario = User.objects.create_user(username=nombre)
        usuario.groups.add(grupo)
        return usuario

    def datos_venta(self, cantidad=2):
        return {"cliente": self.comprador.pk, "disco": self.disco.pk, "fecha": "2026-10-02",
                "cantidad": cantidad, "precio_unitario": "12000"}

    def test_rutas_clientes_y_ventas_exigen_inicio_de_sesion(self):
        for url in ("/ventas/", "/ventas/clientes/"):
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_listas_sin_clientes_o_ventas(self):
        self.comprador.delete()
        self.client.force_login(self.consulta)
        self.assertContains(self.client.get(reverse("clientes_lista")), "No hay clientes")
        self.assertContains(self.client.get(reverse("ventas_lista")), "No hay ventas")

    def test_anonimo_redirige_login_en_todas_las_rutas(self):
        venta = self.venta()
        rutas = [("clientes_lista", None), ("clientes_crear", None), ("clientes_editar", self.comprador.pk),
                 ("clientes_eliminar", self.comprador.pk), ("ventas_lista", None), ("ventas_crear", None),
                 ("ventas_editar", venta.pk), ("ventas_eliminar", venta.pk)]
        for nombre, pk in rutas:
            with self.subTest(nombre=nombre):
                url = reverse(nombre, args=[pk] if pk else [])
                self.assertEqual(self.client.get(url).status_code, 302)
                self.assertEqual(self.client.post(url, {}).status_code, 302)

    def test_consulta_ve_listas_y_no_puede_escribir(self):
        venta = self.venta()
        self.client.force_login(self.consulta)
        for modelo, pk in (("clientes", self.comprador.pk), ("ventas", venta.pk)):
            lista = self.client.get(reverse(f"{modelo}_lista"))
            self.assertEqual(lista.status_code, 200)
            self.assertNotContains(lista, reverse(f"{modelo}_crear"))
            for accion in ("crear", "editar", "eliminar"):
                url = reverse(f"{modelo}_{accion}", args=[pk] if accion != "crear" else [])
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_operador_crea_edita_pero_no_elimina(self):
        self.client.force_login(self.operador)
        respuesta = self.client.post(reverse("ventas_crear"), self.datos_venta(3))
        self.assertRedirects(respuesta, reverse("ventas_lista"))
        venta = Venta.objects.get()
        formulario = self.client.get(reverse("ventas_editar", args=[venta.pk])).context["form"]
        self.assertEqual(formulario.instance.pk, venta.pk)
        self.assertEqual(formulario.initial["cantidad"], 3)
        self.assertRedirects(self.client.post(reverse("ventas_editar", args=[venta.pk]), self.datos_venta(4)), reverse("ventas_lista"))
        self.assertEqual(self.stock(self.disco), 4)
        self.assertEqual(self.client.post(reverse("ventas_eliminar", args=[venta.pk])).status_code, 403)

    def test_error_stock_muestra_formulario_sin_mutaciones(self):
        self.client.force_login(self.operador)
        respuesta = self.client.post(reverse("ventas_crear"), self.datos_venta(9))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("cantidad", respuesta.context["form"].errors)
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(self.stock(self.disco), 8)

    def test_registrar_precarga_disco_y_precio_desde_su_ficha(self):
        self.client.force_login(self.operador)
        respuesta = self.client.get(reverse("ventas_crear"), {"disco": self.otro.pk})
        self.assertEqual(str(respuesta.context["form"]["disco"].value()), str(self.otro.pk))
        self.assertEqual(respuesta.context["form"]["precio_unitario"].value(), Decimal("15000"))

    def test_error_stock_conserva_precio_del_disco_sin_guardar(self):
        self.client.force_login(self.operador)
        datos = self.datos_venta(9)
        datos["precio_unitario"] = "1"
        respuesta = self.client.post(reverse("ventas_crear"), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("cantidad", respuesta.context["form"].errors)
        self.assertEqual(respuesta.context["form"]["precio_unitario"].value(), Decimal("12000"))
        self.assertEqual(Venta.objects.count(), 0)

    def test_borrado_venta_solo_post_y_restituye_stock(self):
        venta = self.venta()
        self.client.force_login(self.administrador)
        url = reverse("ventas_eliminar", args=[venta.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Venta.objects.filter(pk=venta.pk).exists())
        self.assertRedirects(self.client.post(url), reverse("ventas_lista"))
        self.assertEqual(self.stock(self.disco), 8)

    def test_cliente_crud_y_proteccion_borrado(self):
        self.client.force_login(self.administrador)
        self.assertRedirects(self.client.post(reverse("clientes_crear"), {"nombre": "Nuevo", "correo": "nuevo@example.com"}), reverse("clientes_lista"))
        nuevo = Cliente.objects.get(correo="nuevo@example.com")
        self.assertRedirects(self.client.post(reverse("clientes_editar", args=[nuevo.pk]), {"nombre": "Editado", "correo": "nuevo@example.com", "telefono": "123"}), reverse("clientes_lista"))
        nuevo.refresh_from_db()
        self.assertEqual(nuevo.nombre, "Editado")
        self.assertEqual(self.client.get(reverse("clientes_eliminar", args=[nuevo.pk])).status_code, 200)
        self.assertTrue(Cliente.objects.filter(pk=nuevo.pk).exists())
        self.assertRedirects(self.client.post(reverse("clientes_eliminar", args=[nuevo.pk])), reverse("clientes_lista"))
        self.venta()
        respuesta = self.client.post(reverse("clientes_eliminar", args=[self.comprador.pk]), follow=True)
        self.assertTrue(Cliente.objects.filter(pk=self.comprador.pk).exists())
        self.assertTrue(list(respuesta.context["messages"]))

    def test_busquedas_y_filtro_fecha(self):
        venta = self.venta()
        self.client.force_login(self.consulta)
        for q in ("Cliente", "prueba@example.com", "Álbum", "Artista"):
            respuesta = self.client.get(reverse("ventas_lista"), {"q": q, "fecha": "2026-10-02"})
            self.assertContains(respuesta, "Álbum de prueba")
            self.assertIn(venta, respuesta.context["ventas"])
        respuesta = self.client.get(reverse("ventas_lista"), {"fecha": "2026-10-03"})
        self.assertEqual(list(respuesta.context["ventas"]), [])
        respuesta = self.client.get(reverse("ventas_lista"), {"fecha": "no-es-fecha"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(list(respuesta.context["messages"]))
        self.assertIn(self.comprador, self.client.get(reverse("clientes_lista"), {"q": "prueba@example.com"}).context["clientes"])
        self.assertEqual(list(self.client.get(reverse("clientes_lista"), {"q": "ausente"}).context["clientes"]), [])

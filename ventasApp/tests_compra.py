from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from artistasApp.models import Artista
from discosApp.models import Disco
from .models import Cliente, Venta


class ComprasClienteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        artista = Artista.objects.create(
            nombre="Artista de prueba", genero="Rock", pais="Chile",
            anio_formacion=2000, integrantes=1, bio="Prueba técnica",
        )
        cls.disco = Disco.objects.create(
            artista=artista, titulo="Disco de prueba", genero="Rock", anio=2020,
            formato="CD", precio=21990, stock=6,
        )
        cls.otro_disco = Disco.objects.create(
            artista=artista, titulo="Otro disco de prueba", genero="Rock", anio=2021,
            formato="CD", precio=15000, stock=4,
        )
        cls.usuario = User.objects.create_user("comprador_prueba", password="ClaveTest123!")
        cls.comprador = Cliente.objects.create(
            usuario=cls.usuario, nombre="Comprador de prueba", correo="comprador@example.com",
        )
        cls.otro_usuario = User.objects.create_user("otro_comprador", password="ClaveTest123!")
        cls.otro_cliente = Cliente.objects.create(
            usuario=cls.otro_usuario, nombre="Otro comprador", correo="otro@example.com",
        )
        cls.operador = User.objects.create_user("operador_prueba", password="ClaveTest123!")

    def setUp(self):
        self.url = reverse("compra_crear", args=[self.disco.pk])
        self.client.force_login(self.usuario)

    def comprobar_sin_compra(self, stock=6):
        self.disco.refresh_from_db()
        self.assertEqual(self.disco.stock, stock)
        self.assertEqual(Venta.objects.count(), 0)

    def test_get_muestra_precio_cantidad_y_no_registra_venta(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["disco"].precio, Decimal("21990"))
        self.assertEqual(respuesta.context["form"].initial["cantidad"], 1)
        self.assertEqual(respuesta.context["total"], Decimal("21990"))
        self.comprobar_sin_compra()

    def test_post_registra_compra_propietario_fecha_precio_y_descuenta_stock(self):
        respuesta = self.client.post(self.url, {"cantidad": 2})
        self.assertRedirects(respuesta, reverse("compras_lista"))
        compra = Venta.objects.get()
        self.assertEqual(compra.cliente, self.comprador)
        self.assertEqual(compra.disco, self.disco)
        self.assertEqual(compra.fecha, timezone.localdate())
        self.assertEqual(compra.cantidad, 2)
        self.assertEqual(compra.precio_unitario, Decimal("21990"))
        self.assertEqual(compra.total, Decimal("43980"))
        self.disco.refresh_from_db()
        self.assertEqual(self.disco.stock, 4)

    def test_post_ignora_cliente_disco_precio_y_fecha_enviados(self):
        respuesta = self.client.post(self.url, {
            "cantidad": 1, "cliente": self.otro_cliente.pk, "disco": self.otro_disco.pk,
            "precio_unitario": 1, "fecha": "2000-01-01",
        })
        self.assertEqual(respuesta.status_code, 302)
        compra = Venta.objects.get()
        self.assertEqual(compra.cliente, self.comprador)
        self.assertEqual(compra.disco, self.disco)
        self.assertEqual(compra.precio_unitario, Decimal("21990"))
        self.assertEqual(compra.fecha, timezone.localdate())
        self.otro_disco.refresh_from_db()
        self.assertEqual(self.otro_disco.stock, 4)

    def test_compra_usa_precio_actual_al_confirmar(self):
        self.client.get(self.url)
        Disco.objects.filter(pk=self.disco.pk).update(precio=25000)
        respuesta = self.client.post(self.url, {"cantidad": 1})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Venta.objects.get().precio_unitario, Decimal("25000"))

    def test_cantidad_invalida_no_crea_venta(self):
        for cantidad in ["", "0", "-1", "1.5", "abc", "2147483648"]:
            with self.subTest(cantidad=cantidad):
                respuesta = self.client.post(self.url, {"cantidad": cantidad})
                self.assertEqual(respuesta.status_code, 200)
                self.assertIn("cantidad", respuesta.context["form"].errors)
                self.comprobar_sin_compra()

    def test_stock_insuficiente_muestra_error_y_total_sin_crear(self):
        respuesta = self.client.post(self.url, {"cantidad": 7})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Stock insuficiente")
        self.assertEqual(respuesta.context["total"], Decimal("153930"))
        self.comprobar_sin_compra()

    def test_stock_agotado_no_permite_confirmar(self):
        Disco.objects.filter(pk=self.disco.pk).update(stock=0)
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "Sin stock disponible")
        respuesta = self.client.post(self.url, {"cantidad": 1})
        self.assertEqual(respuesta.status_code, 200)
        self.comprobar_sin_compra(stock=0)

    def test_anonimo_debe_iniciar_sesion(self):
        self.client.logout()
        for metodo in [self.client.get, self.client.post]:
            respuesta = metodo(self.url)
            self.assertEqual(respuesta.status_code, 302)
            self.assertIn(reverse("login"), respuesta.url)
        self.assertEqual(self.client.get(reverse("compras_lista")).status_code, 302)
        self.comprobar_sin_compra()

    def test_usuario_sin_cliente_recibe_403(self):
        self.client.force_login(self.operador)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, {"cantidad": 1}).status_code, 403)
        self.assertEqual(self.client.get(reverse("compras_lista")).status_code, 403)
        self.comprobar_sin_compra()

    def test_historial_muestra_solo_compras_del_usuario(self):
        propia = Venta.objects.create(
            cliente=self.comprador, disco=self.disco, cantidad=1, precio_unitario=21990,
        )
        Venta.objects.create(
            cliente=self.otro_cliente, disco=self.otro_disco, cantidad=2, precio_unitario=15000,
        )
        respuesta = self.client.get(reverse("compras_lista"), {"cliente": self.otro_cliente.pk})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(list(respuesta.context["compras"]), [propia])
        self.assertContains(respuesta, self.disco.titulo)
        self.assertNotContains(respuesta, self.otro_disco.titulo)

    def test_cliente_no_accede_a_ventas_globales(self):
        self.assertEqual(self.client.get(reverse("ventas_lista")).status_code, 403)
        self.assertEqual(self.client.get(reverse("ventas_crear")).status_code, 403)

    def test_disco_inexistente_devuelve_404(self):
        self.assertEqual(self.client.get(reverse("compra_crear", args=[999999])).status_code, 404)

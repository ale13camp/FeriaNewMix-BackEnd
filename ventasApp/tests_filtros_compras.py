from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from artistasApp.models import Artista
from discosApp.models import Disco
from .models import Cliente, Venta


class FiltrosMisComprasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        artista = Artista.objects.create(
            nombre="Artista de prueba", genero="Rock", pais="Chile",
            anio_formacion=2000, integrantes=1, bio="Prueba técnica",
        )
        cls.discos = []
        for titulo in ["AM", "AM en directo", "Otro álbum"]:
            cls.discos.append(Disco.objects.create(
                artista=artista, titulo=titulo, genero="Rock", anio=2020,
                formato="CD", precio=21990, stock=20,
            ))
        cls.discos[0].imagen = "discos/portada_prueba.jpg"
        cls.discos[0].save()
        cls.usuario = User.objects.create_user("cliente_filtros")
        cls.cliente = Cliente.objects.create(
            usuario=cls.usuario, nombre="Cliente de prueba", correo="cliente@example.com",
        )
        cls.otro_usuario = User.objects.create_user("otro_cliente_filtros")
        cls.otro_cliente = Cliente.objects.create(
            usuario=cls.otro_usuario, nombre="Otro cliente", correo="otro@example.com",
        )
        cls.usuario_sin_compras = User.objects.create_user("cliente_sin_compras")
        Cliente.objects.create(
            usuario=cls.usuario_sin_compras, nombre="Sin compras", correo="sincompras@example.com",
        )
        cls.compras = []
        for disco, fecha in zip(cls.discos, [date(2026, 9, 1), date(2026, 10, 3), date(2026, 10, 4)]):
            cls.compras.append(Venta.objects.create(
                cliente=cls.cliente, disco=disco, fecha=fecha, cantidad=1, precio_unitario=disco.precio,
            ))
        cls.compra_ajena = Venta.objects.create(
            cliente=cls.otro_cliente, disco=cls.discos[0], fecha=date(2026, 10, 3),
            cantidad=2, precio_unitario=cls.discos[0].precio,
        )

    def setUp(self):
        self.url = reverse("compras_lista")
        self.client.force_login(self.usuario)

    def ids_compras(self, respuesta):
        return {compra.pk for compra in respuesta.context["compras"]}

    def test_busca_titulo_sin_importar_mayusculas_y_quita_espacios(self):
        respuesta = self.client.get(self.url, {"q": "  am  "})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.ids_compras(respuesta), {self.compras[0].pk, self.compras[1].pk})

    def test_combina_titulo_con_fechas_inclusivas(self):
        respuesta = self.client.get(self.url, {
            "q": "AM", "fecha_desde": "2026-09-01", "fecha_hasta": "2026-10-03",
        })
        self.assertEqual(self.ids_compras(respuesta), {self.compras[0].pk, self.compras[1].pk})
        respuesta = self.client.get(self.url, {
            "q": "AM", "fecha_desde": "2026-10-03", "fecha_hasta": "2026-10-03",
        })
        self.assertEqual(self.ids_compras(respuesta), {self.compras[1].pk})

    def test_permite_un_solo_limite_de_fecha(self):
        respuesta = self.client.get(self.url, {"fecha_desde": "2026-10-03"})
        self.assertEqual(self.ids_compras(respuesta), {self.compras[1].pk, self.compras[2].pk})
        respuesta = self.client.get(self.url, {"fecha_hasta": "2026-09-01"})
        self.assertEqual(self.ids_compras(respuesta), {self.compras[0].pk})

    def test_fechas_invalidas_muestran_error_sin_fallar(self):
        for campo in ["fecha_desde", "fecha_hasta"]:
            for fecha in ["2026-02-30", "2026-13-01", "texto"]:
                with self.subTest(campo=campo, fecha=fecha):
                    respuesta = self.client.get(self.url, {campo: fecha})
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertIn(campo, respuesta.context["form"].errors)
                    self.assertEqual(self.ids_compras(respuesta), set())
                    self.assertContains(respuesta, "fecha válida")

    def test_rango_invertido_muestra_error_claro(self):
        respuesta = self.client.get(self.url, {
            "fecha_desde": "2026-10-04", "fecha_hasta": "2026-09-01",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["form"].non_field_errors())
        self.assertContains(respuesta, "La fecha desde no puede ser posterior a la fecha hasta.")
        self.assertEqual(self.ids_compras(respuesta), set())

    def test_filtros_no_permiten_consultar_compras_de_otro_cliente(self):
        respuesta = self.client.get(self.url, {
            "q": "AM", "fecha_desde": "2026-10-03", "fecha_hasta": "2026-10-03",
            "cliente": self.otro_cliente.pk, "id": self.compra_ajena.pk,
        })
        self.assertEqual(self.ids_compras(respuesta), {self.compras[1].pk})
        self.assertNotIn(self.compra_ajena.pk, self.ids_compras(respuesta))

    def test_get_sin_filtros_muestra_historial_propio_sin_mutaciones(self):
        stocks = list(Disco.objects.order_by("pk").values_list("pk", "stock"))
        ventas = list(Venta.objects.order_by("pk").values())
        respuesta = self.client.get(self.url)
        self.assertEqual(self.ids_compras(respuesta), {compra.pk for compra in self.compras})
        self.assertEqual(list(Disco.objects.order_by("pk").values_list("pk", "stock")), stocks)
        self.assertEqual(list(Venta.objects.order_by("pk").values()), ventas)

    def test_muestra_portada_fallback_y_enlace_al_disco(self):
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, self.discos[0].imagen.url)
        self.assertContains(respuesta, "Sin portada")
        for disco in self.discos:
            self.assertContains(respuesta, reverse("discos_detalle", args=[disco.pk]))

    def test_distingue_historial_vacio_y_busqueda_sin_resultados(self):
        respuesta = self.client.get(self.url, {"q": "No existe este título"})
        self.assertContains(respuesta, "No hay compras que coincidan con los filtros.")
        self.assertNotContains(respuesta, "Todavía no tienes compras registradas.")
        self.client.force_login(self.usuario_sin_compras)
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "Todavía no tienes compras registradas.")

    def test_conserva_valores_del_formulario_y_ofrece_limpiar(self):
        respuesta = self.client.get(self.url, {
            "q": "AM", "fecha_desde": "2026-09-01", "fecha_hasta": "2026-10-03",
        })
        self.assertContains(respuesta, 'value="AM"')
        self.assertContains(respuesta, 'value="2026-09-01"')
        self.assertContains(respuesta, 'value="2026-10-03"')
        self.assertContains(respuesta, "Limpiar")

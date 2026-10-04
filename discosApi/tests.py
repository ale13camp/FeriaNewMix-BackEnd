import io
import tempfile
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from jsonschema import Draft7Validator

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from artistasApp.models import Artista
from discosApp.models import Disco
from ventasApp.models import Cliente, Venta


class DatosApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {}
        for nombre in ("Administrador", "Operador", "Consulta", "Cliente"):
            grupo = Group.objects.create(name=nombre)
            usuario = User.objects.create_user(nombre.lower())
            usuario.groups.add(grupo)
            cls.usuarios[nombre] = usuario
        cls.usuarios["Administrador"].set_password("PruebaApi123!")
        cls.usuarios["Administrador"].save()
        cls.usuarios["Superusuario"] = User.objects.create_user("super", is_superuser=True)
        cls.usuarios["SinGrupo"] = User.objects.create_user("singrupo")
        cls.usuarios["SoloStaff"] = User.objects.create_user("staff", is_staff=True)
        cls.comprador = Cliente.objects.create(nombre="Cliente propio", correo="privado@example.test",
                                             telefono="987654321", usuario=cls.usuarios["Cliente"])
        cls.ajeno = Cliente.objects.create(nombre="Cliente ajeno", correo="ajeno@example.test", telefono="912345678")
        cls.artista = Artista.objects.create(nombre="Artista API", genero="Rock", pais="Chile",
                                            anio_formacion=2000, integrantes=1, bio="Prueba")
        cls.disco = Disco.objects.create(titulo="Disco API", artista=cls.artista, genero="Rock", anio=2020,
                                        formato="CD", precio=12000, stock=10)
        cls.otro = Disco.objects.create(titulo="Otro disco", artista=cls.artista, genero="Rock", anio=2021,
                                       formato="Vinilo", precio=15000, stock=4)

    def setUp(self):
        self.api = APIClient()

    def autenticar(self, rol="Administrador"):
        token = RefreshToken.for_user(self.usuarios[rol]).access_token
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return token

    def datos_disco(self, **cambios):
        return dict(titulo="Disco nuevo", artista=self.artista.pk, genero="Rock", anio=2022,
                    formato="CD", precio="18000", stock=6, descripcion="Prueba", **cambios)

    def datos_venta(self, **cambios):
        datos = {"cliente": self.comprador.pk, "disco": self.disco.pk, "cantidad": 2, "fecha": "2026-10-02"}
        datos.update(cambios)
        return datos

    def venta(self, cliente=None, disco=None, cantidad=1):
        return Venta.objects.create(cliente=cliente or self.comprador, disco=disco or self.disco,
                                    cantidad=cantidad, precio_unitario=17321, fecha="2026-10-02")

    def stock(self, disco):
        disco.refresh_from_db()
        return disco.stock

    def comprobar_publico(self, respuesta):
        self.assertTrue(respuesta["Content-Type"].startswith("application/json"))
        texto = respuesta.content.decode()
        for secreto in ("privado@example.test", "ajeno@example.test", "987654321", "912345678",
                        "precio_unitario", '"total"', '"correo"', '"telefono"', '"usuario"', "password", "pbkdf2_"):
            self.assertNotIn(secreto, texto)


class AutenticacionApiTests(DatosApi):
    def test_negocio_exige_jwt_incluso_con_sesion_web(self):
        self.api.force_login(self.usuarios["Administrador"])
        for ruta in ("clientes", "discos", "ventas"):
            respuesta = self.api.get(f"/api/{ruta}/")
            self.assertEqual(respuesta.status_code, 401)
            self.assertTrue(respuesta["WWW-Authenticate"].startswith("Bearer"))

    def test_tokens_invalidos_y_expirados_se_rechazan(self):
        token = self.autenticar()
        token.set_exp(lifetime=timedelta(seconds=-1))
        for valor in ("token-invalido", str(token)):
            self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {valor}")
            self.assertEqual(self.api.get("/api/discos/").status_code, 401)

    def test_obtener_y_refrescar_tokens_minimos(self):
        respuesta = self.api.post("/api/token/", {"username": "administrador", "password": "PruebaApi123!"}, format="json")
        self.assertEqual(respuesta.status_code, 200)
        token = RefreshToken(respuesta.data["refresh"])
        self.assertEqual(set(token.payload), {"token_type", "exp", "iat", "jti", "user_id"})
        self.assertEqual(token["exp"] - token["iat"], 86400)
        self.assertEqual(token.access_token["exp"] - token.access_token["iat"], 300)
        refresco = self.api.post("/api/token/refresh/", {"refresh": str(token)}, format="json")
        self.assertEqual(refresco.status_code, 200)
        self.api.credentials(HTTP_AUTHORIZATION="Bearer " + refresco.data["access"])
        self.assertEqual(self.api.get("/api/discos/").status_code, 200)
        self.assertEqual(self.api.post("/api/token/refresh/", {"refresh": "invalido"}, format="json").status_code, 401)

    def test_grupos_se_revisan_con_token_ya_emitido(self):
        self.autenticar("Consulta")
        self.assertEqual(self.api.get("/api/discos/").status_code, 200)
        self.usuarios["Consulta"].groups.clear()
        self.assertEqual(self.api.get("/api/discos/").status_code, 403)

    def test_cuentas_sin_grupo_y_staff_no_tienen_acceso(self):
        for rol in ("SinGrupo", "SoloStaff"):
            self.autenticar(rol)
            for ruta in ("clientes", "discos", "ventas"):
                self.assertEqual(self.api.get(f"/api/{ruta}/").status_code, 403)

    def test_superusuario_sin_grupo_puede_administrar(self):
        self.autenticar("Superusuario")
        self.assertEqual(self.api.post("/api/clientes/", {"nombre": "Nuevo", "correo": "nuevo@example.test"}, format="json").status_code, 201)

    def test_precedencia_consulta_sobre_cliente_no_permite_comprar(self):
        usuario = self.usuarios["Cliente"]
        usuario.groups.add(Group.objects.get(name="Consulta"))
        self.autenticar("Cliente")
        respuesta = self.api.get("/api/clientes/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 2)
        self.assertEqual(self.api.post("/api/ventas/", self.datos_venta(), format="json").status_code, 403)


class CrudApiTests(DatosApi):
    def test_admin_crud_cliente_y_vinculo_usuario(self):
        self.autenticar()
        datos = {"nombre": "Nuevo", "correo": "nuevo@example.test", "telefono": "123", "usuario": self.usuarios["SinGrupo"].pk}
        respuesta = self.api.post("/api/clientes/", datos, format="json")
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(set(respuesta.data), {"id", "nombre", "correo", "telefono", "usuario"})
        url = f'/api/clientes/{respuesta.data["id"]}/'
        self.assertEqual(self.api.get(url).data["usuario"], self.usuarios["SinGrupo"].pk)
        datos["nombre"] = "Editado"
        self.assertEqual(self.api.put(url, datos, format="json").data["nombre"], "Editado")
        borrado = self.api.delete(url)
        self.assertEqual(borrado.status_code, 204)
        self.assertEqual(borrado.content, b"")
        self.assertEqual(self.api.get(url).status_code, 404)

    def test_vinculo_duplicado_rechazado_sin_identidad(self):
        self.autenticar()
        respuesta = self.api.post("/api/clientes/", {"nombre": "Otro", "correo": "nuevo@example.test", "usuario": self.usuarios["Cliente"].pk}, format="json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertNotIn("privado@example.test", respuesta.content.decode())
        self.assertNotIn("Cliente propio", respuesta.content.decode())
        self.assertEqual(Cliente.objects.count(), 2)

    def test_admin_crud_disco(self):
        self.autenticar()
        respuesta = self.api.post("/api/discos/", self.datos_disco(), format="json")
        self.assertEqual(respuesta.status_code, 201)
        url = f'/api/discos/{respuesta.data["id"]}/'
        self.assertEqual(self.api.get(url).data["precio"], "18000")
        datos = self.datos_disco()
        datos["titulo"] = "Editado"
        self.assertEqual(self.api.put(url, datos, format="json").data["titulo"], "Editado")
        self.assertEqual(self.api.delete(url).status_code, 204)
        self.assertEqual(self.api.get(url).status_code, 404)

    def test_operador_crea_y_edita_sin_ver_privados_ni_cambiar_usuario(self):
        self.autenticar("Operador")
        datos = {"nombre": "Nuevo", "correo": "nuevo@example.test", "telefono": "123", "usuario": self.usuarios["SinGrupo"].pk}
        respuesta = self.api.post("/api/clientes/", datos, format="json")
        self.assertEqual(respuesta.status_code, 201)
        self.comprobar_publico(respuesta)
        cliente = Cliente.objects.get(pk=respuesta.data["id"])
        self.assertIsNone(cliente.usuario_id)
        datos["nombre"] = "Editado"
        respuesta = self.api.put(f"/api/clientes/{cliente.pk}/", datos, format="json")
        self.assertEqual(respuesta.status_code, 200)
        self.comprobar_publico(respuesta)
        cliente.refresh_from_db()
        self.assertEqual(cliente.correo, "nuevo@example.test")
        self.assertIsNone(cliente.usuario_id)
        self.assertEqual(self.api.post("/api/discos/", self.datos_disco(), format="json").status_code, 201)
        self.assertEqual(self.api.put(f"/api/discos/{self.disco.pk}/", self.datos_disco(), format="json").status_code, 200)
        venta = self.api.post("/api/ventas/", self.datos_venta(), format="json")
        self.assertEqual(venta.status_code, 201)
        self.comprobar_publico(venta)
        respuesta = self.api.put(f'/api/ventas/{venta.data["id"]}/', self.datos_venta(cantidad=1), format="json")
        self.assertEqual(respuesta.status_code, 200)
        self.comprobar_publico(respuesta)

    def test_operador_no_elimina_ningun_recurso(self):
        venta = self.venta()
        self.autenticar("Operador")
        for recurso, pk in (("clientes", self.comprador.pk), ("discos", self.disco.pk), ("ventas", venta.pk)):
            self.assertEqual(self.api.delete(f"/api/{recurso}/{pk}/").status_code, 403)
        self.assertTrue(Venta.objects.filter(pk=venta.pk).exists())
        self.assertEqual(self.stock(self.disco), 9)

    def test_consulta_solo_lee_y_respuestas_sin_privados(self):
        venta = self.venta()
        self.autenticar("Consulta")
        for recurso, pk in (("clientes", self.comprador.pk), ("discos", self.disco.pk), ("ventas", venta.pk)):
            for ruta in (f"/api/{recurso}/", f"/api/{recurso}/{pk}/"):
                respuesta = self.api.get(ruta)
                self.assertEqual(respuesta.status_code, 200)
                self.comprobar_publico(respuesta)
            for metodo, ruta in (("post", f"/api/{recurso}/"), ("put", f"/api/{recurso}/{pk}/"), ("delete", f"/api/{recurso}/{pk}/")):
                respuesta = getattr(self.api, metodo)(ruta, {}, format="json")
                self.assertEqual(respuesta.status_code, 403)

    def test_put_incompleto_y_valores_invalidos_no_guardan(self):
        self.autenticar()
        self.assertEqual(self.api.put(f"/api/discos/{self.disco.pk}/", {"titulo": "Cambio parcial"}, format="json").status_code, 400)
        for campo, valor in (("precio", 0), ("precio", -1), ("stock", -1), ("anio", 0), ("artista", 99999), ("formato", "Otro")):
            datos = self.datos_disco()
            datos[campo] = valor
            self.assertEqual(self.api.post("/api/discos/", datos, format="json").status_code, 400)
        self.assertEqual(Disco.objects.count(), 2)
        self.assertEqual(self.api.post("/api/clientes/", {"nombre": "Nuevo", "correo": "incorrecto"}, format="json").status_code, 400)

    def test_metodos_ausentes_y_ids_desconocidos(self):
        self.autenticar()
        for recurso in ("clientes", "discos", "ventas"):
            self.assertEqual(self.api.get(f"/api/{recurso}/99999/").status_code, 404)
            self.assertEqual(self.api.patch(f"/api/{recurso}/{self.disco.pk}/", {}, format="json").status_code, 405)
            self.assertEqual(self.api.delete(f"/api/{recurso}/").status_code, 405)


class CompraApiTests(DatosApi):
    def test_cliente_solo_ve_su_ficha_y_sus_ventas(self):
        propia = self.venta()
        ajena = self.venta(cliente=self.ajeno, disco=self.otro)
        self.autenticar("Cliente")
        clientes = self.api.get("/api/clientes/")
        self.assertEqual(clientes.status_code, 200)
        self.assertEqual(clientes.data, [{"id": self.comprador.pk, "nombre": "Cliente propio"}])
        ventas = self.api.get("/api/ventas/")
        self.assertEqual([item["id"] for item in ventas.data], [propia.pk])
        for respuesta in (clientes, ventas, self.api.get(f"/api/ventas/{propia.pk}/"), self.api.get(f"/api/clientes/{self.comprador.pk}/")):
            self.comprobar_publico(respuesta)
        self.assertEqual(self.api.get(f"/api/clientes/{self.ajeno.pk}/").status_code, 404)
        self.assertEqual(self.api.get(f"/api/ventas/{ajena.pk}/").status_code, 404)
        self.assertEqual(len(self.api.get("/api/discos/").data), 2)

    def test_cliente_compra_propia_ignorando_identidad_fecha_importes(self):
        self.autenticar("Cliente")
        datos = {"disco": self.disco.pk, "cantidad": 2, "cliente": "no-es-id",
                 "fecha": "fecha-maliciosa", "precio_unitario": "1", "total": "1", "usuario": self.usuarios["SinGrupo"].pk}
        respuesta = self.api.post("/api/ventas/", datos, format="json")
        self.assertEqual(respuesta.status_code, 201)
        self.comprobar_publico(respuesta)
        venta = Venta.objects.get(pk=respuesta.data["id"])
        self.assertEqual(venta.cliente, self.comprador)
        self.assertEqual(venta.fecha, timezone.localdate())
        self.assertEqual(venta.precio_unitario, Decimal("12000"))
        self.assertEqual(self.stock(self.disco), 8)

    def test_cliente_no_modifica_ni_elimina_ventas_discos_clientes(self):
        venta = self.venta()
        self.autenticar("Cliente")
        self.assertEqual(self.api.post("/api/clientes/", {}, format="json").status_code, 403)
        self.assertEqual(self.api.post("/api/discos/", {}, format="json").status_code, 403)
        for recurso, pk in (("clientes", self.comprador.pk), ("discos", self.disco.pk), ("ventas", venta.pk)):
            self.assertEqual(self.api.put(f"/api/{recurso}/{pk}/", {}, format="json").status_code, 403)
            self.assertEqual(self.api.delete(f"/api/{recurso}/{pk}/").status_code, 403)

    def test_cliente_sin_ficha_no_compra_ni_ve_ajenos(self):
        self.comprador.usuario = None
        self.comprador.save()
        self.autenticar("Cliente")
        respuesta = self.api.get("/api/clientes/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data, [])
        self.assertEqual(self.api.get("/api/ventas/").data, [])
        self.assertEqual(self.api.post("/api/ventas/", {"disco": self.disco.pk, "cantidad": 1}, format="json").status_code, 400)
        self.assertEqual(Venta.objects.count(), 0)

    def test_cliente_error_validacion_no_revela_datos_privados(self):
        self.autenticar("Cliente")
        for cantidad in (0, -1, "1.5", 9999):
            respuesta = self.api.post("/api/ventas/", {"disco": self.disco.pk, "cantidad": cantidad}, format="json")
            self.assertEqual(respuesta.status_code, 400)
            self.comprobar_publico(respuesta)
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(self.stock(self.disco), 10)


class StockApiTests(DatosApi):
    def test_venta_admin_crud_stock_y_precio_del_servidor(self):
        self.autenticar()
        respuesta = self.api.post("/api/ventas/", self.datos_venta(precio_unitario="1", total="1"), format="json")
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.data["precio_unitario"], "12000")
        self.assertEqual(respuesta.data["total"], "24000")
        self.assertEqual(self.stock(self.disco), 8)
        url = f'/api/ventas/{respuesta.data["id"]}/'
        self.assertEqual(self.api.get(url).data["total"], "24000")
        self.assertEqual(self.api.get("/api/ventas/").data[0]["total"], "24000")
        self.assertEqual(self.api.put(url, self.datos_venta(cantidad=4), format="json").status_code, 200)
        self.assertEqual(self.stock(self.disco), 6)
        self.assertEqual(self.api.put(url, self.datos_venta(cantidad=1), format="json").status_code, 200)
        self.assertEqual(self.stock(self.disco), 9)
        respuesta = self.api.delete(url)
        self.assertEqual(respuesta.status_code, 204)
        self.assertEqual(respuesta.content, b"")
        self.assertEqual(self.stock(self.disco), 10)

    def test_mismo_disco_conserva_precio_historico(self):
        venta = self.venta(cantidad=2)
        self.disco.refresh_from_db()
        self.disco.precio = 20000
        self.disco.save()
        self.autenticar()
        respuesta = self.api.put(f"/api/ventas/{venta.pk}/", self.datos_venta(cantidad=3, precio_unitario=1), format="json")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["precio_unitario"], "17321")
        self.assertEqual(respuesta.data["total"], "51963")
        self.assertEqual(self.stock(self.disco), 7)

    def test_cambiar_disco_toma_precio_nuevo_y_restaura_stock(self):
        venta = self.venta(cantidad=3)
        self.autenticar()
        respuesta = self.api.put(f"/api/ventas/{venta.pk}/", self.datos_venta(disco=self.otro.pk, cantidad=2), format="json")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["precio_unitario"], "15000")
        self.assertEqual(self.stock(self.disco), 10)
        self.assertEqual(self.stock(self.otro), 2)

    def test_stock_insuficiente_rollback_creacion_y_edicion(self):
        self.autenticar()
        self.assertEqual(self.api.post("/api/ventas/", self.datos_venta(cantidad=11), format="json").status_code, 400)
        self.assertEqual(Venta.objects.count(), 0)
        venta = self.venta(cantidad=3)
        respuesta = self.api.put(f"/api/ventas/{venta.pk}/", self.datos_venta(disco=self.otro.pk, cantidad=5), format="json")
        self.assertEqual(respuesta.status_code, 400)
        venta.refresh_from_db()
        self.assertEqual(venta.disco_id, self.disco.pk)
        self.assertEqual(venta.cantidad, 3)
        self.assertEqual(self.stock(self.disco), 7)
        self.assertEqual(self.stock(self.otro), 4)

    def test_relaciones_y_cantidad_invalidas_no_afectan_stock(self):
        self.autenticar()
        for campo, valor in (("cliente", 99999), ("disco", 99999), ("cantidad", 0), ("cantidad", -1), ("cantidad", "1.5")):
            respuesta = self.api.post("/api/ventas/", self.datos_venta(**{campo: valor}), format="json")
            self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(self.stock(self.disco), 10)
        self.assertEqual(Venta.objects.count(), 0)

    def test_borrado_protegido_es_400_sin_objetos_privados(self):
        self.venta()
        self.autenticar()
        for recurso, pk in (("clientes", self.comprador.pk), ("discos", self.disco.pk)):
            respuesta = self.api.delete(f"/api/{recurso}/{pk}/")
            self.assertEqual(respuesta.status_code, 400)
            self.assertIn("ventas", respuesta.data["detail"].lower())
            self.assertNotIn("Cliente propio", respuesta.content.decode())
            self.assertNotIn("privado@example.test", respuesta.content.decode())

    def test_error_tardio_de_modelo_y_integridad_hacen_rollback(self):
        self.autenticar("Operador")
        original = Venta.save
        for error in (ValidationError({"cliente": "privado@example.test 17321"}), IntegrityError("SQL privado@example.test")):
            def guardar_con_error(instancia, *args, **kwargs):
                original(instancia, *args, **kwargs)
                raise error
            with patch.object(Venta, "save", guardar_con_error):
                respuesta = self.api.post("/api/ventas/", self.datos_venta(), format="json")
            self.assertEqual(respuesta.status_code, 400)
            self.comprobar_publico(respuesta)
            self.assertNotIn("SQL", respuesta.content.decode())
            self.assertEqual(Venta.objects.count(), 0)
            self.assertEqual(self.stock(self.disco), 10)

    def test_error_inesperado_500_generico_y_rollback(self):
        self.autenticar("Operador")
        original = Venta.save
        def guardar_con_error(instancia, *args, **kwargs):
            original(instancia, *args, **kwargs)
            raise RuntimeError("SQL privado@example.test /privados/ficha.pdf password")
        with patch.object(Venta, "save", guardar_con_error):
            respuesta = self.api.post("/api/ventas/", self.datos_venta(), format="json")
        self.assertEqual(respuesta.status_code, 500)
        self.assertEqual(respuesta.data, {"detail": "No se pudo completar la operación."})
        self.comprobar_publico(respuesta)
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(self.stock(self.disco), 10)


class ArchivosApiTests(DatosApi):
    def imagen(self):
        contenido = io.BytesIO()
        Image.new("RGB", (2, 2), "white").save(contenido, format="PNG")
        return SimpleUploadedFile("portada.png", contenido.getvalue(), content_type="image/png")

    def test_upload_valido_imagen_publica_pdf_solo_nombre_admin(self):
        with tempfile.TemporaryDirectory() as carpeta, override_settings(MEDIA_ROOT=carpeta, PRIVATE_MEDIA_ROOT=carpeta):
            self.autenticar()
            datos = self.datos_disco()
            datos.update(imagen=self.imagen(), documento=SimpleUploadedFile("ficha.pdf", b"%PDF-1.4\nPrueba", content_type="application/pdf"))
            respuesta = self.api.post("/api/discos/", datos, format="multipart")
            self.assertEqual(respuesta.status_code, 201)
            self.assertEqual(respuesta.data["documento"], "ficha.pdf")
            self.assertIn("/media/discos/portada", respuesta.data["imagen"])
            self.assertNotIn("documentos/", respuesta.content.decode())
            pk = respuesta.data["id"]
            for rol in ("Operador", "Consulta", "Cliente"):
                self.autenticar(rol)
                for ruta in ("/api/discos/", f"/api/discos/{pk}/"):
                    respuesta = self.api.get(ruta)
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertNotIn("documento", respuesta.content.decode())
                    self.assertNotIn("ficha.pdf", respuesta.content.decode())

    def test_operador_sube_pdf_sin_recibir_metadatos_privados(self):
        with tempfile.TemporaryDirectory() as carpeta, override_settings(MEDIA_ROOT=carpeta, PRIVATE_MEDIA_ROOT=carpeta):
            self.autenticar("Operador")
            datos = self.datos_disco()
            datos["documento"] = SimpleUploadedFile("ficha.pdf", b"%PDF-1.4\n")
            respuesta = self.api.post("/api/discos/", datos, format="multipart")
            self.assertEqual(respuesta.status_code, 201)
            self.assertNotIn("documento", respuesta.data)
            disco = Disco.objects.get(pk=respuesta.data["id"])
            self.assertTrue(disco.documento.name.endswith("ficha.pdf"))
            datos.pop("documento")
            respuesta = self.api.put(f"/api/discos/{disco.pk}/", datos, format="multipart")
            self.assertEqual(respuesta.status_code, 200)
            self.assertNotIn("documento", respuesta.data)
            disco.refresh_from_db()
            self.assertTrue(disco.documento.name.endswith("ficha.pdf"))

    def test_uploads_invalidos_se_rechazan_sin_guardar(self):
        self.autenticar("Operador")
        for campo, archivo in (("documento", SimpleUploadedFile("mal.pdf", b"texto")),
                               ("documento", SimpleUploadedFile("mal.txt", b"%PDF-1.4")),
                               ("imagen", SimpleUploadedFile("mal.png", b"texto"))):
            datos = self.datos_disco()
            datos[campo] = archivo
            respuesta = self.api.post("/api/discos/", datos, format="multipart")
            self.assertEqual(respuesta.status_code, 400)
            self.assertNotIn("mal.", respuesta.content.decode())
        self.assertEqual(Disco.objects.count(), 2)


class DocumentacionApiTests(DatosApi):
    def test_docs_y_schema_publicos_incluso_jwt_invalido(self):
        self.api.credentials(HTTP_AUTHORIZATION="Bearer invalido")
        for ruta in ("/api/swagger/", "/api/redoc/", "/api/schema/?format=json"):
            self.assertEqual(self.api.get(ruta).status_code, 200)

    def test_schema_documenta_jwt_crud_y_formas_de_privacidad(self):
        respuesta = self.api.get("/api/schema/?format=json")
        self.assertEqual(respuesta.status_code, 200)
        schema = respuesta.json()
        self.assertEqual(schema["components"]["securitySchemes"]["jwtAuth"]["scheme"], "bearer")
        for recurso in ("clientes", "discos", "ventas"):
            lista = schema["paths"][f"/api/{recurso}/"]
            detalle = schema["paths"][f"/api/{recurso}/{{id}}/"]
            self.assertEqual(set(lista), {"get", "post"})
            self.assertEqual(set(detalle), {"get", "put", "delete"})
            for operacion in list(lista.values()) + list(detalle.values()):
                self.assertIn({"jwtAuth": []}, operacion["security"])
                for estado in ("401", "403", "500"):
                    self.assertIn(estado, operacion["responses"])
            self.assertIn("204", detalle["delete"]["responses"])
            self.assertNotIn("content", detalle["delete"]["responses"]["204"])
        componentes = schema["components"]["schemas"]
        self.assertEqual(set(componentes["ClientePublico"]["properties"]), {"id", "nombre"})
        self.assertNotIn("precio_unitario", componentes["VentaPublica"]["properties"])
        self.assertEqual(set(componentes["CompraEntradaRequest"]["properties"]), {"disco", "cantidad"})
        self.assertEqual(componentes["DiscoEntradaRequest"]["properties"]["documento"]["format"], "binary")

    def test_schema_put_ventas_solo_ofrece_entrada_operativa(self):
        respuesta = self.api.get("/api/schema/?format=json")
        self.assertEqual(respuesta.status_code, 200)
        put = respuesta.json()["paths"]["/api/ventas/{id}/"]["put"]
        ejemplos = put["requestBody"]["content"]["application/json"]["examples"].values()
        self.assertTrue(ejemplos)
        for ejemplo in ejemplos:
            self.assertIn("cliente", ejemplo["value"])
            self.assertIn("disco", ejemplo["value"])
            self.assertIn("cantidad", ejemplo["value"])

    def test_schema_valida_variantes_runtime_y_entradas_sin_solapamiento_exclusivo(self):
        self.disco.imagen = "discos/portada-prueba.png"
        self.disco.save()
        venta = self.venta()
        schema = self.api.get("/api/schema/?format=json").json()
        for rol in ("Administrador", "Consulta"):
            self.autenticar(rol)
            for recurso, pk, componente in (("clientes", self.comprador.pk, "ClienteRespuesta"),
                                           ("discos", self.disco.pk, "DiscoRespuesta"),
                                           ("ventas", venta.pk, "VentaRespuesta")):
                respuesta = self.api.get(f"/api/{recurso}/{pk}/")
                self.assertEqual(respuesta.status_code, 200)
                contrato = {"$ref": f"#/components/schemas/{componente}", "components": schema["components"]}
                errores = list(Draft7Validator(contrato).iter_errors(respuesta.data))
                self.assertFalse(errores, f"{rol} {recurso}: {errores}")
        for componente, entrada in (("ClienteEscrituraRequest", {"nombre": "Prueba", "correo": "prueba@example.test", "usuario": 1}),
                                    ("VentaEscrituraRequest", {"cliente": 1, "disco": 1, "cantidad": 2}),
                                    ("VentaEscrituraRequest", {"disco": 1, "cantidad": 2})):
            contrato = {"$ref": f"#/components/schemas/{componente}", "components": schema["components"]}
            errores = list(Draft7Validator(contrato).iter_errors(entrada))
            self.assertFalse(errores, f"{componente}: {errores}")

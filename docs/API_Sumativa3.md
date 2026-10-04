# API REST de Feria NewMix: Sumativa 3

## 1. Propósito y estado

La API permite que otra aplicación consulte el catálogo y gestione los mismos clientes, discos y ventas que usa la web. Cliente y Disco son los dos mantenedores. Venta relaciona un cliente con un disco y representa una compra de una o más unidades. No incluye carrito, pasarela de pago ni cobro real.

La implementación se realizó en la rama `codex/sumativa-3-api`. El 4 de octubre de 2026 aprobaron **35 pruebas API y las 129 pruebas totales** del proyecto. También aprobaron `check`, la revisión de migraciones y la validación del esquema OpenAPI sin advertencias. Se comprobaron las consultas HTTP con los cuatro perfiles y el uso de Authorize con respuesta 200 desde Swagger local. Antes del cambio se habían repetido las 94 pruebas de la web; ese resultado se conserva como base previa y se distingue de la comprobación de los endpoints nuevos.

**AWS está aplazado.** Se registraron acceso inicial, clonación del proyecto y preparación del entorno en EC2. Siguen pendientes la configuración de la base remota, migraciones, Gunicorn/NGINX y demostración de la web, API, Swagger y JWT desde AWS. No se asigna una calificación ni se marca ese criterio como cumplido.

La fuente principal es `Eva Sumativa 3 - flex.docx`, entregada por el usuario. Se utilizaron las secciones de requerimientos funcionales, DRF, JWT, respuestas JSON, datos sensibles, Swagger, infraestructura y entregables, además de su imagen de Escala de Apreciación. Las decisiones concretas de esta API se explican aquí para distinguirlas de los ejemplos del curso.

## 2. Arquitectura y archivos

![Arquitectura lógica de Feria NewMix](evidencias_api/arquitectura.png)

La web entrega páginas HTML y usa la sesión de Django. Un cliente de la API envía solicitudes HTTP y recibe JSON; Swagger es un cliente para probarlas. Ambas entradas usan Django, el ORM y los modelos existentes. En local se utiliza SQLite para la revisión provisional. La ejecución en EC2 y su base remota se muestran en el diagrama como etapa pendiente.

| Archivo o carpeta | Responsabilidad |
|---|---|
| `config/settings.py` | Instalar DRF, SimpleJWT y drf-spectacular; definir autenticación, duración de tokens y esquema. |
| `config/urls.py` | Conectar la API, JWT, esquema, Swagger y ReDoc. |
| `discosApi/serializers.py` | Validar entradas y elegir los campos de salida según perfil. |
| `discosApi/permissions.py` | Resolver el grupo efectivo y permitir o rechazar cada método. |
| `discosApi/exceptions.py` | Transformar errores internos en respuestas seguras. |
| `discosApi/schema.py` | Describir entradas, salidas por perfil y ejemplos OpenAPI. |
| `discosApi/views.py` | Atender solicitudes con vistas de función, `@api_view` y `Response`. |
| `discosApi/urls.py` | Rutas de clientes, discos y ventas. |
| `discosApi/tests.py` | Pruebas de API con datos y base temporales. |
| `ventasApp/models.py` | Modelos Cliente y Venta; guardado individual de ventas y movimiento de stock. |
| `discosApp/models.py` | Modelo Disco, precio, stock y archivos. |
| `discosApp/validators.py` | Validación de imágenes y PDF. |

Se conserva el modelo de la Sumativa 2. Se utilizan `ModelSerializer` con campos explícitos y vistas de función para mantener el código explicable en segundo año. La salida de negocio usa `JSONRenderer`; el esquema OpenAPI y las páginas de documentación tienen su propio formato.

## 3. Instalación local

Dentro de la carpeta del proyecto, en PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

Si `.venv` ya está preparado, activarlo y actualizar las dependencias. Si no se puede activar, reemplazar `python` en los comandos por `.\.venv\Scripts\python.exe`. Las dependencias de la ampliación son Django REST Framework 3.16.1, SimpleJWT 5.5.1 y drf-spectacular 0.30.0; Django se mantiene en 5.2.17.

En una instalación nueva, copiar `.env.example` a `.env` sólo si no existe ya un archivo propio. Crear una `SECRET_KEY` propia y completar la conexión. `.env` es privado y no forma parte del repositorio. SQLite permite la revisión local; no acredita MySQL ni EC2.

```powershell
python manage.py migrate
python manage.py importar_catalogo
python manage.py crear_perfiles
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

La importación agrega el catálogo original que falta y conserva registros existentes. `crear_perfiles` prepara Administrador, Operador, Consulta y Cliente. Crear las cuentas desde Admin o usar el registro web del cliente. No hay contraseñas predeterminadas publicadas. `is_staff` permite entrar al Admin de Django, pero por sí solo no concede un rol para la API.

Para demostraciones de escritura, preparar una base aparte antes de migrar y crear registros de prueba:

```powershell
New-Item -ItemType Directory -Force -Path .evaluacion/sumativa3
$env:DB_ENGINE = "sqlite"
$env:SQLITE_NAME = ".evaluacion/sumativa3/demostracion.sqlite3"
python manage.py migrate
python manage.py crear_perfiles
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8001
```

Ejecutar ese bloque en una terminal dedicada: las variables afectan los comandos de esa terminal. Desde el Admin de esa base, preparar un Artista, Cliente y Disco identificados como demostración, y las cuentas con sus grupos. No copiar la base real ni ejecutar POST, PUT o DELETE sobre los registros del usuario sólo para conseguir una captura. Las pruebas automatizadas de archivos usan carpetas temporales; para probar subidas manuales utilizar una copia de demostración con sus propias carpetas de archivos.

## 4. Autenticación JWT

`POST /api/token/` recibe las credenciales de una cuenta de Django y entrega `access` y `refresh`. El Access Token dura **5 minutos**; el Refresh Token dura **1 día**. Son dos tokens distintos: el de acceso autoriza los endpoints y el de renovación permite obtener otro token de acceso.

Ejemplo sintético de entrada:

```json
{
  "username": "cuenta_demostracion",
  "password": "CONTRASENA_DE_LA_CUENTA_DE_PRUEBA"
}
```

Forma de la respuesta, con textos de reemplazo que no son tokens válidos:

```json
{
  "refresh": "REFRESH_TOKEN_PRIVADO",
  "access": "ACCESS_TOKEN_PRIVADO"
}
```

Para consultar la API, enviar esta cabecera:

```http
Authorization: Bearer ACCESS_TOKEN_PRIVADO
```

`POST /api/token/refresh/` recibe:

```json
{
  "refresh": "REFRESH_TOKEN_PRIVADO"
}
```

Devuelve un nuevo `access`. Un token inexistente, inválido o vencido no autoriza las rutas protegidas y produce 401. Obtener un token no concede por sí solo permisos de negocio: una cuenta sin un grupo reconocido recibe 403 al entrar en la API.

Se utiliza la estructura habitual de SimpleJWT, sin agregar nombre, correo, teléfono o roles propios al token. Los permisos se consultan desde los grupos actuales de la base en cada solicitud. Por ello, cambiar un grupo afecta a la próxima solicitud aunque el Access Token siga dentro de su plazo. No publicar tokens ni respuestas de autenticación en capturas, commits o informe.

## 5. Roles y privacidad

El superusuario y el grupo Administrador tienen capacidad administrativa. La API no utiliza `is_staff` como sustituto de Administrador. Una cuenta autenticada sin un grupo válido no accede a los recursos.

| Perfil efectivo | Clientes | Discos | Ventas |
|---|---|---|---|
| Administrador | GET, POST, PUT y DELETE. | GET, POST, PUT y DELETE. | GET, POST, PUT y DELETE. |
| Operador | GET, POST y PUT. | GET, POST y PUT. | GET, POST y PUT. |
| Consulta | GET. | GET. | GET. |
| Cliente | GET de su propio registro. | GET del catálogo. | GET de sus propias ventas y POST de su compra. |
| Sin grupo reconocido | Sin acceso. | Sin acceso. | Sin acceso. |

Para cuentas con varios grupos, la precedencia es **Administrador > Operador > Consulta > Cliente**. El superusuario equivale a Administrador. Se aplica un solo perfil efectivo, tanto a los permisos como a los campos de salida: una cuenta Operador y Cliente actúa como Operador; una cuenta Consulta y Cliente sólo consulta. Para una demostración clara, asignar un único grupo de negocio por cuenta.

| Recurso | Campos para Administrador | Campos para los demás perfiles autorizados |
|---|---|---|
| Cliente | `id`, `nombre`, `correo`, `telefono`, `usuario`. | `id`, `nombre`. |
| Disco | `id`, `titulo`, `artista`, `genero`, `anio`, `formato`, `precio`, `stock`, `descripcion`, `imagen`, `documento` como nombre base. | Los mismos campos de catálogo, sin `documento`. |
| Venta | `id`, `cliente`, `disco`, `fecha`, `cantidad`, `precio_unitario`, `total`. | `id`, `cliente`, `disco`, `fecha`, `cantidad`. |

**El precio de Disco es un precio público del catálogo.** El precio unitario y total de Venta corresponden a la transacción y sólo aparecen en la respuesta administrativa. Correo, teléfono y vínculo a la cuenta también quedan fuera de las respuestas no administrativas, incluso si un Operador acaba de enviarlos al crear o editar un Cliente.

Un Operador puede registrar correo y teléfono de clientes, pero no asignar el vínculo `usuario`. Ningún endpoint permite escribir contraseñas o grupos. Ni siquiera las respuestas administrativas muestran contraseña, hash de contraseña ni tokens de otra cuenta.

Las listas del Cliente se filtran por su vínculo de cuenta. Para un detalle, el filtro de propiedad se aplica antes de buscar el ID: si intenta leer el cliente o la venta de otra persona obtiene 404, igual que un registro inexistente. No puede editar o borrar Cliente, Disco o Venta desde esta API. Su edición de perfil sigue siendo una función de la web.

## 6. Endpoints y métodos

Base local de los ejemplos: `http://127.0.0.1:8000`. `{id}` se reemplaza por el número real de un registro de la base de prueba.

| Ruta | Método | Operación | Éxito |
|---|---|---|---|
| `/api/clientes/` | GET | Listar clientes permitidos. | 200 y lista JSON. |
| `/api/clientes/` | POST | Crear cliente: Administrador u Operador. | 201 y registro JSON. |
| `/api/clientes/{id}/` | GET | Consultar un cliente permitido. | 200 y registro JSON. |
| `/api/clientes/{id}/` | PUT | Modificar cliente: Administrador u Operador. | 200 y registro JSON. |
| `/api/clientes/{id}/` | DELETE | Eliminar cliente: sólo Administrador, si no tiene ventas. | 204 sin cuerpo. |
| `/api/discos/` | GET | Listar discos. | 200 y lista JSON. |
| `/api/discos/` | POST | Crear disco: Administrador u Operador. | 201 y registro JSON. |
| `/api/discos/{id}/` | GET | Consultar un disco. | 200 y registro JSON. |
| `/api/discos/{id}/` | PUT | Modificar disco: Administrador u Operador. | 200 y registro JSON. |
| `/api/discos/{id}/` | DELETE | Eliminar disco: sólo Administrador, si no tiene ventas. | 204 sin cuerpo. |
| `/api/ventas/` | GET | Listar ventas permitidas. | 200 y lista JSON. |
| `/api/ventas/` | POST | Registrar venta administrativa o compra propia. | 201 y registro JSON. |
| `/api/ventas/{id}/` | GET | Consultar una venta permitida. | 200 y registro JSON. |
| `/api/ventas/{id}/` | PUT | Modificar venta: Administrador u Operador. | 200 y registro JSON. |
| `/api/ventas/{id}/` | DELETE | Eliminar venta y devolver stock: sólo Administrador. | 204 sin cuerpo. |

Las rutas de negocio admiten GET y POST en la colección, y GET, PUT y DELETE en el detalle. No se agrega PATCH en esta evaluación. PUT requiere `nombre` y `correo` para Cliente; `titulo`, `artista`, `genero`, `anio`, `formato` y `precio` para Disco; y `cliente`, `disco`, `cantidad` para Venta. Los campos opcionales del modelo pueden omitirse. Los archivos omitidos se conservan. Los campos calculados y de sólo lectura se generan en el servidor. Los métodos no admitidos producen 405.

| Ruta adicional | Método | Acceso |
|---|---|---|
| `/api/token/` | POST | Autenticación mediante credenciales. |
| `/api/token/refresh/` | POST | Renovación mediante Refresh Token. |
| `/api/schema/` | GET | Esquema público. |
| `/api/swagger/` | GET | Swagger UI público. |
| `/api/redoc/` | GET | ReDoc público. |

La documentación pública describe las formas de respuesta por rol mediante ejemplos sintéticos. Abrir Swagger no permite consultar los recursos sin token. Artista se conserva como modelo de catálogo y relación de Disco; no se añade un cuarto CRUD API de artistas porque los dos mantenedores de esta ampliación son Cliente y Disco.

## 7. Ejemplos JSON de prueba

Los nombres, correos e IDs siguientes son sintéticos. No prueban que esos registros existan. Crear o seleccionar las relaciones en la base de demostración antes de enviar los ejemplos. Las listas devuelven un arreglo; el detalle devuelve un objeto.

### Crear o modificar un cliente

Entrada de Administrador u Operador:

```json
{
  "nombre": "Cliente de demostración",
  "correo": "cliente@example.invalid",
  "telefono": ""
}
```

El Administrador también puede gestionar el vínculo opcional `usuario` con una cuenta de la base de prueba. Un vínculo duplicado se rechaza con un mensaje genérico; no se revela la identidad del cliente que ya lo utiliza. La respuesta del Operador conserva sólo los datos públicos:

```json
{
  "id": 101,
  "nombre": "Cliente de demostración"
}
```

### Crear o modificar un disco

Entrada JSON cuando no se suben archivos:

```json
{
  "titulo": "Disco de demostración",
  "artista": 101,
  "genero": "Rock",
  "anio": 2026,
  "formato": "CD",
  "precio": "12000",
  "stock": 10,
  "descripcion": "Registro creado en la base de prueba."
}
```

`artista` debe corresponder a un Artista existente. `formato` admite `Vinilo`, `CD` o `Cassette`. `precio` se expresa en **pesos chilenos, CLP, sin decimales** y debe ser mayor que cero. El stock es entero y puede ser cero, pero no negativo. La representación decimal de la API utiliza texto, por ejemplo `"12000"`, para conservar el valor exacto.

### Registrar una venta con Administrador u Operador

```json
{
  "cliente": 101,
  "disco": 101,
  "fecha": "2026-10-04",
  "cantidad": 2
}
```

El servidor toma el precio del Disco. Si el catálogo de prueba vale 12000 CLP, guarda un precio unitario de 12000 CLP y calcula un total de 24000 CLP. En la respuesta administrativa esos importes aparecen; en la respuesta del Operador quedan excluidos. No se aceptan valores enviados por el cliente como autoridad para fijar el precio o total.

### Comprar con el perfil Cliente

```json
{
  "disco": 101,
  "cantidad": 2
}
```

La cuenta determina el Cliente propietario. El servidor determina fecha actual, precio vigente y total. El serializer de compra utiliza sólo `disco` y `cantidad`: los campos extra `cliente`, `fecha`, `precio_unitario` y `total` se ignoran antes de validar relaciones. Enviarlos no permite elegir otro cliente ni modificar los valores decididos por el servidor. La respuesta del Cliente no incluye importes de la Venta ni datos personales privados.

## 8. Precio histórico, stock y relaciones

Crear una venta descuenta unidades. Cambiar la cantidad o el disco devuelve primero el movimiento anterior y luego aplica el nuevo. Eliminar individualmente una venta devuelve sus unidades. La cantidad debe ser positiva y el stock suficiente. Si la operación falla, la transacción se revierte y conserva la venta y el stock anterior.

Al crear, se guarda el precio del catálogo. Al editar una venta del mismo disco se conserva el precio que tenía la venta, aunque el catálogo haya cambiado. Si se cambia de disco se utiliza el precio vigente del nuevo disco. El total se calcula multiplicando cantidad por ese precio unitario.

La API debe invocar el guardado o borrado individual de Venta para utilizar la lógica de stock existente. No se modifica una venta con `QuerySet.update()` ni se elimina un conjunto directamente, porque esas operaciones pueden omitir sus métodos. El mecanismo de transacción y bloqueo se comprueba mediante pruebas; las pruebas locales con SQLite no sustituyen una prueba de concurrencia en la base remota.

Las relaciones usan `PROTECT`: un Cliente o Disco con ventas no puede eliminarse. La API retorna 400 con un mensaje que permite comprender la dependencia sin listar nombres privados, SQL o representaciones internas de los objetos relacionados.

## 9. Imágenes y PDF con multipart

Para crear o editar un Disco con archivo se utiliza `multipart/form-data`, enviando los campos del Disco y los archivos `imagen` o `documento`. En un cliente HTTP se elige el formulario multipart; el cliente genera el límite de separación de la cabecera Content-Type. No enviar contenido binario como una cadena JSON.

| Campo | Validación | Salida de la API |
|---|---|---|
| `imagen` | JPG/JPEG, PNG o WebP, contenido verificado y hasta 5 MB. | URL pública de imagen para los perfiles autorizados. |
| `documento` | Extensión PDF, firma inicial `%PDF-` y hasta 10 MB. | Sólo Administrador ve el nombre base; nunca URL ni ruta privada. Los demás perfiles no reciben metadatos del PDF. |

Administrador y Operador pueden subir los archivos. La autorización para subir un PDF no concede al Operador acceso a sus metadatos en la respuesta. La revisión de firma y extensión del PDF es básica; no se presenta como un análisis completo del documento.

El archivo privado se almacena en `privados/`. La API no agrega un enlace público hacia esa carpeta ni expone `.url` o `.path`. La descarga protegida que ya tenía la web conserva su propio control de sesión y permiso; no se utiliza su ruta como un nuevo endpoint JWT.

## 10. Errores y códigos HTTP

| Código | Situación |
|---|---|
| 200 | Consulta o modificación válida. |
| 201 | Creación válida. |
| 204 | Eliminación válida, sin cuerpo de respuesta. |
| 400 | Campos inválidos, stock insuficiente, relación inexistente o eliminación protegida. |
| 401 | Access Token ausente, inválido o vencido en un recurso protegido. |
| 403 | Cuenta autenticada que no puede ejecutar la operación. |
| 404 | Recurso inexistente o ajeno al Cliente. |
| 405 | Método no admitido por la ruta. |
| 500 | Error inesperado con un mensaje genérico. |

Las validaciones de negocio utilizan `detail` con un mensaje genérico que indica qué revisar sin repetir valores privados. Los errores de autenticación propios de SimpleJWT pueden incluir un código técnico junto al mensaje. Una eliminación 204 cumple el protocolo sin JSON adicional.

| Error de negocio | Mensaje `detail` |
|---|---|
| Validación del serializer o error de integridad. | `Datos no válidos. Revisa los campos y las relaciones.` |
| Validación del modelo, como cantidad o stock. | `No se pudo guardar. Revisa la cantidad, el stock y los datos.` |
| Eliminación protegida por ventas. | `No se puede eliminar un registro con ventas asociadas.` |
| Registro inexistente o ajeno. | `Registro no encontrado.` |

No se devuelve el traceback, una consulta SQL, rutas de archivos, contraseña, hash, correo, teléfono, vínculo de cuenta ni importes privados en errores no administrativos. Los errores de integridad y los errores inesperados utilizan mensajes genéricos; no se convierte la excepción interna directamente en texto público. Un fallo inesperado retorna 500 con este cuerpo:

```json
{
  "detail": "No se pudo completar la operación."
}
```

## 11. Swagger y Authorize

1. Iniciar el servidor y abrir `http://127.0.0.1:8000/api/swagger/`.
2. Abrir `POST /api/token/`, seleccionar **Try it out** y enviar credenciales de una cuenta de prueba propia.
3. Copiar sólo el `access`. Tratar `access` y `refresh` como secretos.
4. Seleccionar **Authorize**. En el esquema JWT de tipo bearer, pegar el Access Token en el campo. Swagger añade `Bearer` a la cabecera.
5. Autorizar y cerrar el cuadro. Ejecutar `GET /api/discos/` y revisar 200 y el JSON.
6. Ejecutar consultas con los distintos perfiles. Comprobar que Cliente sólo ve sus registros y que los campos privados aparecen exclusivamente para Administrador.
7. Antes de publicar una captura, ocultar credenciales y tokens. No capturar la respuesta de token ni el cuadro Authorize con su valor visible.
8. Para mostrar renovación, usar `POST /api/token/refresh/` con el Refresh Token en una demostración privada y actualizar Authorize con el nuevo Access Token.

La demostración de escritura se realiza con datos de prueba en la base separada. Probar CRUD, validación de cantidad, stock y una eliminación protegida. También mostrar una solicitud sin token con 401 y una operación no permitida con 403. La documentación pública y los ejemplos no deben contener información real de usuarios.

La revisión local real dejó estas evidencias, tomadas en el servidor aislado del puerto 8001:

- [Vista general de Swagger](evidencias_api/02_swagger_local.jpg).
- [Configuración de Authorize con campo vacío](evidencias_api/03_authorize_jwt.jpg).
- [Solicitud sin JWT rechazada con 401](evidencias_api/04_sin_jwt_401.jpg).
- [GET protegido de discos con 200 y datos sintéticos](evidencias_api/05_con_jwt_200.jpg).
- [Estado Authorized con token oculto](evidencias_api/06_jwt_autorizado.jpg).

El esquema se genera desde el código con drf-spectacular. Describe métodos, campos requeridos, entradas JSON y multipart, formas de respuesta por perfil, códigos de error y seguridad `jwtAuth`. `@extend_schema` se coloca antes de `@api_view`; las anotaciones se especifican por método para distinguir entradas de salidas. Las variantes que comparten campos se describen con `anyOf`, para que una respuesta válida no se rechace por coincidir con más de una forma documentada. Una prueba valida las respuestas sintéticas y entradas contra el esquema.

## 12. Recomendaciones de seguridad apoyadas por IA

La IA se utilizó para proponer y revisar medidas que luego deben comprobarse en el código y pruebas. No se atribuyen a la IA resultados que no se hayan verificado.

La solicitud real que inició esta implementación fue **"PLEASE IMPLEMENT THIS PLAN"**, seguida del plan aprobado. Su alcance fue agregar la API REST, JWT, control de roles y privacidad, Swagger, pruebas y documentación, conservando la web y los datos existentes y dejando AWS aplazado. Se conserva esa frase como evidencia de la solicitud; el resumen del plan no se presenta como una cita literal.

| Recomendación aplicada en el diseño | Cómo se revisa |
|---|---|
| Exigir JWT y autenticación en los recursos. | Peticiones sin token, con token inválido y vencido deben dar 401. |
| Definir un perfil efectivo a partir de grupos actuales. | Matriz de cuatro roles, cuenta sin grupo y `is_staff` aislado. |
| Elegir campos explícitos por perfil. | Listas, detalles, altas, modificaciones y errores sin filtraciones. |
| Filtrar propiedad antes de consultar un detalle del Cliente. | ID ajeno da 404 y no permite alterarlo. |
| Tomar identidad, fecha y precio de compra desde el servidor. | Intentos de cambiar esos valores no alteran la compra. |
| Validar stock y guardar venta y stock juntos. | Crear, editar, cambiar disco, borrar y revertir un cambio inválido. |
| Mantener archivos privados fuera de la URL pública. | Validaciones de archivo y respuesta sin URL ni ruta PDF. |
| Usar errores genéricos para fallos internos. | 400 de integridad y 500 inesperado sin SQL ni datos privados. |
| Utilizar Access Token corto y Refresh Token separado. | Duraciones de 5 minutos y 1 día; renovación y token vencido. |

Son decisiones concretas del proyecto. La ayuda de IA complementa el trabajo y la verificación; no reemplaza comprender serializers, permisos, JWT y transacciones durante la presentación.

## 13. Verificación y evidencias

Los comandos se ejecutan en el entorno del proyecto:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test discosApi
python manage.py test
python manage.py spectacular --file schema.yml --validate --fail-on-warn
```

La suite usa una base temporal y registros sintéticos. El esquema puede generarse a un archivo temporal; no publicar archivos que contengan tokens o respuestas con información privada. `makemigrations --check --dry-run` comprueba si faltan migraciones, sin crear una migración nueva.

| Comprobación | Resultado registrado |
|---|---|
| Base previa: 94 pruebas de la web. | Aprobadas el 4 de octubre de 2026 antes de la API. |
| Pruebas específicas de API. | 35 aprobadas en 3,139 s; código 0. |
| Suite completa después de la API. | 129 aprobadas en 14,665 s; código 0. |
| `check` y revisión de migraciones después del cambio. | Sin incidencias y `No changes detected`; código 0. |
| Esquema OpenAPI con `--validate --fail-on-warn`. | Válido y sin advertencias; código 0. |
| Rutas públicas de esquema, Swagger y ReDoc. | Respuestas y HTML cubiertos por pruebas; HTTP 200 y Swagger visual comprobados. |
| CRUD, roles, privacidad, stock, JWT, archivos y errores. | Cubiertos por las 35 pruebas API aprobadas. |
| Authorize y consumo desde Swagger en el navegador. | Uso real de Authorize y GET protegido 200 en servidor local aislado. |
| Token/refresh y consultas HTTP de los cuatro roles. | 200 en autenticación, renovación y GET; 401 sin token o con token inválido. |
| Revisión independiente de código y esquema. | Corrección de la unión OpenAPI verificada; sin hallazgos abiertos en su alcance. |
| AWS, base remota y consumo desde EC2. | Aplazados; sin demostración completa. |

Las 35 pruebas incluyen CRUD de tres recursos, roles y precedencia, JWT/refresh/vencimiento, aislamiento de Cliente, manipulación de campos, privacidad de consulta y escritura, precio histórico, stock, rollback, relaciones protegidas, uploads válidos e inválidos, 404/405/500 seguros, documentación pública y validez del esquema. Utilizan SQLite y no demuestran bloqueos concurrentes de MySQL. El rollback de base tampoco garantiza revertir un archivo que el storage ya haya escrito antes de un fallo posterior.

Las consultas HTTP adicionales se ejecutaron sobre un servidor local aislado con SQLite y datos sintéticos, en el puerto 8001. Se emitieron y renovaron tokens para Administrador, Operador, Consulta y Cliente; cada perfil recibió 200 al consultar los tres recursos. Se comprobaron también 401 sin JWT o con JWT inválido, y 200 para web/documentación. El registro público de códigos y conteos está en [verificacion_http.json](evidencias_api/verificacion_http.json), sin credenciales, tokens ni datos de las personas.

Después de actualizar las contraseñas por petición del usuario, se repitieron token, refresh y consultas GET de los tres recursos con las cuatro cuentas locales: todas dieron 200. Los datos del negocio se conservaron. Los códigos y conteos están en [verificacion_http_local.json](evidencias_api/verificacion_http_local.json); no se publica la contraseña elegida.

Las capturas de la web anterior se conservan en `docs/evidencias/`. Las nuevas evidencias locales de la API se guardan en `docs/evidencias_api/`, con datos sensibles ocultos. Una captura local no demuestra consumo desde EC2. Los resultados se transcribieron del reporte de implementación, sus logs y las comprobaciones HTTP/UI reales; las comprobaciones pendientes se completan sólo después de ejecutarlas.

## 14. Checklist de los diez criterios

Los títulos corresponden a la Escala de Apreciación del Word. La tabla registra preparación y evidencia; **no asigna puntaje ni nota**. El criterio de documentación también requiere una demostración técnica presencial, que no puede declararse realizada con un archivo.

| N.º | Criterio de evaluación | Evidencia prevista o disponible | Estado actual |
|---|---|---|---|
| 1 | Configura correctamente Django REST framework. | Dependencias, settings y `check` sin incidencias. | Verificado localmente. |
| 2 | Implementa endpoints RESTful para los mantenedores y transacciones. | CRUD de Cliente, Disco y Venta; 35 pruebas API aprobadas. | Verificado localmente. |
| 3 | Implementa autenticación JWT. | Token, refresh, expiración y protección probados; uso real de Authorize. | Verificado localmente. |
| 4 | Genera respuestas JSON válidas y estructuradas. | JSON de listas/detalles, validaciones y códigos HTTP. | Verificado localmente. |
| 5 | Implementa control de acceso basado en roles. | Cuatro roles, precedencia, cuenta sin rol y `is_staff` aislado. | Verificado localmente. |
| 6 | Protege adecuadamente la información sensible. | Serializers por perfil, propiedad y errores seguros. | Verificado localmente. |
| 7 | Integra Swagger/OpenAPI de forma funcional. | Esquema válido sin advertencias; rutas, ejemplos, Authorize y GET 200. | Verificado localmente. |
| 8 | Aplica recomendaciones de seguridad obtenidas mediante IA. | Medidas de esta guía y pruebas de seguridad aprobadas. | Documentado y verificado localmente. |
| 9 | Despliega exitosamente la solución en AWS EC2. | Acceso/clonación iniciales; faltan base, servicios y consumo remoto. | Pendiente: AWS aplazado. |
| 10 | Presenta documentación y demostración técnica completa. | README, guía, informe y capturas locales; demostración presencial requerida. | Documentación local preparada; demostración presencial y remota pendientes. |

## 15. Alcance de la entrega

La ampliación conserva la web y añade una entrada REST sobre los modelos existentes. El foco es proteger datos y acciones según perfil, mantener el stock y dejar instrucciones que puedan repetirse con datos de prueba. Una entrega local verificada debe distinguirse de la disponibilidad remota: el paso a AWS sigue pendiente hasta configurar y comprobar su base, servicios y endpoints.

Para el requisito de nube, revisar la guía existente [despliegue_ec2.md](despliegue_ec2.md) y completar sólo con resultados reales. Para el funcionamiento previo de la web, consultar [README](../README.md), [fuentes.md](fuentes.md) y [uso_ia.md](uso_ia.md). No se reemplaza el documento técnico anterior ni se inventan evidencias para completar la rúbrica.

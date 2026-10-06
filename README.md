# Feria NewMix: catálogo y ventas de discos

Este proyecto amplía el prototipo de Feria NewMix. Permite administrar artistas, discos y clientes, y registrar ventas que relacionan un cliente con un disco. Un cliente nuevo puede crear su cuenta, comprar un disco y consultar sus propias compras. Usa Django ORM, formularios, plantillas y permisos de usuario. La ampliación de la Sumativa 3 agrega una API REST con Django REST Framework, autenticación JWT y documentación Swagger/OpenAPI sobre los mismos modelos.

Los mantenedores que participan en la transacción son **Cliente** y **Disco**. **Venta** guarda sus llaves foráneas. **Artista** conserva la información del catálogo original y se relaciona con Disco.

El catálogo de origen contiene 13 artistas, 37 discos y sus 50 imágenes. Los JSON se conservan para importar esos datos a la base; las vistas consultan los modelos ORM. No se incluyen clientes ni ventas inventados como registros reales.

Repositorio del proyecto: [ale13camp/FeriaNewMix-BackEnd](https://github.com/ale13camp/FeriaNewMix-BackEnd).

El 4 de octubre de 2026 se verificó el despliegue en AWS EC2 con MariaDB, Gunicorn y NGINX. Django utiliza el motor `mysql` y la base `newmix` de la instancia. Se comprobaron web, API, JWT de los cuatro perfiles, Swagger y phpMyAdmin remoto; 86 comprobaciones HTTP de CRUD, permisos y stock conservaron los registros originales. Las evidencias y los límites están en la [guía EC2](docs/despliegue_ec2.md). HTTPS sigue pendiente; las contraseñas y los tokens se probaron mediante túnel SSH. La presentación presencial al docente todavía debe realizarse.

El **5 de octubre de 2026** se renovó el acceso tras reiniciar el laboratorio. Se verificó Swagger en el navegador de EC2: emisión JWT 200, estado **Authorized** y **Execute** de `GET /api/discos/1/` con 200. También aprobaron 76 comprobaciones de la web remota: 62 funcionales y 14 de cierre. Incluyen formularios, búsqueda, Admin, imagen/PDF, permisos, CSRF, validación y baja del registro sintético. El cierre conservó los 4 clientes, 37 discos, 6 ventas y todo su stock; los 50 archivos originales coincidieron por SHA256 y se retiraron los dos archivos de prueba. La IP observada fue `35.168.62.2`; debe revisarse antes de otra presentación porque puede cambiar.

## Abrir la copia local preparada

En este equipo ya están preparados `.venv`, `.env` y la base local. Desde esta carpeta se puede iniciar el proyecto sin repetir su instalación:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Abrir `http://127.0.0.1:8000/`. Los accesos de prueba están en `.evaluacion/ACCESO_LOCAL.txt`, un archivo privado que no se sube a GitHub. Para detener el servidor iniciado en la terminal, presionar `Ctrl+C`. Esta preparación es local; en otro equipo se siguen las instrucciones de instalación siguientes.

La verificación inicial del 3 de octubre de 2026 aprobó 43 pruebas. El ajuste del precio automático amplió la suite a 53; el registro y las compras, a 73; y las mejoras del perfil y filtros, a 94. También se comprobaron las migraciones, rutas, 50 imágenes y los recorridos de cliente en el navegador. Los resultados históricos están en `docs/evidencias/verificacion_local.txt`. El 4 de octubre se repitieron las 94 pruebas antes de la ampliación de la API y aprobaron. La ampliación agrega 35 pruebas API: aprobaron las 129 pruebas totales, `check`, la revisión de migraciones y la validación del esquema OpenAPI sin advertencias. Los resultados y límites están en [API Sumativa 3](docs/API_Sumativa3.md). El servidor EC2 ejecutó la rama `codex/sumativa-3-api`, commit `a53105b5eb3a880cd8a44d15bc5342c6854fd128`, durante la verificación remota. Las 129 pruebas corresponden a la suite local; las 86 comprobaciones HTTP corresponden al backend con MariaDB en EC2.

## Estructura

```text
config/          Configuración, rutas generales y WSGI.
artistasApp/     Modelo Artista, formularios, vistas, rutas y Admin.
discosApp/       Modelo Disco, catálogo, archivos e importación inicial.
discosApi/       Serializers, permisos por rol, vistas REST, rutas y pruebas API.
ventasApp/       Modelos Cliente y Venta, CRUD, stock, compra e historial propio.
usuariosApp/     Registro de clientes y creación de cuatro grupos de permisos.
templates/       Base común, formularios, listas, confirmación y login.
static/          Bootstrap, CSS e imágenes originales.
media/           Imágenes cargadas; se crea al utilizar la aplicación.
privados/        Documentos PDF; acceso mediante una vista protegida.
docs/            Fuentes, uso de IA, guía API y guía de despliegue.
```

`media/`, `privados/`, `.env`, bases SQLite y entornos virtuales quedan fuera de Git. Las migraciones forman parte del código que debe subirse al repositorio.

## Recorrido según los PDF 0 a 10

### 0. Entorno y configuración inicial

El PDF `0 al iniciar.pdf`, pp. 1–5, explica entorno virtual, dependencias, proyecto, idioma, aplicación, vistas y rutas. Este proyecto ya existe: no hay que volver a ejecutar `startproject` o `startapp` sobre sus carpetas.

Desde PowerShell, dentro de la carpeta del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si `.venv` ya funciona, basta con activarlo e instalar las dependencias. El directorio `venv` heredado puede contener una ruta a otro equipo; se utiliza `.venv` para el entorno de este trabajo. Si PowerShell restringe la activación, se pueden ejecutar los comandos con `.\.venv\Scripts\python.exe` en lugar de `python`.

`requirements.txt` fija Django 5.2.17, Pillow, python-dotenv, mysqlclient 2.3.0, Django REST Framework 3.16.1, SimpleJWT 5.5.1 y drf-spectacular 0.30.0. Gunicorn se instala en Linux. Si mysqlclient no se instala, hay que revisar las dependencias del cliente MySQL del equipo; no reemplazar el motor silenciosamente.

`config/settings.py` define español de Chile y zona horaria `America/Santiago`.

### 1. Rutas entre aplicaciones

El PDF `1 rutas entre aplicaciones.pdf`, pp. 1–3, explica las rutas propias y `include()`. `config/urls.py` conecta las rutas de artistas, discos, ventas, autenticación y Admin.

Las rutas de catálogo originales se conservan. Para administrar se utilizan las rutas nombradas `artistas_lista`, `discos_lista`, `clientes_lista` y `ventas_lista`, junto con sus acciones crear, editar y eliminar. Los enlaces de las plantillas utilizan sus nombres con `{% url %}`.

### 2. Plantillas y archivos estáticos

El PDF `2 templates en django.pdf`, pp. 1–5 y 7–10, explica `templates`, `render`, datos y `static`. Las vistas entregan un contexto a las plantillas. Bootstrap y el CSS se sirven desde `static/`.

### 3. Herencia y datos mostrados

El PDF `3 cargando datos al templates en django.pdf`, pp. 1–6, usa Bootstrap local, una plantilla base, bloques y bucles. Aquí las páginas heredan de `base.html` y muestran los resultados del ORM con `for`.

Los datos simulados en listas son parte de la explicación inicial del PDF. En esta evaluación, las listas de artistas, discos, clientes y ventas se obtienen de la base de datos.

### 4. Modelos, relaciones y base de datos

El PDF `4 creando el modelo.pdf`, pp. 1–8, presenta MySQL/phpMyAdmin, modelos, `ForeignKey` y migraciones. `tips_modelo.pptx`, diapositivas 3–7, complementa los campos y relaciones.

| Modelo | Datos principales | Relación |
|---|---|---|
| Artista | Nombre, género, país, año de formación, integrantes, biografía e imagen | Un artista puede tener varios discos. |
| Disco | Título, género, año, formato, precio, stock, descripción, imagen y documento | Pertenece a un artista. |
| Cliente | Nombre y correo; teléfono y cuenta de usuario opcionales | Puede tener varias ventas; una cuenta corresponde a un cliente. |
| Venta | Fecha, cantidad y precio unitario | Tiene un cliente y un disco. |

Los precios se expresan en pesos chilenos con `DecimalField` y sin decimales. El total de la venta se calcula como cantidad por precio unitario. El precio de la venta queda guardado, de modo que una modificación posterior del precio del disco no modifica ventas anteriores.

Al registrar una venta, el precio unitario se completa con el precio del disco seleccionado. El botón de su ficha abre el formulario con ese disco y su precio precargados. El campo no se edita manualmente: Django toma el precio del catálogo aunque el navegador envíe otro valor. Al editar una venta del mismo disco se conserva su precio histórico; si se cambia de disco, se toma el precio del nuevo disco.

Las relaciones usan `PROTECT`: no se elimina un artista que tiene discos, ni un cliente o disco asociado a ventas. Primero hay que resolver los registros relacionados desde las funciones autorizadas.

Para MySQL local, crear la base `newmix` y su usuario desde phpMyAdmin, como explica el PDF 4. Copiar el ejemplo de configuración **si no existe ya un `.env` propio**:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Pegar la clave generada en `SECRET_KEY` y completar los valores de `.env`:

```dotenv
SECRET_KEY=REEMPLAZAR_CON_LA_CLAVE_GENERADA
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=mysql
DB_NAME=newmix
DB_USER=newmix_app
DB_PASSWORD=REEMPLAZAR_CON_LA_CONTRASENA_PROPIA
DB_HOST=127.0.0.1
DB_PORT=3306
```

Si aún no hay servidor MySQL disponible, `DB_ENGINE=sqlite` permite comprobaciones locales provisionales. Luego hay que ejecutar la preparación de la base también con MySQL y demostrar sus tablas en phpMyAdmin. Las dos bases son independientes; cambiar `.env` no traslada automáticamente los datos.

```powershell
python manage.py migrate
python manage.py importar_catalogo
```

Las migraciones incluidas crean las tablas. `makemigrations` se usa cuando se cambia un modelo, no como sustituto de `migrate`. `importar_catalogo` conserva los IDs originales, copia las imágenes a `media/` y sólo agrega los registros que no existen. Repetirlo no debe sobrescribir ediciones existentes; no es un comando para restaurar el stock original.

### 5. Django Admin

El PDF `5 El Admin de Django.pdf`, pp. 1 y 3, explica el superusuario y registro de modelos. Las cuatro entidades se registran en Admin para administrar y buscar sus datos.

```powershell
python manage.py crear_perfiles
python manage.py createsuperuser
```

El comando `createsuperuser` solicita los datos; no hay cuentas ni contraseñas predeterminadas en este README. Ingresar a `/admin/`, crear los usuarios necesarios y asignarles el grupo correspondiente. El superusuario tiene todos los permisos.

Pertenecer al grupo Administrador da permisos; para ingresar al sitio Admin también se necesita marcar al usuario como personal (`is_staff`). Operador y Consulta pueden trabajar desde la interfaz web sin acceso al Admin. Para conservar el perfil asignado, usar un solo grupo y evitar permisos individuales adicionales que lo amplíen.

### 5_b. Variables de entorno

El PDF `5_b Variables de entorno.pdf`, pp. 1–2, explica `.env`, `load_dotenv`, `os.getenv` y `.gitignore`. La configuración sensible se carga desde `.env`. `.env.example` muestra los nombres necesarios sin credenciales reales.

No se suben claves privadas, contraseñas o `.env` a GitHub. La aplicación rechaza la clave de ejemplo que comienza con `CAMBIAR`.

### 6. Formularios

El PDF `6 formularios en Django.pdf`, pp. 1–5, enseña `ModelForm`, widgets y recepción de POST. Los formularios del proyecto están asociados a sus modelos. Una solicitud GET muestra el formulario; una solicitud POST valida y guarda los datos.

Al editar se entrega `instance=registro` para mostrar sus valores. Las plantillas incluyen `{% csrf_token %}` y muestran los errores del formulario.

### 7. Validación

El PDF `7 Validación de formularios.pdf`, pp. 1–4, explica campos opcionales y validación. Aquí se valida correo, campos obligatorios, años y cantidades positivas. El stock del disco puede ser cero, pero no negativo. El precio y la cantidad vendida deben ser mayores que cero.

Una venta con más unidades que las disponibles se rechaza. Los mensajes permiten corregir el formulario. Los datos de clientes y ventas que se creen para una demostración deben identificarse como prueba.

### 8. CRUD y búsqueda

El PDF `8 CRUD Empleado.pdf`, pp. 1–9, explica lista, alta, edición precargada y confirmación de borrado. `filtros.pdf`, p. 1, apoya las consultas ORM para búsqueda.

En cada lista se puede buscar, agregar, editar o eliminar según permisos. El enlace de eliminar muestra una confirmación; el borrado se ejecuta mediante POST.

Las ventas actualizan stock al crear, editar y eliminar: al crear se descuentan unidades; al editar se devuelve el movimiento anterior y se aplica el nuevo; al eliminar se restituyen unidades. Esta lógica también se aplica al guardado y borrado individual en Admin.

El ajuste de stock usa una transacción de base de datos para guardar juntos la venta y su movimiento. Es una decisión añadida para esta evaluación, no un tema explicado en los PDF principales. No usar `bulk_create`, `bulk_update`, `QuerySet.update()` o borrado directo de conjuntos de ventas para alterar transacciones: esas operaciones pueden omitir la lógica de los métodos del modelo. Usar los formularios, el Admin configurado o los métodos individuales de Venta.

### 9. Imágenes y documentos

El PDF `9 Manejo de imagenes.pdf`, pp. 1–6, explica Pillow, `ImageField`, `MEDIA_ROOT`, `request.FILES` y formularios `multipart/form-data`.

Artista y Disco permiten cargar imágenes JPG, PNG o WebP de hasta 5 MB, verificando su contenido. Disco también permite adjuntar un PDF de hasta 10 MB mediante `FileField`. Se revisan su extensión y firma inicial; esa revisión básica no analiza todo el contenido del documento.

Las imágenes quedan en `media/`. Los documentos quedan en `privados/`, definido por `PRIVATE_MEDIA_ROOT`, y se descargan mediante la vista `discos_documento`, con sesión y permiso de lectura de discos, usando `FileResponse`. No se configura una URL pública de NGINX hacia `privados/`.

La base guarda la referencia del archivo; el contenido se guarda en disco. Para respaldar la información hay que copiar la base y las carpetas de archivos.

### 10. Inicio de sesión y perfiles

El PDF `10 Inicio de sesión y permisos.pdf`, pp. 1–7, explica autenticación y `permission_required`. Se usan las rutas de Django Authentication y una plantilla de login propia. El cierre de sesión usa POST con CSRF.

| Perfil | Consultar y buscar | Crear | Modificar | Eliminar | Administrar usuarios |
|---|---|---|---|---|---|
| Administrador | Sí | Sí | Sí | Sí, con restricciones de relaciones | Sí, desde Admin con `is_staff` |
| Operador | Sí | Sí | Sí | No | No |
| Consulta | Sí | No | No | No | No |
| Cliente | Catálogo y sus propias compras | Su compra | Sus datos de perfil | No | No |

El menú y los botones dependen de permisos. Las vistas verifican los permisos en el servidor, incluso si alguien escribe una URL directamente. La restricción por sesión con `login_required` es una decisión de implementación adicional; no se atribuye a la captura del PDF 10.

El inicio es público y muestra **Registrarme como cliente**. El formulario `/cuentas/registro/` solicita usuario, nombre, correo, teléfono opcional y contraseña con confirmación. Django valida la contraseña; la cuenta y el Cliente se guardan juntos. El registro inicia la sesión y asigna únicamente el grupo Cliente, sin acceso al Admin ni al CRUD general.

El cliente entra a la tienda, abre la ficha del disco y selecciona **Comprar**. Sólo ingresa la cantidad. El servidor toma su cliente, el disco de la ficha, la fecha y el precio vigente del catálogo. **Confirmar compra** registra una Venta y descuenta stock; una cantidad inválida o sin stock suficiente se rechaza. El total mostrado cambia con la cantidad. **Mis compras** muestra únicamente las ventas de su cuenta, sin edición ni eliminación. No hay carrito ni cobro real en línea, según lo confirmado por el usuario.

**Mi perfil**, en `/cuentas/perfil/`, permite editar nombre, correo y teléfono. El nombre de usuario es de sólo lectura. Al guardar se actualizan juntos los datos del Cliente y el nombre/correo de su cuenta User. Una cuenta no puede elegir un cliente ajeno ni modificar permisos desde este formulario.

Desde el perfil se accede a **Cambiar contraseña**, en `/cuentas/cambiar-contrasena/`. El formulario valida la contraseña actual, la nueva y su confirmación. Si el cambio es correcto, conserva la sesión y vuelve al perfil con un mensaje. Ambas páginas requieren una cuenta de cliente vinculada.

**Mis compras** muestra portadas y títulos enlazados a las fichas. Permite buscar por título y filtrar por fecha desde/hasta, incluyendo ambos límites. **Limpiar** vuelve al historial completo del cliente. Una fecha inválida o un rango invertido muestra un error para corregirlo. Estas mejoras no requieren nuevas tablas ni cambios de stock.

Los clientes creados antes de esta ampliación conservan sus datos y pueden seguir usándose en ventas administrativas aunque no tengan una cuenta vinculada. En otras instalaciones hay que ejecutar `python manage.py migrate` y `python manage.py crear_perfiles` para aplicar la migración y preparar el nuevo grupo.

## Ejecutar y revisar localmente

Con el entorno activado, `.env` completo y migraciones aplicadas:

```powershell
python manage.py check
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/` e iniciar sesión con una cuenta propia. Para detener el servidor, presionar Ctrl+C. `runserver` se usa para desarrollo; EC2 utiliza Gunicorn y NGINX.

Los comandos siguientes permiten revisar sistema, migraciones y pruebas. Su inclusión es una instrucción, no una afirmación de que ya pasaron:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Para la demostración presencial: revisar CRUD y búsquedas en las cuatro entidades, los cuatro perfiles, una carga de imagen/PDF y una venta con ajuste de stock. Mostrar también registro de cliente, compra e historial propio. Confirmar los mismos registros y relaciones en phpMyAdmin conectado al MySQL de EC2.

## API REST: Sumativa 3

La API usa los modelos Cliente y Disco como mantenedores, y Venta como transacción. Las vistas de la web siguen usando sesiones; las rutas de negocio de la API requieren un Access Token JWT. El token de acceso dura 5 minutos y el de renovación 1 día. Los permisos se comprueban con los grupos actuales de Django en cada petición.

Con el servidor local en ejecución:

| Ruta | Uso |
|---|---|
| `/api/clientes/` y `/api/clientes/{id}/` | Lista, alta y detalle, edición o eliminación de clientes según perfil. |
| `/api/discos/` y `/api/discos/{id}/` | Lista, alta y detalle, edición o eliminación de discos según perfil. |
| `/api/ventas/` y `/api/ventas/{id}/` | Consulta y operaciones de ventas; Cliente sólo compra y consulta sus registros. |
| `/api/token/` | Obtener Access Token y Refresh Token con una cuenta propia. |
| `/api/token/refresh/` | Obtener un nuevo Access Token a partir del Refresh Token. |
| `/api/schema/` | Esquema OpenAPI. |
| `/api/swagger/` | Documentación interactiva y botón Authorize. |
| `/api/redoc/` | Documentación de lectura. |

Las colecciones admiten GET y POST; el detalle admite GET, PUT y DELETE. El Administrador tiene CRUD completo, el Operador puede consultar, crear y modificar, y Consulta sólo lee. Cliente consulta el catálogo, su registro y sus compras; para comprar envía sólo `disco` y `cantidad`. Los campos sensibles se restringen según perfil. El precio del catálogo es público, mientras que los importes de las ventas son privados y sólo se retornan al Administrador.

Para revisar la API sin cambiar la base local:

```powershell
python manage.py test discosApi
python manage.py test
python manage.py spectacular --file schema.yml --validate --fail-on-warn
```

Las pruebas crean una base temporal. Para una demostración manual que modifique datos, usar una base separada con registros identificados como prueba. No publicar tokens, contraseñas ni ejemplos con información real de clientes. La [guía técnica de la API](docs/API_Sumativa3.md) detalla instalación, JSON de ejemplo, privacidad, stock, errores, Swagger y el estado de los diez criterios de la evaluación.

## Documentación y requisitos externos

- [Guía de despliegue EC2](docs/despliegue_ec2.md): configuración comprobada, instrucciones para repetirla y evidencia remota. Incluye las plantillas públicas de `docs/config_ec2/`, sin credenciales.
- [Fuentes y decisiones](docs/fuentes.md): material de clases por archivo y página, y decisiones añadidas.
- [Uso de IA](docs/uso_ia.md): prompt real de esta conversación y resumen de su aplicación.
- [API Sumativa 3](docs/API_Sumativa3.md): contrato de servicios, seguridad, verificación y checklist de la evaluación.
- [Informe técnico Sumativa 3 en Word](<docs/Informe tecnico Sumativa 3 Feria NewMix.docx>): documento de entrega de la API y su evaluación.

Las evidencias remotas del 4 y 5 de octubre se encuentran en `docs/evidencias_ec2/`. Los JSON de verificación publican códigos y conteos, sin contraseñas, tokens ni datos personales. El laboratorio AWS debe estar activo durante la presentación; comprobar antes la IP actual y el túnel. La guía API incluye un recorrido para mostrar los diez criterios. La calificación depende de la evaluación del docente y de la demostración presencial.

# Demostración técnica de Feria NewMix

Preparación actualizada el 5 de octubre de 2026. La rúbrica de **Eva Sumativa 3 - flex.docx** contiene diez criterios de 10 puntos, con niveles Logrado 10, Medianamente logrado 7, Por lograr 4 y No logrado 0. Esta guía organiza la evidencia para la revisión; la puntuación la decide el evaluador.

El proyecto conserva la web y expone Cliente, Disco y Venta mediante una API REST. Venta relaciona los dos mantenedores y ajusta stock. Las pruebas locales y remotas del 4 de octubre están documentadas. La revisión del 5 de octubre añadió Swagger interactivo en EC2 y 76 comprobaciones web: 62 funcionales de imagen/PDF y permisos, más 14 de cierre. La exposición presencial debe realizarla el estudiante.

## Preparar el entorno antes de exponer

1. Iniciar AWS Academy y comprobar que el laboratorio indique Ready. Revisar la IPv4 actual de la instancia; puede cambiar al reiniciar. Confirmar que NGINX y ALLOWED_HOSTS la acepten. El 5 de octubre se observó `35.168.62.2`; revisar la dirección actual antes de usarla.
2. Comprobar acceso SSH y servicios `mariadb`, `newmix` y `nginx` activos. Confirmar `mariadb.socket` habilitado/activo y MariaDB sólo en `127.0.0.1:3306`; el 5 de octubre se corrigió su dependencia de arranque. Confirmar la rama `codex/sumativa-3-api` y el commit del código desplegado. Los documentos pueden tener un commit posterior al de implementación.
3. Abrir el túnel privado. La web de EC2 llega al PC mediante `http://127.0.0.1:8008/`; Swagger mediante `/api/swagger/`; phpMyAdmin mediante `http://127.0.0.1:8081/`. Estas direcciones locales apuntan a EC2, no a la base local del PC.
4. Si phpMyAdmin no está activo, iniciar su servidor temporal privado. El laboratorio puede detenerlo al cerrar la sesión; no reinstalar MariaDB ni repetir la restauración de datos.
5. Utilizar las cuentas privadas de demostración de Administrador, Operador, Consulta y Cliente. No mostrar contraseñas, tokens, `.env`, hashes ni los datos privados de clientes. El acceso autenticado se demuestra por SSH mientras HTTPS público esté pendiente.

## Recorrido sugerido de diez a doce minutos

| Paso | Qué mostrar y explicar | Criterios |
|---|---|---|
| 1 | EC2 activa, dirección actual, conexión SSH, entorno virtual y servicios; explicar NGINX → Gunicorn/Django → MariaDB. | 9 y 10 |
| 2 | `requirements.txt`, `settings.py`, rutas y un serializer. Explicar que la API usa los mismos modelos que la web. | 1 y 2 |
| 3 | Solicitar token en `/api/token/`, identificar access y refresh en privado, renovar con `/api/token/refresh/`. | 3 |
| 4 | Desde Swagger, seleccionar Authorize, pegar sólo access, confirmar Authorized y ejecutar GET de Disco. Mostrar código 200 y JSON real, evitando el bloque Curl con el token. | 3, 4 y 7 |
| 5 | Consultar sin token y obtener 401. Comparar Administrador con Consulta: los campos privados de Cliente y los importes de Venta sólo aparecen para Administrador. Consulta no crea ni elimina. | 3, 5 y 6 |
| 6 | Crear un Cliente y un Disco temporales claramente identificados. Ejecutar POST, GET, PUT y DELETE de mantenedores con Administrador. Usar una Venta temporal sobre ese Disco para enseñar stock. | 2 y 4 |
| 7 | Crear venta de una unidad: stock 10 → 9. Editar a dos: 9 → 8. Eliminar únicamente esa venta: 8 → 10. Mostrar IDs y ForeignKey en phpMyAdmin. | 2, 4 y 9 |
| 8 | Explicar validadores, serializers por rol, filtros de propiedad, mensajes de error y archivos privados. Mostrar en `docs/uso_ia.md` la solicitud real y las medidas aplicadas. | 5, 6 y 8 |
| 9 | Mostrar informe, diagrama, capturas y resultados de pruebas. Explicar los límites: HTTPS público pendiente y demostración de la fecha indicada. Cerrar el túnel y phpMyAdmin al finalizar. | 10 |

Las escrituras se realizan únicamente sobre registros creados para esta demostración. Anotar sus IDs al crearlos y retirar primero la venta, luego el Disco y el Cliente temporales. No modificar o borrar los registros originales para demostrar el CRUD. Si una prueba falla, conservar el mensaje y resolver el registro temporal antes de cerrar.

## Evidencia por criterio

| Nº | Criterio de la rúbrica | Evidencia disponible | Paso presencial |
|---|---|---|---|
| 1 | Configura correctamente Django REST framework. | Dependencias y configuración; `check` sin incidencias. | Explicar apps y REST_FRAMEWORK. |
| 2 | Implementa endpoints RESTful para los mantenedores y transacciones. | CRUD Cliente/Disco/Venta; pruebas de precio y stock. | Ejecutar acciones sobre datos temporales. |
| 3 | Implementa autenticación JWT. | Emisión, renovación, rechazo sin JWT y Authorize. | Explicar access, refresh y protección. |
| 4 | Genera respuestas JSON válidas y estructuradas. | Serializers explícitos y códigos 200/201/204/400/401/403/404. | Mostrar JSON y error de validación; DELETE 204 sin cuerpo. |
| 5 | Implementa control de acceso basado en roles. | Cuatro grupos y pruebas de acciones permitidas/rechazadas. | Comparar Administrador, Operador y Consulta. |
| 6 | Protege adecuadamente la información sensible. | Campos por rol, propiedad del Cliente, documentos privados y errores seguros. | Comparar respuestas sin exponer secretos. |
| 7 | Integra Swagger/OpenAPI de forma funcional. | Esquema validado; JWT 200, Authorized y Execute GET Disco 200 en EC2 el 5 de octubre. | Repetir el recorrido sin mostrar tokens. |
| 8 | Aplica recomendaciones de seguridad obtenidas mediante IA. | Solicitud real, recomendaciones aplicadas y verificación en código. | Explicar una medida y señalar dónde se implementó. |
| 9 | Despliega exitosamente la solución en AWS EC2. | MariaDB, migraciones, NGINX/Gunicorn, API y phpMyAdmin remotos comprobados. | Mostrar el servidor y la conectividad actual. |
| 10 | Presenta documentación y demostración técnica completa. | Informes, guías, capturas y resultados locales/remotos. | Realizar la exposición y responder preguntas. |

## Explicaciones breves para practicar

- **Serializer:** convierte los modelos a JSON y valida los datos recibidos; sus campos explícitos permiten restringir la salida según perfil.
- **JWT:** access autoriza las solicitudes y dura cinco minutos; refresh permite obtener otro access y dura un día. La autorización también comprueba los grupos actuales de Django.
- **Roles:** Administrador tiene CRUD; Operador consulta, crea y modifica; Consulta lee; Cliente consulta su información y registra su propia compra. La precedencia es Administrador > Operador > Consulta > Cliente.
- **Privacidad:** los correos, teléfonos, vínculo a usuario e importes de Venta se restringen en la API. El precio del Disco es parte pública del catálogo. Los documentos privados no devuelven URL pública.
- **ForeignKey:** Venta guarda el ID de Cliente y Disco; las relaciones evitan reemplazarlos por nombres sueltos. PROTECT impide eliminar registros que tienen ventas asociadas.
- **Stock:** crear, modificar o eliminar una Venta ajusta el Disco dentro de una transacción. El precio histórico se conserva aunque cambie después el catálogo.
- **Base:** EC2 utiliza MariaDB mediante el backend mysql de Django; SQLite se reserva para la revisión local. phpMyAdmin consulta la misma newmix de la instancia.
- **IA:** apoyó configuración, validación, permisos, errores y documentación. Se conserva el prompt real; el estudiante debe explicar el código y contrastar sus resultados.

## Revisión complementaria de Sumativa 2

El informe técnico de la web conserva las pruebas anteriores de modelos, Admin, formularios, búsqueda, imágenes, PDF y perfiles. El 5 de octubre aprobaron 76 comprobaciones remotas: 62 funcionales de alta, edición, búsqueda/filtros, Admin, confirmación de baja, roles, validación y CSRF, más 14 de cierre. Se cargaron una imagen y un PDF sintéticos, se compararon las descargas por SHA256 y se comprobaron la protección del PDF y los rechazos según perfil. Los 4 clientes, 37 discos y 6 ventas originales coincidieron antes/después. La baja web del disco sintético y la retirada de sus dos archivos quedaron verificadas. El cierre conservó los 4 clientes, 37 discos y 6 ventas originales, todo su stock y los 50 archivos originales exactos por SHA256, sin archivos de prueba adicionales. No presentar una captura local como si proviniera de EC2.

Evidencias nuevas: `docs/evidencias_ec2/swagger_get_ec2.png`, `swagger_ui_verificado.json`, `web_rubrica_verificado_20261005.json` y `cierre_web_demo_verificado_20261005.json`. Las plantillas de servicios, MariaDB/socket y NGINX se conservan en `docs/config_ec2/` sin credenciales. El recorrido Swagger fue real: emisión JWT 200, Authorize en estado Authorized y Execute de GET `/api/discos/1/` con respuesta 200 mediante el túnel a EC2.

Las evidencias técnicas reducen los pendientes de implementación. La disponibilidad del laboratorio y la explicación presencial son necesarias para completar la entrega; ninguna tabla de este documento asigna una nota obtenida.

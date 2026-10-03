# Fuentes y decisiones del proyecto

La fuente principal es **Eva Sumativa 2 - flex.docx**, ubicado en `C:\Users\asd123\Desktop\Ale Back End\`. Exige mantenedores y una transacción con ForeignKey, Django ORM, migraciones, CRUD web y Admin, imágenes y documentos, tres perfiles, `.env`, GitHub y EC2 con base de datos dentro de la instancia y revisión desde phpMyAdmin.

Se consultaron sus secciones **Contexto**, **Requerimientos de Base de Datos**, **Modelado de Datos Obligatorio**, **Gestión de Imágenes y Archivos**, **Seguridad de la Aplicación**, **Uso Obligatorio de Inteligencia Artificial** y **Entregables**. Se indican secciones porque no se verificó una paginación fija del Word; no se inventan números de página.

Los PDF y la presentación se encuentran en `C:\Users\asd123\Desktop\Ale Back End\Unidad 1 y 2`. Los números siguientes corresponden a páginas del archivo PDF, no a líneas del código.

## Orden de los temas de clase

| Fuente exacta | Páginas | Aplicación en el proyecto |
|---|---|---|
| `0 al iniciar.pdf` | 1–2 | Entorno virtual, Django, requirements y servidor de desarrollo. |
| `0 al iniciar.pdf` | 3–5 | Idioma, zona horaria, aplicaciones, vistas y rutas. |
| `1 rutas entre aplicaciones.pdf` | 1–3 | `urls.py` por aplicación e `include()`. |
| `2 templates en django.pdf` | 1–5 | Organización de plantillas, `render` y contexto. |
| `2 templates en django.pdf` | 7–10 | Imágenes estáticas y CSS con `{% static %}`. |
| `3 cargando datos al templates en django.pdf` | 1–6 | Bootstrap local, `base.html`, bloques, `extends`, `for` y navegación. |
| `4 creando el modelo.pdf` | 1–3 | MySQL/phpMyAdmin, usuario y mysqlclient; SQLite como configuración inicial. |
| `4 creando el modelo.pdf` | 4–8 | Modelos, llaves foráneas, migraciones y tablas. |
| `5 El Admin de Django.pdf` | 1 y 3 | Superusuario, registro de modelos, usuarios y grupos. |
| `5_b Variables de entorno.pdf` | 1–2 | python-dotenv, `.env`, `os.getenv`, `.gitignore` y `.env.example`. |
| `6 formularios en Django.pdf` | 1–5 | `ModelForm`, widgets, POST, validación y plantillas. |
| `7 Validación de formularios.pdf` | 1–4 | Campos opcionales y validación con `clean_*`. |
| `8 CRUD Empleado.pdf` | 1–5 | Listar y agregar mediante ORM y formularios. |
| `8 CRUD Empleado.pdf` | 6–9 | Editar con `instance`, confirmación y eliminación sólo por POST. |
| `9 Manejo de imagenes.pdf` | 1–6 | Pillow, ImageField, media, `request.FILES` y `multipart/form-data`. |
| `10 Inicio de sesión y permisos.pdf` | 1–4 | Login, autenticación, CSRF y ajustes de sesión. |
| `10 Inicio de sesión y permisos.pdf` | 5–7 | `permission_required` y permisos asignados desde Admin. |

## Material complementario entregado

| Fuente exacta | Ubicación | Aplicación |
|---|---|---|
| `tips_modelo.pptx` | Diapositivas 3–5 | Campos, validadores, DecimalField, fechas y `upload_to`. |
| `tips_modelo.pptx` | Diapositivas 6–7 | `choices`, ForeignKey y opciones como PROTECT. |
| `filtros.pdf` | Página 1 | `all`, `filter`, búsquedas y orden de resultados. |
| `crear proyecto.pdf` | Páginas 7–12 y 22–26 | Preparación de proyecto, Git y clonación/ejecución. |
| `crear proyecto.pdf` | Páginas 27–41 | Ramas, cambios, revisión y actualización. |
| `Manejo de versiones Github.pdf` | Páginas 3–13 | Conceptos, comandos, estados y ramas de Git. |
| `AWS/Levantar Django con NGINX y GUNICORN en AMI Linux 2023 AWS.pdf` | Páginas 1–4 | Preparación de servidor, clonación, entorno y dependencias. |
| `AWS/Levantar Django con NGINX y GUNICORN en AMI Linux 2023 AWS.pdf` | Páginas 5–8 | Gunicorn, systemd, NGINX y revisión desde navegador. |

Los ejemplos de Git y AWS explican procedimientos. No son evidencia de que el repositorio o la instancia de este proyecto se haya configurado o desplegado.

## Decisiones añadidas para esta evaluación

1. **Cliente, Disco y Venta.** La evaluación permite elegir una problemática. Se mantiene el catálogo musical y se añade una venta entre cliente y disco, opción confirmada por el usuario. Cada venta contiene un disco; no se agrega carrito o procesamiento de pagos.
2. **Precio histórico y stock.** Venta guarda el precio unitario en CLP sin decimales. Su total se calcula. El stock se ajusta al crear, editar o eliminar. Las transacciones de base de datos y el bloqueo de registros son una ayuda técnica añadida para mantener coherencia; no se afirma que los PDF principales enseñen esa lógica. El Word permite ayuda de IA para modelos, CRUD y optimización.
3. **Protección de relaciones.** Se utiliza PROTECT para evitar eliminar registros con dependencias. Esta opción aparece en `tips_modelo.pptx`, diapositiva 7. No se copia literalmente la combinación RESTRICT/CASCADE del ejemplo Empleado.
4. **Tres grupos.** Administrador, Operador y Consulta corresponden a los perfiles pedidos por el Word. El comando `crear_perfiles` organiza los permisos Django. `login_required` complementa `permission_required`; no se atribuye a una captura donde no fue confirmado.
5. **Archivos privados.** El Word exige FileField, y el PDF 9 explica la recepción de archivos de imagen. Se añade un documento PDF en Disco. Se guarda en `PRIVATE_MEDIA_ROOT` y se entrega con `FileResponse` tras comprobar permisos. Se añaden validación básica de tipo y límites de tamaño.
6. **Importación repetible.** Los JSON originales y sus imágenes sirven como fuente de importación. No reemplazan las consultas ORM. No se crean clientes o ventas ficticios para aparentar datos reales.
7. **SQLite provisional.** Se permite revisar localmente sin MySQL. El requisito de EC2/phpMyAdmin exige después una conexión real a MySQL y evidencia de ella; no se declara cumplido con SQLite.
8. **Registro y compra del cliente.** Es una ampliación solicitada por el usuario. Se vincula cada cuenta a un Cliente, se valida el registro con UserCreationForm y se limita el historial a sus compras. Comprar registra una Venta y descuenta stock, sin cobro real, según su confirmación. El detalle de este flujo no se atribuye a los ejemplos de los PDF.

## Correcciones frente a ejemplos de clase

- Se redirige a una ruta después de guardar, siguiendo el CRUD del PDF 8; no se copia `redirect(request, 'tiendaApp/empleados.html')` de `6 formularios en Django.pdf`, p. 3.
- Los borrados requieren POST y confirmación, siguiendo `8 CRUD Empleado.pdf`, pp. 8–9, aunque `filtros.pdf`, p. 1, contiene un ejemplo de borrado directo.
- El logout usa POST con CSRF para la versión del proyecto; no se copia sin verificar el enlace GET de `10 Inicio de sesión y permisos.pdf`, p. 3.
- Las migraciones se conservan en Git para poder reproducir la base; la observación sobre conflictos de `crear proyecto.pdf`, p. 42, no se interpreta como excluirlas siempre.
- Para comprobar Python se utiliza `python3 --version`. La línea incompleta `sudo dnf install -y` de la guía AWS, p. 2, no es un comando de verificación.

## Documentación externa de apoyo

Estas fuentes oficiales se consultaron como apoyo técnico. No pertenecen al material de clases entregado:

- [Django 5.2: lista de despliegue](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/): DEBUG, clave secreta, hosts, static y revisión de configuración.
- [Django 5.2: bases de datos](https://docs.djangoproject.com/en/5.2/ref/databases/#mysql-notes): compatibilidad y conexión MySQL.
- [Django 5.2: transacciones](https://docs.djangoproject.com/en/5.2/topics/db/transactions/): guardar un conjunto de operaciones de forma atómica.
- [Gunicorn: despliegue](https://gunicorn.org/deploy/): servicio y proxy inverso.
- [phpMyAdmin: configuración](https://docs.phpmyadmin.net/en/latest/config.html): conexión y autenticación por cookie.

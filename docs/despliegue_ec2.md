# EC2, MariaDB y phpMyAdmin: configuración y verificación

El despliegue de Feria NewMix se verificó el **4 de octubre de 2026** en AWS EC2. El repositorio es [ale13camp/FeriaNewMix-BackEnd](https://github.com/ale13camp/FeriaNewMix-BackEnd). La instancia ejecutó la rama `codex/sumativa-3-api`, commit `a53105b5eb3a880cd8a44d15bc5342c6854fd128`, desde `/var/www/newmix`.

El **5 de octubre de 2026** se verificó otra vez el acceso después de reiniciar el laboratorio. La IPv4 observada fue `35.168.62.2`; NGINX y `ALLOWED_HOSTS` se ajustaron para esa dirección. Esta IP corresponde a esa revisión y puede cambiar. Se repitió Swagger interactivo por túnel y aprobaron 76 comprobaciones de la web remota: 62 funcionales y 14 de cierre.

La configuración comprobada utiliza Amazon Linux 2023, Python 3.12.14, MariaDB 10.11.18, Gunicorn, NGINX, PHP 8.3.33 y phpMyAdmin 5.2.3. Django identifica MariaDB mediante el backend `mysql`. La base, la aplicación y phpMyAdmin están en la misma instancia. Las cuentas, permisos, datos, stock y 50 archivos se conservaron.

Las siguientes secciones permiten entender o repetir la preparación en una instalación nueva. Los textos en mayúsculas son valores de reemplazo, y los comandos de creación no deben ejecutarse sobre archivos o bases existentes sin revisarlos antes. El acceso utilizado en la verificación fue EC2 Instance Connect con clave efímera y huella SSH comprobada; los ejemplos con `.pem` son una alternativa para quien ya tenga una clave válida.

HTTPS sigue pendiente. Las credenciales y JWT se comprobaron por túnel SSH. MariaDB, Gunicorn y phpMyAdmin escuchan sólo en localhost; la nueva regla SSH autorizada se limitó a la IP del computador del usuario. Las reglas previas de la instancia se conservaron. No se abrieron los puertos 3306, 8000 o 8081 a Internet.

El requisito de base MySQL se implementó con MariaDB en EC2, usando la conexión `mysql` de Django. phpMyAdmin consulta esa misma base `newmix`; una base del computador local no demuestra el requisito remoto.

Se toma como referencia `AWS/Levantar Django con NGINX y GUNICORN en AMI Linux 2023 AWS.pdf`, pp. 1–8. La versión y paquetes disponibles del servidor se comprueban antes de instalarlos: no se supone que Python 3.14 esté disponible sólo porque aparece en el ejemplo de clase.

## 1. Preparar GitHub y acceder a la instancia

El repositorio debe contener código, plantillas, static, datos de importación, `requirements.txt`, `.env.example`, README y migraciones. Debe conservar un historial real de commits. No incluir `.env`, claves privadas, `media/`, `privados/`, entornos virtuales o bases locales.

La URL concreta y los commits se verifican en el repositorio propio. No se debe inventar una URL o historial para completar la entrega.

Desde PowerShell, usando la clave existente:

```powershell
ssh -i "RUTA_LOCAL_DE_LA_CLAVE.pem" USUARIO_SSH@IP_O_DNS_EC2
```

Dentro del servidor Linux:

```bash
cat /etc/os-release
python3 --version
git --version
```

Se necesita un Python compatible con las dependencias del proyecto, soporte `venv`, Git, NGINX, MySQL Server y las bibliotecas de desarrollo que requiere mysqlclient. Para phpMyAdmin también se necesita PHP con sus extensiones requeridas. La instalación depende de la distribución y repositorios reales; debe resolverse después de verificar esos datos, sin copiar comandos de otra distribución.

Si se usa Amazon Linux 2023, se consulta su gestor `dnf` y los repositorios disponibles. Si la instancia usa otra distribución, se adapta la instalación. No continuar si MySQL, PHP o el Python compatible todavía no están disponibles.

En el grupo de seguridad de EC2, el acceso SSH debe corresponder a la IP autorizada del estudiante. El sitio usa HTTP/HTTPS según su configuración. MySQL, Gunicorn y el phpMyAdmin de demostración de esta guía escuchan en la instancia, sin abrir sus puertos hacia Internet.

## 2. Clonar desde GitHub

La ruta comprobada es `/var/www/newmix` y el usuario del servidor es `ec2-user`. Sustituir `USUARIO_SSH` si se instala en otro servidor. Estos comandos de clonación suponen que aún no existe el directorio de proyecto.

```bash
sudo mkdir -p /var/www
sudo mkdir /var/www/newmix
sudo chown USUARIO_SSH:USUARIO_SSH /var/www/newmix
git clone --branch codex/sumativa-3-api https://github.com/ale13camp/FeriaNewMix-BackEnd.git /var/www/newmix
cd /var/www/newmix
git remote -v
git log --oneline -5
```

Guardar la salida de la clonación y del remoto como evidencia real. Si la carpeta ya tiene un proyecto, revisar su contenido y remoto antes de usarla; no sobrescribirla para repetir una captura.

## 3. Crear la base MariaDB/MySQL dentro de EC2

Una vez instalado y activo MySQL Server, ingresar con una cuenta que pueda crear base y usuario. El método de acceso administrativo depende de la instalación:

```bash
mysql -u root -p
```

Ejemplo SQL, sustituyendo la contraseña antes de ejecutar:

```sql
CREATE DATABASE newmix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'newmix_app'@'127.0.0.1' IDENTIFIED BY 'CONTRASENA_PROPIA';
GRANT ALL PRIVILEGES ON newmix.* TO 'newmix_app'@'127.0.0.1';
```

Estos privilegios pertenecen a la base `newmix`, no a todas las bases del servidor. El usuario necesita crear y modificar sus tablas al ejecutar migraciones. Si la base o el usuario ya existen, revisar su configuración; no borrarlos para repetir este ejemplo.

Comprobar la conexión por TCP desde la propia instancia:

```bash
mysql -h 127.0.0.1 -P 3306 -u newmix_app -p newmix
```

```sql
SELECT DATABASE();
SHOW TABLES;
```

Antes de migrar, una base nueva puede no tener tablas. Django y phpMyAdmin usan `127.0.0.1`, puerto `3306`, la misma base y el mismo usuario. No se necesita exponer 3306 públicamente. En la instancia verificada, `newmix_app` sólo tiene privilegios sobre `newmix.*`, sin Super ni Grant.

MariaDB debe escuchar sólo en localhost. En esta instalación de Amazon Linux, `mariadb.socket` también define el puerto de escucha: cambiar únicamente `bind-address` no fue suficiente. Se aplicó `/etc/my.cnf.d/newmix-local.cnf` y el siguiente complemento `/etc/systemd/system/mariadb.socket.d/newmix-local.conf`:

```ini
[Socket]
ListenStream=
ListenStream=@mariadb
ListenStream=/var/lib/mysql/mysql.sock
ListenStream=127.0.0.1:3306
```

El reinicio del laboratorio del 5 de octubre mostró que MariaDB volvía a escuchar en `0.0.0.0:3306` porque el socket no estaba habilitado para el arranque normal del servicio. No se abrió ese puerto en el grupo de seguridad. Se habilitó `mariadb.socket` y se añadió `/etc/systemd/system/mariadb.service.d/newmix-socket.conf`:

```ini
[Unit]
Requires=mariadb.socket
After=mariadb.socket
```

Después de guardar los complementos se recargó systemd y se habilitó el socket:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mariadb.socket
```

Para revisar el estado actual, sin repetir la creación de la base:

```bash
systemctl is-enabled mariadb.socket
systemctl is-active mariadb.socket mariadb.service
sudo ss -lntp 'sport = :3306'
```

La comprobación posterior del arranque normal de `mariadb.service` mostró `mariadb.socket` activo/habilitado y escucha exclusivamente en `127.0.0.1:3306`. El complemento de servicio conserva la dependencia; el complemento de socket conserva la dirección local.

Esta configuración corresponde al paquete instalado en la instancia. Antes de adaptarla a otro servidor, revisar `systemctl cat mariadb.socket`. Después de recargar systemd y reiniciar los servicios en una ventana de mantenimiento, comprobar la escucha efectiva con `sudo ss -lntp`; la verificación registrada mostró únicamente `127.0.0.1:3306`.

## 4. Entorno y variables

Desde `/var/www/newmix`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

El entorno verificado se creó con `python3.12` y utiliza Python 3.12.14. En una instalación nueva, sustituir `python3` por el ejecutable compatible comprobado. No se copia el entorno virtual de Windows hacia Linux. Si mysqlclient falla al compilar, revisar las bibliotecas y cabeceras del cliente MySQL y Python antes de cambiar dependencias.

Crear `.env` sólo si no existe un archivo propio:

```bash
cp .env.example .env
chmod 600 .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Usar la clave generada en el archivo:

```dotenv
SECRET_KEY=REEMPLAZAR_CON_LA_CLAVE_GENERADA
DEBUG=False
ALLOWED_HOSTS=IP_O_DNS_EC2,127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=
DB_ENGINE=mysql
DB_NAME=newmix
DB_USER=newmix_app
DB_PASSWORD=CONTRASENA_PROPIA
DB_HOST=127.0.0.1
DB_PORT=3306
COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
TRUST_PROXY_HEADERS=True
```

`ALLOWED_HOSTS` lleva IP o nombre, sin `http://`. Con HTTPS, `CSRF_TRUSTED_ORIGINS` puede contener el origen real, por ejemplo `https://DOMINIO_REAL`. Las opciones COOKIE_SECURE y SECURE_SSL_REDIRECT sólo se activan cuando HTTPS ya funciona. TRUST_PROXY_HEADERS=True permite que Django reconozca el protocolo original y evita redirigir HTTPS en un bucle. Sólo debe activarse con Gunicorn en 127.0.0.1 y NGINX sobrescribiendo X-Forwarded-Proto con $scheme, como se muestra abajo; no confiar en cabeceras enviadas directamente por clientes. No se publican las claves ni la contraseña en capturas.

## 5. Migrar y preparar el catálogo

```bash
python manage.py check
python manage.py migrate
python manage.py importar_catalogo
python manage.py crear_perfiles
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

`importar_catalogo` carga los 13 artistas y 37 discos del catálogo original cuando no existen. No introduce clientes ni ventas ficticios. Los registros creados por la demostración deben identificarse como datos de prueba. Repetir la importación conserva ediciones de registros existentes.

En el despliegue comprobado se restauró el respaldo aprobado del usuario después de confirmar que las tablas de negocio estaban vacías. El resultado fue 5 cuentas, 4 grupos, 13 artistas, 37 discos, 4 clientes, 6 ventas y 50 archivos. Se compararon 575 campos y los hashes de los 50 archivos; no se ejecutó la importación de catálogo para reiniciar stock. Los respaldos SQL se conservaron privados con permiso 600. Una restauración sobre otra base exige un respaldo previo y comprobar que no sobrescriba registros existentes.

Para comprobar que se utiliza MySQL y que existen datos:

```bash
python manage.py shell -c "from django.db import connection; from artistasApp.models import Artista; from discosApp.models import Disco; print(connection.vendor); print('Artistas:', Artista.objects.count()); print('Discos:', Disco.objects.count())"
```

La salida debe corresponder a la ejecución real. Si no muestra `mysql`, revisar `.env` y el entorno antes de declarar cumplida la conexión.

## 6. phpMyAdmin en la misma instancia

En la instancia se instaló phpMyAdmin 5.2.3 en `/home/ec2-user/phpmyadmin`, con PHP 8.3.33. Se descargó desde el sitio oficial y se comprobó su SHA256 antes de extraer. Para otra instalación, verificar la versión compatible y su integridad; confirmar que el directorio contiene `index.php` y preparar `config.inc.php`.

Ejemplo de la parte de conexión en `config.inc.php`:

```php
<?php
$cfg['blowfish_secret'] = 'REEMPLAZAR_CON_UN_SECRETO_DE_32_CARACTERES';
$i = 1;
$cfg['Servers'][$i]['auth_type'] = 'cookie';
$cfg['Servers'][$i]['host'] = '127.0.0.1';
$cfg['Servers'][$i]['port'] = '3306';
$cfg['Servers'][$i]['AllowNoPassword'] = false;
$cfg['Servers'][$i]['AllowRoot'] = false;
$cfg['Servers'][$i]['only_db'] = 'newmix';
```

El secreto de cookie se genera y se guarda en la instancia. No utilizar el texto de ejemplo como secreto. Se puede generar una cadena de 32 caracteres con:

```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

Para una **demostración temporal y privada**, se puede utilizar el servidor incorporado de PHP. El siguiente ejemplo permanece activo mientras esa terminal siga abierta:

```bash
php -S 127.0.0.1:8081 -t RUTA_REAL_DE_PHPMYADMIN
```

Este servidor se limita a la revisión mediante túnel; no es una configuración pública de producción. Desde otra terminal PowerShell del computador:

```powershell
ssh -i "RUTA_LOCAL_DE_LA_CLAVE.pem" -N -L 8081:127.0.0.1:8081 -L 8008:127.0.0.1:80 USUARIO_SSH@IP_O_DNS_EC2
```

Abrir `http://127.0.0.1:8081/`, entrar con `newmix_app` y su contraseña y seleccionar `newmix`. Aunque el navegador use una dirección local, el túnel llega al phpMyAdmin de EC2 y éste consulta el MySQL de esa instancia.

Revisar las tablas de artistas, discos, clientes y ventas, las llaves foráneas y los registros creados desde la aplicación. La web de EC2 y Swagger también se consultan por el túnel en `http://127.0.0.1:8008/` y `http://127.0.0.1:8008/api/swagger/`.

En la demostración comprobada se utilizó la unidad temporal `newmix-phpmyadmin`, con PHP en `127.0.0.1:8081`, sesiones privadas y configuración con permiso 600. Se dejó activa para revisión y no se habilitó al arrancar. Para detener esa unidad:

```bash
sudo systemctl stop newmix-phpmyadmin
```

Cerrar también el túnel al terminar. Detener phpMyAdmin no detiene MariaDB ni la web. Si se necesita acceso permanente, configurar PHP y HTTPS con la distribución real antes de publicarlo.

## 7. Gunicorn con systemd

Gunicorn ejecuta `config.wsgi:application`. NGINX recibirá las solicitudes y las enviará a Gunicorn en `127.0.0.1:8000`.

Crear `/etc/systemd/system/newmix.service`, sustituyendo `USUARIO_SSH` y las rutas si fueran distintas:

```ini
[Unit]
Description=Feria NewMix Django
After=network.target mariadb.service
Requires=mariadb.service

[Service]
User=USUARIO_SSH
Group=USUARIO_SSH
WorkingDirectory=/var/www/newmix
ExecStart=/var/www/newmix/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 --access-logfile - --error-logfile - config.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

El usuario del servicio debe ser propietario de `.env` y tener escritura en `media/` y `privados/`. `config/settings.py` carga `.env`; no se repiten sus credenciales en el archivo del servicio.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now newmix
sudo systemctl status newmix --no-pager
curl -I http://127.0.0.1:8000/
```

Si falla, revisar el error real antes de continuar:

```bash
sudo journalctl -u newmix -n 50 --no-pager
```

## 8. NGINX

En la distribución que carga `/etc/nginx/conf.d/*.conf`, crear `/etc/nginx/conf.d/newmix.conf`. Si utiliza otra organización, adaptar la ubicación a la configuración real de NGINX.

```nginx
server {
    listen 80;
    server_name IP_O_DNS_EC2 127.0.0.1 localhost;
    client_max_body_size 16M;

    location /static/ {
        alias /var/www/newmix/staticfiles/;
    }

    location /media/ {
        alias /var/www/newmix/media/;
        add_header X-Content-Type-Options nosniff;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

`$http_host` conserva el puerto 8008 del túnel en las solicitudes. NGINX fija `Host`, `X-Real-IP` y `X-Forwarded-Proto`, y agrega la dirección de origen a `X-Forwarded-For`. NGINX necesita lectura en `staticfiles/` y `media/` y permiso para atravesar sus directorios padres. Ajustar sólo esos permisos según el usuario real de NGINX. No hacer pública la carpeta completa del proyecto ni ampliar los permisos de `.env` o `privados/` para resolver un error de lectura.

El límite de 16M admite una imagen de hasta 5 MB y un PDF de hasta 10 MB en el mismo formulario, incluyendo el espacio adicional de la solicitud multipart.

No añadir un `alias` a `privados/`. El documento se obtiene desde la vista protegida `discos_documento`, que devuelve `FileResponse` después de comprobar permisos.

```bash
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

Abrir `http://IP_O_DNS_EC2/` para comprobar la configuración inicial. El bloque mostrado es HTTP: antes de usar credenciales reales en un sitio público se debe configurar HTTPS y activar sus opciones. Esta guía no afirma que exista un dominio o certificado.

## Plantillas públicas de la configuración comprobada

Las siguientes plantillas corresponden a los servicios y complementos utilizados. No incluyen `.env`, contraseñas, claves SSH ni secretos de phpMyAdmin. Antes de instalarlas en otra instancia, revisar su usuario, rutas, IP, distribución y configuración existente; no sobrescribir archivos del servidor para repetir la demostración.

- [Servicio Gunicorn/Django](config_ec2/newmix.service).
- [Configuración local de MariaDB](config_ec2/mariadb-local.cnf).
- [Socket MariaDB limitado a localhost](config_ec2/mariadb-socket.conf).
- [Dependencia del servicio MariaDB con su socket](config_ec2/mariadb-service-socket.conf).
- [NGINX para web, static y media](config_ec2/nginx.conf).

## 9. Evidencias obtenidas y revisión antes de presentar

| Requisito | Resultado registrado y fecha de verificación |
|---|---|
| Código en EC2 | Remoto GitHub comprobado; rama `codex/sumativa-3-api`, commit `a53105b5eb3a880cd8a44d15bc5342c6854fd128`. |
| EC2 y servicios | Acceso AWS/SSH comprobado antes de cambios; MariaDB, Gunicorn y NGINX activos y habilitados. Web HTTP 200. |
| Base remota | Motor `mysql`, base `newmix`, migraciones aplicadas y datos/archivos conservados. |
| phpMyAdmin | El 4 de octubre: sesión, tablas y consulta de 13 llaves foráneas de la misma base EC2. El 5 se repitieron sesión y tablas con 37 discos. |
| API, JWT y Swagger | El 4 de octubre: token/refresh de cuatro perfiles, 401 sin JWT, Swagger/esquema 200. El 5: JWT 200, Authorized y Execute GET `/api/discos/1/` 200 en Swagger remoto. |
| CRUD y stock | 86 comprobaciones HTTP: 200/201/204, rechazos 403/404, compras y reversión de stock. Registros temporales eliminados y originales intactos. |
| Comprobaciones de configuración | `check`, `pip check`, revisión de migraciones, esquema OpenAPI y `nginx -t` correctos. |
| Web, Admin y controles | El 5 de octubre aprobaron 76 comprobaciones: 62 funcionales de alta/edición, búsqueda/filtros, Admin, roles, CSRF y validación, más 14 de cierre. Baja web verificada y registro/archivos de prueba retirados. |
| Archivos | 50 archivos restaurados con hashes coincidentes el 4 de octubre. El 5 se cargaron imagen/PDF de prueba y se comprobó SHA256 de las descargas y protección del PDF; `privados/` fuera de aliases NGINX. |
| Persistencia de MariaDB | El 5 de octubre se habilitó el socket y se fijó su dependencia desde el servicio; arranque normal comprobado con `127.0.0.1:3306`. |
| HTTPS y presentación | HTTPS público pendiente; presentación técnica presencial todavía debe realizarse. |

Las capturas y resúmenes públicos están en `evidencias_ec2/`: [web](evidencias_ec2/web_ec2.png), [Swagger](evidencias_ec2/swagger_ec2.png), [tablas](evidencias_ec2/phpmyadmin_newmix.png), [relaciones](evidencias_ec2/phpmyadmin_relaciones.png), [JWT/lecturas](evidencias_ec2/http_verificado.json) y [CRUD/stock](evidencias_ec2/crud_verificado.json). Los resúmenes no incluyen credenciales, tokens ni datos personales. La revisión del 5 de octubre añade [Swagger Execute 200](evidencias_ec2/swagger_get_ec2.png), [JWT/Authorize en el navegador](evidencias_ec2/swagger_ui_verificado.json) y [web, archivos y permisos](evidencias_ec2/web_rubrica_verificado_20261005.json). El [cierre verificado](evidencias_ec2/cierre_web_demo_verificado_20261005.json) registra 4 clientes, 37 discos y 6 ventas originales, stock intacto y 50 archivos exactos por SHA256; el disco sintético y sus dos archivos ya no existen.

`python manage.py check --deploy` registró cuatro advertencias: `security.W004` (HSTS), `security.W008` (redirección HTTPS), `security.W012` (cookie de sesión segura) y `security.W016` (cookie CSRF segura). Por eso las contraseñas y JWT se usan mediante el túnel, y no se declara una publicación HTTPS terminada. No se ejecutó la suite Django contra la base de negocio de EC2; las pruebas automatizadas se realizan en bases temporales locales.

Antes de presentar, activar el laboratorio AWS, comprobar que la instancia esté disponible, verificar su IP actual y reabrir el túnel. La IP pública puede cambiar después de detener y arrancar EC2; en ese caso revisar `ALLOWED_HOSTS` y `server_name`. Confirmar que phpMyAdmin temporal esté activo si se va a mostrar. La guía [API Sumativa 3](API_Sumativa3.md) ofrece el recorrido de los diez criterios y distingue la evidencia obtenida de la presentación pendiente.

Fuentes del curso y documentación oficial de apoyo: [fuentes.md](fuentes.md).

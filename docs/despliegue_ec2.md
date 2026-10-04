# Guía propuesta para EC2, MySQL y phpMyAdmin

Esta guía describe cómo desplegar Feria NewMix. **No registra un despliegue realizado.** El repositorio confirmado es https://github.com/ale13camp/FeriaNewMix-BackEnd. Antes de ejecutar el despliegue hay que conocer IP o DNS de EC2, sistema operativo, usuario SSH y ruta local de la clave privada. Los textos en mayúsculas son valores que hay que reemplazar.

La base MySQL debe estar en la propia instancia EC2, según el Word de evaluación. phpMyAdmin debe consultar esa misma base; mostrar una base del computador local no demuestra el requisito.

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

El ejemplo usa `/var/www/newmix` como ruta propuesta. No es una ruta confirmada del servidor. Sustituir `USUARIO_SSH` por el usuario real; estos comandos suponen que aún no existe el directorio de proyecto.

```bash
sudo mkdir -p /var/www
sudo mkdir /var/www/newmix
sudo chown USUARIO_SSH:USUARIO_SSH /var/www/newmix
git clone https://github.com/ale13camp/FeriaNewMix-BackEnd.git /var/www/newmix
cd /var/www/newmix
git remote -v
git log --oneline -5
```

Guardar la salida de la clonación y del remoto como evidencia real. Si la carpeta ya tiene un proyecto, revisar su contenido y remoto antes de usarla; no sobrescribirla para repetir una captura.

## 3. Crear MySQL dentro de EC2

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

Antes de migrar, una base nueva puede no tener tablas. Django y phpMyAdmin usarán `127.0.0.1`, puerto `3306`, la misma base y el mismo usuario. No se necesita exponer 3306 públicamente.

## 4. Entorno y variables

Desde `/var/www/newmix`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

El Python de este entorno debe ser el que se comprobó en la instancia. No se copia el entorno virtual de Windows hacia Linux. Si mysqlclient falla al compilar, revisar las bibliotecas y cabeceras del cliente MySQL y Python antes de cambiar dependencias.

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

Para comprobar que se utiliza MySQL y que existen datos:

```bash
python manage.py shell -c "from django.db import connection; from artistasApp.models import Artista; from discosApp.models import Disco; print(connection.vendor); print('Artistas:', Artista.objects.count()); print('Discos:', Disco.objects.count())"
```

La salida debe corresponder a la ejecución real. Si no muestra `mysql`, revisar `.env` y el entorno antes de declarar cumplida la conexión.

## 6. phpMyAdmin en la misma instancia

Instalar phpMyAdmin desde su distribución oficial o un paquete de la distribución compatible con el PHP disponible. Confirmar que su directorio contiene `index.php` y preparar `config.inc.php`. No se fija una ruta de instalación que aún no ha sido verificada.

Ejemplo de la parte de conexión en `config.inc.php`:

```php
<?php
$cfg['blowfish_secret'] = 'REEMPLAZAR_CON_UN_SECRETO_DE_32_CARACTERES';
$i = 1;
$cfg['Servers'][$i]['auth_type'] = 'cookie';
$cfg['Servers'][$i]['host'] = '127.0.0.1';
$cfg['Servers'][$i]['port'] = '3306';
$cfg['Servers'][$i]['AllowNoPassword'] = false;
```

El secreto de cookie se genera y se guarda en la instancia. No utilizar el texto de ejemplo como secreto. Se puede generar una cadena de 32 caracteres con:

```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

Para una **demostración temporal y privada**, se puede utilizar el servidor incorporado de PHP, manteniendo esta terminal abierta:

```bash
php -S 127.0.0.1:8081 -t RUTA_REAL_DE_PHPMYADMIN
```

Este servidor se limita a la revisión mediante túnel; no es una configuración pública de producción. Desde otra terminal PowerShell del computador:

```powershell
ssh -i "RUTA_LOCAL_DE_LA_CLAVE.pem" -N -L 8081:127.0.0.1:8081 USUARIO_SSH@IP_O_DNS_EC2
```

Abrir `http://127.0.0.1:8081/`, entrar con `newmix_app` y su contraseña y seleccionar `newmix`. Aunque el navegador use una dirección local, el túnel llega al phpMyAdmin de EC2 y éste consulta el MySQL de esa instancia.

Revisar las tablas de artistas, discos, clientes y ventas, las llaves foráneas y los registros creados desde la aplicación. Cerrar el servidor PHP y el túnel después de la demostración. Si se necesita acceso permanente, configurar PHP y HTTPS con la distribución real antes de publicarlo.

## 7. Gunicorn con systemd

Gunicorn ejecuta `config.wsgi:application`. NGINX recibirá las solicitudes y las enviará a Gunicorn en `127.0.0.1:8000`.

Crear `/etc/systemd/system/newmix.service`, sustituyendo `USUARIO_SSH` y las rutas si fueran distintas:

```ini
[Unit]
Description=Feria NewMix Django
After=network.target

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
    server_name IP_O_DNS_EC2;
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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

NGINX necesita lectura en `staticfiles/` y `media/` y permiso para atravesar sus directorios padres. Ajustar sólo esos permisos según el usuario real de NGINX. No hacer pública la carpeta completa del proyecto ni ampliar los permisos de `.env` o `privados/` para resolver un error de lectura.

El límite de 16M admite una imagen de hasta 5 MB y un PDF de hasta 10 MB en el mismo formulario, incluyendo el espacio adicional de la solicitud multipart.

No añadir un `alias` a `privados/`. El documento se obtiene desde la vista protegida `discos_documento`, que devuelve `FileResponse` después de comprobar permisos.

```bash
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

Abrir `http://IP_O_DNS_EC2/` para comprobar la configuración inicial. El bloque mostrado es HTTP: antes de usar credenciales reales en un sitio público se debe configurar HTTPS y activar sus opciones. Esta guía no afirma que exista un dominio o certificado.

## 9. Evidencias de la evaluación

Registrar sólo después de ejecutar y comprobar:

| Requisito | Evidencia real que se debe reunir |
|---|---|
| GitHub | URL propia, remoto, commits y salida de `git clone` en EC2. |
| EC2 | Acceso SSH, entorno activo, estado de Gunicorn/NGINX y página real. |
| MySQL | Motor `mysql`, migraciones aplicadas y tablas dentro de EC2. |
| phpMyAdmin | Tablas, relaciones y registros de la misma base de EC2. |
| CRUD | Agregar, listar, buscar, editar y confirmar eliminación desde la web. |
| Venta | Cliente y disco relacionados, cantidad, precio y cambio coherente de stock. |
| Archivos | Cargar y visualizar imagen; cargar y descargar PDF con permiso. |
| Perfiles | Acciones permitidas de cada usuario y rechazo de acciones no autorizadas. |

`python manage.py check --deploy` ayuda a revisar la configuración para publicación, pero no reemplaza las pruebas del navegador ni resuelve advertencias por sí solo. Interpretar su salida según si HTTPS ya está configurado. Respaldar MySQL y las carpetas `media/` y `privados/`.

Esta guía quedará pendiente de comprobar hasta disponer de los accesos concretos y registrar resultados reales. Fuentes del curso y documentación oficial de apoyo: [fuentes.md](fuentes.md).

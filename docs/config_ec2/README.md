# Configuración usada en EC2

Copias sin secretos de la configuración comprobada el 5 de octubre de 2026. Son referencias para explicar el despliegue existente; no se deben volver a instalar ni importar los datos sin revisar primero el estado del servidor.

| Archivo | Ruta usada en la instancia |
| --- | --- |
| newmix.service | /etc/systemd/system/newmix.service |
| mariadb-local.cnf | /etc/my.cnf.d/newmix-local.cnf |
| mariadb-socket.conf | /etc/systemd/system/mariadb.socket.d/newmix-local.conf |
| mariadb-service-socket.conf | /etc/systemd/system/mariadb.service.d/newmix-socket.conf |
| nginx.conf | /etc/nginx/conf.d/newmix.conf |

En nginx.conf se reemplazó la dirección por `IP_PUBLICA_ACTUAL`. Debe coincidir con la IP o dominio autorizado de `ALLOWED_HOSTS`, definidos en el archivo privado `.env`. El entorno virtual, los archivos estáticos y las migraciones se preparan según [la guía EC2](../despliegue_ec2.md).

El socket y el servicio MariaDB están habilitados. La dependencia Requires/After conserva la activación del socket al iniciar el servicio. Gunicorn y MariaDB escuchan en localhost; el servidor temporal de phpMyAdmin también. La configuración privada de phpMyAdmin contiene su secreto de cookie y no se publica.

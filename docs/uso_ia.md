# Uso de inteligencia artificial

La evaluación `Eva Sumativa 2 - flex.docx`, en **Uso Obligatorio de Inteligencia Artificial**, permite apoyo para modelos, formularios, CRUD, login, perfiles, permisos, archivos y optimización. Esta conversación utiliza Codex como asistente.

## Prompt real del usuario

> Quiero que ejecutes este archivo Word Eva Sumativa 2 - flex.docx que sea simple como un estudiante de ingeniería en informática de 2do año, no inventes nada. Hazme cualquier pregunta si es necesario. Hazlo simple pero detallado. En la carpeta proyecto_discos 1.2 esta el proyecto en el cual hay que trabajar. Y en la carpeta Unidad 1 y 2 están los pdf con los que hay que sacar la información siguiendo el orden de explicación.

## Respuesta y aplicación práctica

El siguiente texto es un **resumen de la respuesta y del trabajo de esta conversación**, no una transcripción literal ni una respuesta inventada:

El asistente revisó el Word de evaluación, los PDF y el código existente. Identificó que el catálogo necesitaba persistencia mediante modelos ORM, CRUD, archivos y control de acceso. Propuso añadir Clientes y Ventas para relacionar un cliente con un disco; el usuario aceptó esa opción. A partir de ello se organizó la implementación de modelos, formularios, vistas, permisos y documentación, conservando el catálogo original.

El apoyo se aplica en las siguientes partes del proyecto:

- Modelos Cliente y Venta y relación ForeignKey con Disco.
- Formularios ModelForm y CRUD de las entidades.
- Ajuste de stock y conservación del precio de cada venta.
- Grupos Administrador, Operador, Consulta y Cliente, permisos de vistas y menú.
- Carga de imágenes y documentos y acceso protegido al PDF.
- Configuración `.env`, importación del catálogo y guía de despliegue.

En esa primera etapa, la propuesta de despliegue y de conexión MySQL no constituía una ejecución. Los resultados posteriores se registran con su fecha y evidencia; la continuación de EC2 del 4 de octubre se describe abajo.

## Ajuste solicitado el 3 de octubre de 2026

El usuario pidió: «En registrar venta, el precio que sale en el disco que salga exacto en el precio unitario». Después indicó: «trabaja en el repositorio de FeriaNewMix-BackEnd».

Se ajustó el formulario para completar el precio con el disco seleccionado, precargarlo desde su ficha y tomar el valor del catálogo en el servidor. Una consulta GET protegida actualiza el precio también cuando se agrega o edita un disco desde el Admin. La comprobación en el navegador mostró AM con 21990 y Favourite Worst Nightmare con 13990. La suite completa aprobó 53 pruebas. La captura `evidencias/18_precio_automatico.jpg` muestra el formulario actualizado. Las ventas anteriores conservan su precio histórico al editar el mismo disco.

## Registro y compras solicitados el 3 de octubre de 2026

El usuario pidió: «En el inicio agrega un registro para cliente nuevo, en donde pueda tener acceso para comprar dentro de la pagina». Ante la pregunta de si la compra debía registrar la venta y descontar stock sin cobro real, respondió: «Sí, registrar compra y descontar stock».

Se añadió registro mediante UserCreationForm, cuenta vinculada al Cliente, inicio de sesión automático y un grupo Cliente con dos permisos de lectura del catálogo. La compra obtiene cliente, disco, fecha y precio desde el servidor; sólo recibe la cantidad del formulario. Mis compras filtra los registros de la cuenta. La suite aprobó 73 pruebas. En el navegador se comprobó una compra técnica de dos unidades de AM: precio unitario 21990, total 43980 y stock de 5 a 3. Esa compra y su cuenta de verificación se retiraron después; el stock volvió a 5 y se conservaron las ventas previas. Las capturas 19 a 22 documentan inicio, registro, confirmación e historial. No se incorporó un cobro real.

## Mejoras del perfil del cliente

El usuario pidió: «el perfil del cliente, siento que le faltan cosas dame ideas para agregarle». El asistente recomendó comenzar con Mi perfil, cambiar contraseña y mejorar Mis compras. El usuario respondió: «si hazlo».

Se añadió edición de nombre, correo y teléfono propios, sincronización con User y cambio de contraseña validando la actual y conservando la sesión. Mis compras incorpora portadas, enlaces y búsqueda por título y fechas inclusivas. Las cuentas ajenas quedan fuera de las consultas y no se aceptan campos de privilegios enviados en el formulario. La suite completa aprobó 94 pruebas; las capturas 23 a 25 muestran los recorridos con una cuenta técnica separada. Sus datos y compras se retiraron al terminar, devolviendo el stock de prueba y conservando las ventas previas del usuario. No se cambiaron las contraseñas de sus cuentas al comprobar esta función.

## Evidencia anterior conservada

El proyecto original contiene `static/IA/IA.md` e imágenes de evidencia en `static/IA/`. El archivo menciona Claude (Anthropic), modo Cowork, y contiene solicitudes sobre Bootstrap, plantillas, estilo y carrusel. Se conserva como evidencia histórica del prototipo; no se presenta como conversación de Codex ni se agregan prompts atribuidos a ese trabajo anterior.

## Revisión por el estudiante

El estudiante debe poder explicar qué hace cada modelo, cómo se relacionan Cliente, Disco y Venta, cómo funcionan GET y POST en los formularios, por qué se revisan permisos en las vistas y cómo una venta modifica stock. La revisión presencial debe utilizar el código y los resultados reales, junto con las fuentes indicadas en [fuentes.md](fuentes.md).

## Continuación de EC2 y revisión de la rúbrica: 4 de octubre de 2026

La solicitud real del usuario fue:

> Continúa el despliegue de FeriaNewMix-BackEnd en EC2 y configura MariaDB y phpMyAdmin. Revisa primero `.evaluacion/GUIA_MANUAL_EC2_Y_PHPMYADMIN.md`. Los permisos de AWS ya están en «Permitir siempre»; comprueba el acceso antes de realizar cambios.

Se revisó la guía privada y se comprobó el acceso antes de modificar el servidor. La ayuda de IA se aplicó a la preparación de MariaDB, variables privadas, restauración conservando datos, Gunicorn/NGINX, phpMyAdmin por túnel, pruebas JWT y verificación de CRUD/stock. El usuario autorizó expresamente SSH desde la IP de su computador. Las credenciales temporales, contraseñas, claves y respaldos permanecen fuera del repositorio público.

La evidencia real registra la conexión Django `mysql/newmix`, servicios activos, web/Swagger/phpMyAdmin y JWT de cuatro roles. Las 86 comprobaciones HTTP utilizaron registros temporales, los retiraron al terminar y compararon los originales antes/después. Se diferenciaron de las 129 pruebas locales; no se ejecutó la suite Django sobre la base de negocio remota. Los resultados se encuentran en [la guía EC2](despliegue_ec2.md) y `evidencias_ec2/`.

Después, el usuario pidió revisar lo que faltaba para completar la entrega y obtener la mayor cantidad de puntos de la rúbrica. Se actualizó la documentación para relacionar los diez criterios con código y evidencia reales, y se preparó un recorrido de presentación. No se asigna una nota ni se presenta la exposición del estudiante como realizada. HTTPS permanece pendiente y las credenciales/JWT se usan por túnel durante la demostración.

El estudiante debe revisar y comprender estas decisiones antes de presentar: la base remota compartida por web/API, la diferencia entre sesión y JWT, los permisos por perfil, la protección de datos, los movimientos de stock y el alcance de las pruebas. La ayuda de IA no reemplaza esa explicación ni la evaluación presencial.


## Verificación tras reiniciar el laboratorio: 5 de octubre de 2026

Al continuar la revisión de la rúbrica se comprobó de nuevo el acceso antes de realizar cambios. La IP observada después del reinicio fue `35.168.62.2`. La verificación detectó que MariaDB había vuelto a escuchar en todas las interfaces al arrancar sin su socket habilitado; se corrigió habilitando `mariadb.socket` y haciendo que el servicio lo requiera. El arranque normal posterior conservó la escucha en localhost. Esta corrección se respalda con ejecución, no sólo con la propuesta de IA.

En Swagger de EC2 se emitió JWT con 200, se confirmó Authorized y se ejecutó GET `/api/discos/1/` con 200 desde el navegador y por túnel. El perfil Consulta recibió una respuesta sin campos privados. Se registró el recorrido y se preparó una captura con el token oculto.

También aprobaron 76 comprobaciones de la web remota: 62 funcionales de formularios, búsqueda/filtros, Django Admin, edición por perfil, validación, CSRF, imagen y PDF, más 14 de cierre. Las descargas de prueba coincidieron por SHA256 y los 4 clientes, 37 discos y 6 ventas originales coincidieron antes/después. Después de capturarlo se comprobó la baja web del disco sintético y se retiraron sus dos archivos. El cierre verificó los 4 clientes, 37 discos y 6 ventas originales, el stock de los 37 discos y los 50 archivos originales exactos por SHA256, sin archivos de prueba adicionales. El resultado está en [cierre_web_demo_verificado_20261005.json](evidencias_ec2/cierre_web_demo_verificado_20261005.json).

La evidencia del 5 de octubre complementa las 129 pruebas locales y las 86 comprobaciones API del día anterior, sin mezclarlas como una única suite. La presentación presencial y HTTPS público siguen pendientes; el guion organiza lo que el estudiante debe explicar y no asigna una nota obtenida.

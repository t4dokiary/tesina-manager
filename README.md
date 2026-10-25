# TesisManager FCC BUAP

Sistema web para el seguimiento y control de tesis de posgrado de la Facultad de
Ciencias de la Computación (FCC) de la BUAP. La aplicación centraliza el
expediente de cada proyecto, los entregables académicos y la comunicación entre
alumnos, asesores y coordinación.

## Funcionalidades principales

El sistema implementa los siguientes casos de uso:

- **CU01 — Control de acceso y gestión de usuarios:** autenticación y vistas
  diferenciadas para **Alumno**, **Asesor** y **Coordinación**. Coordinación
  puede validar usuarios, asignar responsables, administrar convocatorias y
  revisar expedientes.
- **CU02 — Entregables y versiones PDF:** registro del protocolo y carga de
  borradores en PDF. Cada entrega se almacena como una versión numerada
  (`v1`, `v2`, etc.) y no se sobrescribe; el asesor puede agregar correcciones
  y retroalimentación.
- **CU03 — Minutas y acuerdos:** registro de reuniones de asesoría, modalidad,
  temas tratados, firma del asesor y firma de conformidad del alumno. Las
  minutas pueden contener acuerdos con responsable, fecha límite y estado de
  cumplimiento.
- **CU04 — Alertas de rezago:** un proyecto genera alerta cuando han
  transcurrido **más de 30 días** desde su último avance. Coordinación dispone
  de un panel para monitorear estos casos.
- **Convocatorias:** periodos oficiales para registrar protocolos y dar
  seguimiento a los trámites de titulación.

Los archivos multimedia se guardan en `media/`, organizados por tipo y, para
protocolos y entregables, por año, mes y matrícula.

## Stack tecnológico

- **Backend:** Python 3.10 o superior y Django 5.2.
- **Base de datos:** MySQL o MariaDB en el puerto `3306`.
- **Conector:** `mysqlclient` (módulo `MySQLdb`) en la configuración actual;
  PyMySQL puede utilizarse como alternativa si se agrega el adaptador
  correspondiente.
- **Frontend:** HTML, Django Templates, Bootstrap 5.3.3 y Bootstrap Icons
  1.11.3 mediante CDN.
- **Servidor de desarrollo:** `runserver`.
- **Servidor Linux recomendado:** Gunicorn detrás de Nginx y systemd.
- **Control de versiones:** Git.

## Requisitos previos

Antes de instalar la aplicación, tener disponible:

1. Python 3.10+ y `pip`.
2. MySQL o MariaDB escuchando en `127.0.0.1:3306`.
3. Git.
4. En Windows, XAMPP con el módulo **MySQL** iniciado. XAMPP puede mostrar el
   servicio como MySQL aunque internamente utilice MariaDB.
5. Un usuario de base de datos con permisos para crear tablas en la base
   `tesina_db`.

> **Nota sobre el nombre de la base:** el archivo
> `tesina_manager/settings.py` viene configurado actualmente con
> `NAME = 'tesis_db'`. Los pasos siguientes usan el nombre solicitado
> `tesina_db`; después de crearla, cambiar `NAME` a `tesina_db` o, si se desea
> conservar la configuración original, crear una base llamada `tesis_db`.
> `HOST` debe permanecer como `127.0.0.1`.

## Instalación y ejecución en Windows

### 1. Obtener el código y crear el entorno virtual

Abrir PowerShell en la carpeta del proyecto:

```powershell
git clone <URL-DEL-REPOSITORIO> tesina-manager
cd tesina-manager
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación de scripts para el usuario actual:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Cerrar y abrir PowerShell si es necesario, volver a `cd` al proyecto y activar
el entorno.

### 2. Instalar dependencias

El repositorio no incluye actualmente un `requirements.txt`. Instalar las
dependencias base dentro de `venv`:

```powershell
python -m pip install --upgrade pip
pip install "Django>=5.2,<6.0" mysqlclient
```

`gunicorn` no se utiliza para ejecutar el servidor en Windows porque está
orientado a entornos Unix; se instala en el procedimiento de Ubuntu.

El proyecto actual ya fue creado con un entorno Python 3.14 y contiene
`mysqlclient`; Python 3.10+ es el rango recomendado para instalaciones nuevas.

### 3. Crear la base de datos en XAMPP

1. Abrir el **XAMPP Control Panel**.
2. Iniciar **MySQL** y comprobar que el puerto sea `3306`.
3. Abrir `http://localhost/phpmyadmin` o el cliente MySQL.
4. Ejecutar:

```sql
CREATE DATABASE tesina_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Para una instalación local típica de XAMPP, la configuración de desarrollo es:

```python
# tesina_manager/settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "tesina_db",
        "USER": "root",
        "PASSWORD": "",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
    }
}
```

En ambientes compartidos o de producción, crear un usuario MySQL dedicado y
no utilizar `root` ni una contraseña vacía.

### 4. Aplicar migraciones y comprobar la configuración

Desde la raíz del proyecto, con `venv` activo:

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Las migraciones existentes de `seguimiento` se aplicarán con `migrate`. Usar
`makemigrations` únicamente después de modificar modelos; no editar archivos
de migración ya aplicados.

### 5. Crear datos de prueba (opcional)

El cargador recomendado crea una convocatoria, proyectos, un caso al corriente,
un caso con rezago, un entregable, una minuta y acuerdos:

```powershell
python .\seguimiento\management\commands\seed_data.py
```

También existe un comando de carga masiva:

```powershell
python manage.py poblar_usuarios
```

### 6. Ejecutar el servidor

```powershell
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/`. El panel administrativo está disponible en
`http://127.0.0.1:8000/admin/`.

Para acceder desde otro equipo de la red local, usar:

```powershell
python manage.py runserver 0.0.0.0:8000
```

En ese caso, agregar la IP o el nombre del equipo a `ALLOWED_HOSTS` y no dejar
`DEBUG=True` en un entorno público.

## Instalación y ejecución en Linux/Ubuntu

### 1. Instalar paquetes del sistema

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
    libmysqlclient-dev build-essential mariadb-server nginx
```

El paquete `libmysqlclient-dev` proporciona las cabeceras necesarias para
compilar `mysqlclient`. En una instalación MySQL administrada por Oracle,
instalar el paquete de desarrollo equivalente.

Activar y asegurar MariaDB:

```bash
sudo systemctl enable --now mariadb
sudo mariadb-secure-installation
```

Crear la base y un usuario de aplicación:

```bash
sudo mariadb
```

```sql
CREATE DATABASE tesina_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tesina_user'@'localhost' IDENTIFIED BY 'CAMBIAR_ESTA_CONTRASENA';
GRANT ALL PRIVILEGES ON tesina_db.* TO 'tesina_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Configurar esas credenciales en `tesina_manager/settings.py` o, idealmente,
leerlas desde variables de entorno antes de publicar la aplicación.

### 2. Crear el entorno e instalar Python

```bash
git clone <URL-DEL-REPOSITORIO> /var/www/tesina-manager
cd /var/www/tesina-manager
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install "Django>=5.2,<6.0" mysqlclient gunicorn
python manage.py check
python manage.py migrate
```

Para una prueba rápida:

```bash
python manage.py runserver 127.0.0.1:8000
```

### 3. Preparar archivos estáticos y permisos de multimedia

Agregar un directorio de estáticos de producción en
`tesina_manager/settings.py` (sin reemplazar `STATICFILES_DIRS`):

```python
STATIC_ROOT = BASE_DIR / "staticfiles"
```

Después ejecutar:

```bash
python manage.py collectstatic --noinput
sudo mkdir -p /var/www/tesina-manager/media
sudo chown -R www-data:www-data /var/www/tesina-manager/media
sudo chmod -R u+rwX,g+rwX /var/www/tesina-manager/media
```

No otorgar permisos `777`. La cuenta que ejecute Gunicorn necesita leer y
escribir PDFs en `media/`.

### 4. Configurar Gunicorn con systemd

Crear `/etc/systemd/system/tesina-manager.service`:

```ini
[Unit]
Description=TesisManager FCC BUAP
After=network.target mariadb.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/tesina-manager
Environment="PATH=/var/www/tesina-manager/venv/bin"
ExecStart=/var/www/tesina-manager/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/tesina-manager.sock \
    tesina_manager.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Activar y revisar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tesina-manager
sudo systemctl status tesina-manager
sudo journalctl -u tesina-manager -f
```

### 5. Configurar Nginx

Crear `/etc/nginx/sites-available/tesina-manager`:

```nginx
server {
    listen 80;
    server_name tesis.example.com;

    client_max_body_size 20M;

    location /static/ {
        alias /var/www/tesina-manager/staticfiles/;
    }

    location /media/ {
        alias /var/www/tesina-manager/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/tesina-manager.sock;
    }
}
```

Habilitar el sitio y validar la configuración:

```bash
sudo ln -s /etc/nginx/sites-available/tesina-manager \
    /etc/nginx/sites-enabled/tesina-manager
sudo nginx -t
sudo systemctl reload nginx
```

En producción, configurar HTTPS (por ejemplo, con Certbot), `ALLOWED_HOSTS`,
`CSRF_TRUSTED_ORIGINS`, `SECRET_KEY` y `DEBUG=False`. No servir el proyecto
con `runserver`.

## Roles y credenciales de prueba

### Roles

| Rol | Responsabilidades principales |
|---|---|
| **Alumno** | Consulta su expediente, registra el protocolo, sube versiones PDF, consulta retroalimentación, revisa minutas y firma acuerdos. |
| **Asesor** | Consulta proyectos asignados, revisa entregables, carga correcciones, registra minutas, define acuerdos y marca su cumplimiento. |
| **Coordinación** | Valida usuarios y protocolos, asigna asesores, administra convocatorias, consulta expedientes y monitorea alertas de más de 30 días. |

### Datos de prueba del cargador `seed_data.py`

Después de ejecutar el cargador recomendado:

| Rol | Usuario | Contraseña | Escenario |
|---|---|---|---|
| Coordinación | `coordinador` | `admin123` | Administración general |
| Asesor | `asesor_carlos` | `asesor123` | Docente con proyecto asignado |
| Alumno | `alumno_luis` | `alumno123` | Proyecto al corriente |
| Alumno | `alumno_ana` | `alumno123` | Proyecto con rezago de más de 30 días |

Estas credenciales son únicamente para desarrollo y demostración. Cambiarlas o
eliminarlas antes de cualquier despliegue real.

> **Importante:** `poblar_usuarios` es un cargador masivo independiente. Su
> implementación asigna internamente la contraseña `2465` a los usuarios
> `coord1`--`coord5`, `asesor1`--`asesor25` y `alumno1`--`alumno40`, aunque el
> mensaje final del script muestra otra contraseña. Para evitar confusión,
> utilizar `seed_data.py` para las credenciales documentadas arriba.

## Estructura del proyecto

```text
tesina-manager/
├── manage.py                         # Punto de entrada de Django
├── tesina_manager/                   # Configuración del proyecto
│   ├── settings.py                   # Base de datos, media, estáticos y zona horaria
│   ├── urls.py                       # Rutas y servicio de media en desarrollo
│   ├── asgi.py                       # Entrada ASGI
│   └── wsgi.py                       # Entrada WSGI/Gunicorn
├── seguimiento/                      # Aplicación funcional principal
│   ├── models.py                     # Usuarios, tesis, PDFs, minutas y alertas
│   ├── forms.py                      # Formularios de registro y gestión
│   ├── validators.py                 # Validaciones de archivos y datos
│   ├── views/                        # Vistas por rol y vistas generales
│   ├── templates/seguimiento/        # Plantillas HTML
│   ├── static/seguimiento/           # CSS y JavaScript propios
│   ├── migrations/                   # Historial de esquema
│   ├── management/commands/          # seed_data y poblar_usuarios
│   ├── admin.py                      # Registro del panel administrativo
│   └── tests.py                      # Pruebas de la aplicación
├── media/                            # PDFs subidos por usuarios (no es código)
├── protocolos/                       # Archivos de protocolos existentes
├── venv/                             # Entorno local; no versionar
└── README.md
```

## Comandos de mantenimiento

Con el entorno virtual activo:

```powershell
# Windows
python manage.py check
python manage.py showmigrations
python manage.py makemigrations seguimiento
python manage.py migrate
python manage.py createsuperuser
python manage.py test
python manage.py collectstatic --noinput
```

```bash
# Linux/Ubuntu: equivalentes
python manage.py check
python manage.py showmigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py test
python manage.py collectstatic --noinput
```

Respaldar la base de datos regularmente. Ejemplo para MySQL/MariaDB:

```bash
mysqldump -u tesina_user -p --single-transaction tesina_db > tesina_db.sql
```

Los PDFs de `media/` deben respaldarse por separado:

```bash
tar -czf media-backup.tar.gz media/
```

## Solución de problemas comunes

### El puerto 3306 está ocupado

Comprobar qué proceso está utilizando el puerto:

```powershell
# Windows
Get-NetTCPConnection -LocalPort 3306 -ErrorAction SilentlyContinue
```

```bash
# Linux
sudo ss -ltnp | grep 3306
```

Detener el servicio duplicado (por ejemplo, MySQL instalado fuera de XAMPP) o
cambiar el puerto del servicio. Si se cambia el puerto, actualizar `PORT` en
`DATABASES` y reiniciar el servidor de base de datos. No iniciar dos servicios
MySQL/MariaDB sobre el mismo puerto.

### `Can't connect to MySQL server` o `Access denied`

1. Confirmar que MySQL/MariaDB esté iniciado.
2. Verificar `NAME`, `USER`, `PASSWORD`, `HOST` y `PORT` en
   `tesina_manager/settings.py`.
3. Usar `127.0.0.1` en vez de `localhost` para evitar diferencias de resolución
   y sockets.
4. Probar las credenciales directamente con el cliente `mysql` o
   `mariadb`.
5. Confirmar que el usuario tenga permisos sobre `tesina_db`.

### Error al instalar `mysqlclient`

En Windows, actualizar `pip` y usar una versión de Python para la que exista
wheel disponible. En Ubuntu, instalar `libmysqlclient-dev` y
`build-essential` antes de ejecutar `pip install mysqlclient`. Si se opta por
PyMySQL, instalarlo y configurar el adaptador compatible en el proyecto; no
mezclar ambos conectores sin una razón concreta.

### `OperationalError: database ... does not exist`

Crear la base con el nombre exacto que aparece en `DATABASES`. El código
original usa `tesis_db`, mientras que esta guía propone `tesina_db`; ambos
nombres no son intercambiables.

### `Permission denied` al subir o servir PDFs

En Windows, comprobar que el usuario que ejecuta `runserver` tenga permisos de
escritura sobre `media/` y que las subcarpetas existan. En Linux:

```bash
sudo chown -R www-data:www-data /var/www/tesina-manager/media
sudo chmod -R u+rwX,g+rwX /var/www/tesina-manager/media
```

No usar `chmod -R 777`. También verificar que Nginx tenga el `alias` terminado
en `/` y que `MEDIA_ROOT` apunte al mismo directorio.

### Los PDFs no aparecen en desarrollo

La publicación de `MEDIA_URL` está habilitada en `tesina_manager/urls.py` solo
cuando `DEBUG=True`. Confirmar que el archivo se guardó bajo `media/`, que la
URL comience con `/media/` y que no se esté probando ese comportamiento en
producción con `runserver`.

### Fallan las migraciones o aparecen cambios inesperados

Ejecutar:

```powershell
python manage.py makemigrations --check
python manage.py showmigrations
python manage.py migrate
```

No borrar migraciones aplicadas ni la base de datos para resolver un problema
normal de esquema. Revisar primero la migración pendiente y respaldar la base
antes de cualquier operación correctiva.

## Seguridad antes de producción

- Cambiar `SECRET_KEY`; la clave incluida en el archivo de desarrollo no debe
  reutilizarse.
- Establecer `DEBUG=False` y definir `ALLOWED_HOSTS`.
- Usar un usuario MySQL dedicado con contraseña fuerte y privilegios mínimos.
- Servir la aplicación con HTTPS y proteger las rutas de PDFs.
- Configurar `CSRF_TRUSTED_ORIGINS`, cookies seguras y límites de tamaño de
  subida.
- Sustituir o eliminar todas las credenciales de demostración.
- Mantener fuera del control de versiones `venv/`, `media/`, secretos y
  respaldos de la base de datos.
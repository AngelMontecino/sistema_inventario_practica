# Sistema de Inventario y POS

Sistema de gestión de inventario y punto de venta web, desarrollado con FastAPI (Backend) y Django (Frontend).

##  Requisitos Previos

- [Docker](https://www.docker.com/get-started) y [Docker Compose](https://docs.docker.com/compose/install/) instalados.

## Configuración e Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd sistema_inventario_backend
```

### 2. Configurar Variables de Entorno (.env)

Crea un archivo llamado `.env` en la raíz del proyecto (al mismo nivel que `docker-compose.yml`) y copia el siguiente contenido. Estas variables configuran tanto el backend, frontend como los servicios de base de datos y caché.

```ini
# --- Base de Datos (PostgreSQL) ---
DB_USER=postgres
DB_PASSWORD=tu_password_segura
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sistema_inventario
DB_INTERNAL_PORT=5432

# --- Redis (Caché & Borradores) ---
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_INTERNAL_PORT=6379
REDIS_DB=0
REDIS_LOCATION=redis://127.0.0.1:6379/1

# --- Backend (FastAPI) ---
SECRET_KEY=tu_clave_secreta_backend
ACCESS_TOKEN_EXPIRE_MINUTES=30
BACKEND_PORT=8000
BACKEND_INTERNAL_PORT=8000

# --- Frontend (Django) ---
DJANGO_SECRET_KEY=tu_clave_secreta_django
DEBUG=True
FRONTEND_PORT=3000
FRONTEND_INTERNAL_PORT=3000
BACKEND_URL=http://127.0.0.1:8000
```

> **Nota:** Al ejecutar con Docker, los hosts (`DB_HOST`, `REDIS_HOST`, `BACKEND_URL`) se configurarán automáticamente para usar los nombres de servicio internos (`db`, `redis`, `backend`), por lo que no necesitas cambiar esto para desarrollo local en contenedores. El archivo `docker-compose.yml` se encarga de inyectar estas variables.

### 3. Ejecutar el Proyecto con Docker

Para iniciar toda la aplicación (Base de datos, Redis, Backend y Frontend):

```bash
docker-compose up --build
```

Esto levantará los siguientes servicios:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentación API (Swagger)**: http://localhost:8000/docs
- **Base de Datos**: Puerto 5432 (accesible desde localhost)
- **Redis**: Puerto 6379 (accesible desde localhost)

### 4. Acceso Inicial

- **Usuario Admin por defecto**: (Si ya tienes una base de datos restaurada)
- **Restaurar Datos**:
  Si necesitas cargar datos iniciales (usuarios, productos), puedes usar los scripts incluidos:

  ```bash
  # Restaurar usuarios y sucursales
  docker-compose exec backend python gestor_usuarios.py load
  
  # Restaurar productos y categorías
  docker-compose exec backend python gestor_respaldos.py load
  ```



## Estructura del Proyecto

- `backend/`: API RESTful con FastAPI.
- `frontend/`: Interfaz de usuario con Django.
- `docker-compose.yml`: Orquestación de contenedores.
- `.env`: Variables de entorno compartidas.

## Scripts de Utilidad

El proyecto incluye scripts en la carpeta `backend/` para gestión de datos:
- `gestor_respaldos.py`: Respaldar/Restaurar Productos y Categorías.
- `gestor_usuarios.py`: Respaldar/Restaurar Usuarios y Sucursales.

Para crear un nuevo respaldo (dump) desde dentro del contenedor:
```bash
docker-compose exec backend python gestor_usuarios.py
```
Esto generará un archivo `.json` en el volumen del backend.

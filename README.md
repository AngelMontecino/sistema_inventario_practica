# Sistema de Inventario (Full Stack)

Sistema de gestión de inventarios con Backend en FastAPI y Frontend en Django.

## Tecnologías

### Backend

*   [FastAPI](https://fastapi.tiangolo.com/): Framework  para APIs.
*   [SQLAlchemy 2.0](https://www.sqlalchemy.org/): ORM para bases de datos.
*   [Pydantic V2](https://docs.pydantic.dev/): Validación de datos.
*   [PostgreSQL](https://www.postgresql.org/): Base de datos relacional.
*   [Passlib[bcrypt]](https://passlib.readthedocs.io/): Hashing de contraseñas.
*   [Python-Jose](https://python-jose.readthedocs.io/): Generación de tokens JWT.
### Frontend
*   **Django**: Framework Web (actuando como cliente).
*   **Bootstrap 5**: Diseño.
*   **Httpx**: Cliente HTTP para consumir la API.

---

## Instalación y Configuración

El proyecto funciona como un monorepo con dos carpetas principales: `backend` y `frontend`.

### 1. Clonar y Entorno Virtual
```bash
git clone <url-del-repo>
cd sistema_inventario
```

#### Para el Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Para el Frontend:
Abrir una **nueva terminal**:
```bash
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuración de Variables de Entorno (.env)

Es necesario crear un archivo `.env` en cada carpeta del proyecto (`backend/` y `frontend/`) para manejar configuraciones.

#### Backend (`backend/.env`)
Crea el archivo `backend/.env` con el siguiente contenido:
```env
# Base de datos
DB_USER=angel
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=<PUERTO_DB>
DB_NAME=sistema_inventario

# Seguridad
SECRET_KEY=tu_secret_key_segura_para_production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=puerto_redis
REDIS_DB=0
# REDIS_PASSWORD=tu_password 
```

#### Frontend (`frontend/.env`)
Crea el archivo `frontend/.env`:
```env
# Django 
DJANGO_SECRET_KEY=tu_django_secret_key_segura
DEBUG=True

# Backend 
BACKEND_URL=http://127.0.0.1:<PUERTO_BACKEND>

# Redis (Sesiones)
REDIS_LOCATION=redis://127.0.0.1:<PUERTO_REDIS>/1
```

### 3. Ejecutar el Proyecto

#### Backend (API)
En la terminal del backend:
```bash
# Puerto Backend
fastapi dev app/main.py --port <PUERTO_BACKEND>
```

#### Frontend (Web App)
En la terminal del frontend:
```bash
# Puerto Frontend
python manage.py runserver <PUERTO_FRONTEND>
```



##  Estructura del Proyecto

```
sistema_inventario/
├── backend/                # API FastAPI
│   ├── app/
│   │   ├── routers/        # Endpoints 
│   │   ├── crud.py
│   │   ├── models.py
│   │   └── schemas.py
│   └── ...
│
└── frontend/               # Cliente Django
    ├── core/               # Configuración Django
    └── web/                # Aplicación principal
        ├── templates/      # HTML 
        ├── views.py        # Lógica de consumo de API
        └── ...
```

##  Documentación API
Una vez corriendo el backend, visita:
*   [http://127.0.0.1:<PUERTO_BACKEND>/docs](http://127.0.0.1:<PUERTO_BACKEND>/docs)

##  Acceso Web
Una vez corriendo el frontend, visita:
*   [http://127.0.0.1:<PUERTO_FRONTEND>/](http://127.0.0.1:<PUERTO_FRONTEND>/)

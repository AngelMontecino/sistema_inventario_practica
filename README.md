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

### 2. Variables de Entorno (Backend)
Crea un archivo `.env` en `backend/` con las credenciales de tu BD PostgreSQL:
```env
DB_USER=angel
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sistema_inventario
```

### 3. Ejecutar el Proyecto

#### Backend (API)
En la terminal del backend:
```bash
# Puerto 8001
fastapi dev app/main.py --port 8001
```

#### Frontend (Web App)
En la terminal del frontend:
```bash
# Puerto 8002
python manage.py runserver 8002
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
*   [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

##  Acceso Web
Una vez corriendo el frontend, visita:
*   [http://127.0.0.1:8002/](http://127.0.0.1:8002/)

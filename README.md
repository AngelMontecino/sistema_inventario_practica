# Sistema de Inventario 



##  Tecnologías

*   [FastAPI](https://fastapi.tiangolo.com/): Framework  para APIs.
*   [SQLAlchemy 2.0](https://www.sqlalchemy.org/): ORM para bases de datos.
*   [Pydantic V2](https://docs.pydantic.dev/): Validación de datos.
*   [PostgreSQL](https://www.postgresql.org/): Base de datos relacional.
*   [Passlib[bcrypt]](https://passlib.readthedocs.io/): Hashing de contraseñas.
*   [Python-Jose](https://python-jose.readthedocs.io/): Generación de tokens JWT.

##  Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <url-del-repo>
cd sistema_inventario
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate   # En Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Crea un archivo `.env` en la raíz (o asegúrate de configurar las variables en tu entorno):
```env
DB_USER=angel
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sistema_inventario
```

### 5. Ejecutar el Servidor
```bash
fastapi dev app/main.py --port 8001
```
El servidor iniciará en `http://127.0.0.1:8001`.

##  Documentación API
Una vez corriendo, puedes acceder a la documentación interactiva en:
*   **http://127.0.0.1:8001/docs**

## Estructura del Proyecto
```
app/
├── crud.py          # Lógica de base de datos
├── database.py      # Conexión a DB
├── dependencies.py  # Dependencias (Auth)
├── main.py          # Punto de entrada
├── models.py        # Modelos SQLAlchemy
├── routers/         # Endpoints de la API
├── schemas.py       # Esquemas Pydantic
└── security.py      # Hashing y JWT
```

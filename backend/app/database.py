import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

#  Cargar variables del archivo .env
load_dotenv()

#  Construir la URL de conexión segura
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

#  Crear el motor 
engine = create_engine(DATABASE_URL)

#  Crear la sesión 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependencia para obtener la DB en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
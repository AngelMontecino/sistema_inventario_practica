from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, productos
from app import models 

def create_tables():
    Base.metadata.create_all(bind=engine)
    print(" Tablas creadas o verificadas")

app = FastAPI(title="Sistema de Inventario", on_startup=[create_tables])

app.include_router(auth.router)
app.include_router(productos.router)

@app.get("/")
def read_root():
    return {"sistema": "Backend Inventario"}
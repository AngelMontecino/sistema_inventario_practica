from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, productos, sucursales, terceros, inventarios, documentos, caja
from app import models 

def create_tables():
    Base.metadata.create_all(bind=engine)
    print(" Tablas creadas o verificadas")

app = FastAPI(title="Sistema de Inventario", on_startup=[create_tables])

app.include_router(auth.router)
app.include_router(sucursales.router)
app.include_router(productos.router)
app.include_router(terceros.router)
app.include_router(inventarios.router)
app.include_router(documentos.router)
app.include_router(caja.router)

@app.get("/")
def read_root():
    return {"sistema": "Backend Inventario"}
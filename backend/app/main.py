from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, productos, sucursales, terceros, inventarios, documentos, caja, dashboard
from app import models 

def create_tables():
    Base.metadata.create_all(bind=engine)
    pass
   

from contextlib import asynccontextmanager
from app.core.redis import redis_service

@asynccontextmanager
async def lifespan(app: FastAPI):

    redis_service.connect()
    create_tables()
    yield

    redis_service.close()

app = FastAPI(title="Sistema de Inventario", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(sucursales.router)
app.include_router(productos.router)
app.include_router(terceros.router)
app.include_router(inventarios.router)
app.include_router(documentos.router)
app.include_router(caja.router)
app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {"sistema": "Backend Inventario"}
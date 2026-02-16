from typing import List
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.database import get_db
from app.dependencies import get_current_active_user, get_redis
from app.core.redis import RedisService

router = APIRouter(
    prefix="/sucursales",
    tags=["Sucursales"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.SucursalResponse, status_code=status.HTTP_201_CREATED)
def crear_sucursal(
    sucursal: schemas.SucursalCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user),
    redis: RedisService = Depends(get_redis)
):
    if current_user.rol not in [models.TipoRol.ADMIN, models.TipoRol.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    db_sucursal = crud.get_sucursal_by_nombre(db, nombre=sucursal.nombre)
    if db_sucursal:
        raise HTTPException(status_code=400, detail="Ya existe una sucursal con este nombre")
    
    if sucursal.direccion:
        db_sucursal_dir = crud.get_sucursal_by_direccion(db, direccion=sucursal.direccion)
        if db_sucursal_dir:
            raise HTTPException(status_code=400, detail="Ya existe una sucursal con esta dirección")

    if sucursal.telefono:
        db_sucursal_tel = crud.get_sucursal_by_telefono(db, telefono=sucursal.telefono)
        if db_sucursal_tel:
             raise HTTPException(status_code=400, detail="Ya existe una sucursal con este número de teléfono")

    nueva_sucursal = crud.create_sucursal(db=db, sucursal=sucursal)
    
    # Invalidate cache
    redis.delete_pattern("sucursales:*")
    
    return nueva_sucursal

@router.get("/", response_model=List[schemas.SucursalResponse])
def listar_sucursales(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user),
    redis: RedisService = Depends(get_redis)
):
    cache_key = f"sucursales:list:{skip}:{limit}"
    cached_data = redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    sucursales = crud.get_sucursales(db, skip=skip, limit=limit)
    
    redis.set(cache_key, json.dumps(jsonable_encoder(sucursales)), ttl=300)
    
    return sucursales

@router.put("/{sucursal_id}", response_model=schemas.SucursalResponse)
def editar_sucursal(
    sucursal_id: int,
    sucursal_update: schemas.SucursalUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user),
    redis: RedisService = Depends(get_redis)
):
    if current_user.rol not in [models.TipoRol.ADMIN, models.TipoRol.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    db_sucursal = crud.update_sucursal(db, sucursal_id=sucursal_id, sucursal_update=sucursal_update)
    if not db_sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    # Invalidate cache
    redis.delete_pattern("sucursales:*")
    
    return db_sucursal

@router.put("/{sucursal_id}/principal", response_model=schemas.SucursalResponse)
def establecer_principal(
    sucursal_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user),
    redis: RedisService = Depends(get_redis)
):
    if current_user.rol not in [models.TipoRol.ADMIN, models.TipoRol.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    db_sucursal = crud.set_sucursal_principal(db, sucursal_id=sucursal_id)
    if not db_sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    # Invalidate cache
    redis.delete_pattern("sucursales:*")
    
    return db_sucursal

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.database import get_db
from app.dependencies import get_current_active_user

router = APIRouter(
    prefix="/sucursales",
    tags=["Sucursales"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.SucursalResponse, status_code=status.HTTP_201_CREATED)
def crear_sucursal(
    sucursal: schemas.SucursalCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    if current_user.rol != models.TipoRol.ADMIN:
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

    return crud.create_sucursal(db=db, sucursal=sucursal)

@router.get("/", response_model=List[schemas.SucursalResponse])
def listar_sucursales(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    return crud.get_sucursales(db, skip=skip, limit=limit)

@router.put("/{sucursal_id}", response_model=schemas.SucursalResponse)
def editar_sucursal(
    sucursal_id: int,
    sucursal_update: schemas.SucursalUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    if current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    db_sucursal = crud.update_sucursal(db, sucursal_id=sucursal_id, sucursal_update=sucursal_update)
    if not db_sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return db_sucursal

@router.put("/{sucursal_id}/principal", response_model=schemas.SucursalResponse)
def establecer_principal(
    sucursal_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    if current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    db_sucursal = crud.set_sucursal_principal(db, sucursal_id=sucursal_id)
    if not db_sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return db_sucursal

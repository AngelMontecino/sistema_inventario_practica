from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/terceros", tags=["Clientes y Proveedores"])

@router.post("/", response_model=schemas.ClienteProveedorResponse, status_code=status.HTTP_201_CREATED)
def crear_tercero(
    tercero: schemas.ClienteProveedorCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    # Validar RUT único
    existe = crud.get_tercero_by_rut(db, tercero.rut)
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe un cliente/proveedor con este RUT")
    
    return crud.create_tercero(db=db, tercero=tercero)

@router.get("/", response_model=List[schemas.ClienteProveedorResponse])
def listar_terceros(
    skip: int = 0, 
    limit: int = 100, 
    rut: Optional[str] = None,
    rol: Optional[str] = None,
    busqueda: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Lista clientes o proveedores con filtros.
    rut: Busca un registro específico por RUT.
    rol: cliente o proveedor para filtrar por tipo.
    busqueda: Filtro parcial por nombre.
    """
    return crud.get_terceros(db, skip=skip, limit=limit, rut=rut, rol=rol, busqueda=busqueda)

@router.get("/{tercero_id}", response_model=schemas.ClienteProveedorResponse)
def obtener_tercero(
    tercero_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    db_tercero = crud.get_tercero(db, tercero_id=tercero_id)
    if not db_tercero:
        raise HTTPException(status_code=404, detail="Cliente/Proveedor no encontrado")
    return db_tercero

@router.put("/{tercero_id}", response_model=schemas.ClienteProveedorResponse)
def actualizar_tercero(
    tercero_id: int, 
    tercero_update: schemas.ClienteProveedorUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    db_tercero = crud.update_tercero(db, tercero_id=tercero_id, tercero_update=tercero_update)
    if not db_tercero:
        raise HTTPException(status_code=404, detail="Cliente/Proveedor no encontrado")
    return db_tercero

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/inventarios", tags=["Inventario"])

@router.post("/", response_model=schemas.InventarioResponse, status_code=status.HTTP_201_CREATED)
def inicializar_stock(
    inventario: schemas.InventarioCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    if current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    nuevo_inventario = crud.create_inventario(db=db, inventario=inventario)
    if not nuevo_inventario:
         raise HTTPException(status_code=400, detail="El producto ya está registrado en esta sucursal")
    return nuevo_inventario

@router.get("/", response_model=List[schemas.InventarioResponse])
def consultar_inventario(
    skip: int = 0, 
    limit: int = 100, 
    sucursal_id: Optional[int] = None,
    alerta_stock: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Consulta stock disponible.
    sucursal_id: Filtra por sucursal específica.
    alerta_stock: Si es True, muestra solo productos con stock bajo (crítico).
    """
    return crud.get_inventarios(db, skip=skip, limit=limit, sucursal_id=sucursal_id, alerta_stock=alerta_stock)

@router.put("/{inventario_id}", response_model=schemas.InventarioResponse)
def ajustar_stock(
    inventario_id: int, 
    inventario_update: schemas.InventarioUpdate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Ajuste manual de stock, ubicación o niveles de alerta.
    """
    if current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    db_inventario = crud.update_inventario(db, inventario_id=inventario_id, inventario_update=inventario_update)
    if not db_inventario:
        raise HTTPException(status_code=404, detail="Registro de inventario no encontrado")
    return db_inventario

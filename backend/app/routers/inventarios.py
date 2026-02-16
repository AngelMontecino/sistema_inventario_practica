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
    if nuevo_inventario == "ExcedeStockMaximo":
         raise HTTPException(status_code=400, detail="La cantidad inicial excede el stock máximo permitido")
    if not nuevo_inventario:
         raise HTTPException(status_code=400, detail="El producto ya está registrado en esta sucursal")
    return nuevo_inventario

@router.get("/", response_model=List[schemas.InventarioResponse])
def consultar_inventario(
    skip: int = 0, 
    limit: int = 100, 
    sucursal_id: Optional[int] = None,
    producto_id: Optional[int] = None,
    alerta_stock: Optional[bool] = False,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Consulta stock disponible.
    sucursal_id: Filtra por sucursal específica.
    producto_id: Filtra por producto específico.
    alerta_stock: Si es True, muestra solo productos con stock bajo (crítico).
    categoria_id: Filtra por categoría de producto.
    """
    return crud.get_inventarios(db, skip=skip, limit=limit, sucursal_id=sucursal_id, producto_id=producto_id, alerta_stock=alerta_stock, categoria_id=categoria_id)

@router.get("/agrupado", response_model=schemas.InventarioPaginatedResponse)
def obtener_inventario_agrupado(
    skip: int = 0,
    limit: int = 100,
    sucursal_id: Optional[int] = None,
    busqueda: Optional[str] = None,
    categoria_id: Optional[int] = None,
    alerta_stock: bool = False,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Retorna el stock total agrupado por producto para una sucursal.
    """
    try:
        target_sucursal = None
        if current_user.rol == models.TipoRol.SUPERADMIN:
            target_sucursal = sucursal_id 
        elif current_user.rol == models.TipoRol.ADMIN:
            target_sucursal = sucursal_id if sucursal_id else current_user.id_sucursal
        else:
            target_sucursal = current_user.id_sucursal

        resultado = crud.get_inventario_agrupado(
            db, 
            sucursal_id=target_sucursal, 
            busqueda=busqueda, 
            categoria_id=categoria_id,
            alerta_stock=alerta_stock,
            skip=skip,
            limit=limit
        )
        return resultado
    except Exception as e:
      
        raise e

@router.get("/{inventario_id}", response_model=schemas.InventarioResponse)
def leer_inventario(
    inventario_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    db_inventario = crud.get_inventario(db, inventario_id=inventario_id)
    if db_inventario is None:
        raise HTTPException(status_code=404, detail="Inventario no encontrado")
    return db_inventario

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
    if db_inventario == "ExcedeStockMaximo":
        raise HTTPException(status_code=400, detail="La cantidad excede el stock máximo permitido")
    if not db_inventario:
        raise HTTPException(status_code=404, detail="Registro de inventario no encontrado")
    return db_inventario

@router.delete("/{inventario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_inventario(
    inventario_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    if current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
        
    resultado = crud.delete_inventario(db, inventario_id=inventario_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Inventario no encontrado")
    if resultado is False:
        raise HTTPException(status_code=400, detail="No se puede eliminar: El inventario tiene stock físico > 0. Ajuste a 0 primero.")
    return None



from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/productos", tags=["Productos y Categorías"])


# CATEGORIAS


@router.post("/categorias/", response_model=schemas.CategoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    categoria: schemas.CategoriaCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    return crud.create_categoria(db=db, categoria=categoria)

@router.get("/categorias/", response_model=List[schemas.CategoriaResponse])
def listar_categorias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # TODO: Implementar árbol jerárquico si se requiere
    return crud.get_categorias(db, skip=skip, limit=limit)


# PRODUCTOS


@router.post("/", response_model=schemas.ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(
    producto: schemas.ProductoCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    # Validar código de barras único
    if producto.codigo_barras:
        existe = db.query(models.Producto).filter(models.Producto.codigo_barras == producto.codigo_barras).first()
        if existe:
            raise HTTPException(status_code=400, detail="El código de barras ya existe")
            
    return crud.create_producto(db=db, producto=producto)

@router.get("/", response_model=List[schemas.ProductoResponse])
def listar_productos(
    skip: int = 0, 
    limit: int = 100, 
    busqueda: Optional[str] = None,
    id_categoria: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return crud.get_productos(db, skip=skip, limit=limit, busqueda=busqueda, id_categoria=id_categoria)

@router.get("/{producto_id}", response_model=schemas.ProductoResponse)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    db_producto = crud.get_producto(db, producto_id=producto_id)
    if db_producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_producto

@router.put("/{producto_id}", response_model=schemas.ProductoResponse)
def actualizar_producto(
    producto_id: int, 
    producto_update: schemas.ProductoCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    db_producto = crud.update_producto(db, producto_id=producto_id, producto_update=producto_update)
    if db_producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_producto

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
    if current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    return crud.create_categoria(db=db, categoria=categoria)

@router.get("/categorias/", response_model=List[schemas.CategoriaResponse])
def listar_categorias(
    flat: bool = False,
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_active_user)
):
    if flat:
        # Devuelve lista plana ordenada 
        return crud.get_categorias_flat_sorted(db)
    # Devuelve el árbol completo (categorías y subcategorías)
    return crud.get_categorias_arbol(db)

@router.get("/categorias/{categoria_id}", response_model=schemas.CategoriaResponse)
def obtener_categoria(categoria_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_active_user)):
    # Devuelve categoría específica con sus hijas
    db_categoria = crud.get_categoria(db, categoria_id=categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_categoria

@router.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(
    categoria_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    if current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    resultado = crud.delete_categoria(db, categoria_id=categoria_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if resultado is False:
        raise HTTPException(status_code=400, detail="No se puede eliminar la categoría porque tiene productos asociados")
    return None


# PRODUCTOS


@router.post("/", response_model=schemas.ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(
    producto: schemas.ProductoCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    if current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    # Validar código de barras único
    if producto.codigo_barras:
        existe = crud.get_producto_by_codigo(db, producto.codigo_barras)
        if existe:
            raise HTTPException(status_code=400, detail="El código de barras ya existe")
            
    return crud.create_producto(db=db, producto=producto)

@router.get("/", response_model=schemas.ProductoPaginatedResponse)
def listar_productos(
    skip: int = 0, 
    limit: int = 100, 
    busqueda: Optional[str] = None,
    id_categoria: Optional[int] = None,
    unidad_medida: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    return crud.get_productos(
        db, 
        skip=skip, 
        limit=limit, 
        busqueda=busqueda, 
        id_categoria=id_categoria,
        unidad_medida=unidad_medida,
        precio_min=precio_min,
        precio_max=precio_max
    )

@router.get("/{producto_id}", response_model=schemas.ProductoResponse)
def obtener_producto(producto_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_active_user)):
    db_producto = crud.get_producto(db, producto_id=producto_id)
    if db_producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_producto

@router.put("/{producto_id}", response_model=schemas.ProductoResponse)
def actualizar_producto(
    producto_id: int, 
    producto_update: schemas.ProductoUpdate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    if current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    db_producto = crud.update_producto(db, producto_id=producto_id, producto_update=producto_update)
    if db_producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_producto

@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(
    producto_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    if current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
        
    resultado = crud.delete_producto(db, producto_id=producto_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if resultado == "ConHistorial":
         raise HTTPException(status_code=400, detail="No se puede eliminar: El producto tiene historial de movimientos")
    if resultado == "ConStock":
         raise HTTPException(status_code=400, detail="No se puede eliminar: El producto tiene stock físico > 0")
         
    return None

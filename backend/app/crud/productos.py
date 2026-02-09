from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from app import models, schemas

# CATEGORIA

def get_categorias(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Categoria).offset(skip).limit(limit).all()

def get_categoria(db: Session, categoria_id: int):
    return db.query(models.Categoria).filter(models.Categoria.id_categoria == categoria_id).first()

def get_categorias_arbol(db: Session):

    return db.query(models.Categoria).filter(models.Categoria.id_padre == None).all()

def get_subcategorias(db: Session, categoria_id: int):
    return db.query(models.Categoria).filter(models.Categoria.id_padre == categoria_id).all()

def _flatten_categorias(categorias, level=0, result=None):
    if result is None:
        result = []
    
    for cat in categorias:
    
        prefix = "— " * level
        nombre_display = f"{prefix}{cat.nombre}"
        
        cat_copy = models.Categoria(
            id_categoria=cat.id_categoria,
            nombre=nombre_display,
            id_padre=cat.id_padre
        )
      
        
        result.append(cat_copy)
        
        if cat.hijas:
            _flatten_categorias(cat.hijas, level + 1, result)
            
    return result

def get_categorias_flat_sorted(db: Session):
    arbol = get_categorias_arbol(db)
    return _flatten_categorias(arbol)

def _tiene_productos_recursivo(categoria: models.Categoria) -> bool:
    # Verificar si la categoría actual tiene productos
    if categoria.productos:
        return True
    
    # Verificar recursivamente en las hijas
    for hija in categoria.hijas:
        if _tiene_productos_recursivo(hija):
            return True
            
    return False

def delete_categoria(db: Session, categoria_id: int):
    categoria = db.query(models.Categoria).filter(models.Categoria.id_categoria == categoria_id).first()
    if not categoria:
        return None
    
    # Verificar recursivamente si tiene productos en toda la rama
    if _tiene_productos_recursivo(categoria):
        return False # Indica que no se puede borrar por integridad
        
    db.delete(categoria)
    db.commit()
    return True

def create_categoria(db: Session, categoria: schemas.CategoriaCreate):
    # Convertir 0 a None para evitar error de FK si el frontend envía 0
    cat_data = categoria.model_dump()
    if cat_data.get("id_padre") == 0:
        cat_data["id_padre"] = None
        
    db_categoria = models.Categoria(**cat_data)
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


# PRODUCTO


def get_producto(db: Session, producto_id: int):
    return db.query(models.Producto).filter(models.Producto.id_producto == producto_id).first()

def get_productos(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    busqueda: str = None, 
    id_categoria: int = None,
    unidad_medida: str = None,
    precio_min: float = None,
    precio_max: float = None
):
    query = db.query(models.Producto).options(joinedload(models.Producto.categoria))
    
    if id_categoria:
        query = query.filter(models.Producto.id_categoria == id_categoria)
        
    if unidad_medida:
        query = query.filter(models.Producto.unidad_medida == unidad_medida)
        
    if precio_min is not None:
        query = query.filter(models.Producto.precio_venta >= precio_min)
        
    if precio_max is not None:
        query = query.filter(models.Producto.precio_venta <= precio_max)

    if busqueda:
        # Búsqueda insensible a mayúsculas por nombre o código de barras, e ID
        filtros_busqueda = [
            models.Producto.nombre.ilike(f"%{busqueda}%"),
            models.Producto.codigo_barras.ilike(f"%{busqueda}%")
        ]
        
        # Si es numérico, intentar buscar por ID exacto
        if busqueda.isdigit():
            filtros_busqueda.append(models.Producto.id_producto == int(busqueda))
            
        query = query.filter(or_(*filtros_busqueda))
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
        
    return {"total": total, "items": items}

def get_producto_by_codigo(db: Session, codigo: str):
    return db.query(models.Producto).filter(models.Producto.codigo_barras == codigo).first()

def update_producto(db: Session, producto_id: int, producto_update: schemas.ProductoUpdate):
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        return None
    
    update_data = producto_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_producto, key, value)
    
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def create_producto(db: Session, producto: schemas.ProductoCreate):
    # Validar código de barras si existe
    if producto.codigo_barras:
        existe = get_producto_by_codigo(db, producto.codigo_barras)
        if existe:
            return None 
    
    db_producto = models.Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    db.refresh(db_producto)
    return db_producto

def delete_producto(db: Session, producto_id: int):
    producto = get_producto(db, producto_id)
    if not producto:
        return None 
        
    # Validar historial
    usos = db.query(models.DetalleDocumento).filter(models.DetalleDocumento.id_producto == producto_id).count()
    if usos > 0:
        return "ConHistorial" 
        
    # Validar stock físico
    stock_total = db.query(func.sum(models.Inventario.cantidad)).filter(models.Inventario.id_producto == producto_id).scalar()
    if stock_total and stock_total > 0:
        return "ConStock"
        
    # Borrar inventarios vacíos (si existen)
    db.query(models.Inventario).filter(models.Inventario.id_producto == producto_id).delete()
    
    db.delete(producto)
    db.commit()
    return True

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from app import models, schemas

# INVENTARIO

def get_inventario(db: Session, inventario_id: int):
    return db.query(models.Inventario).filter(models.Inventario.id_inventario == inventario_id).first()

def get_inventario_by_sucursal_producto(db: Session, sucursal_id: int, producto_id: int, ubicacion: str = None):
    query = db.query(models.Inventario).filter(
        models.Inventario.id_sucursal == sucursal_id,
        models.Inventario.id_producto == producto_id
    )
    if ubicacion:
        query = query.filter(models.Inventario.ubicacion_especifica == ubicacion)
    return query.first()

def get_inventarios(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    sucursal_id: int = None, 
    producto_id: int = None,
    alerta_stock: bool = False
):
    query = db.query(models.Inventario).options(joinedload(models.Inventario.producto))
    
    if sucursal_id:
        query = query.filter(models.Inventario.id_sucursal == sucursal_id)

    if producto_id:
        query = query.filter(models.Inventario.id_producto == producto_id)
        
    if alerta_stock:
        # Stock crítico: cantidad <= stock_minimo
        query = query.filter(models.Inventario.cantidad <= models.Inventario.stock_minimo)
        
    return query.offset(skip).limit(limit).all()

def create_inventario(db: Session, inventario: schemas.InventarioCreate):
    # Verificar si ya existe relación sucursal-producto-ubicacion
    existe = get_inventario_by_sucursal_producto(
        db, 
        inventario.id_sucursal, 
        inventario.id_producto, 
        ubicacion=inventario.ubicacion_especifica
    )
    if existe:
        return None # Ya existe en esa ubicación
        
    db_inventario = models.Inventario(**inventario.model_dump())
    db.add(db_inventario)
    db.commit()
    db.refresh(db_inventario)
    return db_inventario

def update_inventario(db: Session, inventario_id: int, inventario_update: schemas.InventarioUpdate):
    db_inventario = get_inventario(db, inventario_id)
    if not db_inventario:
        return None
        
    update_data = inventario_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_inventario, key, value)
        
    db.add(db_inventario)
    db.commit()
    db.refresh(db_inventario)
    return db_inventario

def delete_inventario(db: Session, inventario_id: int):
    inv = get_inventario(db, inventario_id)
    if not inv:
        return None # Not found
    
    if inv.cantidad > 0:
        return False # No eliminar con stock
        
    db.delete(inv)
    db.commit()
    return True

def get_inventario_agrupado(db: Session, sucursal_id: int, busqueda: str = None):
    # Base query
    query = db.query(
        models.Inventario.id_producto,
        models.Producto.nombre,
        models.Producto.codigo_barras,
        func.sum(models.Inventario.cantidad).label("total_cantidad")
    ).join(models.Producto)\
     .filter(models.Inventario.id_sucursal == sucursal_id)

    if busqueda:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                models.Producto.nombre.ilike(f"%{busqueda}%"),
                models.Producto.codigo_barras.ilike(f"%{busqueda}%")
            )
        )

    # Agrupar por producto y sumar cantidad
    stats = query.group_by(models.Inventario.id_producto, models.Producto.nombre, models.Producto.codigo_barras)\
     .all()
    
    # Formatear
    resultado = []
    for row in stats:
        resultado.append({
            "id_producto": row.id_producto,
            "nombre": row.nombre,
            "codigo_barras": row.codigo_barras,
            "total_cantidad": row.total_cantidad
        })
    return resultado

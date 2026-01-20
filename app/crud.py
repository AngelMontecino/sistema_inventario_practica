from sqlalchemy.orm import Session
from app import models, schemas, security


# SUCURSAL


def get_sucursal(db: Session, sucursal_id: int):
    return db.query(models.Sucursal).filter(models.Sucursal.id_sucursal == sucursal_id).first()

def get_sucursales(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sucursal).offset(skip).limit(limit).all()

def create_sucursal(db: Session, sucursal: schemas.SucursalCreate):
    db_sucursal = models.Sucursal(**sucursal.model_dump())
    db.add(db_sucursal)
    db.commit()
    db.refresh(db_sucursal)
    return db_sucursal


# USUARIO

def get_usuario(db: Session, usuario_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id_usuario == usuario_id).first()

def get_usuario_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def get_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()

def create_usuario(db: Session, usuario: schemas.UsuarioCreate):
    # Implementación de hashing de password
    hashed_password = security.get_password_hash(usuario.password)
    db_usuario = models.Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        password=hashed_password,
        id_sucursal=usuario.id_sucursal,
        rol=usuario.rol,
        estado=usuario.estado
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario



# CATEGORIA


def get_categorias(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Categoria).offset(skip).limit(limit).all()

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
    id_categoria: int = None
):
    query = db.query(models.Producto)
    if id_categoria:
        query = query.filter(models.Producto.id_categoria == id_categoria)
    if busqueda:
        # Búsqueda insensible a mayúsculas por nombre o código de barras
        query = query.filter(
            (models.Producto.nombre.ilike(f"%{busqueda}%")) | 
            (models.Producto.codigo_barras.ilike(f"%{busqueda}%"))
        )
    return query.offset(skip).limit(limit).all()

def update_producto(db: Session, producto_id: int, producto_update: schemas.ProductoCreate):
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
    db_producto = models.Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

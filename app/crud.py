from sqlalchemy.orm import Session
from app import models, schemas, security

# ==========================================
# SUCURSAL
# ==========================================

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


# ==========================================
# USUARIO
# ==========================================

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


# ==========================================
# CATEGORIA
# ==========================================

def get_categorias(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Categoria).offset(skip).limit(limit).all()

def create_categoria(db: Session, categoria: schemas.CategoriaCreate):
    db_categoria = models.Categoria(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


# ==========================================
# PRODUCTO
# ==========================================

def get_producto(db: Session, producto_id: int):
    return db.query(models.Producto).filter(models.Producto.id_producto == producto_id).first()

def get_productos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Producto).offset(skip).limit(limit).all()

def create_producto(db: Session, producto: schemas.ProductoCreate):
    db_producto = models.Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

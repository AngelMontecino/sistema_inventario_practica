from sqlalchemy.orm import Session
from app import models, schemas, security


# SUCURSAL


def get_sucursal(db: Session, sucursal_id: int):
    return db.query(models.Sucursal).filter(models.Sucursal.id_sucursal == sucursal_id).first()

def get_sucursal_by_nombre(db: Session, nombre: str):
    return db.query(models.Sucursal).filter(models.Sucursal.nombre == nombre).first()

def get_sucursal_by_direccion(db: Session, direccion: str):
    if not direccion: return None
    return db.query(models.Sucursal).filter(models.Sucursal.direccion == direccion).first()

def get_sucursal_by_telefono(db: Session, telefono: str):
    if not telefono: return None
    return db.query(models.Sucursal).filter(models.Sucursal.telefono == telefono).first()



def get_sucursales(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sucursal).offset(skip).limit(limit).all()

def create_sucursal(db: Session, sucursal: schemas.SucursalCreate):
    db_sucursal = models.Sucursal(**sucursal.model_dump())
    db.add(db_sucursal)
    db.commit()
    db.refresh(db_sucursal)
    return db_sucursal

def update_sucursal(db: Session, sucursal_id: int, sucursal_update: schemas.SucursalUpdate):
    db_sucursal = get_sucursal(db, sucursal_id)
    if not db_sucursal:
        return None
    
    update_data = sucursal_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sucursal, key, value)
    
    db.add(db_sucursal)
    db.commit()
    db.refresh(db_sucursal)
    return db_sucursal

def set_sucursal_principal(db: Session, sucursal_id: int):
    #  Buscar la sucursal que queremos hacer principal
    db_sucursal = get_sucursal(db, sucursal_id)
    if not db_sucursal:
        return None
    
    #  Desmarcar cualquier otra sucursal que sea principal actualmente
    #    (Podría haber solo una, o ninguna)
    db.query(models.Sucursal).filter(models.Sucursal.es_principal == True).update({"es_principal": False})
    
    # Marcar la seleccionada como principal
    db_sucursal.es_principal = True
    db.add(db_sucursal)
    db.commit()
    db.refresh(db_sucursal)
    return db_sucursal


# USUARIO

def get_usuario(db: Session, usuario_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id_usuario == usuario_id).first()

def get_usuario_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def get_usuarios(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    id_sucursal: int = None
):
    query = db.query(models.Usuario)
    if id_sucursal:
        query = query.filter(models.Usuario.id_sucursal == id_sucursal)
    return query.offset(skip).limit(limit).all()

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

def update_usuario(db: Session, usuario_id: int, usuario_update: schemas.UsuarioUpdate):
    db_usuario = get_usuario(db, usuario_id)
    if not db_usuario:
        return None
    
    update_data = usuario_update.model_dump(exclude_unset=True)
    
    # Si se actualiza el password, hay que hashearlo
    if "password" in update_data:
        update_data["password"] = security.get_password_hash(update_data["password"])
        
    for key, value in update_data.items():
        setattr(db_usuario, key, value)
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario



# CATEGORIA


def get_categorias(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Categoria).offset(skip).limit(limit).all()

def get_categoria(db: Session, categoria_id: int):
    return db.query(models.Categoria).filter(models.Categoria.id_categoria == categoria_id).first()

def get_categorias_arbol(db: Session):

    return db.query(models.Categoria).filter(models.Categoria.id_padre == None).all()

def get_subcategorias(db: Session, categoria_id: int):
    return db.query(models.Categoria).filter(models.Categoria.id_padre == categoria_id).all()

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
    if busqueda:
        query = query.filter(
            (models.Producto.nombre.ilike(f"%{busqueda}%")) | 
            (models.Producto.codigo_barras.ilike(f"%{busqueda}%"))
        )
    return query.offset(skip).limit(limit).all()

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
    return db_producto

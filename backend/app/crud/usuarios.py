from sqlalchemy.orm import Session
from app import models, schemas, security

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

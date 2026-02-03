from sqlalchemy.orm import Session
from app import models, schemas

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

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app import models, schemas

# CLIENTE / PROVEEDOR

def get_tercero(db: Session, tercero_id: int):
    return db.query(models.ClienteProveedor).filter(models.ClienteProveedor.id_tercero == tercero_id).first()

def get_tercero_by_rut(db: Session, rut: str):
    return db.query(models.ClienteProveedor).filter(models.ClienteProveedor.rut == rut).first()

def get_terceros(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    rut: str = None, 
    rol: str = None, 
    busqueda: str = None
):
    query = db.query(models.ClienteProveedor)
    
    if rut:
        # Búsqueda exacta por RUT para validación rápida
        query = query.filter(models.ClienteProveedor.rut == rut)
    
    if rol:
        if rol.lower() == "cliente":
            query = query.filter(models.ClienteProveedor.es_cliente == True)
        elif rol.lower() == "proveedor":
            query = query.filter(models.ClienteProveedor.es_proveedor == True)
            
    if busqueda:
        # Búsqueda por nombre o RUT
        
        # Limpiar busqueda de puntos para comparar solo números (y guión/k)
        busqueda_limpia = busqueda.replace(".", "")
        
        query = query.filter(
            or_(
                models.ClienteProveedor.nombre.ilike(f"%{busqueda}%"),
                # Comparamos el RUT de la BD (sin puntos) con la búsqueda (sin puntos)
                func.replace(models.ClienteProveedor.rut, '.', '').ilike(f"%{busqueda_limpia}%")
            )
        )
        
    
    # Clonar query para contar total antes de paginar
    total = query.count()
    
    items = query.offset(skip).limit(limit).all()
    
    return {"total": total, "items": items}

def create_tercero(db: Session, tercero: schemas.ClienteProveedorCreate):
    db_tercero = models.ClienteProveedor(**tercero.model_dump())
    db.add(db_tercero)
    db.commit()
    db.refresh(db_tercero)
    return db_tercero

def update_tercero(db: Session, tercero_id: int, tercero_update: schemas.ClienteProveedorUpdate):
    db_tercero = get_tercero(db, tercero_id)
    if not db_tercero:
        return None
        
    update_data = tercero_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tercero, key, value)
        
    db.add(db_tercero)
    db.commit()
    db.refresh(db_tercero)
    return db_tercero

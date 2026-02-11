from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas, security
from app.database import get_db
from app.dependencies import get_current_active_user

router = APIRouter(tags=["Administración"])

@router.post("/token", response_model=schemas.Token)
def iniciar_sesion(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Buscar usuario por email (username en el form es el email)
    user = crud.get_usuario_by_email(db, email=form_data.username)
    
    # Validar usuario y contraseña
    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validar si el usuario está activo
    if not user.estado:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo",
        )
    
    # Crear Token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "rol": user.rol.value if hasattr(user.rol, 'value') else user.rol,
        "nombre": user.nombre,
        "id_sucursal": user.id_sucursal,
        "id_usuario": user.id_usuario,
        "nombre_sucursal": user.sucursal.nombre if user.sucursal else None
    }



@router.post("/usuarios/", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    usuario: schemas.UsuarioCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    # Validar permisos de creación
    if current_user.rol == models.TipoRol.SUPERADMIN:
        pass # Puede crear cualquier rol
    elif current_user.rol == models.TipoRol.ADMIN:
        # ADMIN solo puede crear VENDEDOR
        if usuario.rol != models.TipoRol.VENDEDOR:
             raise HTTPException(status_code=403, detail="Como Administrador, solo puedes crear Vendedores.")
    else:
        # VENDEDOR no puede crear usuarios 
        raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
   

    db_usuario = crud.get_usuario_by_email(db, email=usuario.email)
    if db_usuario:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    return crud.create_usuario(db=db, usuario=usuario)

@router.get("/usuarios/", response_model=List[schemas.UsuarioResponse])
def listar_usuarios(
    skip: int = 0, 
    limit: int = 100, 
    id_sucursal: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):

    return crud.get_usuarios(db, skip=skip, limit=limit, id_sucursal=id_sucursal)

@router.put("/usuarios/{usuario_id}", response_model=schemas.UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    usuario_update: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    # Lógica de permisos (RBAC)
    
    # 1. SUPERADMIN: Puede editar a cualquiera
    if current_user.rol == models.TipoRol.SUPERADMIN:
        pass 

    # 2. ADMIN: Restricciones
    elif current_user.rol == models.TipoRol.ADMIN:
        # No puede editar a otro ADMIN o SUPERADMIN (a menos que sea él mismo)
        if usuario_id != current_user.id_usuario:
             # Buscar al usuario objetivo para ver su rol actual
             target_user = crud.get_usuario(db, usuario_id)
             if target_user and target_user.rol in [models.TipoRol.ADMIN, models.TipoRol.SUPERADMIN]:
                 raise HTTPException(status_code=403, detail="No tienes permisos para editar a otro Administrador o Superadmin.")
        
        # Validar cambios de Rol (No puede ascender a nadie a ADMIN o SUPERADMIN)
        if usuario_update.rol and usuario_update.rol in [models.TipoRol.ADMIN, models.TipoRol.SUPERADMIN]:
             # Si se está editando a sí mismo, tal vez pueda mantener su rol, pero no cambiarse a SUPERADMIN
             if usuario_update.rol == models.TipoRol.SUPERADMIN:
                 raise HTTPException(status_code=403, detail="No puedes auto-ascenderte a Superadmin.")
             # Si intenta hacer a otro ADMIN
             if usuario_id != current_user.id_usuario:
                 raise HTTPException(status_code=403, detail="No tienes permisos para asignar el rol de Administrador.")

    # 3. VENDEDOR: Solo a sí mismo y con restricciones
    elif current_user.id_usuario == usuario_id:
        # Validar que no intente cambiar campos sensibles
        if usuario_update.rol is not None:
             raise HTTPException(status_code=403, detail="No tienes permisos para cambiar tu rol")
        if usuario_update.id_sucursal is not None:
             raise HTTPException(status_code=403, detail="No tienes permisos para cambiar tu sucursal")
        if usuario_update.estado is not None:
             raise HTTPException(status_code=403, detail="No tienes permisos para cambiar tu estado")
    else:
        # Vendedor intentando editar a otro
        raise HTTPException(status_code=403, detail="No tienes permisos para editar este usuario")

    db_usuario = crud.update_usuario(db, usuario_id=usuario_id, usuario_update=usuario_update)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return db_usuario

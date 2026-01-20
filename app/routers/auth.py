from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db

router = APIRouter(tags=["Administración"])

@router.post("/token", response_model=schemas.Token)
def iniciar_sesion(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    #  Buscar usuario por email (username en el form es el email)
    user = crud.get_usuario_by_email(db, email=form_data.username)
    
    # Validar usuario y contraseña
    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear Token 
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/sucursales/", response_model=schemas.SucursalResponse, status_code=status.HTTP_201_CREATED)
def crear_sucursal(sucursal: schemas.SucursalCreate, db: Session = Depends(get_db)):
    return crud.create_sucursal(db=db, sucursal=sucursal)

@router.post("/usuarios/", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = crud.get_usuario_by_email(db, email=usuario.email)
    if db_usuario:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    return crud.create_usuario(db=db, usuario=usuario)

@router.get("/usuarios/", response_model=List[schemas.UsuarioResponse])
def listar_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    usuarios = crud.get_usuarios(db, skip=skip, limit=limit)
    return usuarios

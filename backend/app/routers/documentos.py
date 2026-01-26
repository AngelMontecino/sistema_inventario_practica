from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/documentos", tags=["Documentos (Ventas/Compras)"])

@router.post("/", response_model=schemas.DocumentoResponse, status_code=status.HTTP_201_CREATED)
def crear_documento(
    documento: schemas.DocumentoCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Registra una VENTA o COMPRA.
    - **Venta**: Valida stock y descuenta inventario.
    - **Compra**: Aumenta stock en inventario.
    """
    resultado = crud.create_documento(db=db, documento=documento)
    if isinstance(resultado, dict) and "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    return resultado

@router.get("/{documento_id}", response_model=schemas.DocumentoResponse)
def obtener_documento(
    documento_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    db_documento = crud.get_documento(db, documento_id=documento_id)
    if not db_documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return db_documento

@router.put("/{documento_id}/anular", response_model=schemas.DocumentoResponse)
def anular_documento(
    documento_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Anula un documento y revierte los movimientos de stock asociados.
    """
    db_documento = crud.anular_documento(db, documento_id=documento_id)
    if not db_documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return db_documento

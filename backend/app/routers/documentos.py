from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
from app.database import get_db
from app.dependencies import get_current_active_user
from app.core.redis import delete_cache

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
    # Validar Caja Abierta 
    estado_caja = crud.verificar_estado_caja(db, documento.id_sucursal)
    if estado_caja["estado"] != "ABIERTA":
         if estado_caja["estado"] == "PENDIENTE_CIERRE":
             raise HTTPException(status_code=400, detail=f"BLOQUEO: {estado_caja['mensaje']}")
         raise HTTPException(status_code=400, detail="No hay caja abierta en esta sucursal. Debe abrir caja para realizar operaciones.")

    # Asignar usuario autenticado
    try:
        documento.id_usuario = current_user.id_usuario
        resultado = crud.create_documento(db=db, documento=documento)
        if isinstance(resultado, dict) and "error" in resultado:
            raise HTTPException(status_code=400, detail=resultado["error"])
        
        # Invalidar caché
        delete_cache(f"caja:resumen:{documento.id_sucursal}")
        return resultado
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Error Interno: {str(e)}")

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

    # Invalidar caché
    delete_cache(f"caja:resumen:{db_documento.id_sucursal}")
    return db_documento

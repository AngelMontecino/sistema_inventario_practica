from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/caja", tags=["Caja"])

@router.post("/apertura", response_model=schemas.MovimientoCajaResponse, status_code=status.HTTP_201_CREATED)
def abrir_caja(
    monto_inicial: float,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Registra APERTURA de caja para la sucursal del usuario.
    """
    return crud.abrir_caja(db=db, sucursal_id=current_user.id_sucursal, usuario_id=current_user.id_usuario, monto=monto_inicial)

@router.post("/cierre", response_model=schemas.CierreCajaResponse)
def cerrar_caja(
    cierre_data: schemas.CierreCajaRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Registra CIERRE de caja y retorna cuadratura.
    """
    return crud.cerrar_caja(db=db, sucursal_id=current_user.id_sucursal, usuario_id=current_user.id_usuario, monto_real=cierre_data.monto_real)

@router.get("/resumen", response_model=schemas.CajaResumenResponse)
def obtener_resumen(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Obtiene el resumen actual de la caja desde la última apertura.
    """
    return crud.obtener_resumen_caja(db=db, sucursal_id=current_user.id_sucursal)

@router.post("/movimientos", response_model=schemas.MovimientoCajaResponse, status_code=status.HTTP_201_CREATED)
def registrar_movimiento(
    movimiento: schemas.MovimientoCajaCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Registra un ingreso o egreso manual (NO VENTA/COMPRA).
    El usuario debe especificar tipo INGRESO o EGRESO.
    """
    if movimiento.tipo in [models.TipoMovimientoCaja.APERTURA, models.TipoMovimientoCaja.CIERRE]:
         raise HTTPException(status_code=400, detail="Use los endpoints de apertura/cierre para estas operaciones")
    
    # Asegurar que el usuario registra en su sucursal (o permitir admin cambiar)
    # Por ahora forzamos sucursal del usuario logueado si no coincide 
    if movimiento.id_sucursal != current_user.id_sucursal:
        raise HTTPException(status_code=403, detail="No puede registrar movimientos en otra sucursal")
        
    resultado = crud.registrar_movimiento_caja(db=db, movimiento=movimiento)
    if isinstance(resultado, dict) and "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    return resultado

@router.get("/reportes", response_model=List[schemas.ReporteCajaItem])
def obtener_reportes(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    sucursal_id: Optional[int] = None,
    usuario_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Lista las sesiones de caja (Apertura - Cierre) en un rango de fechas.
    Incluye detalle contable de cada sesión.
    """
    return crud.get_reporte_caja_historico(
        db=db, 
        fecha_inicio=fecha_inicio, 
        fecha_fin=fecha_fin, 
        sucursal_id=sucursal_id, 
        usuario_id=usuario_id
    )

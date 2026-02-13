from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_active_user
from app.core.redis import get_cache, set_cache, delete_cache
import json
from fastapi.encoders import jsonable_encoder

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
    resultado = crud.abrir_caja(db=db, sucursal_id=current_user.id_sucursal, usuario_id=current_user.id_usuario, monto=monto_inicial)
    if isinstance(resultado, dict) and "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    
    # Invalidate cache
    delete_cache(f"caja:resumen:{current_user.id_sucursal}")
    return resultado

@router.get("/estado", response_model=schemas.EstadoCajaResponse)
def consultar_estado_caja(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Consulta el estado de la caja de la sucursal: ABIERTA, CERRADA, PENDIENTE_CIERRE
    """
    resultado = crud.verificar_estado_caja(db, current_user.id_sucursal)
    
    # Serializar 'info' si existe (es un objeto ORM MovimientosCaja)
    info_data = None
    if resultado.get("info"):
        obj = resultado["info"]
        info_data = {
            "id_movimiento": obj.id_movimiento,
            "fecha": obj.fecha,
            "usuario_nombre": obj.usuario.nombre,
            "usuario_id": obj.id_usuario
        }
    
    return {
        "estado": resultado["estado"],
        "mensaje": resultado["mensaje"],
        "info": info_data
    }

@router.post("/cierre", response_model=schemas.CierreCajaResponse)
def cerrar_caja(
    cierre_data: schemas.CierreCajaRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Registra CIERRE de caja y retorna cuadratura.
    """
    # Recuperar apertura objetivo 
    apertura_target = None
    if cierre_data.id_apertura:
        apertura_target = crud.get_movimiento(db, cierre_data.id_apertura)
        if not apertura_target or apertura_target.tipo != models.TipoMovimientoCaja.APERTURA:
             raise HTTPException(status_code=404, detail="Apertura no encontrada")
    else:
        apertura_target = crud.get_ultimo_cierre_o_apertura(db, current_user.id_sucursal)
        if not apertura_target or apertura_target.tipo != models.TipoMovimientoCaja.APERTURA:
             raise HTTPException(status_code=400, detail="No hay caja abierta para cerrar")

    # Validar Propiedad
    if current_user.rol != models.TipoRol.ADMIN:
        if apertura_target.id_usuario != current_user.id_usuario:
             raise HTTPException(status_code=403, detail="No tienes permisos para cerrar una caja abierta por otro usuario")

    # Proceder
    resultado = crud.cerrar_caja(
        db=db, 
        sucursal_id=current_user.id_sucursal, 
        usuario_id=current_user.id_usuario, 
        monto_real=cierre_data.monto_real,
        id_apertura=apertura_target.id_movimiento
    )
    if isinstance(resultado, dict) and "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    
    # Invalidate cache
    delete_cache(f"caja:resumen:{current_user.id_sucursal}")
    return resultado

@router.get("/resumen", response_model=schemas.CajaResumenResponse)
def obtener_resumen(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Obtiene el resumen actual de la caja desde la última apertura.
    """
    cache_key = f"caja:resumen:{current_user.id_sucursal}"
    cached_data = get_cache(cache_key)
    
    if cached_data:
        pass 
        return json.loads(cached_data)

    resumen = crud.obtener_resumen_caja(db=db, sucursal_id=current_user.id_sucursal)
    
    # Caché del resultado 
    resumen_schema = schemas.CajaResumenResponse.model_validate(resumen)
    encoded_data = jsonable_encoder(resumen_schema)
    set_cache(cache_key, json.dumps(encoded_data), ttl=60) # Caché por 60s
    
    return resumen

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
    if movimiento.id_sucursal != current_user.id_sucursal and current_user.rol != models.TipoRol.ADMIN:
        raise HTTPException(status_code=403, detail="No puede registrar movimientos en otra sucursal")
    
    # Forzar ID de usuario desde el token
    movimiento.id_usuario = current_user.id_usuario
    # Forzar sucursal si no es admin 
    if current_user.rol != models.TipoRol.ADMIN:
        movimiento.id_sucursal = current_user.id_sucursal
        
    resultado = crud.registrar_movimiento_caja(db=db, movimiento=movimiento)
    if isinstance(resultado, dict) and "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    
    # Invalidate cache
    delete_cache(f"caja:resumen:{current_user.id_sucursal}")
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

@router.get("/sesion/{id_apertura}", response_model=schemas.CajaSesionDetalleResponse)
def obtener_detalle_sesion(
    id_apertura: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Obtiene el detalle completo de una sesión de caja (Apertura -> Cierre).
    """
    detalle = crud.get_detalle_sesion_caja(db, id_apertura)
    if not detalle:
         raise HTTPException(status_code=404, detail="Sesión de caja no encontrada")
    
    if current_user.rol != models.TipoRol.ADMIN:
        # Recuperar objeto apertura para chequear sucursal
        # (El crud ya filtra, pero el detalle checa permissions extra)
        apertura = crud.get_movimiento(db, id_apertura)
        if apertura and apertura.id_sucursal != current_user.id_sucursal:
             raise HTTPException(status_code=403, detail="No tiene permiso para ver esta caja")
             
    return detalle

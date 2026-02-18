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
    resultado = crud.abrir_caja(db=db, sucursal_id=current_user.id_sucursal, usuario_id=current_user.id_usuario, monto=monto_inicial)
    if isinstance(resultado, dict) and "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    
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
    
    return resultado

@router.get("/resumen", response_model=schemas.CajaResumenResponse)
def obtener_resumen(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Obtiene el resumen actual de la caja desde la última apertura.
    """

    resumen = crud.obtener_resumen_caja(db=db, sucursal_id=current_user.id_sucursal)
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

#  BORRADORES 
from app.core.redis import redis_service
from typing import Dict, Any

@router.post("/borrador", status_code=status.HTTP_200_OK)
def guardar_borrador(
    borrador: Dict[str, Any],
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Guarda un borrador de venta en Redis para el usuario y sucursal actual.
    24 horas
    """
    if not redis_service.client:
        raise HTTPException(status_code=503, detail="Servicio de caché no disponible")

    key = f"draft:{current_user.id_sucursal}:{current_user.id_usuario}"
    
   
    import json
    try:
        json_data = json.dumps(borrador)
        redis_service.set(key, json_data, ttl=86400) # 24 horas
        return {"mensaje": "Borrador guardado correctamente"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Error guardando borrador: {str(e)}")

@router.get("/borrador", response_model=Dict[str, Any])
def obtener_borrador(
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Recupera el borrador activo del usuario.
    """
    if not redis_service.client:
        raise HTTPException(status_code=503, detail="Servicio de caché no disponible")

    key = f"draft:{current_user.id_sucursal}:{current_user.id_usuario}"
    data = redis_service.get(key)
    
    if not data:
        return {} # Retorna vacio si no hay borrador

    import json
    try:
        return json.loads(data)
    except:
         return {}

@router.delete("/borrador", status_code=status.HTTP_200_OK)
def eliminar_borrador(
    current_user: models.Usuario = Depends(get_current_active_user)
):
    """
    Elimina el borrador del usuario.
    """
    if not redis_service.client:
        raise HTTPException(status_code=503, detail="Servicio de caché no disponible")

    key = f"draft:{current_user.id_sucursal}:{current_user.id_usuario}"
    redis_service.delete(key)
    return {"mensaje": "Borrador eliminado"}

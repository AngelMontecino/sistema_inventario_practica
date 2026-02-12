from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from datetime import datetime
from app import models, schemas

# CAJA (APERTURA / CIERRE / CUADRATURA)

def get_ultimo_cierre_o_apertura(db: Session, sucursal_id: int):
    return db.query(models.MovimientosCaja)\
        .filter(
            models.MovimientosCaja.id_sucursal == sucursal_id,
            models.MovimientosCaja.tipo.in_([models.TipoMovimientoCaja.APERTURA, models.TipoMovimientoCaja.CIERRE])
        )\
        .order_by(desc(models.MovimientosCaja.fecha))\
        .first()

def abrir_caja(db: Session, sucursal_id: int, usuario_id: int, monto: float):
    # Verificar estado actual
    ultimo = get_ultimo_cierre_o_apertura(db, sucursal_id)
    if ultimo and ultimo.tipo == models.TipoMovimientoCaja.APERTURA:
        # Ya existe una caja abierta 
        return {"error": f"Ya existe una caja abierta por {ultimo.usuario.nombre}. Solo puede haber una caja abierta por sucursal."}
        
    movimiento = models.MovimientosCaja(
        id_sucursal=sucursal_id,
        id_usuario=usuario_id,
        tipo=models.TipoMovimientoCaja.APERTURA,
        monto=monto,
        descripcion="Apertura de Caja"
    )
    db.add(movimiento)
    db.commit()
    db.refresh(movimiento)
    return movimiento

def verificar_estado_caja(db: Session, sucursal_id: int):
    ultimo = get_ultimo_cierre_o_apertura(db, sucursal_id)
    
    if not ultimo or ultimo.tipo == models.TipoMovimientoCaja.CIERRE:
        return {"estado": "CERRADA", "mensaje": "No hay caja abierta"}
    
    # Es APERTURA
    hoy = datetime.now().date()
    fecha_apertura = ultimo.fecha.date()
    
    if fecha_apertura < hoy:
        return {
            "estado": "PENDIENTE_CIERRE", 
            "mensaje": f"Caja abierta del día {fecha_apertura}. Debe cerrarla antes de continuar.",
            "info": ultimo
        }
    
    return {
        "estado": "ABIERTA", 
        "mensaje": "Caja abierta y operativa",
        "info": ultimo
    }

def registrar_movimiento_caja(db: Session, movimiento: schemas.MovimientoCajaCreate):
    # Dynamic import to avoid circular dependency
    from .documentos import get_documento

    # Validar Caja Abierta
    ultimo = get_ultimo_cierre_o_apertura(db, movimiento.id_sucursal)
    if not ultimo or ultimo.tipo == models.TipoMovimientoCaja.CIERRE:
        return {"error": "Caja cerrada. Debe abrir caja antes de registrar movimientos."}

    # Validar Documento Asociado (Misma Sucursal)
    monto_final = movimiento.monto
    if movimiento.id_documento_asociado:
        doc = get_documento(db, movimiento.id_documento_asociado)
        if not doc:
            return {"error": "El documento asociado no existe."}
        if doc.id_sucursal != movimiento.id_sucursal:
             return {"error": "El documento asociado pertenece a otra sucursal."}
        if doc.estado_pago == models.EstadoPago.ANULADO:
             return {"error": "No se puede asociar un movimiento a un documento ANULADO."}
        
        # monto de total del documento si no se especifica
        if monto_final is None:
            monto_final = doc.total # Usamos la propiedad calculada
            
    if monto_final is None:
         return {"error": "Debe especificar un monto si no asocia un documento."}

    # Crear objeto ignorando el campo monto del esquema si era None, usandolo en constructor
    datos_mov = movimiento.model_dump()
    datos_mov["monto"] = monto_final
    
    db_mov = models.MovimientosCaja(**datos_mov)
    db.add(db_mov)
    db.commit()
    db.refresh(db_mov)
    return db_mov

def obtener_resumen_caja(db: Session, sucursal_id: int, id_apertura: Optional[int] = None):
    # Buscar última apertura o la específica solicitada
    ultimo = None
    if id_apertura:
        ultimo = db.query(models.MovimientosCaja).filter(
            models.MovimientosCaja.id_movimiento == id_apertura,
            models.MovimientosCaja.tipo == models.TipoMovimientoCaja.APERTURA,
            models.MovimientosCaja.id_sucursal == sucursal_id
        ).first()
        if not ultimo:
            return {"error": "Apertura no encontrada o no pertenece a la sucursal"}
    else:
        ultimo = get_ultimo_cierre_o_apertura(db, sucursal_id)
    
    if not ultimo or ultimo.tipo == models.TipoMovimientoCaja.CIERRE:
        # No hay caja abierta
        return {
            "saldo_inicial": 0,
            "ingresos_ventas": 0,
            "egresos_compras": 0,
            "ingresos_extra": 0,
            "egresos_extra": 0,
            "saldo_teorico": 0,
            "estado": "CERRADA"
        }
    
    # Calcular hasta AHORA
    resumen = calcular_resumen_periodo(db, sucursal_id, ultimo.fecha, datetime.now(), ultimo.monto)
    resumen["estado"] = "ABIERTA"
    return resumen

def cerrar_caja(db: Session, sucursal_id: int, usuario_id: int, monto_real: float, id_apertura: Optional[int] = None):
    resumen = obtener_resumen_caja(db, sucursal_id, id_apertura=id_apertura)
    if "error" in resumen:
        return resumen

    # Registrar cierre
    cierre = models.MovimientosCaja(
        id_sucursal=sucursal_id,
        id_usuario=usuario_id,
        tipo=models.TipoMovimientoCaja.CIERRE,
        monto=monto_real, 
        descripcion=f"Cierre de Caja {id_apertura if id_apertura else 'General'}. Diferencia: {float(monto_real) - float(resumen['saldo_teorico'])}"
    )
    db.add(cierre)
    db.commit()
    db.refresh(cierre)

    # Calcular reporte de productos
    productos = obtener_reporte_productos(db, sucursal_id, resumen["fecha_inicio"], datetime.now()) # resumen needs start date

    return {
        **resumen,
        "monto_real": monto_real,
        "diferencia": float(monto_real) - float(resumen['saldo_teorico']),
        "productos": productos
    }


def calcular_resumen_periodo(db: Session, sucursal_id: int, fecha_inicio: datetime, fecha_fin: datetime, saldo_inicial: float):
    #  Sumar Ventas (Ingresos)
    ventas = db.query(func.sum(models.DetalleDocumento.cantidad * models.DetalleDocumento.precio_unitario * (1 - models.DetalleDocumento.descuento / 100)))\
        .join(models.Documento)\
        .filter(
            models.Documento.id_sucursal == sucursal_id,
            models.Documento.fecha_emision >= fecha_inicio,
            models.Documento.fecha_emision <= fecha_fin, # Added fecha_fin check
            models.Documento.tipo_operacion == models.TipoOperacion.VENTA,
            models.Documento.estado_pago == models.EstadoPago.PAGADO
        ).scalar() or 0
        
    # Sumar Compras (Egresos)
    compras = db.query(func.sum(models.DetalleDocumento.cantidad * models.DetalleDocumento.precio_unitario * (1 - models.DetalleDocumento.descuento / 100)))\
        .join(models.Documento)\
        .filter(
            models.Documento.id_sucursal == sucursal_id,
            models.Documento.fecha_emision >= fecha_inicio,
            models.Documento.fecha_emision <= fecha_fin,
            models.Documento.tipo_operacion == models.TipoOperacion.COMPRA,
            models.Documento.estado_pago == models.EstadoPago.PAGADO
        ).scalar() or 0
        
    # Sumar Movimientos Extra (EXCLUYENDO los asociados a documentos para no duplicar con Ventas/Compras)
    ingresos_extra = db.query(func.sum(models.MovimientosCaja.monto))\
        .filter(
            models.MovimientosCaja.id_sucursal == sucursal_id,
            models.MovimientosCaja.fecha >= fecha_inicio,
            models.MovimientosCaja.fecha <= fecha_fin,
            models.MovimientosCaja.tipo == models.TipoMovimientoCaja.INGRESO,
            models.MovimientosCaja.id_documento_asociado.is_(None)
        ).scalar() or 0
        
    egresos_extra = db.query(func.sum(models.MovimientosCaja.monto))\
        .filter(
            models.MovimientosCaja.id_sucursal == sucursal_id,
            models.MovimientosCaja.fecha >= fecha_inicio,
            models.MovimientosCaja.fecha <= fecha_fin,
            models.MovimientosCaja.tipo == models.TipoMovimientoCaja.EGRESO,
            models.MovimientosCaja.id_documento_asociado.is_(None)
        ).scalar() or 0
        
    saldo_teorico = saldo_inicial + ventas + ingresos_extra - compras - egresos_extra
    
    # Obtener Lista de Documentos
    docs = db.query(models.Documento)\
        .options(joinedload(models.Documento.tercero), joinedload(models.Documento.usuario))\
        .filter(
            models.Documento.id_sucursal == sucursal_id,
            models.Documento.fecha_emision >= fecha_inicio,
            models.Documento.fecha_emision <= fecha_fin,
            models.Documento.estado_pago == models.EstadoPago.PAGADO
        ).order_by(models.Documento.fecha_emision.desc()).all()
        
    # Obtener Lista de Movimientos Extra
    movs_extra = db.query(models.MovimientosCaja)\
        .options(joinedload(models.MovimientosCaja.usuario))\
        .filter(
            models.MovimientosCaja.id_sucursal == sucursal_id,
            models.MovimientosCaja.fecha >= fecha_inicio,
            models.MovimientosCaja.fecha <= fecha_fin,
            models.MovimientosCaja.tipo.in_([models.TipoMovimientoCaja.INGRESO, models.TipoMovimientoCaja.EGRESO]),
            models.MovimientosCaja.id_documento_asociado.is_(None)
        ).order_by(models.MovimientosCaja.fecha.desc()).all()

    return {
        "saldo_inicial": int(saldo_inicial),
        "ingresos_ventas": int(ventas),
        "egresos_compras": int(compras),
        "ingresos_extra": int(ingresos_extra),
        "egresos_extra": int(egresos_extra),
        "saldo_teorico": int(saldo_teorico),
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "documentos": docs,
        "movimientos_extra": movs_extra
    }

def obtener_reporte_productos(db: Session, sucursal_id: int, fecha_inicio: datetime, fecha_fin: datetime):
    """
    Agrupa los productos vendidos y comprados en el periodo.
    """
    # Ventas
    ventas = db.query(
        models.Producto.id_producto,
        models.Producto.nombre,
        models.Producto.codigo_barras,
        func.sum(models.DetalleDocumento.cantidad).label("cantidad"),
        func.sum(models.DetalleDocumento.cantidad * models.DetalleDocumento.precio_unitario * (1 - models.DetalleDocumento.descuento / 100)).label("total")
    ).join(models.DetalleDocumento.producto)\
     .join(models.DetalleDocumento.documento)\
     .filter(
        models.Documento.id_sucursal == sucursal_id,
        models.Documento.fecha_emision >= fecha_inicio,
        models.Documento.fecha_emision <= fecha_fin,
        models.Documento.tipo_operacion == models.TipoOperacion.VENTA,
        models.Documento.estado_pago == models.EstadoPago.PAGADO
    ).group_by(models.Producto.id_producto, models.Producto.nombre, models.Producto.codigo_barras).all()


    compras = db.query(
        models.Producto.id_producto,
        models.Producto.nombre,
        models.Producto.codigo_barras,
        func.sum(models.DetalleDocumento.cantidad).label("cantidad"),
        func.sum(models.DetalleDocumento.cantidad * models.DetalleDocumento.precio_unitario * (1 - models.DetalleDocumento.descuento / 100)).label("total")
    ).join(models.DetalleDocumento.producto)\
     .join(models.DetalleDocumento.documento)\
     .filter(
        models.Documento.id_sucursal == sucursal_id,
        models.Documento.fecha_emision >= fecha_inicio,
        models.Documento.fecha_emision <= fecha_fin,
        models.Documento.tipo_operacion == models.TipoOperacion.COMPRA,
        models.Documento.estado_pago == models.EstadoPago.PAGADO
    ).group_by(models.Producto.id_producto, models.Producto.nombre, models.Producto.codigo_barras).all()

    # Unificar
    reporte = {}
    
    for v in ventas:
        pid = v.id_producto
        reporte[pid] = {
            "id_producto": pid,
            "nombre": v.nombre,
            "codigo_barras": v.codigo_barras,
            "cantidad_ventas": int(v.cantidad),
            "total_ventas": int(v.total),
            "cantidad_compras": 0,
            "total_compras": 0
        }
        
    for c in compras:
        pid = c.id_producto
        if pid not in reporte:
            reporte[pid] = {
                "id_producto": pid,
                "nombre": c.nombre,
                "codigo_barras": c.codigo_barras,
                "cantidad_ventas": 0,
                "total_ventas": 0,
                "cantidad_compras": 0,
                "total_compras": 0
            }
        reporte[pid]["cantidad_compras"] = int(c.cantidad)
        reporte[pid]["total_compras"] = int(c.total)
        
    return list(reporte.values())

def get_reporte_caja_historico(db, fecha_inicio: datetime, fecha_fin: datetime, sucursal_id: Optional[int] = None, usuario_id: Optional[int] = None):
    # Buscar Aperturas en rango
    query = db.query(models.MovimientosCaja).filter(
        models.MovimientosCaja.tipo == models.TipoMovimientoCaja.APERTURA,
        models.MovimientosCaja.fecha >= fecha_inicio,
        models.MovimientosCaja.fecha <= fecha_fin
    )
    if sucursal_id:
        query = query.filter(models.MovimientosCaja.id_sucursal == sucursal_id)
    if usuario_id:
        query = query.filter(models.MovimientosCaja.id_usuario == usuario_id)
        
    aperturas = query.order_by(desc(models.MovimientosCaja.fecha)).all()
    
    reporte = []
    for ape in aperturas:
        # Buscar Cierre correspondiente (el siguiente cierre de esa sucursal despues de ape.fecha)
        # O asumir que el periodo es hasta el siguiente cierre.
        cierre = db.query(models.MovimientosCaja).filter(
            models.MovimientosCaja.id_sucursal == ape.id_sucursal,
            models.MovimientosCaja.tipo == models.TipoMovimientoCaja.CIERRE,
            models.MovimientosCaja.fecha > ape.fecha
        ).order_by(models.MovimientosCaja.fecha.asc()).first()
        
        fecha_fin_calculo = cierre.fecha if cierre else datetime.now() # Si no hay cierre, usar now? o marcar como ABIERTA
        
        # Calcular resumen
        resumen = calcular_resumen_periodo(db, ape.id_sucursal, ape.fecha, fecha_fin_calculo, ape.monto)
        
        # Extraer diferencia del cierre si existe
        diff = None
        monto_real = None
        if cierre:
            desc_parts = cierre.descripcion.split("Diferencia: ")
            if len(desc_parts) > 1:
                try:
                    diff = float(desc_parts[1])
                except:
                    pass
            monto_real = cierre.monto

        item = {
            **resumen,
            "id_apertura": ape.id_movimiento,
            "fecha_apertura": ape.fecha,
            "fecha_cierre": cierre.fecha if cierre else None,
            "usuario_apertura": ape.usuario.nombre,
            "usuario_cierre": cierre.usuario.nombre if cierre else None,
            "sucursal": ape.sucursal.nombre,
            "estado": "CERRADA" if cierre else "ABIERTA",
            "monto_real": monto_real,
            "diferencia": diff
        }
        reporte.append(item)
        
    return reporte

def get_movimiento(db: Session, movimiento_id: int):
    return db.query(models.MovimientosCaja).filter(models.MovimientosCaja.id_movimiento == movimiento_id).first()

def get_detalle_sesion_caja(db: Session, id_apertura: int):
    # 1 Obtener Apertura
    apertura = get_movimiento(db, id_apertura)
    if not apertura or apertura.tipo != models.TipoMovimientoCaja.APERTURA:
        return None
    
    # 2 Buscar Cierre
    cierre = db.query(models.MovimientosCaja).filter(
        models.MovimientosCaja.id_sucursal == apertura.id_sucursal,
        models.MovimientosCaja.tipo == models.TipoMovimientoCaja.CIERRE,
        models.MovimientosCaja.fecha > apertura.fecha
    ).order_by(models.MovimientosCaja.fecha.asc()).first()
    
    fecha_fin = cierre.fecha if cierre else datetime.now()
    
    # 3 Calcular Resumen Base 
    resumen = calcular_resumen_periodo(db, apertura.id_sucursal, apertura.fecha, fecha_fin, apertura.monto)
    
    # 4 Obtener Movimientos de Caja (Ingresos/Egresos/Apertura/Cierre)
    movs = db.query(models.MovimientosCaja).filter(
        models.MovimientosCaja.id_sucursal == apertura.id_sucursal,
        models.MovimientosCaja.fecha >= apertura.fecha,
        models.MovimientosCaja.fecha <= fecha_fin
    ).order_by(models.MovimientosCaja.fecha.asc()).all()
    
    # 5 Obtener Documentos (Ventas/Compras) del periodo
    # Optimización: Cargar detalles y productos para el reporte detallado
    docs = db.query(models.Documento).options(
        joinedload(models.Documento.usuario),
        joinedload(models.Documento.tercero),
        joinedload(models.Documento.detalles).joinedload(models.DetalleDocumento.producto).joinedload(models.Producto.inventarios)
    ).filter(
        models.Documento.id_sucursal == apertura.id_sucursal,
        models.Documento.fecha_emision >= apertura.fecha,
        models.Documento.fecha_emision <= fecha_fin,
        models.Documento.estado_pago == models.EstadoPago.PAGADO 
    ).order_by(models.Documento.fecha_emision.asc()).all()
    
    
    # 6. Obtener reporte de productos
    productos = obtener_reporte_productos(db, apertura.id_sucursal, apertura.fecha, fecha_fin)

    # 7 Construir Respuesta
    diff = None
    monto_real = None
    if cierre:
         desc_parts = cierre.descripcion.split("Diferencia: ")
         if len(desc_parts) > 1:
             try:
                 diff = float(desc_parts[1])
             except:
                 pass
         monto_real = cierre.monto

    return {
        **resumen,
        "id_apertura": apertura.id_movimiento,
        "fecha_apertura": apertura.fecha,
        "fecha_cierre": cierre.fecha if cierre else None,
        "usuario_apertura": apertura.usuario.nombre,
        "usuario_cierre": cierre.usuario.nombre if cierre else None,
        "sucursal": apertura.sucursal.nombre,
        "estado": "CERRADA" if cierre else "ABIERTA",
        "monto_real": monto_real,
        "diferencia": diff,
        "movimientos": movs,
        "documentos_summary": docs,
        "productos": productos
    }

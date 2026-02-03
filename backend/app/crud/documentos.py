from sqlalchemy.orm import Session
from app import models, schemas

# DOCUMENTOS

def get_documento(db: Session, documento_id: int):
    return db.query(models.Documento).filter(models.Documento.id_documento == documento_id).first()

def create_documento(db: Session, documento: schemas.DocumentoCreate):
    # Dynamic imports
    from .caja import get_ultimo_cierre_o_apertura, registrar_movimiento_caja
    from .inventarios import get_inventario_by_sucursal_producto
    from .productos import get_producto
    
    # Validar Folio (usar el enviado o generar uno)
    folio = documento.folio
    if not folio:
        import time
        folio = f"{documento.tipo_documento.value[0]}-{int(time.time())}"
    
    db_documento = models.Documento(
        id_sucursal=documento.id_sucursal,
        id_tercero=documento.id_tercero,
        id_usuario=documento.id_usuario,
        tipo_operacion=documento.tipo_operacion,
        tipo_documento=documento.tipo_documento,
        folio=folio,
        estado_pago=documento.estado_pago,
        observaciones=documento.observaciones
    )
    db.add(db_documento)
    db.flush() 
    
    # Validar Caja Abierta
    ultimo_caja = get_ultimo_cierre_o_apertura(db, documento.id_sucursal)
    if not ultimo_caja or ultimo_caja.tipo == models.TipoMovimientoCaja.CIERRE:
         db.rollback()
         return {"error": "La caja está cerrada. Debe abrir caja antes de operar."}

    # Procesar detalles y calcular total
    total_doc = 0
    
    for detalle in documento.detalles:
        # Verificar Inventario
        inventario = get_inventario_by_sucursal_producto(db, documento.id_sucursal, detalle.id_producto)
        
        # Obtener precio del producto si no se envió
        producto_info = get_producto(db, detalle.id_producto)
        if not producto_info:
             db.rollback()
             return {"error": f"Producto ID {detalle.id_producto} no encontrado"}

        precio_final = detalle.precio_unitario
        if precio_final is None:
            precio_final = producto_info.precio_venta

        # Calcular subtotal para el total del documento
        # (precio * cantidad) * (1 - descuento/100)
        factor_desc = (100 - detalle.descuento) / 100
        total_doc += float(precio_final * detalle.cantidad) * float(factor_desc)

        # Verificar Inventario
        inventario = get_inventario_by_sucursal_producto(
            db, 
            documento.id_sucursal, 
            detalle.id_producto,
            ubicacion=detalle.ubicacion_especifica
        )

        if documento.tipo_operacion == models.TipoOperacion.VENTA:
            # VENTA: Descontar Stock
            # Validar stock suficiente
            if not inventario or inventario.cantidad < detalle.cantidad:
                db.rollback()
                ubicacion_msg = f" en {detalle.ubicacion_especifica}" if detalle.ubicacion_especifica else ""
                raise ValueError(f"Stock insuficiente para el producto {detalle.id_producto}{ubicacion_msg}")
            
            # Descontar
            inventario.cantidad -= detalle.cantidad
            db.add(inventario)
        # Logica para COMPRA
        elif documento.tipo_operacion == models.TipoOperacion.COMPRA:
            if not inventario:
                # Si no existe inventario, crearlo
                inventario = models.Inventario(
                    id_sucursal=documento.id_sucursal,
                    id_producto=detalle.id_producto,
                    cantidad=0,
                    ubicacion_especifica="Bodega General" 
                )
                db.add(inventario)
                db.flush()
            
            # Aumentar stock
            inventario.cantidad += detalle.cantidad
            
        # Crear detalle
        db_detalle = models.DetalleDocumento(
            id_documento=db_documento.id_documento,
            id_producto=detalle.id_producto,
            cantidad=detalle.cantidad,
            precio_unitario=precio_final,
            descuento=detalle.descuento
        )
        db.add(db_detalle)
        
    db.commit()
    db.refresh(db_documento)
    
    # --- REGISTRAR MOVIMIENTO DE CAJA ---
    # Si es VENTA -> INGRESO. Si es COMPRA -> EGRESO.
    tipo_mov = models.TipoMovimientoCaja.INGRESO if documento.tipo_operacion == models.TipoOperacion.VENTA else models.TipoMovimientoCaja.EGRESO
    
    # Crear esquema para el movimiento
    mov_caja = schemas.MovimientoCajaCreate(
        id_sucursal=documento.id_sucursal,
        id_usuario=documento.id_usuario,
        tipo=tipo_mov,
        monto=total_doc,
        descripcion=f"Movimiento por Doc {db_documento.folio} ({documento.tipo_documento.value})",
        id_documento_asociado=db_documento.id_documento
    )
    

    res_caja = registrar_movimiento_caja(db, mov_caja)
    
    if isinstance(res_caja, dict) and "error" in res_caja:
 
        pass

    return db_documento

def anular_documento(db: Session, documento_id: int):
    # Dynamic import
    from .inventarios import get_inventario_by_sucursal_producto

    documento = get_documento(db, documento_id)
    if not documento:
        return None
    
    if documento.estado_pago == models.EstadoPago.ANULADO:
        return documento # Ya anulado
        
    # Revertir Stock
    for detalle in documento.detalles:
        inventario = get_inventario_by_sucursal_producto(db, documento.id_sucursal, detalle.id_producto)
        if inventario:
            if documento.tipo_operacion == models.TipoOperacion.VENTA:
                # Devolver stock
                inventario.cantidad += detalle.cantidad
            elif documento.tipo_operacion == models.TipoOperacion.COMPRA:
                # Restar stock (corrección)
                # OJO: Podría quedar negativo si ya se vendió, pero asumimos corrección contable
                inventario.cantidad -= detalle.cantidad
    
    documento.estado_pago = models.EstadoPago.ANULADO
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento

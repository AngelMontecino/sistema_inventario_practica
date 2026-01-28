from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from datetime import datetime   
from app import models, schemas, security


# SUCURSAL


def get_sucursal(db: Session, sucursal_id: int):
    return db.query(models.Sucursal).filter(models.Sucursal.id_sucursal == sucursal_id).first()

def get_sucursal_by_nombre(db: Session, nombre: str):
    return db.query(models.Sucursal).filter(models.Sucursal.nombre == nombre).first()

def get_sucursal_by_direccion(db: Session, direccion: str):
    if not direccion: return None
    return db.query(models.Sucursal).filter(models.Sucursal.direccion == direccion).first()

def get_sucursal_by_telefono(db: Session, telefono: str):
    if not telefono: return None
    return db.query(models.Sucursal).filter(models.Sucursal.telefono == telefono).first()



def get_sucursales(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sucursal).offset(skip).limit(limit).all()

def create_sucursal(db: Session, sucursal: schemas.SucursalCreate):
    db_sucursal = models.Sucursal(**sucursal.model_dump())
    db.add(db_sucursal)
    db.commit()
    db.refresh(db_sucursal)
    return db_sucursal

def update_sucursal(db: Session, sucursal_id: int, sucursal_update: schemas.SucursalUpdate):
    db_sucursal = get_sucursal(db, sucursal_id)
    if not db_sucursal:
        return None
    
    update_data = sucursal_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sucursal, key, value)
    
    db.add(db_sucursal)
    db.commit()
    db.refresh(db_sucursal)
    return db_sucursal

def set_sucursal_principal(db: Session, sucursal_id: int):
    #  Buscar la sucursal que queremos hacer principal
    db_sucursal = get_sucursal(db, sucursal_id)
    if not db_sucursal:
        return None
    
    #  Desmarcar cualquier otra sucursal que sea principal actualmente
    #    (Podría haber solo una, o ninguna)
    db.query(models.Sucursal).filter(models.Sucursal.es_principal == True).update({"es_principal": False})
    
    # Marcar la seleccionada como principal
    db_sucursal.es_principal = True
    db.add(db_sucursal)
    db.commit()
    db.refresh(db_sucursal)
    return db_sucursal


# USUARIO

def get_usuario(db: Session, usuario_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id_usuario == usuario_id).first()

def get_usuario_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def get_usuarios(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    id_sucursal: int = None
):
    query = db.query(models.Usuario)
    if id_sucursal:
        query = query.filter(models.Usuario.id_sucursal == id_sucursal)
    return query.offset(skip).limit(limit).all()

def create_usuario(db: Session, usuario: schemas.UsuarioCreate):
    # Implementación de hashing de password
    hashed_password = security.get_password_hash(usuario.password)
    db_usuario = models.Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        password=hashed_password,
        id_sucursal=usuario.id_sucursal,
        rol=usuario.rol,
        estado=usuario.estado
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def update_usuario(db: Session, usuario_id: int, usuario_update: schemas.UsuarioUpdate):
    db_usuario = get_usuario(db, usuario_id)
    if not db_usuario:
        return None
    
    update_data = usuario_update.model_dump(exclude_unset=True)
    
    # Si se actualiza el password, hay que hashearlo
    if "password" in update_data:
        update_data["password"] = security.get_password_hash(update_data["password"])
        
    for key, value in update_data.items():
        setattr(db_usuario, key, value)
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario



# CATEGORIA


def get_categorias(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Categoria).offset(skip).limit(limit).all()

def get_categoria(db: Session, categoria_id: int):
    return db.query(models.Categoria).filter(models.Categoria.id_categoria == categoria_id).first()

def get_categorias_arbol(db: Session):

    return db.query(models.Categoria).filter(models.Categoria.id_padre == None).all()

def get_subcategorias(db: Session, categoria_id: int):
    return db.query(models.Categoria).filter(models.Categoria.id_padre == categoria_id).all()

def _tiene_productos_recursivo(categoria: models.Categoria) -> bool:
    # Verificar si la categoría actual tiene productos
    if categoria.productos:
        return True
    
    # Verificar recursivamente en las hijas
    for hija in categoria.hijas:
        if _tiene_productos_recursivo(hija):
            return True
            
    return False

def delete_categoria(db: Session, categoria_id: int):
    categoria = db.query(models.Categoria).filter(models.Categoria.id_categoria == categoria_id).first()
    if not categoria:
        return None
    
    # Verificar recursivamente si tiene productos en toda la rama
    if _tiene_productos_recursivo(categoria):
        return False # Indica que no se puede borrar por integridad
        
    db.delete(categoria)
    db.commit()
    return True

def create_categoria(db: Session, categoria: schemas.CategoriaCreate):
    # Convertir 0 a None para evitar error de FK si el frontend envía 0
    cat_data = categoria.model_dump()
    if cat_data.get("id_padre") == 0:
        cat_data["id_padre"] = None
        
    db_categoria = models.Categoria(**cat_data)
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria



# PRODUCTO


def get_producto(db: Session, producto_id: int):
    return db.query(models.Producto).filter(models.Producto.id_producto == producto_id).first()

def get_productos(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    busqueda: str = None, 
    id_categoria: int = None,
    unidad_medida: str = None,
    precio_min: float = None,
    precio_max: float = None
):
    query = db.query(models.Producto).options(joinedload(models.Producto.categoria))
    
    if id_categoria:
        query = query.filter(models.Producto.id_categoria == id_categoria)
        
    if unidad_medida:
        query = query.filter(models.Producto.unidad_medida == unidad_medida)
        
    if precio_min is not None:
        query = query.filter(models.Producto.precio_venta >= precio_min)
        
    if precio_max is not None:
        query = query.filter(models.Producto.precio_venta <= precio_max)

    if busqueda:
        # Búsqueda insensible a mayúsculas por nombre o código de barras, e ID
        filtros_busqueda = [
            models.Producto.nombre.ilike(f"%{busqueda}%"),
            models.Producto.codigo_barras.ilike(f"%{busqueda}%")
        ]
        
        # Si es numérico, intentar buscar por ID exacto
        if busqueda.isdigit():
            filtros_busqueda.append(models.Producto.id_producto == int(busqueda))
            
        from sqlalchemy import or_
        query = query.filter(or_(*filtros_busqueda))
        
    return query.offset(skip).limit(limit).all()

def get_producto_by_codigo(db: Session, codigo: str):
    return db.query(models.Producto).filter(models.Producto.codigo_barras == codigo).first()

def update_producto(db: Session, producto_id: int, producto_update: schemas.ProductoUpdate):
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        return None
    
    update_data = producto_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_producto, key, value)
    
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def create_producto(db: Session, producto: schemas.ProductoCreate):
    # Validar código de barras si existe
    if producto.codigo_barras:
        existe = get_producto_by_codigo(db, producto.codigo_barras)
        if existe:
            return None 

    db_producto = models.Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    db.refresh(db_producto)
    return db_producto

def delete_producto(db: Session, producto_id: int):
    producto = get_producto(db, producto_id)
    if not producto:
        return None 
        
    # Validar historial
    usos = db.query(models.DetalleDocumento).filter(models.DetalleDocumento.id_producto == producto_id).count()
    if usos > 0:
        return "ConHistorial" 
        
    # Validar stock físico
    stock_total = db.query(func.sum(models.Inventario.cantidad)).filter(models.Inventario.id_producto == producto_id).scalar()
    if stock_total and stock_total > 0:
        return "ConStock"
        
    # Borrar inventarios vacíos (si existen)
    db.query(models.Inventario).filter(models.Inventario.id_producto == producto_id).delete()
    
    db.delete(producto)
    db.commit()
    return True


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
        # Búsqueda por nombre
        query = query.filter(models.ClienteProveedor.nombre.ilike(f"%{busqueda}%"))
        
    
    return query.offset(skip).limit(limit).all()

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


# INVENTARIO

def get_inventario(db: Session, inventario_id: int):
    return db.query(models.Inventario).filter(models.Inventario.id_inventario == inventario_id).first()

def get_inventario_by_sucursal_producto(db: Session, sucursal_id: int, producto_id: int, ubicacion: str = None):
    query = db.query(models.Inventario).filter(
        models.Inventario.id_sucursal == sucursal_id,
        models.Inventario.id_producto == producto_id
    )
    if ubicacion:
        query = query.filter(models.Inventario.ubicacion_especifica == ubicacion)
    return query.first()

def get_inventarios(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    sucursal_id: int = None, 
    producto_id: int = None,
    alerta_stock: bool = False
):
    query = db.query(models.Inventario).options(joinedload(models.Inventario.producto))
    
    if sucursal_id:
        query = query.filter(models.Inventario.id_sucursal == sucursal_id)

    if producto_id:
        query = query.filter(models.Inventario.id_producto == producto_id)
        
    if alerta_stock:
        # Stock crítico: cantidad <= stock_minimo
        query = query.filter(models.Inventario.cantidad <= models.Inventario.stock_minimo)
        
    return query.offset(skip).limit(limit).all()

def create_inventario(db: Session, inventario: schemas.InventarioCreate):
    # Verificar si ya existe relación sucursal-producto-ubicacion
    existe = get_inventario_by_sucursal_producto(
        db, 
        inventario.id_sucursal, 
        inventario.id_producto, 
        ubicacion=inventario.ubicacion_especifica
    )
    if existe:
        return None # Ya existe en esa ubicación
        
    db_inventario = models.Inventario(**inventario.model_dump())
    db.add(db_inventario)
    db.commit()
    db.refresh(db_inventario)
    return db_inventario

def update_inventario(db: Session, inventario_id: int, inventario_update: schemas.InventarioUpdate):
    db_inventario = get_inventario(db, inventario_id)
    if not db_inventario:
        return None
        
    update_data = inventario_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_inventario, key, value)
        
    db.add(db_inventario)
    db.commit()
    db.refresh(db_inventario)
    return db_inventario

def delete_inventario(db: Session, inventario_id: int):
    inv = get_inventario(db, inventario_id)
    if not inv:
        return None # Not found
    
    if inv.cantidad > 0:
        return False # No eliminar con stock
        
    db.delete(inv)
    db.commit()
    return True

def get_inventario_agrupado(db: Session, sucursal_id: int, busqueda: str = None):
    # Base query
    query = db.query(
        models.Inventario.id_producto,
        models.Producto.nombre,
        models.Producto.codigo_barras,
        func.sum(models.Inventario.cantidad).label("total_cantidad")
    ).join(models.Producto)\
     .filter(models.Inventario.id_sucursal == sucursal_id)

    if busqueda:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                models.Producto.nombre.ilike(f"%{busqueda}%"),
                models.Producto.codigo_barras.ilike(f"%{busqueda}%")
            )
        )

    # Agrupar por producto y sumar cantidad
    stats = query.group_by(models.Inventario.id_producto, models.Producto.nombre, models.Producto.codigo_barras)\
     .all()
    
    # Formatear
    resultado = []
    for row in stats:
        resultado.append({
            "id_producto": row.id_producto,
            "nombre": row.nombre,
            "codigo_barras": row.codigo_barras,
            "total_cantidad": row.total_cantidad
        })
    return resultado


# DOCUMENTOS

def get_documento(db: Session, documento_id: int):
    return db.query(models.Documento).filter(models.Documento.id_documento == documento_id).first()

def create_documento(db: Session, documento: schemas.DocumentoCreate):
    # Generar folio simple basado en timestamp para las pruebas
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

    # Procesar detalles y stock
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

        # Logica para VENTA
        if documento.tipo_operacion == models.TipoOperacion.VENTA:
            if not inventario or inventario.cantidad < detalle.cantidad:
                db.rollback()
                return {"error": f"Stock insuficiente para producto ID {detalle.id_producto}"}
            
            # Descontar stock
            inventario.cantidad -= detalle.cantidad
            
        # Logica para COMPRA
        elif documento.tipo_operacion == models.TipoOperacion.COMPRA:
            if not inventario:
                # Si no existe inventario, crearlo (para pruebas)
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
    return db_documento

def anular_documento(db: Session, documento_id: int):
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
        pass
        
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

def registrar_movimiento_caja(db: Session, movimiento: schemas.MovimientoCajaCreate):
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
            "saldo_teorico": 0
        }
    
    # Calcular hasta AHORA
    return calcular_resumen_periodo(db, sucursal_id, ultimo.fecha, datetime.now(), ultimo.monto)

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

    return {
        **resumen,
        "monto_real": monto_real,
        "diferencia": float(monto_real) - float(resumen['saldo_teorico'])
    }


def calcular_resumen_periodo(db: Session, sucursal_id: int, fecha_inicio: datetime, fecha_fin: datetime, saldo_inicial: float):
    #  Sumar Ventas (Ingresos)
    ventas = db.query(func.sum(models.DetalleDocumento.cantidad * models.DetalleDocumento.precio_unitario - models.DetalleDocumento.descuento))\
        .join(models.Documento)\
        .filter(
            models.Documento.id_sucursal == sucursal_id,
            models.Documento.fecha_emision >= fecha_inicio,
            models.Documento.fecha_emision <= fecha_fin, # Added fecha_fin check
            models.Documento.tipo_operacion == models.TipoOperacion.VENTA,
            models.Documento.estado_pago == models.EstadoPago.PAGADO
        ).scalar() or 0
        
    # Sumar Compras (Egresos)
    compras = db.query(func.sum(models.DetalleDocumento.cantidad * models.DetalleDocumento.precio_unitario - models.DetalleDocumento.descuento))\
        .join(models.Documento)\
        .filter(
            models.Documento.id_sucursal == sucursal_id,
            models.Documento.fecha_emision >= fecha_inicio,
            models.Documento.fecha_emision <= fecha_fin,
            models.Documento.tipo_operacion == models.TipoOperacion.COMPRA,
            models.Documento.estado_pago == models.EstadoPago.PAGADO
        ).scalar() or 0
        
    # Sumar Movimientos Extra
    ingresos_extra = db.query(func.sum(models.MovimientosCaja.monto))\
        .filter(
            models.MovimientosCaja.id_sucursal == sucursal_id,
            models.MovimientosCaja.fecha >= fecha_inicio,
            models.MovimientosCaja.fecha <= fecha_fin,
            models.MovimientosCaja.tipo == models.TipoMovimientoCaja.INGRESO
        ).scalar() or 0
        
    egresos_extra = db.query(func.sum(models.MovimientosCaja.monto))\
        .filter(
            models.MovimientosCaja.id_sucursal == sucursal_id,
            models.MovimientosCaja.fecha >= fecha_inicio,
            models.MovimientosCaja.fecha <= fecha_fin,
            models.MovimientosCaja.tipo == models.TipoMovimientoCaja.EGRESO
        ).scalar() or 0
        
    saldo_teorico = saldo_inicial + ventas + ingresos_extra - compras - egresos_extra
    
    return {
        "saldo_inicial": saldo_inicial,
        "ingresos_ventas": ventas,
        "egresos_compras": compras,
        "ingresos_extra": ingresos_extra,
        "egresos_extra": egresos_extra,
        "saldo_teorico": saldo_teorico
    }

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

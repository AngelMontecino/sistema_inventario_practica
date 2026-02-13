from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app import models

def get_dashboard_stats(db: Session, sucursal_id: Optional[int] = None):
    #  Ventas del día 
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    q_ventas = db.query(func.sum(models.DetalleDocumento.cantidad * models.DetalleDocumento.precio_unitario * (1 - models.DetalleDocumento.descuento / 100)))\
        .join(models.Documento)\
        .filter(
            models.Documento.fecha_emision >= hoy_inicio,
            models.Documento.fecha_emision <= hoy_fin,
            models.Documento.tipo_operacion == models.TipoOperacion.VENTA,
            models.Documento.estado_pago == models.EstadoPago.PAGADO
        )
        
    if sucursal_id:
        q_ventas = q_ventas.filter(models.Documento.id_sucursal == sucursal_id)
        
    ventas_dia = q_ventas.scalar() or 0

    #  Total Productos 
    # Contar productos UNICOS (DISTINCT) con stock positivo
    q_prods = db.query(func.count(models.Inventario.id_producto.distinct()))\
        .filter(models.Inventario.cantidad > 0)
        
    if sucursal_id:
        q_prods = q_prods.filter(models.Inventario.id_sucursal == sucursal_id)
        
    total_productos = q_prods.scalar() or 0
    
    #  Alertas de Stock 
    q_alertas = db.query(models.Inventario, models.Producto, models.Sucursal)\
        .join(models.Producto, models.Inventario.id_producto == models.Producto.id_producto)\
        .join(models.Sucursal, models.Inventario.id_sucursal == models.Sucursal.id_sucursal)\
        .filter(
            models.Inventario.cantidad <= models.Inventario.stock_minimo
        )
        
    if sucursal_id:
        q_alertas = q_alertas.filter(models.Inventario.id_sucursal == sucursal_id)
        
    alertas = q_alertas.all()
        
    # Formatear alertas
    lista_alertas = []
    for inv, prod, suc in alertas:
        lista_alertas.append({
            "id_producto": prod.id_producto,
            "id_inventario": inv.id_inventario,
            "nombre": prod.nombre,
            "cantidad": inv.cantidad,
            "stock_minimo": inv.stock_minimo,
            "ubicacion": inv.ubicacion_especifica,
            "sucursal_nombre": suc.nombre 
        })
        
    return {
        "ventas_dia": int(ventas_dia), 
        "total_productos": total_productos,
        "alertas_stock": lista_alertas
    }

from datetime import timedelta

def get_dashboard_charts(db: Session, sucursal_id: Optional[int] = None):
    #  Ventas últimos 7 días 
    hoy = datetime.now()
    fecha_inicio = hoy - timedelta(days=6) # 7 días incluyendo hoy
    
    # Agrupar por fecha (solo dia/mes)
    
    q_ventas_sem = db.query(
        func.date(models.Documento.fecha_emision).label("fecha"), 
        func.sum(models.DetalleDocumento.cantidad * models.DetalleDocumento.precio_unitario * (1 - models.DetalleDocumento.descuento / 100)).label("total")
    ).join(models.DetalleDocumento).filter(
        models.Documento.fecha_emision >= fecha_inicio,
        models.Documento.tipo_operacion == models.TipoOperacion.VENTA,
        models.Documento.estado_pago == models.EstadoPago.PAGADO
    )
    
    if sucursal_id:
        q_ventas_sem = q_ventas_sem.filter(models.Documento.id_sucursal == sucursal_id)
        
    ventas_sem = q_ventas_sem.group_by("fecha").all()
    
    # Rellenar días vacíos
    datos_semana = []
    # Map para acceso rápido
    ventas_map = {str(v.fecha): float(v.total or 0) for v in ventas_sem}
    
    for i in range(7):
        d = fecha_inicio + timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        datos_semana.append({
            "fecha": d.strftime("%d/%m"), # Formato corto para gráfico
            "total": int(ventas_map.get(d_str, 0))
        })

    #  Ventas por Categoría (Top 5) 
    q_cat = db.query(
        models.Categoria.nombre,
        func.sum(models.DetalleDocumento.cantidad * models.DetalleDocumento.precio_unitario * (1 - models.DetalleDocumento.descuento / 100)).label("total")
    ).join(models.Producto, models.DetalleDocumento.id_producto == models.Producto.id_producto)\
     .join(models.Categoria, models.Producto.id_categoria == models.Categoria.id_categoria)\
     .join(models.Documento, models.DetalleDocumento.id_documento == models.Documento.id_documento)\
     .filter(
        models.Documento.tipo_operacion == models.TipoOperacion.VENTA,
        models.Documento.estado_pago == models.EstadoPago.PAGADO
    )
    
    if sucursal_id:
        q_cat = q_cat.filter(models.Documento.id_sucursal == sucursal_id)
        
    top_categorias = q_cat.group_by(models.Categoria.nombre).order_by(func.sum(models.DetalleDocumento.cantidad * models.DetalleDocumento.precio_unitario).desc()).limit(5).all()
    
    datos_categoria = [{"categoria": c.nombre, "total": int(c.total or 0)} for c in top_categorias]

    return {
        "ventas_semanales": datos_semana,
        "ventas_por_categoria": datos_categoria
    }

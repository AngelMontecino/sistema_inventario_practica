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

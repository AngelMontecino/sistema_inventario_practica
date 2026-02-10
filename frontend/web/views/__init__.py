from .auth import login_view, logout_view
from .productos import (
    lista_productos, crear_producto, crear_categoria, editar_producto, 
    asignar_inventario, lista_inventario, detalle_inventario, editar_inventario
)
from .config import (
    lista_sucursales, crear_sucursal, editar_sucursal, 
    lista_usuarios, crear_usuario, editar_usuario
)
from .terceros import lista_terceros, crear_tercero, editar_tercero, api_buscar_terceros
from .documentos import crear_documento, api_buscar_productos, api_ver_stock
from .caja import gestion_caja, abrir_caja, cerrar_caja, registrar_movimiento, ver_reportes, detalle_sesion

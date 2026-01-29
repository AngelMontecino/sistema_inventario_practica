from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Redirigir raíz a login (o home si logueado, controlado en view)
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Productos
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo', views.crear_producto, name='crear_producto'),
    path('productos/categorias/nueva', views.crear_categoria, name='crear_categoria'),
    path('productos/editar/<int:pk>', views.editar_producto, name='editar_producto'),
    
    # Inventario
    path('inventario/', views.lista_inventario, name='lista_inventario'),
    path('inventario/asignar/<int:pk>', views.asignar_inventario, name='asignar_inventario'), # Moved from productos scope logically
    path('inventario/detalle/<int:pk>', views.detalle_inventario, name='detalle_inventario'),
    path('inventario/editar/<int:pk>', views.editar_inventario, name='editar_inventario'),
    
    # Sucursales
    path('sucursales/', views.lista_sucursales, name='lista_sucursales'),
    path('sucursales/nueva', views.crear_sucursal, name='crear_sucursal'),
    path('sucursales/editar/<int:pk>', views.editar_sucursal, name='editar_sucursal'),
    
    # Usuarios
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/nuevo', views.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:pk>', views.editar_usuario, name='editar_usuario'),

    # Terceros
    path('terceros/', views.lista_terceros, name='lista_terceros'),
    path('terceros/nuevo', views.crear_tercero, name='crear_tercero'),
    path('terceros/editar/<int:pk>', views.editar_tercero, name='editar_tercero'),

    # Documentos
    path('documentos/nuevo', views.crear_documento, name='crear_documento'),
    
    # Caja (NUEVO)
    path('caja/', views.gestion_caja, name='gestion_caja'),
    path('caja/apertura', views.abrir_caja, name='abrir_caja'),
    path('caja/cierre', views.cerrar_caja, name='cerrar_caja'),

    # API Proxies
    path('api/productos/buscar', views.api_buscar_productos, name='api_buscar_productos'),
    path('api/stock/consultar', views.api_ver_stock, name='api_ver_stock'),
]

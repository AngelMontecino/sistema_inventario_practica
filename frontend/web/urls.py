from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Redirigir raíz a login
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo', views.crear_producto, name='crear_producto'),
    path('productos/categorias/nueva', views.crear_categoria, name='crear_categoria'),
    path('productos/editar/<int:pk>', views.editar_producto, name='editar_producto'),
    path('productos/asignar/<int:pk>', views.asignar_inventario, name='asignar_inventario'),
    path('sucursales/', views.lista_sucursales, name='lista_sucursales'),
    path('sucursales/nueva', views.crear_sucursal, name='crear_sucursal'),
    path('sucursales/editar/<int:pk>', views.editar_sucursal, name='editar_sucursal'),
    path('inventario/', views.lista_inventario, name='lista_inventario'),
    path('inventario/detalle/<int:pk>', views.detalle_inventario, name='detalle_inventario'),
    path('inventario/editar/<int:pk>', views.editar_inventario, name='editar_inventario'),
]

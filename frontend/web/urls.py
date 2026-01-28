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
]

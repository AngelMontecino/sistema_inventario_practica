from django.shortcuts import redirect
from functools import wraps

def token_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('access_token'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
def admin_required(view_func):
    """
    Decorador para restringir el acceso solo a administradores.

    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1 Verificar autenticación básica (token)
        if not request.session.get('access_token'):
            return redirect('login')
            
        # 2 Verificar Rol
        if request.session.get('rol') != 'ADMIN':
            # Redirigir a lista_productos con error
            from django.urls import reverse
            import urllib.parse
            
            base_url = reverse('lista_productos')
            params = urllib.parse.urlencode({'error': 'Acceso no autorizado'})
            return redirect(f"{base_url}?{params}")
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

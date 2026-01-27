from django.shortcuts import render, redirect
import httpx
from .decorators import token_required

# Configuración del Backend (FastAPI)
BACKEND_URL = "http://127.0.0.1:8001"

def login_view(request):
    # Si ya tiene sesión, redirigir directo
    if request.session.get("access_token"):
         return redirect("lista_productos")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        try:
            # Enviar credenciales a FastAPI 
            response = httpx.post(f"{BACKEND_URL}/token", data={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                # Login exitoso
                data = response.json()
                access_token = data.get("access_token")
                
                # Guardar token en sesion
                request.session["access_token"] = access_token
                
                # Redirigir al inicio o lista de productos
                return redirect("lista_productos") 
            else:
                # Login fallido
                error_msg = "Credenciales inválidas"
                return render(request, "login.html", {"error": error_msg})
                
        except httpx.RequestError as exc:
            return render(request, "login.html", {"error": f"Error de conexión con el servidor: {exc}"})

    return render(request, "login.html")

def logout_view(request):
    request.session.flush() # Limpiar toda la data de sesión
    return redirect("login")

@token_required
def lista_productos(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    productos = []
    error = None

    try:
        response = httpx.get(f"{BACKEND_URL}/productos/", headers=headers)
        
        if response.status_code == 200:
            productos = response.json()
        elif response.status_code == 401:
            # Token expirado o inválido
            request.session.flush()
            return redirect("login")
        else:
            error = f"Error al obtener productos: {response.text}"
            
    except httpx.RequestError as exc:
         error = f"Error de conexión con API: {exc}"

    return render(request, "productos.html", {"productos": productos, "error": error})
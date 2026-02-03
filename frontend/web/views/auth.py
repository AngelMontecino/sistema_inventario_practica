from django.shortcuts import render, redirect
import httpx
from django.conf import settings


from django.conf import settings

BACKEND_URL = settings.BACKEND_URL

def login_view(request):
    # Si ya tiene sesión, redirigir directo
    if request.session.get("access_token"):
         return redirect("home")

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
                
                # Guardar token y datos de usuario en sesion
                request.session["access_token"] = access_token
                request.session["rol"] = data.get("rol")
                request.session["nombre"] = data.get("nombre")
                request.session["id_sucursal"] = data.get("id_sucursal")
                
                # Redirigir al inicio o lista de productos
                return redirect("home") 
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

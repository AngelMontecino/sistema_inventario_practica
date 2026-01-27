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

@token_required
def crear_producto(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    categorias = []
    error = None

    # Lógica POST: Crear producto
    if request.method == "POST":
        try:
            # Preparar payload
            payload = {
                "nombre": request.POST.get("nombre"),
                "codigo_barras": request.POST.get("codigo_barras") or None,
                "precio_venta": float(request.POST.get("precio_venta", 0)),
                "costo_neto": float(request.POST.get("costo_neto", 0)),
                "unidad_medida": request.POST.get("unidad_medida"),
                "id_categoria": int(request.POST.get("id_categoria")) if request.POST.get("id_categoria") else None,
                "descripcion": request.POST.get("descripcion") or None,
            }

            response = httpx.post(f"{BACKEND_URL}/productos/", json=payload, headers=headers)
            
            if response.status_code == 201:
                return redirect("lista_productos")
            elif response.status_code == 401:
                request.session.flush()
                return redirect("login")
            else:
                try:
                    error = response.json().get("detail", "Error desconocido")
                except:
                    error = response.text

        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"
        except ValueError as exc:
            error = f"Error en datos numéricos: {exc}"

    # Lógica GET : Obtener categorías
    try:
        cat_resp = httpx.get(f"{BACKEND_URL}/productos/categorias/", headers=headers)
        if cat_resp.status_code == 200:
            raw_cats = cat_resp.json()
            # Aplanar categorías para el select
            categorias = _aplanar_categorias(raw_cats)
    except httpx.RequestError:
        pass 

    return render(request, "crear_producto.html", {"categorias": categorias, "error": error})

@token_required
def crear_categoria(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    categorias = []
    error = None

    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            id_padre_str = request.POST.get("id_padre")
            id_padre = int(id_padre_str) if id_padre_str else None
            
            payload = {
                "nombre": nombre,
                "id_padre": id_padre
            }

            response = httpx.post(f"{BACKEND_URL}/productos/categorias/", json=payload, headers=headers)
            
            if response.status_code == 201:
                return redirect("lista_productos") 
            elif response.status_code == 401:
                request.session.flush()
                return redirect("login")
            else:
                try:
                    error = response.json().get("detail", "Error desconocido")
                except:
                    error = response.text

        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    # Logica GET: Obtener categorías para el select 
    try:
        cat_resp = httpx.get(f"{BACKEND_URL}/productos/categorias/", headers=headers)
        if cat_resp.status_code == 200:
            raw_cats = cat_resp.json()
            categorias = _aplanar_categorias(raw_cats)
    except httpx.RequestError:
        pass

    return render(request, "crear_categoria.html", {"categorias": categorias, "error": error})

def _aplanar_categorias(categorias_raw, nivel=0):
    """Función recursiva para aplanar el árbol de categorías."""
    lista_plana = []
    for cat in categorias_raw:
        # Crear copia modificada para visualización
        cat_view = {
            "id_categoria": cat["id_categoria"],
            "nombre": ("— " * nivel) + cat["nombre"]
        }
        lista_plana.append(cat_view)
        
        # Procesar hijas si existen
        if cat.get("hijas"):
            lista_plana.extend(_aplanar_categorias(cat["hijas"], nivel + 1))
            
    return lista_plana 

    return render(request, "crear_producto.html", {"categorias": categorias, "error": error})
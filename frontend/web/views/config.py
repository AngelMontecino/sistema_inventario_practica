from django.shortcuts import render, redirect
import httpx
from ..decorators import token_required, admin_required

BACKEND_URL = "http://127.0.0.1:8001"

# --- SUCURSALES ---

@token_required
def lista_sucursales(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    sucursales = []
    error = None

    try:
        response = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
        if response.status_code == 200:
            sucursales = response.json()
        elif response.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
            error = f"Error al cargar sucursales: {response.text}"
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "sucursales.html", {"sucursales": sucursales, "error": error})

@token_required
def crear_sucursal(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    error = None

    if request.method == "POST":
        try:
            payload = {
                "nombre": request.POST.get("nombre"),
                "direccion": request.POST.get("direccion") or None,
                "telefono": request.POST.get("telefono") or None,
                "es_principal": True if request.POST.get("es_principal") else False
            }
            response = httpx.post(f"{BACKEND_URL}/sucursales/", json=payload, headers=headers)
            if response.status_code == 201:
                return redirect("lista_sucursales")
            elif response.status_code == 401:
                request.session.flush()
                return redirect("login")
            else:
                try:
                    error = response.json().get("detail", "Error al crear sucursal")
                except:
                    error = response.text
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    return render(request, "crear_sucursal.html", {"error": error})

@token_required
def editar_sucursal(request, pk):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    sucursal = {}
    error = None

    if request.method == "POST":
        try:
            payload = {
                "nombre": request.POST.get("nombre"),
                "direccion": request.POST.get("direccion") or None,
                "telefono": request.POST.get("telefono") or None,
            }
            response = httpx.put(f"{BACKEND_URL}/sucursales/{pk}", json=payload, headers=headers)
            if response.status_code == 200:
                if request.POST.get("es_principal"):
                    try:
                        resp_principal = httpx.put(f"{BACKEND_URL}/sucursales/{pk}/principal", headers=headers)
                        if resp_principal.status_code != 200:
                            error = "Se actualizaron los datos pero hubo un error al establecer como principal."
                    except httpx.RequestError:
                         pass 

                if not error:
                    return redirect("lista_sucursales")
            elif response.status_code == 401:
                request.session.flush()
                return redirect("login")
            else:
                try:
                    error = response.json().get("detail", "Error al actualizar sucursal")
                except:
                    error = response.text
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    try:
        response = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
        if response.status_code == 200:
            sucursales = response.json()
            sucursal = next((s for s in sucursales if s["id_sucursal"] == pk), None)
            if not sucursal:
                 error = "Sucursal no encontrada localmente."
        elif response.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
            error = "Error al cargar datos."
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "editar_sucursal.html", {"sucursal": sucursal, "error": error})

# --- USUARIOS ---

@admin_required
def lista_usuarios(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    usuarios = []
    error = None

    try:
        response = httpx.get(f"{BACKEND_URL}/usuarios/", headers=headers)
        if response.status_code == 200:
            usuarios = response.json()
        elif response.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
             try:
                error = response.json().get("detail", "Error al cargar usuarios")
             except:
                error = response.text
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "usuarios.html", {"usuarios": usuarios, "error": error})

@admin_required
def crear_usuario(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    sucursales = []
    error = None

    if request.method == "POST":
        try:
            payload = {
                "nombre": request.POST.get("nombre"),
                "email": request.POST.get("email"),
                "password": request.POST.get("password"),
                "rol": request.POST.get("rol"),
                "id_sucursal": int(request.POST.get("id_sucursal")),
                "estado": True 
            }
            response = httpx.post(f"{BACKEND_URL}/usuarios/", json=payload, headers=headers)
            if response.status_code == 201:
                return redirect("lista_usuarios")
            elif response.status_code == 401:
                request.session.flush()
                return redirect("login")
            else:
                 try:
                    error = response.json().get("detail", "Error al crear usuario")
                 except:
                    error = response.text
        except ValueError:
            error = "Error en los datos numéricos (Sucursal)."
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    try:
        suc_resp = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
        if suc_resp.status_code == 200:
            sucursales = suc_resp.json()
    except:
        pass

    return render(request, "crear_usuario.html", {"sucursales": sucursales, "error": error})

@admin_required
def editar_usuario(request, pk):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    usuario = {}
    sucursales = []
    error = None

    if request.method == "POST":
        try:
            payload = {
                "rol": request.POST.get("rol"),
                "id_sucursal": int(request.POST.get("id_sucursal")),
                "estado": True if request.POST.get("estado") == "on" else False
            }
            response = httpx.put(f"{BACKEND_URL}/usuarios/{pk}", json=payload, headers=headers)
            if response.status_code == 200:
                return redirect("lista_usuarios")
            elif response.status_code == 401:
                request.session.flush()
                return redirect("login")
            else:
                try:
                    error = response.json().get("detail", "Error al actualizar usuario")
                except:
                    error = response.text
        except ValueError:
             error = "Error val datos."
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    try:
        suc_resp = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
        if suc_resp.status_code == 200:
            sucursales = suc_resp.json()
            
        resp_users = httpx.get(f"{BACKEND_URL}/usuarios/", headers=headers)
        if resp_users.status_code == 200:
            users_list = resp_users.json()
            usuario = next((u for u in users_list if u['id_usuario'] == pk), None)
            if not usuario:
                error = "Usuario no encontrado."
        elif resp_users.status_code == 401:
             request.session.flush()
             return redirect("login")
             
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "editar_usuario.html", {"usuario": usuario, "sucursales": sucursales, "error": error})

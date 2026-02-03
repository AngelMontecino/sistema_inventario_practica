from django.shortcuts import render, redirect
import httpx
from ..decorators import token_required

from django.conf import settings

BACKEND_URL = settings.BACKEND_URL

@token_required
def dashboard_view(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    stats = {}
    sucursales = []
    
    # Filtro
    sucursal_id_str = request.GET.get("sucursal_id", "")
    sucursal_id = int(sucursal_id_str) if sucursal_id_str else None
    
    error = None

    try:
        # Obtener Stats
        params = {}
        if sucursal_id is not None:
             params["sucursal_id"] = sucursal_id
             
        response = httpx.get(f"{BACKEND_URL}/dashboard/stats", params=params, headers=headers)
        if response.status_code == 200:
            stats = response.json()
        elif response.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
            try:
                 error = response.json().get("detail", "Error al cargar estadísticas")
            except:
                 error = "Error al cargar estadísticas"
                 
        # Obtener Sucursales (para el filtro)
        if request.session.get("rol") == "ADMIN":
             try:
                 resp_suc = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
                 if resp_suc.status_code == 200:
                     sucursales = resp_suc.json()
             except:
                 pass
                 
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "dashboard.html", {
        "stats": stats, 
        "sucursales": sucursales,
        "sucursal_seleccionada": sucursal_id,
        "error": error
    })

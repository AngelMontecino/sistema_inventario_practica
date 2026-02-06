from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import httpx
from ..decorators import token_required

from django.conf import settings

BACKEND_URL = settings.BACKEND_URL

@token_required
def crear_documento(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
  
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # Inyectar datos de sesión si faltan
            if not data.get("id_sucursal"):
                data["id_sucursal"] = request.session.get("id_sucursal")
            
            response = httpx.post(f"{BACKEND_URL}/documentos/", json=data, headers=headers)
            
            if response.status_code == 200 or response.status_code == 201:
                return JsonResponse({"status": "success", "redirect_url": "/inventario/"}) # O detalle confirmacion
            else:
                try:
                    detail = response.json().get("detail", "Error desconocido")
                except:
                    detail = response.text
                return JsonResponse({"status": "error", "message": detail}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "JSON Inválido"}, status=400)
        except httpx.RequestError as exc:
             return JsonResponse({"status": "error", "message": f"Conexión: {exc}"}, status=500)

    # GET: Cargar Interfaz
    terceros = []
    try:
        # Cargar todos los terceros para el select
        resp = httpx.get(f"{BACKEND_URL}/terceros/", headers=headers)
        if resp.status_code == 200:
            terceros = resp.json()
    except:
        pass

    return render(request, "documentos/crear.html", {
        "terceros": terceros,
        "usuario_nombre": request.session.get("nombre"),
        "sucursal_id": request.session.get("id_sucursal")
    })

@token_required
def api_buscar_productos(request):
    """Proxy para buscar productos via AJAX"""
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    q = request.GET.get("q", "")
    
    try:
        response = httpx.get(f"{BACKEND_URL}/productos/", params={"busqueda": q}, headers=headers)
        data = response.json()
        # La API ahora retorna paginación (total, items)
        items = data.get("items", []) if isinstance(data, dict) and "items" in data else data
        return JsonResponse(items, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@token_required
def api_ver_stock(request):
    """Proxy para ver stock específico"""
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = request.GET.get("id_producto")
    s_id = request.GET.get("id_sucursal")
    
    try:
        # Usamos endpoint inventarios con filtros
        params = {"sucursal_id": s_id, "producto_id": p_id}
        response = httpx.get(f"{BACKEND_URL}/inventarios/", params=params, headers=headers)
        data = response.json()
        cantidad = 0
        if data:
            # Sumar si hubiera mltiples ubicaciones
            for item in data:
                cantidad += item.get("cantidad", 0) 
        
        return JsonResponse({"stock": cantidad})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

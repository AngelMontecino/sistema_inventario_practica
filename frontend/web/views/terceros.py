from django.shortcuts import render, redirect
from django.http import JsonResponse
import httpx
from ..decorators import token_required

from django.conf import settings

BACKEND_URL = settings.BACKEND_URL

@token_required
def lista_terceros(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    terceros = []
    error = None
    
    # Filtros
    busqueda = request.GET.get("q", "")
    filtro_rol = request.GET.get("rol", "") # "cliente" o "proveedor"

    # Paginación
    page = int(request.GET.get("page", 1))
    limit = 20 # 20 registros por página
    skip = (page - 1) * limit
    
    total_items = 0

    try:
        params = {
            "skip": skip,
            "limit": limit
        }
        if busqueda: params["busqueda"] = busqueda
        if filtro_rol: params["rol"] = filtro_rol
        
        response = httpx.get(f"{BACKEND_URL}/terceros/", params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            terceros = data.get("items", [])
            total_items = data.get("total", 0)
        elif response.status_code == 401:
             request.session.flush()
             return redirect("login")
        else:
             error = "Error al cargar el listado."
             
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    # Calcular páginas
    import math
    total_pages = math.ceil(total_items / limit) if limit > 0 else 1

    return render(request, "terceros/lista.html", {
        "terceros": terceros, 
        "busqueda": busqueda,
        "filtro_rol": filtro_rol,
        "error": error,
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    })

@token_required
def crear_tercero(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    error = None

    if request.method == "POST":
        try:
             # Checkboxes html envian 'on' si estan marcados, o nada si no.
            es_cliente = True if request.POST.get("es_cliente") else False
            es_proveedor = True if request.POST.get("es_proveedor") else False
            
            # Validación: al menos uno debe ser true
            if not es_cliente and not es_proveedor:
                error = "Debe seleccionar al menos un rol (Cliente o Proveedor)."
            else:
                payload = {
                    "rut": request.POST.get("rut"),
                    "nombre": request.POST.get("nombre"),
                    "direccion": request.POST.get("direccion") or None,
                    "telefono": request.POST.get("telefono") or None,
                    "email": request.POST.get("email") or None,
                    "es_cliente": es_cliente,
                    "es_proveedor": es_proveedor
                }
                
                response = httpx.post(f"{BACKEND_URL}/terceros/", json=payload, headers=headers)
                
                if response.status_code == 201:
                    return redirect("lista_terceros")
                elif response.status_code == 401:
                    request.session.flush()
                    return redirect("login")
                else:
                    try:
                        error = response.json().get("detail", "Error al crear tercero")
                    except:
                        error = response.text
                        
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    return render(request, "terceros/form.html", {"titulo": "Nuevo Tercero", "error": error})

@token_required
def editar_tercero(request, pk):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    tercero = {}
    error = None

    if request.method == "POST":
        try:
            # envian 'on' si estan marcados, o nada si no.
            es_cliente = True if request.POST.get("es_cliente") else False
            es_proveedor = True if request.POST.get("es_proveedor") else False
            
            # Validación: al menos uno debe ser true
            if not es_cliente and not es_proveedor:
                error = "Debe seleccionar al menos un rol (Cliente o Proveedor)."
            else:
                payload = {
                    "rut": request.POST.get("rut"),
                    "nombre": request.POST.get("nombre"),
                    "direccion": request.POST.get("direccion") or None,
                    "telefono": request.POST.get("telefono") or None,
                    "email": request.POST.get("email") or None,
                    "es_cliente": es_cliente,
                    "es_proveedor": es_proveedor
                }
                
                response = httpx.put(f"{BACKEND_URL}/terceros/{pk}", json=payload, headers=headers)
                
                if response.status_code == 200:
                    return redirect("lista_terceros")
                elif response.status_code == 401:
                    request.session.flush()
                    return redirect("login")
                else:
                    try:
                        error = response.json().get("detail", "Error al actualizar")
                    except:
                        error = response.text
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"
    
    # GET: Cargar datos
    if not error: 
        try:
            response = httpx.get(f"{BACKEND_URL}/terceros/{pk}", headers=headers)
            if response.status_code == 200:
                tercero = response.json()
            elif response.status_code == 401:
                request.session.flush()
                return redirect("login")
            else:
                error = "No se encontró el tercero."
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    return render(request, "terceros/form.html", {
        "titulo": f"Editar {tercero.get('nombre', 'Tercero')}",
        "tercero": tercero, 
        "error": error
    })

@token_required
def api_buscar_terceros(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    q = request.GET.get("q", "")
    
    try:
        # Reutilizamos el endpoint lista que ya soporta busqueda
        params = {"busqueda": q}
        response = httpx.get(f"{BACKEND_URL}/terceros/", params=params, headers=headers)
        data = response.json()
      
        if isinstance(data, dict) and "items" in data:
            return JsonResponse(data["items"], safe=False)
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

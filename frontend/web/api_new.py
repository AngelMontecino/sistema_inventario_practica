import httpx
from django.http import JsonResponse
from django.conf import settings

# Configuración del Backend 
# Configuración del Backend 
BACKEND_URL = settings.BACKEND_URL

def api_ver_stock_fresh(request):
    # Obtener token de sesión
    token = request.session.get("access_token")
    if not token:
        return JsonResponse({"error": "No autenticado"}, status=401)
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obtener parametros
    p_id = request.GET.get("id_producto")
    s_id = request.GET.get("id_sucursal")
    
    if not p_id:
        return JsonResponse({"stock": 0, "detalles": []})

    # Llamar al Backend
    try:
        url = f"{BACKEND_URL}/inventarios/"
        params = {"producto_id": p_id}
        if s_id and s_id != "None" and s_id != "":
            params["sucursal_id"] = int(s_id)
            
        response = httpx.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            total = sum(i.get('cantidad', 0) for i in data)
            
            return JsonResponse({
                "stock": total,
                "detalles": data
            })
        else:
            return JsonResponse({"stock": 0, "detalles": [], "error_backend": response.text})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

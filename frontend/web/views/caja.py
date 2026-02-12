from django.shortcuts import render, redirect
import httpx
from ..decorators import token_required

from django.conf import settings

BACKEND_URL = settings.BACKEND_URL

@token_required
def gestion_caja(request):
    """Vista principal de gestión de caja: Resumen y Acciones"""
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    resumen = None
    error = None
    ultimo_estado = "DESCONOCIDO"

    # Obtener Resumen Actual
    try:
        resp = httpx.get(f"{BACKEND_URL}/caja/resumen", headers=headers)
        if resp.status_code == 200:
            resumen = resp.json()
            
        elif resp.status_code == 400:
            
             pass
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    # Obtener Estado 
    estado_caja = {}
    try:
        resp_estado = httpx.get(f"{BACKEND_URL}/caja/estado", headers=headers)
        if resp_estado.status_code == 200:
            estado_caja = resp_estado.json()
    except httpx.RequestError:
        pass

    return render(request, "caja/gestion.html", {
        "resumen": resumen,
        "estado_caja": estado_caja,
        "error": error
    })

@token_required
def abrir_caja(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    error = None
    
    if request.method == "POST":
        try:
            monto = float(request.POST.get("monto_inicial", 0))
       
            
            response = httpx.post(f"{BACKEND_URL}/caja/apertura", params={"monto_inicial": monto}, headers=headers)
            
            if response.status_code == 201 or response.status_code == 200:
                return redirect("gestion_caja")
            else:
                 try:
                    error = response.json().get("detail", "Error al abrir caja")
                 except:
                    error = response.text
        except ValueError:
            error = "Monto inválido."
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    return render(request, "caja/apertura.html", {"error": error})

@token_required
def cerrar_caja(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    error = None
    resumen = {} # Para mostrar lo esperado antes de cerrar o al confirmar

    # Pre-cargar resumen para mostrar al usuario cuanto debería haber
    try:
        resp = httpx.get(f"{BACKEND_URL}/caja/resumen", headers=headers)
        if resp.status_code == 200:
            resumen = resp.json()
    except:
        pass

    if request.method == "POST":
        try:
            monto_real = float(request.POST.get("monto_real", 0))
       
            payload = {
                "monto_real": monto_real
            }
            
            response = httpx.post(f"{BACKEND_URL}/caja/cierre", json=payload, headers=headers)
            
            if response.status_code == 200:
               
                resultado = response.json()
                return render(request, "caja/cierre_exito.html", {"resultado": resultado})
            else:
                 try:
                    error = response.json().get("detail", "Error al cerrar caja")
                 except:
                    error = response.text
        except ValueError:
            error = "Monto inválido."
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    return render(request, "caja/cierre.html", {"resumen": resumen, "error": error})

@token_required
def registrar_movimiento(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    error = None

    if request.method == "POST":
        try:
            tipo = request.POST.get("tipo")
            monto = float(request.POST.get("monto", 0))
            descripcion = request.POST.get("descripcion", "")

            
            id_sucursal = request.session.get("id_sucursal") 
            
           
            if not id_sucursal:
                 
                 id_sucursal = 0

            payload = {
                "tipo": tipo,
                "monto": monto,
                "descripcion": descripcion,
                "id_sucursal": id_sucursal, 
                "id_usuario": 0, # Backend lo toma del token
                "id_documento_asociado": None
            }
            
            
            resp = httpx.post(f"{BACKEND_URL}/caja/movimientos", json=payload, headers=headers)
            
            if resp.status_code == 201:
                return redirect("gestion_caja")
            else:
                 try:
                    error = resp.json().get("detail", "Error al registrar movimiento")
                 except:
                    error = resp.text

        except ValueError:
            error = "Datos inválidos"
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    return render(request, "caja/movimiento_extra.html", {"error": error})

@token_required
def ver_reportes(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Filtros por defecto: Hoy
    from datetime import date, timedelta
    today = date.today().isoformat()
    fecha_inicio = request.GET.get("fecha_inicio", today)
    fecha_fin = request.GET.get("fecha_fin", today)
    sucursal_id = request.GET.get("sucursal_id", "")
    
    reportes = []
    sucursales = []
    error = None
    
    # Cargar sucursales para el filtro (solo si admin o para que el usario vea su propia sucursal)
    try:
        resp_suc = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
        if resp_suc.status_code == 200:
            sucursales = resp_suc.json()
    except:
        pass

    try:
        # Endpoints: fecha_inicio, fecha_fin (datetime)
        params = {
            "fecha_inicio": f"{fecha_inicio}T00:00:00",
            "fecha_fin": f"{fecha_fin}T23:59:59"
        }
        if sucursal_id:
            params["sucursal_id"] = sucursal_id

        if request.session.get("rol") == "VENDEDOR":
            params["sucursal_id"] = request.session.get("id_sucursal") # Fuerza su sucursal

        resp = httpx.get(f"{BACKEND_URL}/caja/reportes", params=params, headers=headers)
        if resp.status_code == 200:
            reportes = resp.json()
            
            from datetime import datetime
            for r in reportes:
                if r.get("fecha_apertura"):
                    r["fecha_apertura"] = datetime.fromisoformat(r["fecha_apertura"])
                if r.get("fecha_cierre"):
                    r["fecha_cierre"] = datetime.fromisoformat(r["fecha_cierre"])
        else:
            error = "No se pudieron cargar los reportes."
    except httpx.RequestError:
        error = "Error de conexión con el servidor."
        
    return render(request, "caja/reportes.html", {
        "reportes": reportes,
        "sucursales": sucursales,
        "sucursal_activa": sucursal_id,
        "fecha_inicio": fecha_inicio, 
        "fecha_fin": fecha_fin,
        "error": error
    })

@token_required
def detalle_sesion(request, id_apertura):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    error = None
    detalle = None

    try:
        resp = httpx.get(f"{BACKEND_URL}/caja/sesion/{id_apertura}", headers=headers)
        if resp.status_code == 200:
            detalle = resp.json()
       
            from datetime import datetime
            if detalle.get("fecha_apertura"): detalle["fecha_apertura"] = datetime.fromisoformat(detalle["fecha_apertura"])
            if detalle.get("fecha_cierre"): detalle["fecha_cierre"] = datetime.fromisoformat(detalle["fecha_cierre"])
            
            for mov in detalle.get("movimientos", []):
                if mov.get("fecha"): mov["fecha"] = datetime.fromisoformat(mov["fecha"])
            
            for doc in detalle.get("documentos_summary", []):
                if doc.get("fecha_emision"): doc["fecha_emision"] = datetime.fromisoformat(doc["fecha_emision"])
                # Convertir detalles a numericos
                for det in doc.get("detalles", []):
                    try:
                        det["cantidad"] = float(det.get("cantidad", 0))
                        det["precio_unitario"] = float(det.get("precio_unitario", 0))
                        det["descuento"] = float(det.get("descuento", 0))
                    except (ValueError, TypeError):
                        pass
            
            # Calcular Totales 
            egresos_compras = float(detalle.get("egresos_compras", 0))
            egresos_extra = float(detalle.get("egresos_extra", 0))
            detalle["total_egresos"] = egresos_compras + egresos_extra

        else:
            error = f"Error al obtener detalle: {resp.status_code}"
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "caja/detalle_sesion.html", {
        "detalle": detalle, 
        "error": error
    })

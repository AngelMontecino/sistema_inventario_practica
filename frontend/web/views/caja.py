from django.shortcuts import render, redirect
import httpx
from ..decorators import token_required

BACKEND_URL = "http://127.0.0.1:8001"

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

    return render(request, "caja/gestion.html", {
        "resumen": resumen,
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

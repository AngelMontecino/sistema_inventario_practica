from django.shortcuts import render
import httpx

# URL del Backend 
API_URL = "http://127.0.0.1:8001"

def index(request):
    return render(request, 'index.html')

def lista_productos(request):
    #  Pedir datos a FastAPI
    try:
        response = httpx.get(f"{API_URL}/productos/")
        productos = response.json() # Convertir JSON a lista de Python
    except:
        productos = [] # Si falla, enviamos lista vacía para que no explote

    return render(request, 'productos.html', {'productos': productos})
from django.shortcuts import render, redirect, reverse
import httpx
from ..decorators import token_required

from django.conf import settings

BACKEND_URL = settings.BACKEND_URL

# --- PRODUCTOS ---

@token_required
def lista_productos(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Capturar Filtros
    busqueda = request.GET.get("q")
    unidad_medida = request.GET.get("unidad_medida")
    id_categoria = request.GET.get("id_categoria")
    precio_min = request.GET.get("precio_min")
    precio_max = request.GET.get("precio_max")
    
    # Paginación
    page = int(request.GET.get("page", 1))
    limit = 100
    skip = (page - 1) * limit
    
    productos = []
    categorias = [] # Para el filtro
    error = None

    # 1. Obtener Categorías para el filtro
    try:
        cat_resp = httpx.get(f"{BACKEND_URL}/productos/categorias/", headers=headers)
        if cat_resp.status_code == 200:
            categorias = _aplanar_categorias(cat_resp.json())
    except httpx.RequestError:
        pass 

    # 2. Obtener Productos con filtros
    try:
        params = {
            "skip": skip,
            "limit": limit
        }
        if busqueda: params["busqueda"] = busqueda
        if unidad_medida: params["unidad_medida"] = unidad_medida
        if id_categoria: params["id_categoria"] = id_categoria
        if precio_min: params["precio_min"] = precio_min
        if precio_max: params["precio_max"] = precio_max

        response = httpx.get(f"{BACKEND_URL}/productos/", headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            productos = data.get("items", [])
            total_items = data.get("total", 0)
        elif response.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
            error = f"Error al obtener productos: {response.text}"
            
    except httpx.RequestError as exc:
         error = f"Error de conexión con API: {exc}"

    # Calcular páginas
    import math
    total_pages = math.ceil(total_items / limit) if limit > 0 else 1
    
   
    
    context = {
        "productos": productos,
        "categorias": categorias,
        "error": error,
        "busqueda": busqueda,
        "unidad_medida": unidad_medida,
        "id_categoria": int(id_categoria) if id_categoria else "",
        "precio_min": precio_min,
        "precio_max": precio_max,
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

    return render(request, "productos/productos.html", context)

@token_required
def crear_producto(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    categorias = []
    error = None

    if request.method == "POST":
        try:
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

    try:
        cat_resp = httpx.get(f"{BACKEND_URL}/productos/categorias/", headers=headers)
        if cat_resp.status_code == 200:
            raw_cats = cat_resp.json()
            categorias = _aplanar_categorias(raw_cats)
    except httpx.RequestError:
        pass 

    return render(request, "productos/crear_producto.html", {"categorias": categorias, "error": error})

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
            payload = {"nombre": nombre, "id_padre": id_padre}

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

    try:
        cat_resp = httpx.get(f"{BACKEND_URL}/productos/categorias/", headers=headers)
        if cat_resp.status_code == 200:
            raw_cats = cat_resp.json()
            categorias = _aplanar_categorias(raw_cats)
    except httpx.RequestError:
        pass

    return render(request, "productos/crear_categoria.html", {"categorias": categorias, "error": error})

@token_required
def editar_producto(request, pk):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    producto = {}
    categorias = []
    error = None

    if request.method == "POST":
        try:
            payload = {
                "nombre": request.POST.get("nombre"),
                "codigo_barras": request.POST.get("codigo_barras") or None,
                "precio_venta": float(request.POST.get("precio_venta", 0)),
                "costo_neto": float(request.POST.get("costo_neto", 0)),
                "unidad_medida": request.POST.get("unidad_medida"),
                "id_categoria": int(request.POST.get("id_categoria")) if request.POST.get("id_categoria") else None,
                "descripcion": request.POST.get("descripcion") or None,
            }
            response = httpx.put(f"{BACKEND_URL}/productos/{pk}", json=payload, headers=headers)
            if response.status_code == 200:
                return redirect("lista_productos")
            elif response.status_code == 401:
                request.session.flush()
                return redirect("login")
            else:
                try:
                    error = response.json().get("detail", "Error al actualizar")
                except:
                    error = response.text
        except ValueError:
            error = "Error en los datos numéricos."
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    try:
        prod_resp = httpx.get(f"{BACKEND_URL}/productos/{pk}", headers=headers)
        if prod_resp.status_code == 200:
            producto = prod_resp.json()
        elif prod_resp.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
            error = "No se pudo cargar el producto."

        cat_resp = httpx.get(f"{BACKEND_URL}/productos/categorias/", headers=headers)
        if cat_resp.status_code == 200:
            raw_cats = cat_resp.json()
            categorias = _aplanar_categorias(raw_cats)
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "productos/editar_producto.html", {"producto": producto, "categorias": categorias, "error": error})

def _aplanar_categorias(categorias_raw, nivel=0):
    lista_plana = []
    for cat in categorias_raw:
        cat_view = {"id_categoria": cat["id_categoria"], "nombre": ("— " * nivel) + cat["nombre"]}
        lista_plana.append(cat_view)
        if cat.get("hijas"):
            lista_plana.extend(_aplanar_categorias(cat["hijas"], nivel + 1))
    return lista_plana 

# --- INVENTARIO ---

@token_required
def asignar_inventario(request, pk):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    producto = {}
    sucursales = []
    error = None

    if request.method == "POST":
        try:
            payload = {
               "id_sucursal": int(request.POST.get("id_sucursal")),
               "id_producto": pk,
               "cantidad": int(request.POST.get("cantidad")),
               "ubicacion_especifica": request.POST.get("ubicacion_especifica"),
               "stock_minimo": int(request.POST.get("stock_minimo", 5)),
               "stock_maximo": int(request.POST.get("stock_maximo", 100))
            }
            response = httpx.post(f"{BACKEND_URL}/inventarios/", json=payload, headers=headers)
            if response.status_code == 201:
                return redirect("lista_productos")
            elif response.status_code == 401:
                request.session.flush()
                return redirect("login")
            else:
                try:
                    error = response.json().get("detail", "Error al asignar inventario")
                except:
                    error = response.text
        except ValueError:
            error = "Error en los datos numéricos."
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    try:
        prod_resp = httpx.get(f"{BACKEND_URL}/productos/{pk}", headers=headers)
        if prod_resp.status_code == 200:
            producto = prod_resp.json()
        elif prod_resp.status_code == 401:
            request.session.flush()
            return redirect("login")
            
        suc_resp = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
        if suc_resp.status_code == 200:
            sucursales = suc_resp.json()
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "inventario/asignar_inventario.html", {"producto": producto, "sucursales": sucursales, "error": error})

@token_required
def lista_inventario(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    inventario = []
    error = None
    
    # Filtros
    sucursal_id = request.GET.get("sucursal_id", "")
    categoria_id = request.GET.get("categoria_id", "")
    busqueda = request.GET.get("q", "")
    alerta = request.GET.get("alerta", "")
    
    # Auto-filtro para vendedores
    if request.session.get("rol") == "VENDEDOR":
        sucursal_id = request.session.get("id_sucursal")
    
    params = {}
    if sucursal_id:
        params["sucursal_id"] = sucursal_id
    if categoria_id:
        params["categoria_id"] = categoria_id
    if busqueda:
        params["busqueda"] = busqueda
    if alerta == "true":
        params["alerta_stock"] = "true"

    sucursales = []
    categorias = []
    
    try:

        if request.session.get("rol") == "ADMIN": 
             resp_suc = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
             if resp_suc.status_code == 200:
                 sucursales = resp_suc.json()

        #  Obtener Categorías (para el filtro)
        resp_cat = httpx.get(f"{BACKEND_URL}/productos/categorias/", params={"flat": "true"}, headers=headers)
        if resp_cat.status_code == 200:
            categorias = resp_cat.json()

        # Obtener Inventario (Agrupado)
        url_inv = f"{BACKEND_URL}/inventarios/agrupado"
        response = httpx.get(url_inv, params=params, headers=headers)
        
        if response.status_code == 200:
            inventario = response.json()
        elif response.status_code == 401:
            return redirect("login")
        else:
            error = f"Error al cargar inventario: {response.status_code}"

    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "inventario/inventario.html", {
        "inventario": inventario,
        "sucursales": sucursales,
        "categorias": categorias,
        "filtro_sucursal": int(sucursal_id) if sucursal_id else None,
        "filtro_categoria": int(categoria_id) if categoria_id else None,
        "filtro_alerta": alerta == "true",
        "busqueda": busqueda,
        "error": error
    })

@token_required
def detalle_inventario(request, pk):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    detalles = []
    producto = {} 
    sucursal_seleccionada = request.GET.get("sucursal_id", "")
    error = None

    try:
        params = {"producto_id": pk}
        if sucursal_seleccionada: params["sucursal_id"] = sucursal_seleccionada
        resp = httpx.get(f"{BACKEND_URL}/inventarios/", params=params, headers=headers)
        if resp.status_code == 200:
            detalles = resp.json()
            if detalles:
                producto = detalles[0].get("producto", {})
            else:
                 try:
                     resp_prod = httpx.get(f"{BACKEND_URL}/productos/{pk}", headers=headers)
                     if resp_prod.status_code == 200:
                         producto = resp_prod.json()
                 except: 
                     pass
        elif resp.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
            error = "Error al cargar detalles del inventario."
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "inventario/detalle_inventario.html", {"detalles": detalles, "producto": producto, "error": error})

@token_required
def editar_inventario(request, pk):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    item = {}
    error = None

    if request.method == "POST":
        try:
            payload = {
                "cantidad": int(request.POST.get("cantidad")),
                "ubicacion_especifica": request.POST.get("ubicacion_especifica"),
                "stock_minimo": int(request.POST.get("stock_minimo")),
                "stock_maximo": int(request.POST.get("stock_maximo")) if request.POST.get("stock_maximo") else None
            }
            response = httpx.put(f"{BACKEND_URL}/inventarios/{pk}", json=payload, headers=headers)
            if response.status_code == 200:
                return redirect("lista_inventario")
            elif response.status_code == 401:
                request.session.flush()
                return redirect("login")
            else:
                 try:
                    error = response.json().get("detail", "Error al actualizar stock")
                 except:
                    error = response.text
        except ValueError:
             error = "Los valores numéricos no son válidos."
        except httpx.RequestError as exc:
            error = f"Error de conexión: {exc}"

    try:
        response = httpx.get(f"{BACKEND_URL}/inventarios/{pk}", headers=headers)
        if response.status_code == 200:
            item = response.json()
        elif response.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
            error = "No se encontró el registro de inventario."
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "inventario/editar_inventario.html", {"item": item, "error": error})

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
                
                # Guardar token y datos de usuario en sesion
                request.session["access_token"] = access_token
                request.session["rol"] = data.get("rol")
                request.session["nombre"] = data.get("nombre")
                
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
    
    # Capturar Filtros
    busqueda = request.GET.get("q")
    unidad_medida = request.GET.get("unidad_medida")
    id_categoria = request.GET.get("id_categoria")
    precio_min = request.GET.get("precio_min")
    precio_max = request.GET.get("precio_max")
    
    productos = []
    categorias = [] # Para el filtro
    error = None

    # 1. Obtener Categorías para el filtro
    try:
        cat_resp = httpx.get(f"{BACKEND_URL}/productos/categorias/", headers=headers)
        if cat_resp.status_code == 200:
            categorias = _aplanar_categorias(cat_resp.json())
    except httpx.RequestError:
        pass # Si falla categorias, al menos cargar productos

    # 2. Obtener Productos con filtros
    try:
        params = {}
        if busqueda: params["busqueda"] = busqueda
        if unidad_medida: params["unidad_medida"] = unidad_medida
        if id_categoria: params["id_categoria"] = id_categoria
        if precio_min: params["precio_min"] = precio_min
        if precio_max: params["precio_max"] = precio_max

        response = httpx.get(f"{BACKEND_URL}/productos/", headers=headers, params=params)
        
        if response.status_code == 200:
            productos = response.json()
        elif response.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
            error = f"Error al obtener productos: {response.text}"
            
    except httpx.RequestError as exc:
         error = f"Error de conexión con API: {exc}"

    context = {
        "productos": productos,
        "categorias": categorias, # Enviamos categorias para el select
        "error": error,
        
        # Preservar estado de los filtros
        "busqueda": busqueda,
        "unidad_medida": unidad_medida,
        "id_categoria": int(id_categoria) if id_categoria else "",
        "precio_min": precio_min,
        "precio_max": precio_max
    }

    return render(request, "productos.html", context)

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


@token_required
def editar_producto(request, pk):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    producto = {}
    categorias = []
    error = None

    # Logica POST: actualizar
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

    # Lógica GET: Cargar datos actuales y categorías
    try:
        # 1. Obtener producto
        prod_resp = httpx.get(f"{BACKEND_URL}/productos/{pk}", headers=headers)
        if prod_resp.status_code == 200:
            producto = prod_resp.json()
        elif prod_resp.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
            error = "No se pudo cargar el producto."

        # 2. Obtener categorías
        cat_resp = httpx.get(f"{BACKEND_URL}/productos/categorias/", headers=headers)
        if cat_resp.status_code == 200:
            raw_cats = cat_resp.json()
            categorias = _aplanar_categorias(raw_cats)
            
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "editar_producto.html", {"producto": producto, "categorias": categorias, "error": error})

def _aplanar_categorias(categorias_raw, nivel=0):
    """Función recursiva para aplanar el árbol de categorías."""
    lista_plana = []
    for cat in categorias_raw:
        cat_view = {
            "id_categoria": cat["id_categoria"],
            "nombre": ("— " * nivel) + cat["nombre"]
        }
        lista_plana.append(cat_view)
        
        if cat.get("hijas"):
            lista_plana.extend(_aplanar_categorias(cat["hijas"], nivel + 1))
            
    return lista_plana 

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

    # POST: Actualizar
    if request.method == "POST":
        try:
            # 1. Actualizar datos básicos (sin es_principal)
            payload = {
                "nombre": request.POST.get("nombre"),
                "direccion": request.POST.get("direccion") or None,
                "telefono": request.POST.get("telefono") or None,
                # "es_principal" se maneja aparte por lógica de negocio del backend
            }
            
            response = httpx.put(f"{BACKEND_URL}/sucursales/{pk}", json=payload, headers=headers)
            
            if response.status_code == 200:
                # 2. Si se marcó como principal, llamar al endpoint específico
                if request.POST.get("es_principal"):
                    try:
                        resp_principal = httpx.put(f"{BACKEND_URL}/sucursales/{pk}/principal", headers=headers)
                        if resp_principal.status_code != 200:
                            # Advertencia pero no error fatal
                            error = "Se actualizaron los datos pero hubo un error al establecer como principal."
                    except httpx.RequestError:
                         pass # Fallo silencioso o log

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
            # Buscar la sucursal especifica
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

@token_required
def asignar_inventario(request, pk):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    producto = {}
    sucursales = []
    error = None

    # POST: Asignar inventario
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

    # GET: Cargar datos
    try:
        # Producto
        prod_resp = httpx.get(f"{BACKEND_URL}/productos/{pk}", headers=headers)
        if prod_resp.status_code == 200:
            producto = prod_resp.json()
        elif prod_resp.status_code == 401:
            request.session.flush()
            return redirect("login")
            
        # Sucursales
        suc_resp = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
        if suc_resp.status_code == 200:
            sucursales = suc_resp.json()
            
    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "asignar_inventario.html", {
        "producto": producto, 
        "sucursales": sucursales, 
        "error": error
    })

@token_required
def lista_inventario(request):
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    sucursales = []
    inventario = []
    sucursal_seleccionada = request.GET.get("sucursal_id", "")
    busqueda = request.GET.get("q", "")
    error = None

    try:
        # Cargar sucursales para el filtro
        resp_sucursales = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
        if resp_sucursales.status_code == 200:
            sucursales = resp_sucursales.json()
        
        # Cargar inventario AGRUPADO
        url_inv = f"{BACKEND_URL}/inventarios/agrupado"
        params = {}
        if sucursal_seleccionada:
            params["sucursal_id"] = sucursal_seleccionada
        if busqueda:
            params["busqueda"] = busqueda
            
        resp_inv = httpx.get(url_inv, params=params, headers=headers)
        if resp_inv.status_code == 200:
            inventario = resp_inv.json()
        elif resp_inv.status_code == 401:
            request.session.flush()
            return redirect("login")
        else:
             error = "Error al cargar el inventario."

    except httpx.RequestError as exc:
        error = f"Error de conexión: {exc}"

    return render(request, "inventario.html", {
        "inventario": inventario, 
        "sucursales": sucursales,
        "sucursal_seleccionada": int(sucursal_seleccionada) if sucursal_seleccionada else None,
        "busqueda": busqueda,
        "error": error
    })

@token_required
def detalle_inventario(request, pk):
    """
    Vista para ver el desglose de stock de un producto específico (por ID producto).
    Puede filtrar por sucursal si viene en la query string.
    """
    token = request.session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    detalles = []
    producto = {} # Para mostrar info del producto
    sucursal_seleccionada = request.GET.get("sucursal_id", "")
    error = None

    try:
        # 1. Obtener detalles del inventario filtrado por producto y opcionalmente sucursal
        params = {"producto_id": pk}
        if sucursal_seleccionada:
            params["sucursal_id"] = sucursal_seleccionada
            
        resp = httpx.get(f"{BACKEND_URL}/inventarios/", params=params, headers=headers)
        
        if resp.status_code == 200:
            detalles = resp.json()
            # Extraer info básica del producto del primer item (si hay)
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

    return render(request, "detalle_inventario.html", {
        "detalles": detalles,
        "producto": producto,
        "error": error
    })

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
            # PUT /inventarios/{id}
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

    # GET para prellenar
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

    return render(request, "editar_inventario.html", {"item": item, "error": error})

# --- GESTIÓN DE USUARIOS (ADMIN) ---

from .decorators import admin_required

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
                "estado": True # Por defecto activo
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

    # Cargar sucursales para el select
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

    # POST: Actualizar
    if request.method == "POST":
        try:
            payload = {
                "rol": request.POST.get("rol"),
                "id_sucursal": int(request.POST.get("id_sucursal")),
                "estado": True if request.POST.get("estado") == "on" else False
                # No enviamos password ni email/nombre si no se editan.
                # La vista simplificada asume que nombre/email no se tocan aqui o se mantiene,
                # pero el requerimiento dice: "Permite cambiar Rol, Sucursal y Estado".
            }
            
            # El schema backend UsuarioUpdate acepta opcionales.
            
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

    # GET: Cargar datos
    try:
        # Sucursales
        suc_resp = httpx.get(f"{BACKEND_URL}/sucursales/", headers=headers)
        if suc_resp.status_code == 200:
            sucursales = suc_resp.json()
            
        # Lista usuarios para filtrar localmente (o un endpoint get usuario id si existiera en router)
        # El router backend NO TIENE get_usuario_by_id especifico expuesto en "/usuarios/{id}"?
        # Revisemos auth.py:
        # @router.put("/usuarios/{usuario_id}") existe.
        # @router.get("/usuarios/") lista todos.
        # NO HAY GET /usuarios/{id}. Debemos buscar en la lista o agregarlo al backend.
        # El requerimiento backend solo decia LISTA y CREAR. 
        # Pero EDITAR requiere cargar datos actuales.
        # Voy a usar la lista y filtrar en python por simplicidad, dado que no quiero modificar mas backend si no es critico,
        # aunque lo ideal seria un GET /usuarios/{id}.
        # Como soy "Antigravity", voy a asumir que puedo filtrar la lista.
        
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
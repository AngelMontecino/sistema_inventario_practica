import json
import sys
import os
from decimal import Decimal 
from sqlalchemy.orm import Session

# configuración de importaciones
sys.path.append(os.getcwd())
try:
    from app.database import SessionLocal, engine
    from app.models import Producto, Categoria, Base
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'app'))
    from app.database import SessionLocal, engine
    from app.models import Producto, Categoria, Base

# nombre del archivo de respaldo
ARCHIVO_RESPALDO = "respaldo_productos.json"

def serializar_objeto(obj):
    # convierte un objeto de SQLAlchemy a un diccionario real.
    datos = {}
    for c in obj.__table__.columns:
        valor = getattr(obj, c.name)
        
        # si el valor es de tipo decimal, lo pasamos a float
        if isinstance(valor, Decimal):
            valor = float(valor)

        datos[c.name] = valor
    return datos

def hacer_dump():
    #generar archivo json
    db = SessionLocal()
    try:
        print("Iniciando respaldo...")
        
        # obtener datos
        categorias = db.query(Categoria).all()
        productos = db.query(Producto).all()
        
        # convertirlos a json
        datos = {
            "categorias": [serializar_objeto(c) for c in categorias],
            "productos": [serializar_objeto(p) for p in productos]
        }
        
        # guardar
        with open(ARCHIVO_RESPALDO, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
            
        print(f"Respaldo completo: {len(categorias)} categorías y {len(productos)} productos guardados en '{ARCHIVO_RESPALDO}'.")
        
    except Exception as e:
        print(f"Error al respaldar: {e}")
        import traceback
        traceback.print_exc() # detalles del fallo
    finally:
        db.close()

def hacer_load():
    # lee el json y restaura los datos en la BD
    db = SessionLocal()
    
    if not os.path.exists(ARCHIVO_RESPALDO):
        print(f"No se encontro el archivo '{ARCHIVO_RESPALDO}'")
        return

    try:
        print("Restaurando base de datos...")
        
        with open(ARCHIVO_RESPALDO, "r", encoding="utf-8") as f:
            datos = json.load(f)

        # cargar categorias
        print(f" - Cargando {len(datos['categorias'])} categorías...")
        for cat_dict in datos['categorias']:
            existe = db.query(Categoria).filter_by(id_categoria=cat_dict['id_categoria']).first()
            if not existe:
                nueva_cat = Categoria(**cat_dict)
                db.add(nueva_cat)
        db.commit()

        # cargar productos
        print(f" - Cargando {len(datos['productos'])} productos...")
        for prod_dict in datos['productos']:
            existe = db.query(Producto).filter_by(id_producto=prod_dict['id_producto']).first()
            if not existe:
                nuevo_prod = Producto(**prod_dict)
                db.add(nuevo_prod)
        db.commit()

        print("Restauración completada")

    except Exception as e:
        print(f"Error al restaurar: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "load":
        hacer_load()
    else:
        hacer_dump()
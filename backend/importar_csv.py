import csv
import sys
import os

# configuracion
sys.path.append(os.getcwd())
from app.database import SessionLocal
from app.models import Producto, Categoria

NOMBRE_ARCHIVO = "productos.csv"
SEPARADOR_CATEGORIA = ">" # lo que separa padre de hijo


# recibe categoria > subcategoria y devuelve el ID de la subcategoria (creando la categoria y subcategoria antes si no existen)
def obtener_o_crear_categoria(db, ruta_categoria):
    # separar la cadena categoria y subcategoria
    nombres = [n.strip() for n in ruta_categoria.split(SEPARADOR_CATEGORIA)]
    
    id_padre_actual = None
    categoria_final = None

    for nombre_cat in nombres:
        # busca si existe esta categoría con este padre especifico
        # Esto permite tener subcategorias dentro de las categorias 
        cat_db = db.query(Categoria).filter(
            Categoria.nombre == nombre_cat,
            Categoria.id_padre == id_padre_actual
        ).first()

        if not cat_db:
            # si no existe, la creamos enlazada al padre anterior
            print(f"Creando categoría nueva: '{nombre_cat}' (Padre ID: {id_padre_actual})")
            nueva_cat = Categoria(
                nombre=nombre_cat,
                id_padre=id_padre_actual
            )
            db.add(nueva_cat)
            db.commit()
            db.refresh(nueva_cat)
            cat_db = nueva_cat
        
        # el padre de la siguiente iteración será esta categoría
        id_padre_actual = cat_db.id_categoria
        categoria_final = cat_db

    return categoria_final.id_categoria

def importar_datos_jerarquicos():
    db = SessionLocal()
    ruta_archivo = os.path.join(os.getcwd(), NOMBRE_ARCHIVO)

    if not os.path.exists(ruta_archivo):
        print(f" No se encontró {NOMBRE_ARCHIVO}")
        return

    try:
        print(" Iniciando importación jerarquica...")
        contador = 0
        productos_nuevos = []

        with open(ruta_archivo, mode='r', encoding='utf-8') as f:
            lector = csv.DictReader(f) # asume separador por coma
            
            for fila in lector:
                try:
                    # obtener la ruta completa 
                    ruta_cat = fila['categoria'].strip()
                    
                    # funcion que navega/crea la jerarquía
                    id_cat_final = obtener_o_crear_categoria(db, ruta_cat)

                    # crear Producto
                    prod = Producto(
                        nombre=fila['nombre'].strip(),
                        codigo_barras=fila['codigo_barras'].strip(),
                        costo_neto=int(fila['costo_neto']),
                        precio_venta=int(fila['precio_venta']),
                        unidad_medida=fila['unidad_medida'].strip(),
                        id_categoria=id_cat_final, # asignamos a la ultima subcategoria
                        descripcion=fila['descripcion']
                    )
                    productos_nuevos.append(prod)
                    contador += 1
                    
                    # guardar en bloques de 100
                    if len(productos_nuevos) >= 100:
                        db.bulk_save_objects(productos_nuevos)
                        db.commit()
                        productos_nuevos = []
                        print(f"{contador} procesados")

                except Exception as e_fila:
                    print(f"Error en fila {fila.get('nombre', '?')}: {e_fila}")
                    continue

            # guardar restantes
            if productos_nuevos:
                db.bulk_save_objects(productos_nuevos)
                db.commit()

        print(f"{contador} productos importados con sus jerarquías.")

    except Exception as e:
        print(f"Error fatal: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    importar_datos_jerarquicos()
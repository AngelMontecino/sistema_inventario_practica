import json
import sys
import os
from sqlalchemy.orm import Session

# configuración de importaciones
sys.path.append(os.getcwd())
try:
    from app.database import SessionLocal
    from app.models import Usuario, TipoRol, Sucursal
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'app'))
    from app.database import SessionLocal
    from app.models import Usuario, TipoRol, Sucursal

# nombre del archivo de respaldo
ARCHIVO_RESPALDO = "respaldo_usuarios.json"

def serializar_objeto(obj):
    # convierte un objeto de SQLAlchemy a un diccionario real
    datos = {}
    for c in obj.__table__.columns:
        valor = getattr(obj, c.name)
        
        if hasattr(valor, "value"):
            valor = valor.value
            
        datos[c.name] = valor
    return datos

def hacer_dump():
    #generar archivo json
    db = SessionLocal()
    try:
        print("Iniciando respaldo de usuarios...")
        
        # obtener datos
        sucursales = db.query(Sucursal).all()
        usuarios = db.query(Usuario).all()
        
        # convertirlos a json
        datos = {
            "sucursales": [serializar_objeto(s) for s in sucursales],
            "usuarios": [serializar_objeto(u) for u in usuarios]
        }
        
        # guardar
        with open(ARCHIVO_RESPALDO, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
            
        print(f"Respaldo completo: {len(sucursales)} sucursales y {len(usuarios)} usuarios guardados en '{ARCHIVO_RESPALDO}'.")
        
    except Exception as e:
        print(f"Error al respaldar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def hacer_load():
    # lee el json y restaura los datos en la BD
    db = SessionLocal()
    
    if not os.path.exists(ARCHIVO_RESPALDO):
        print(f"No se encontro el archivo '{ARCHIVO_RESPALDO}'")
        return

    try:
        print("Restaurando usuarios...")
        
        with open(ARCHIVO_RESPALDO, "r", encoding="utf-8") as f:
            datos = json.load(f)
        # 1. cargar sucursales (primero, pq usuario depende de sucursal)
        lista_sucursales = datos.get('sucursales', [])
        print(f" - Cargando {len(lista_sucursales)} sucursales...")
        creados_suc = 0
        for suc_dict in lista_sucursales:
            existe = db.query(Sucursal).filter_by(id_sucursal=suc_dict['id_sucursal']).first()
            if not existe:
               nueva_suc = Sucursal(**suc_dict)
               db.add(nueva_suc)
               creados_suc += 1
        db.commit()

        # 2. cargar usuarios
        lista_usuarios = datos.get('usuarios', [])
        print(f" - Cargando {len(lista_usuarios)} usuarios...")
        
        creados = 0
        for user_dict in lista_usuarios:
           
            existe = db.query(Usuario).filter_by(id_usuario=user_dict['id_usuario']).first()
            
            if not existe:
                # Verificar si ya existe el email para evitar conflictos de unique constraint
                existe_email = db.query(Usuario).filter_by(email=user_dict['email']).first()
                if existe_email:
                    print(f"   [SKIP] El usuario con email {user_dict['email']} ya existe (ID diferente).")
                    continue
                
              
                
                nuevo_user = Usuario(**user_dict)
                db.add(nuevo_user)
                creados += 1
            else:
                
                pass

        db.commit()
        print(f"Restauración completada. {creados_suc} sucursales y {creados} usuarios nuevos creados.")

    except Exception as e:
        print(f"Error al restaurar: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "load":
        hacer_load()
    else:
        hacer_dump()

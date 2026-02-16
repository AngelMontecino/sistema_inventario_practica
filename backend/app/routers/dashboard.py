from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
from app.core.redis import RedisService
from app.dependencies import get_current_user, get_redis
import json
from fastapi.encoders import jsonable_encoder

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)

from typing import Optional

@router.get("/stats")
def get_dashboard_stats(
    sucursal_id: Optional[int] = None,
    force_refresh: bool = False,
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_user),
    redis: RedisService = Depends(get_redis)
):
    target_sucursal_id = current_user.id_sucursal
    
    if current_user.rol in [models.TipoRol.ADMIN, models.TipoRol.SUPERADMIN]:
        if current_user.rol == models.TipoRol.SUPERADMIN:
            target_sucursal_id = sucursal_id
        else:
            target_sucursal_id = sucursal_id if sucursal_id else current_user.id_sucursal
            
    # Cache 
    cache_key = f"dashboard:stats:{target_sucursal_id if target_sucursal_id else 'global'}"
    
    if not force_refresh:
        cached = redis.get(cache_key)
        if cached:
            return json.loads(cached)

    stats = crud.get_dashboard_stats(db, sucursal_id=target_sucursal_id)
    

    redis.set(cache_key, json.dumps(jsonable_encoder(stats)), ttl=120)
    
    return stats

@router.get("/charts")
def get_dashboard_charts(
    sucursal_id: Optional[int] = None,
    force_refresh: bool = False,
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_user),
    redis: RedisService = Depends(get_redis)
):
    target_sucursal_id = current_user.id_sucursal
    
    if current_user.rol in [models.TipoRol.ADMIN, models.TipoRol.SUPERADMIN]:
        if current_user.rol == models.TipoRol.SUPERADMIN:
            target_sucursal_id = sucursal_id 
        else:
             target_sucursal_id = sucursal_id if sucursal_id else current_user.id_sucursal

    # Cache 
    cache_key = f"dashboard:charts:{target_sucursal_id if target_sucursal_id else 'global'}"
    
    if not force_refresh:
        cached = redis.get(cache_key)
        if cached:
            return json.loads(cached)

    charts = crud.get_dashboard_charts(db, sucursal_id=target_sucursal_id)
    

    redis.set(cache_key, json.dumps(jsonable_encoder(charts)), ttl=120)
    
    return charts

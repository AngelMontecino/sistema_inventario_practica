from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)

from typing import Optional

@router.get("/stats")
def get_dashboard_stats(
    sucursal_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_user)
):
    target_sucursal_id = current_user.id_sucursal
    
    if current_user.rol == models.TipoRol.ADMIN:
        # Si es Admin, puede filtrar. 
        target_sucursal_id = sucursal_id
        
    return crud.get_dashboard_stats(db, sucursal_id=target_sucursal_id)

@router.get("/charts")
def get_dashboard_charts(
    sucursal_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_user)
):
    target_sucursal_id = current_user.id_sucursal
    
    if current_user.rol == models.TipoRol.ADMIN:
        # Si es Admin, puede filtrar. 
        target_sucursal_id = sucursal_id
        
    return crud.get_dashboard_charts(db, sucursal_id=target_sucursal_id)

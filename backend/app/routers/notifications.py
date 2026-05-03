"""
Router de Notificaciones
Permite a los usuarios ver las notificaciones de resultado de subastas.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.models import Notification, User
from app.routers.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    league_id: Optional[int]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    league_id: Optional[int] = Query(None, description="Filter by league"),
    unread_only: bool = Query(False),
    limit: int = Query(20, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener las notificaciones del usuario actual, filtradas por liga si se especifica."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if league_id is not None:
        query = query.filter(Notification.league_id == league_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return notifications


@router.get("/unread-count")
async def get_unread_count(
    league_id: Optional[int] = Query(None, description="Filter by league"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener el número de notificaciones no leídas, filtradas por liga si se especifica."""
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    if league_id is not None:
        query = query.filter(Notification.league_id == league_id)
    count = query.count()
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar una notificación como leída."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"ok": True}


@router.post("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar todas las notificaciones como leídas."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}
    
@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar una notificación específica."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if notif:
        db.delete(notif)
        db.commit()
    return {"ok": True}

@router.delete("/clear-all")
async def clear_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar todas las notificaciones del usuario."""
    db.query(Notification).filter(Notification.user_id == current_user.id).delete()
    db.commit()
    return {"ok": True}

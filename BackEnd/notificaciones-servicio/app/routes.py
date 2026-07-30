import time
from fastapi import APIRouter, HTTPException, Query
from typing import List
from .schemas import NotificacionCreate, NotificacionResponse
from .services import (
    crear_notificacion,
    obtener_notificaciones,
    obtener_notificacion,
    obtener_notificaciones_por_reserva
)

router = APIRouter()

@router.post("/notifications", response_model=NotificacionResponse)
def create(
    notificacion: NotificacionCreate,
    simular_fallo: bool = Query(False),
    simular_demora: int = Query(0)
):
    if simular_demora > 0:
        time.sleep(simular_demora)
    if simular_fallo:
        try:
            crear_notificacion(notificacion.id_reserva, notificacion.correo, estado='FALLIDO')
        except ValueError as ve:
            raise HTTPException(status_code=404, detail=str(ve))
        except Exception:
            pass
        raise HTTPException(
            status_code=503,
            detail="Error de comunicación con el servidor de correo SMTP (Simulado)"
        )
    try:
        resultado = crear_notificacion(notificacion.id_reserva, notificacion.correo, estado='ENVIADO')
        return resultado
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications", response_model=List[NotificacionResponse])
def get_all():
    return obtener_notificaciones()

@router.get("/notifications/{id_notificacion}", response_model=NotificacionResponse)
def get_one(id_notificacion: int):
    notificacion = obtener_notificacion(id_notificacion)
    if notificacion is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return notificacion

@router.get("/notifications/reservation/{id_reserva}", response_model=List[NotificacionResponse])
def get_by_reservation(id_reserva: int):
    return obtener_notificaciones_por_reserva(id_reserva)

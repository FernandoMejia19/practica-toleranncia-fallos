import time
from fastapi import APIRouter, HTTPException, Query
from typing import List
from .schemas import PagoCreate, PagoResponse
from .services import (
    crear_pago,
    obtener_pagos,
    obtener_pago,
    obtener_pagos_por_reserva
)

router = APIRouter()

@router.post("/payments", response_model=PagoResponse)
def create(
    pago: PagoCreate,
    simular_fallo: bool = Query(False),
    simular_demora: int = Query(0)
):
    if simular_demora > 0:
        time.sleep(simular_demora)
        raise HTTPException(
            status_code=504,
            detail="La pasarela de pagos superó el tiempo máximo de respuesta"
        )
    if simular_fallo:
        try:
            crear_pago(pago.id_reserva, pago.monto, estado='FALLIDO')
        except ValueError as ve:
            raise HTTPException(status_code=404, detail=str(ve))
        except Exception:
            pass
        raise HTTPException(
            status_code=503,
            detail="Error de comunicación con la pasarela de pagos (Simulado)"
        )
    try:
        resultado = crear_pago(pago.id_reserva, pago.monto, estado='EXITOSO')
        return resultado
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payments", response_model=List[PagoResponse])
def get_all():
    return obtener_pagos()

@router.get("/payments/{id_pago}", response_model=PagoResponse)
def get_one(id_pago: int):
    pago = obtener_pago(id_pago)
    if pago is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago

@router.get("/payments/reservation/{id_reserva}", response_model=List[PagoResponse])
def get_by_reservation(id_reserva: int):
    return obtener_pagos_por_reserva(id_reserva)

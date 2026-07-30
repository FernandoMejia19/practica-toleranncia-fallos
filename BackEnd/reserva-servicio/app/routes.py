from fastapi import APIRouter, HTTPException, Query
from .clients.inventory_client import (
    InventoryUnavailableError,
    SeatUnavailableError
)
from .clients.payment_client import (
    CircuitOpenError,
    PaymentRejectedError,
    PaymentUnavailableError
)
from .schemas import ReservaCreate
from .services import (
    crear_reserva,
    obtener_reserva,
    obtener_reservas
)

router = APIRouter()

@router.post("/reservations")
def create(
    reserva: ReservaCreate,
    simular_demora_pago: int = Query(
        0,
        ge=0,
        le=30
    ),
    simular_fallo_pago: bool = Query(False),
    tolerancia_activa: bool = Query(True)
):
    try:
        resultado = crear_reserva(
            reserva=reserva,
            simular_demora_pago=simular_demora_pago,
            simular_fallo_pago=simular_fallo_pago,
            tolerancia_activa=tolerancia_activa
        )
        return {
            "mensaje": "Compra procesada correctamente",
            **resultado
        }
    except SeatUnavailableError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        ) from error
    except InventoryUnavailableError as error:
        raise HTTPException(
            status_code=503,
            detail={
                "mensaje": "Inventario no disponible",
                "causa": str(error)
            }
        ) from error
    except CircuitOpenError as error:
        raise HTTPException(
            status_code=503,
            detail={
                "mensaje": "Pagos temporalmente bloqueado",
                "circuit_breaker": "OPEN",
                "causa": str(error)
            }
        ) from error
    except PaymentUnavailableError as error:
        raise HTTPException(
            status_code=503,
            detail={
                "mensaje": (
                    "La reserva fue cancelada porque "
                    "Pagos no respondió a tiempo"
                ),
                "causa": str(error)
            }
        ) from error
    except PaymentRejectedError as error:
        raise HTTPException(
            status_code=402,
            detail={
                "mensaje": "El pago fue rechazado",
                "causa": str(error)
            }
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="No fue posible completar la compra"
        ) from error

@router.get("/reservations")
def get_all():
    return obtener_reservas()

@router.get("/reservations/{id_reserva}")
def get_one(id_reserva: int):
    reserva = obtener_reserva(id_reserva)
    if reserva is None:
        raise HTTPException(
            status_code=404,
            detail="Reserva no encontrada"
        )
    return reserva
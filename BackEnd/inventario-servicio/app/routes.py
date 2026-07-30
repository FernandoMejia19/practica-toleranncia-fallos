from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .schemas import AsientoResponse, ReservaAsientoResponse
from .services import (
    confirmar_asiento,
    liberar_asiento,
    obtener_asiento,
    obtener_asientos,
    reservar_asiento
)

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)

@router.get(
    "/seats",
    response_model=list[AsientoResponse]
)
def listar_asientos(
    db: Session = Depends(get_db)
):
    return obtener_asientos(db)

@router.get(
    "/seats/{id_asiento}",
    response_model=AsientoResponse
)
def consultar_asiento(
    id_asiento: int,
    db: Session = Depends(get_db)
):
    asiento = obtener_asiento(db, id_asiento)
    if asiento is None:
        raise HTTPException(
            status_code=404,
            detail="Asiento no encontrado"
        )
    return asiento

@router.post(
    "/seats/{id_asiento}/hold",
    response_model=ReservaAsientoResponse
)
def retener_asiento(
    id_asiento: int,
    db: Session = Depends(get_db)
):
    asiento = reservar_asiento(db, id_asiento)
    if asiento is None:
        raise HTTPException(
            status_code=409,
            detail="El asiento no está disponible"
        )
    return {
        "id_asiento": asiento.id_asiento,
        "estado": asiento.estado,
        "mensaje": "Asiento reservado temporalmente"
    }

@router.post(
    "/seats/{id_asiento}/confirm",
    response_model=ReservaAsientoResponse
)
def confirmar(
    id_asiento: int,
    db: Session = Depends(get_db)
):
    asiento = confirmar_asiento(db, id_asiento)
    if asiento is None:
        raise HTTPException(
            status_code=409,
            detail="El asiento no puede confirmarse"
        )
    return {
        "id_asiento": asiento.id_asiento,
        "estado": asiento.estado,
        "mensaje": "Asiento vendido correctamente"
    }

@router.post(
    "/seats/{id_asiento}/release",
    response_model=ReservaAsientoResponse
)
def liberar(
    id_asiento: int,
    db: Session = Depends(get_db)
):
    asiento = liberar_asiento(
        db,
        id_asiento
    )
    if asiento is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "El asiento no existe o "
                "no está en estado RESERVADO"
            )
        )
    return {
        "id_asiento": asiento.id_asiento,
        "estado": asiento.estado,
        "mensaje": "Asiento liberado correctamente"
    }
from sqlalchemy.orm import Session
from .models import Asiento

def obtener_asientos(db: Session):
    return db.query(Asiento).order_by(Asiento.id_asiento).all()

def obtener_asiento(db: Session, id_asiento: int):
    return (
        db.query(Asiento)
        .filter(Asiento.id_asiento == id_asiento)
        .first()
    )

def reservar_asiento(db: Session, id_asiento: int):
    filas_actualizadas = (
        db.query(Asiento)
        .filter(
            Asiento.id_asiento == id_asiento,
            Asiento.estado == "DISPONIBLE"
        )
        .update(
            {"estado": "RESERVADO"},
            synchronize_session=False
        )
    )
    if filas_actualizadas == 0:
        db.rollback()
        return None
    db.commit()
    return obtener_asiento(db, id_asiento)

def confirmar_asiento(
    db: Session,
    id_asiento: int
):
    filas_actualizadas = (
        db.query(Asiento)
        .filter(
            Asiento.id_asiento == id_asiento,
            Asiento.estado == "RESERVADO"
        )
        .update(
            {"estado": "VENDIDO"},
            synchronize_session=False
        )
    )
    if filas_actualizadas == 0:
        db.rollback()
        return None
    db.commit()
    return obtener_asiento(
        db,
        id_asiento
    )

def liberar_asiento(
    db: Session,
    id_asiento: int
):
    filas_actualizadas = (
        db.query(Asiento)
        .filter(
            Asiento.id_asiento == id_asiento,
            Asiento.estado == "RESERVADO"
        )
        .update(
            {"estado": "DISPONIBLE"},
            synchronize_session=False
        )
    )
    if filas_actualizadas == 0:
        db.rollback()
        return None
    db.commit()
    return obtener_asiento(
        db,
        id_asiento
    )
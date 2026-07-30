from sqlalchemy import Column, ForeignKey, Integer, String
from .database import Base

class Asiento(Base):
    __tablename__ = "asientos"

    id_asiento = Column(
        Integer,
        primary_key=True,
        index=True
    )
    id_evento = Column(
        Integer,
        ForeignKey("eventos.id_evento"),
        nullable=False
    )
    numero = Column(
        String(10),
        nullable=False
    )
    estado = Column(
        String(20),
        nullable=False,
        default="DISPONIBLE"
    )
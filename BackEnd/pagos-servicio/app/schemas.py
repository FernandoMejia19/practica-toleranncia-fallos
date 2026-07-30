from pydantic import BaseModel
from datetime import datetime

class PagoCreate(BaseModel):
    id_reserva: int
    monto: float

class PagoResponse(BaseModel):
    id_pago: int
    id_reserva: int
    monto: float
    estado: str
    fecha: datetime

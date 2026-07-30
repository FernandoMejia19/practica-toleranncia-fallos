from pydantic import BaseModel, EmailStr
from datetime import datetime

class NotificacionCreate(BaseModel):
    id_reserva: int
    correo: EmailStr

class NotificacionResponse(BaseModel):
    id_notificacion: int
    id_reserva: int
    correo: str
    estado: str
    fecha_envio: datetime

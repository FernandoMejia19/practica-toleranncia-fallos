from pydantic import BaseModel, EmailStr, Field


class ReservaCreate(BaseModel):
    id_asiento: int
    cliente: str
    correo: EmailStr
    monto: float = Field(gt=0)


class ReservaResponse(BaseModel):
    id_reserva: int
    id_asiento: int
    cliente: str
    correo: str
    estado: str
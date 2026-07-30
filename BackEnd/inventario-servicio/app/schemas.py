from pydantic import BaseModel


class AsientoResponse(BaseModel):
    id_asiento: int
    id_evento: int
    numero: str
    estado: str

    class Config:
        from_attributes = True


class ReservaAsientoResponse(BaseModel):
    id_asiento: int
    estado: str
    mensaje: str
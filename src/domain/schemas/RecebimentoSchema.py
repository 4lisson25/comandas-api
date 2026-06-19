from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class RecebimentoCreate(BaseModel):
    comandas_ids: List[int]

    cliente_id: Optional[int] = None
    funcionario_id: int

    desconto_valor: float = 0
    acrescimo_valor: float = 0


class RecebimentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    subtotal: float
    desconto_total: float
    acrescimo_total: float
    valor_final: float

    cliente_id: Optional[int] = None
    funcionario_id: int

    data_hora: datetime

class ComprovanteResponse(BaseModel):
    recebimento_id: int

    cliente: Optional[str] = None

    comandas: list

    subtotal: float

    desconto: float

    acrescimo: float

    valor_final: float

    data_hora: datetime

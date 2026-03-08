from pydantic import BaseModel

class Produto(BaseModel):
    id_produto: int = None
    nome: str
    descricao: str
    cpf: str
    foto: bytes
    valor_unitario: int
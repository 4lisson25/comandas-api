from fastapi import APIRouter
from src.domain.entities.Produto import Produto

router = APIRouter()

# Criar as rotas/endpoints: GET, POST, PUT, DELETE
@router.get("/produto/", tags=["Produto"], status_code=200)
def get_produtos():
    return {"msg": "produtos get todos executado"}

@router.get("/produto/{id}", tags=["Produto"], status_code=200)
def get_produto(id: int):
    return {"msg": "produto get um executado"}

@router.post("/produto/", tags=["Produto"], status_code=200)
def post_produto(corpo: Produto):
    return {"msg": "produto post executado", "nome": corpo.nome, "cpf": corpo.cpf, "telefone": corpo.telefone}

@router.put("/produto/{id}", tags=["Produto"], status_code=200)
def put_produto(id: int, corpo: Produto):
    return {"msg": "produto put executado", "id":id, "nome": corpo.nome, "cpf": corpo.cpf, "telefone": corpo.telefone}

@router.delete("/produto/{id}", tags=["Produto"], status_code=200)
def delete_produto(id: int):
    return {"msg": "produto delete executado", "id":id}
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Schemas
from domain.schemas.ClienteSchema import (
    ClienteCreate,
    ClienteResponse,
    ClienteUpdate
)
from domain.schemas.AuthSchema import ClienteAuth

# ORM
from infra.orm.ClienteModel import ClienteDB

# Database
from infra.database import get_db
from infra.dependencies import get_current_active_user, require_group

router = APIRouter()

# GET TODOS CLIENTES
@router.get(
    "/cliente/",
    response_model=List[ClienteResponse],
    tags=["Cliente"],
    status_code=status.HTTP_200_OK
)
async def get_cliente(
db: Session = Depends(get_db),
current_user: ClienteAuth = Depends(get_current_active_user)
):
    """Retorna todos os clientes - Protegido por autenticação"""    
    try:
        clientes = db.query(ClienteDB).all()
        return clientes

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar clientes: {str(e)}"
        )


# GET CLIENTE POR ID
@router.get(
    "/cliente/{id}",
    response_model=ClienteResponse,
    tags=["Cliente"],
    status_code=status.HTTP_200_OK
)
async def get_cliente(id: int, db: Session = Depends(get_db),
current_user: ClienteAuth = Depends(get_current_active_user)
):
    """Retorna um cliente específico pelo ID"""

    try:
        cliente = db.query(ClienteDB).filter(ClienteDB.id == id).first()

        if not cliente:
            raise HTTPException(
                status_code=404,
                detail="Cliente não encontrado"
            )

        return cliente

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar cliente: {str(e)}"
        )


# POST CLIENTE
@router.post(
    "/cliente/",
    response_model=ClienteResponse,
    tags=["Cliente"],
    status_code=status.HTTP_201_CREATED
)
async def post_cliente(cliente_data: ClienteCreate, db: Session = Depends(get_db),
current_user: ClienteAuth = Depends(require_group([1,3]))
):
    """Cria um novo cliente, precisa estar autenticado e grupo 1 ou 3"""

    try:

        # verificar CPF duplicado
        existing_cliente = db.query(ClienteDB).filter(
            ClienteDB.cpf == cliente_data.cpf
        ).first()

        if existing_cliente:
            raise HTTPException(
                status_code=400,
                detail="Já existe cliente com este CPF"
            )

        novo_cliente = ClienteDB(
            id=None,
            nome=cliente_data.nome,
            cpf=cliente_data.cpf,
            telefone=cliente_data.telefone
        )

        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente)

        return novo_cliente

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar cliente: {str(e)}"
        )


# PUT CLIENTE
@router.put(
    "/cliente/{id}",
    response_model=ClienteResponse,
    tags=["Cliente"],
    status_code=status.HTTP_200_OK
)
async def put_cliente(id: int, cliente_data: ClienteUpdate, db: Session = Depends(get_db),
current_user: ClienteAuth = Depends(require_group([1,3]))
):
    """Atualiza um cliente existente, precisa estar autenticado e em grupo 1 ou 3"""

    try:

        cliente = db.query(ClienteDB).filter(
            ClienteDB.id == id
        ).first()

        if not cliente:
            raise HTTPException(
                status_code=404,
                detail="Cliente não encontrado"
            )

        # verificar CPF duplicado
        if cliente_data.cpf and cliente_data.cpf != cliente.cpf:

            existing_cliente = db.query(ClienteDB).filter(
                ClienteDB.cpf == cliente_data.cpf
            ).first()

            if existing_cliente:
                raise HTTPException(
                    status_code=400,
                    detail="Já existe cliente com este CPF"
                )

        update_data = cliente_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(cliente, field, value)

        db.commit()
        db.refresh(cliente)

        return cliente

    except HTTPException:
        raise
    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar cliente: {str(e)}"
        )


# DELETE CLIENTE
@router.delete(
    "/cliente/{id}",
    tags=["Cliente"],
    status_code=status.HTTP_200_OK
)

async def delete_cliente(id: int, db: Session = Depends(get_db),
current_user: ClienteAuth = Depends(require_group([1]))
):
    """Remove um cliente, precisa autenticação e grupo 1"""
    try:

        cliente = db.query(ClienteDB).filter(
            ClienteDB.id == id
        ).first()

        if not cliente:
            raise HTTPException(
                status_code=404,
                detail="Cliente não encontrado"
            )

        db.delete(cliente)
        db.commit()

        return {"message": "Cliente deletado com sucesso"}
    
    except HTTPException:
        raise
    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar cliente: {str(e)}"
        )
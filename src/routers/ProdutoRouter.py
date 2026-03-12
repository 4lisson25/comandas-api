from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Schemas
from domain.schemas.ProdutoSchema import (
    ProdutoCreate,
    ProdutoUpdate,
    ProdutoResponse
)

# ORM
from infra.orm.ProdutoModel import ProdutoDB

# Database
from infra.database import get_db

router = APIRouter()

# GET TODOS PRODUTOS
@router.get(
    "/produto/",
    response_model=List[ProdutoResponse],
    tags=["Produto"],
    status_code=status.HTTP_200_OK
)
async def get_produtos(db: Session = Depends(get_db)):
    try:
        produtos = db.query(ProdutoDB).all()
        return produtos

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar produtos: {str(e)}"
        )


# GET PRODUTO POR ID
@router.get(
    "/produto/{id}",
    response_model=ProdutoResponse,
    tags=["Produto"],
    status_code=status.HTTP_200_OK
)
async def get_produto(id: int, db: Session = Depends(get_db)):

    try:
        produto = db.query(ProdutoDB).filter(
            ProdutoDB.id == id
        ).first()

        if not produto:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado"
            )

        return produto

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar produto: {str(e)}"
        )


# POST PRODUTO
@router.post(
    "/produto/",
    response_model=ProdutoResponse,
    tags=["Produto"],
    status_code=status.HTTP_201_CREATED
)
async def post_produto(produto_data: ProdutoCreate, db: Session = Depends(get_db)):

    try:

        novo_produto = ProdutoDB(
            id=None,
            nome=produto_data.nome,
            descricao=produto_data.descricao,
            foto=produto_data.foto,
            valor_unitario=produto_data.valor_unitario
        )

        db.add(novo_produto)
        db.commit()
        db.refresh(novo_produto)

        return novo_produto

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar produto: {str(e)}"
        )


# PUT PRODUTO
@router.put(
    "/produto/{id}",
    response_model=ProdutoResponse,
    tags=["Produto"],
    status_code=status.HTTP_200_OK
)
async def put_produto(id: int, produto_data: ProdutoUpdate, db: Session = Depends(get_db)):

    try:

        produto = db.query(ProdutoDB).filter(
            ProdutoDB.id == id
        ).first()

        if not produto:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado"
            )

        update_data = produto_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(produto, field, value)

        db.commit()
        db.refresh(produto)

        return produto

    except HTTPException:
        raise
    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar produto: {str(e)}"
        )


# DELETE PRODUTO
@router.delete(
    "/produto/{id}",
    tags=["Produto"],
    status_code=status.HTTP_200_OK
)
async def delete_produto(id: int, db: Session = Depends(get_db)):

    try:

        produto = db.query(ProdutoDB).filter(
            ProdutoDB.id == id
        ).first()

        if not produto:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado"
            )

        db.delete(produto)
        db.commit()

        return {"message": "Produto excluído com sucesso"}

    except HTTPException:
        raise
    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar produto: {str(e)}"
        )
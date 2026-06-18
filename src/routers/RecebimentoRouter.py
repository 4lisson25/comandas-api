from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from domain.schemas.RecebimentoSchema import (
    RecebimentoCreate,
    RecebimentoResponse,
    ComprovanteResponse
)

from domain.schemas.AuthSchema import FuncionarioAuth

from infra.orm.RecebimentoModel import RecebimentoDB

from infra.orm.ComandaModel import (
    ComandaDB,
    ComandaProdutoDB
)

from infra.orm.ProdutoModel import ProdutoDB

from infra.orm.ClienteModel import ClienteDB
from infra.orm.FuncionarioModel import FuncionarioDB

from infra.database import get_async_db
from infra.dependencies import (
    get_current_active_user,
    require_group
)

from infra.rate_limit import limiter
from services.AuditoriaService import AuditoriaService

router = APIRouter()


# ==================================================
# DASHBOARD
# ==================================================

@router.get(
    "/recebimento/dashboard",
    tags=["Recebimento"],
    summary="Listar comandas abertas para recebimento"
)
@limiter.limit("moderate")
async def dashboard_recebimento(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)
):
    try:

        result = await db.execute(
            select(
                ComandaDB,
                ClienteDB
            )
            .outerjoin(
                ClienteDB,
                ClienteDB.id == ComandaDB.cliente_id
            )
            .where(
                ComandaDB.status == 0
            )
        )

        comandas = result.all()

        retorno = []

        for comanda, cliente in comandas:

            produtos_result = await db.execute(
                select(ComandaProdutoDB)
                .where(
                    ComandaProdutoDB.comanda_id == comanda.id
                )
            )

            produtos = produtos_result.scalars().all()

            total = sum(
                item.quantidade * item.valor_unitario
                for item in produtos
            )

            retorno.append({
                "id": comanda.id,
                "comanda": comanda.comanda,
                "cliente_id": comanda.cliente_id,
                "cliente": cliente.nome if cliente else None,
                "status": comanda.status,
                "total": total,
                "data_hora": comanda.data_hora
            })

        return retorno

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar dashboard: {str(e)}"
        )


# ==================================================
# DETALHE DAS COMANDAS
# ==================================================

@router.get(
    "/recebimento/comandas/detalhe",
    tags=["Recebimento"],
    summary="Detalhar comandas para conferência"
)
@limiter.limit("moderate")
async def detalhe_comandas(
    comandas: str,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)
):
    try:

        ids = [int(x.strip()) for x in comandas.split(",")]

        retorno = []

        for comanda_id in ids:

            result = await db.execute(
                select(ComandaDB)
                .where(ComandaDB.id == comanda_id)
            )

            comanda = result.scalar_one_or_none()

            if not comanda:
                continue

            produtos_result = await db.execute(
                select(ComandaProdutoDB)
                .where(
                    ComandaProdutoDB.comanda_id == comanda.id
                )
            )

            produtos = produtos_result.scalars().all()

            total = 0

            itens = []

            for item in produtos:

                subtotal_item = (
                    float(item.quantidade) *
                    float(item.valor_unitario)
                )

                total += subtotal_item

                itens.append({
                    "produto_id": item.produto_id,
                    "quantidade": item.quantidade,
                    "valor_unitario": item.valor_unitario,
                    "subtotal": subtotal_item
                })

            retorno.append({
                "id": comanda.id,
                "comanda": comanda.comanda,
                "status": comanda.status,
                "produtos": itens,
                "total": total
            })

        return retorno

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar detalhes: {str(e)}"
        )


# ==================================================
# RECEBIMENTO
# ==================================================

@router.post(
    "/recebimento/",
    response_model=RecebimentoResponse,
    tags=["Recebimento"],
    summary="Receber uma ou mais comandas"
)
@limiter.limit("restrictive")
async def receber_comandas(
    recebimento: RecebimentoCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)
):
    try:

        subtotal = 0

        for comanda_id in recebimento.comandas_ids:

            result = await db.execute(
                select(ComandaDB)
                .where(
                    ComandaDB.id == comanda_id
                )
            )

            comanda = result.scalar_one_or_none()

            if not comanda:
                raise HTTPException(
                    status_code=404,
                    detail=f"Comanda {comanda_id} não encontrada"
                )

            if comanda.status != 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Comanda {comanda_id} não está aberta"
                )

            produtos_result = await db.execute(
                select(ComandaProdutoDB)
                .where(
                    ComandaProdutoDB.comanda_id == comanda_id
                )
            )

            produtos = produtos_result.scalars().all()

            for item in produtos:

                subtotal += (
                    float(item.quantidade) *
                    float(item.valor_unitario)
                )

            comanda.status = 1

            if recebimento.cliente_id:
                comanda.cliente_id = recebimento.cliente_id

        valor_final = (
            float(subtotal)
            - float(recebimento.desconto_valor)
            + float(recebimento.acrescimo_valor)
        )

        novo_recebimento = RecebimentoDB(
            subtotal=subtotal,
            desconto_total=recebimento.desconto_valor,
            acrescimo_total=recebimento.acrescimo_valor,
            valor_final=valor_final,
            cliente_id=recebimento.cliente_id,
            funcionario_id=recebimento.funcionario_id
        )

        db.add(novo_recebimento)

        await db.commit()
        await db.refresh(novo_recebimento)

        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="RECEBIMENTO",
            recurso="COMANDA",
            dados_novos={
                "comandas_ids": recebimento.comandas_ids,
                "subtotal": subtotal,
                "desconto": recebimento.desconto_valor,
                "acrescimo": recebimento.acrescimo_valor,
                "valor_final": valor_final
            },
            request=request
        )

        return RecebimentoResponse(
            id=novo_recebimento.id,
            subtotal=subtotal,
            desconto_total=recebimento.desconto_valor,
            acrescimo_total=recebimento.acrescimo_valor,
            valor_final=valor_final,
            cliente_id=recebimento.cliente_id,
            funcionario_id=recebimento.funcionario_id,
            data_hora=datetime.now()
        )

    except HTTPException:
        raise

    except Exception as e:

        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao realizar recebimento: {str(e)}"
        )


# ==================================================
# COMPROVANTE
# ==================================================

@router.get(
    "/recebimento/comprovante",
    response_model=ComprovanteResponse,
    tags=["Recebimento"],
    summary="Gerar comprovante"
)
@limiter.limit("moderate")
async def gerar_comprovante(
    comandas: str,
    desconto: float = 0,
    acrescimo: float = 0,
    request: Request = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)
):
    try:

        ids = [int(x.strip()) for x in comandas.split(",")]

        lista_comandas = []

        subtotal = 0

        for comanda_id in ids:

            result = await db.execute(
                select(ComandaDB)
                .where(
                    ComandaDB.id == comanda_id
                )
            )

            comanda = result.scalar_one_or_none()

            if not comanda:
                continue

            produtos_result = await db.execute(
                select(ComandaProdutoDB)
                .where(
                    ComandaProdutoDB.comanda_id == comanda.id
                )
            )

            produtos = produtos_result.scalars().all()

            total_comanda = sum(
                float(item.quantidade) * float(item.valor_unitario)
                for item in produtos
            )

            subtotal += total_comanda

            itens = []

            for item in produtos:

                produto_result = await db.execute(
                    select(ProdutoDB)
                    .where(ProdutoDB.id == item.produto_id)
                )

                produto = produto_result.scalar_one_or_none()

                itens.append({
                    "nome": produto.nome if produto else "Produto",
                    "quantidade": item.quantidade,
                    "valor_unitario": item.valor_unitario
                })

            lista_comandas.append({
                "id": comanda.id,
                "comanda": comanda.comanda,
                "total": total_comanda,
                "produtos": itens
            })

        valor_final = (
            float(subtotal)
            - float(desconto)
            + float(acrescimo)
        )

        return ComprovanteResponse(
            recebimento_id=0,
            comandas=lista_comandas,
            subtotal=subtotal,
            desconto=desconto,
            acrescimo=acrescimo,
            valor_final=valor_final,
            data_hora=datetime.now()
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar comprovante: {str(e)}"
        )
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from infra import database


class RecebimentoDB(database.Base):
    __tablename__ = "tb_recebimento"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True
    )

    subtotal = Column(Float, nullable=False)

    desconto_total = Column(
        Float,
        nullable=False,
        default=0
    )

    acrescimo_total = Column(
        Float,
        nullable=False,
        default=0
    )

    valor_final = Column(
        Float,
        nullable=False
    )

    cliente_id = Column(
        Integer,
        ForeignKey("tb_cliente.id"),
        nullable=True
    )

    funcionario_id = Column(
        Integer,
        ForeignKey("tb_funcionario.id"),
        nullable=False
    )

    data_hora = Column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    cliente = relationship("ClienteDB")

    funcionario = relationship("FuncionarioDB")
"""Modelos de entrada, persistência e saída usados pela aplicação."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    """Dados aceitos para criar uma solicitação de pagamento."""

    # Campos extras costumam indicar erro do cliente e são rejeitados.
    model_config = ConfigDict(extra="forbid")

    card_token: str = Field(pattern=r"^tok_[A-Za-z0-9_-]{8,80}$")
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Literal["BRL"] = "BRL"


class Payment(BaseModel):
    """Representa os dados recuperados do PostgreSQL."""

    # O identificador conecta o POST às consultas GET posteriores.
    id: uuid.UUID
    card_token: str
    amount: Decimal
    currency: str
    created_at: datetime


class PaymentResponse(BaseModel):
    """Representa a situação apresentada ao cliente."""

    id: uuid.UUID
    amount: str = Field(pattern=r"^\d+\.\d{2}$")
    currency: Literal["BRL"]
    status: Literal["processando", "aprovado"]
    created_at: datetime

    @classmethod
    def from_record(
        cls,
        payment: Payment,
        delay_seconds: int,
    ) -> "PaymentResponse":
        """Cria a resposta e calcula o status a partir da data de criação."""

        # O status é derivado; ele nunca precisa ser escrito no repositório.
        elapsed_seconds = (
            datetime.now(payment.created_at.tzinfo) - payment.created_at
        ).total_seconds()
        status = "aprovado" if elapsed_seconds >= delay_seconds else "processando"

        return cls(
            id=payment.id,
            amount=f"{payment.amount:.2f}",
            currency=payment.currency,
            status=status,
            created_at=payment.created_at,
        )

    def with_current_status(self, delay_seconds: int) -> "PaymentResponse":
        """Recalcula o status de uma resposta que veio do cache."""

        # Repetimos o cálculo porque o tempo continua passando durante o TTL.
        elapsed_seconds = (
            datetime.now(self.created_at.tzinfo) - self.created_at
        ).total_seconds()
        status = "aprovado" if elapsed_seconds >= delay_seconds else "processando"
        return self.model_copy(update={"status": status})

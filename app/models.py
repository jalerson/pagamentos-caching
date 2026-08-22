"""Modelo usado pela aplicação para representar um pagamento persistido."""

from datetime import datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel


class Payment(BaseModel):
    """Representa os dados recuperados do PostgreSQL."""

    # O identificador conecta o POST às consultas GET posteriores.
    id: uuid.UUID
    card_token: str
    amount: Decimal
    currency: str
    created_at: datetime

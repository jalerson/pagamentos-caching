"""Persistência das solicitações de pagamento no PostgreSQL."""

import uuid

import asyncpg

from .models import Payment, PaymentCreate


class PaymentsRepository:
    """Encapsula as consultas SQL relacionadas aos pagamentos."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        # O pool reutiliza conexões entre diferentes requisições HTTP.
        self._pool = pool

    @classmethod
    async def connect(cls, database_url: str) -> "PaymentsRepository":
        """Abre o pool de conexões e devolve o repositório pronto para uso."""

        pool = await asyncpg.create_pool(database_url)
        return cls(pool)

    async def close(self) -> None:
        """Fecha todas as conexões quando a aplicação é encerrada."""

        await self._pool.close()

    async def create(self, command: PaymentCreate) -> Payment:
        """Insere uma solicitação e devolve os dados gravados pelo banco."""

        row = await self._pool.fetchrow(
            """
            INSERT INTO payments (id, card_token, amount, currency, created_at)
            VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            RETURNING id, card_token, amount, currency, created_at
            """,
            uuid.uuid4(),
            command.card_token,
            command.amount,
            command.currency,
        )
        # INSERT ... RETURNING sempre devolve uma linha quando a inserção funciona.
        assert row is not None
        return self._to_payment(row)

    async def find(self, payment_id: uuid.UUID) -> Payment | None:
        """Devolve o pagamento encontrado ou None quando o UUID não existe."""

        row = await self._pool.fetchrow(
            """
            SELECT id, card_token, amount, currency, created_at
            FROM payments
            WHERE id = $1
            """,
            payment_id,
        )
        return self._to_payment(row) if row is not None else None

    @staticmethod
    def _to_payment(row: asyncpg.Record) -> Payment:
        """Converte a linha do PostgreSQL para o modelo usado pela aplicação."""

        return Payment(**dict(row))

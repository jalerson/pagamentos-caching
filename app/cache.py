"""Acesso ao cache Redis usado nas consultas de pagamentos."""

import uuid

from redis.asyncio import Redis

from .models import PaymentResponse


class PaymentCache:
    """Guarda respostas de pagamentos no Redis por um tempo limitado."""

    def __init__(self, redis: Redis, ttl_seconds: int) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def key(payment_id: uuid.UUID) -> str:
        """Monta a chave usada para localizar um pagamento no Redis."""

        return f"pagamento:{payment_id}"

    async def get(self, payment_id: uuid.UUID) -> PaymentResponse | None:
        """Devolve o pagamento armazenado ou None quando a chave não existe."""

        # Redis devolve bytes ou None quando a chave expirou ou nunca existiu.
        value = await self.redis.get(self.key(payment_id))
        if value is None:
            return None
        return PaymentResponse.model_validate_json(value)

    async def set(self, payment: PaymentResponse) -> None:
        """Salva o pagamento e define seu TTL em segundos."""

        # ex configura a expiração junto com a gravação da chave.
        await self.redis.set(
            self.key(payment.id),
            payment.model_dump_json(),
            ex=self.ttl_seconds,
        )

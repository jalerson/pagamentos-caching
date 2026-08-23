"""Testes do cache sem depender de um servidor Redis real."""

import asyncio
from datetime import datetime, timedelta, timezone
import uuid

from app.cache import PaymentCache
from app.models import PaymentResponse


class FakeRedis:
    """Implementa somente os métodos Redis usados por PaymentCache."""

    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.expirations: dict[str, int] = {}

    async def get(self, key: str) -> bytes | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int) -> None:
        self.values[key] = value.encode("utf-8")
        self.expirations[key] = ex


def test_cache_round_trip_uses_configured_ttl() -> None:
    """Confirma que a resposta é salva e recuperada com o TTL informado."""

    async def scenario() -> None:
        redis = FakeRedis()
        cache = PaymentCache(redis, ttl_seconds=15)  # type: ignore[arg-type]
        payment_id = uuid.uuid4()
        payment = PaymentResponse(
            id=payment_id,
            amount="249.90",
            currency="BRL",
            status="processando",
            created_at=datetime.now(timezone.utc),
        )

        assert await cache.get(payment_id) is None
        await cache.set(payment)
        assert redis.expirations[cache.key(payment_id)] == 15
        assert await cache.get(payment_id) == payment

    asyncio.run(scenario())


def test_cached_payment_becomes_approved_after_delay() -> None:
    """Confirma que o status também é recalculado para dados em cache."""

    payment = PaymentResponse(
        id=uuid.uuid4(),
        amount="249.90",
        currency="BRL",
        status="processando",
        created_at=datetime.now(timezone.utc) - timedelta(seconds=31),
    )

    assert payment.with_current_status(delay_seconds=30).status == "aprovado"

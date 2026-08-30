"""Testes diretos dos detalhes da resposta HTTP de criação."""

import asyncio
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import Response

from app.api import get_payment, request_payment
from app.models import PaymentCreate, PaymentResponse
from app.repository import PaymentsRepository
from app.settings import settings


class CacheWithStalePayment:
    """Simula um HIT com uma resposta que já ficou desatualizada."""

    def __init__(self, payment: PaymentResponse) -> None:
        self.payment = payment

    async def get(self, payment_id: uuid.UUID) -> PaymentResponse | None:
        return self.payment if payment_id == self.payment.id else None

    async def set(self, payment: PaymentResponse) -> None:
        raise AssertionError("Um HIT não deve atualizar o cache")


class RepositoryThatMustNotBeUsed:
    """Falha o teste se o endpoint consultar o banco durante um HIT."""

    async def find(self, payment_id: uuid.UUID) -> None:
        raise AssertionError("Um HIT não deve consultar o PostgreSQL")


def test_creation_does_not_suggest_retry_interval() -> None:
    """Retry-After não faz parte do contrato solicitado para a API."""

    async def scenario() -> None:
        repository = await PaymentsRepository.connect(settings.database_url)
        try:
            response = Response()
            payment = await request_payment(
                PaymentCreate(
                    card_token="tok_demo_visa_4242",
                    amount="249.90",
                    currency="BRL",
                ),
                response,
                repository,
            )

            assert payment.status == "processando"
            assert "location" in response.headers
            assert "retry-after" not in response.headers
        finally:
            await repository.close()

    asyncio.run(scenario())


def test_cache_hit_can_return_stale_status() -> None:
    """Um HIT devolve a cópia armazenada mesmo após o tempo de aprovação."""

    async def scenario() -> None:
        payment_id = uuid.uuid4()
        cached_payment = PaymentResponse(
            id=payment_id,
            amount="249.90",
            currency="BRL",
            status="processando",
            created_at=datetime.now(timezone.utc) - timedelta(seconds=31),
        )
        response = Response()

        result = await get_payment(
            payment_id,
            response,
            CacheWithStalePayment(cached_payment),  # type: ignore[arg-type]
            RepositoryThatMustNotBeUsed(),  # type: ignore[arg-type]
        )

        assert result == cached_payment
        assert result.status == "processando"
        assert response.headers["X-Cache"] == "HIT"

    asyncio.run(scenario())

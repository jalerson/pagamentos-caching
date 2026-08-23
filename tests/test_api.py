"""Testes diretos dos detalhes da resposta HTTP de criação."""

import asyncio

from fastapi import Response

from app.api import request_payment
from app.repository import PaymentsRepository
from app.models import PaymentCreate
from app.settings import settings


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

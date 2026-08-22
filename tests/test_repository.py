"""Testes da persistência de pagamentos no PostgreSQL."""

import asyncio
import uuid

from app.repository import PaymentsRepository
from app.schemas import PaymentCreate
from app.settings import settings


def test_creates_and_finds_payment_in_database() -> None:
    """O repositório deve gravar e recuperar o pagamento pelo UUID."""

    async def scenario() -> None:
        repository = await PaymentsRepository.connect(settings.database_url)
        try:
            command = PaymentCreate(
                card_token="tok_demo_visa_4242",
                amount="249.90",
                currency="BRL",
            )

            payment = await repository.create(command)

            assert await repository.find(payment.id) == payment
            assert await repository.find(uuid.uuid4()) is None
        finally:
            await repository.close()

    asyncio.run(scenario())

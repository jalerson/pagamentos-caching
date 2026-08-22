from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

import pytest
from pydantic import ValidationError

from app.models import Payment
from app.schemas import PaymentCreate, PaymentResponse


def test_accepts_tokenized_payment() -> None:
    command = PaymentCreate(
        card_token="tok_demo_visa_4242",
        amount="249.90",
        currency="BRL",
    )
    assert command.amount == Decimal("249.90")


def test_rejects_card_number_negative_amount_and_extra_fields() -> None:
    with pytest.raises(ValidationError) as error:
        PaymentCreate.model_validate(
            {
                "card_token": "4242 4242 4242 4242",
                "amount": "-10.00",
                "currency": "USD",
                "campo_extra": True,
            }
        )
    assert len(error.value.errors()) == 4


def test_derives_status_from_creation_time() -> None:
    """O repositório não precisa armazenar o status do pagamento."""

    recent = Payment(
        id=uuid.uuid4(),
        card_token="tok_demo_visa_4242",
        amount=Decimal("249.90"),
        currency="BRL",
        created_at=datetime.now(timezone.utc),
    )
    old = Payment(
        id=uuid.uuid4(),
        card_token="tok_demo_visa_4242",
        amount=Decimal("249.90"),
        currency="BRL",
        created_at=datetime.now(timezone.utc) - timedelta(seconds=31),
    )

    assert PaymentResponse.from_record(recent, 30).status == "processando"
    assert PaymentResponse.from_record(old, 30).status == "aprovado"


def test_does_not_store_status_in_payment_model() -> None:
    """O status pertence à resposta calculada, não ao objeto persistido."""

    assert "status" not in Payment.model_fields

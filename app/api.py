"""Define os 2 endpoints HTTP da aplicação."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from .cache import PaymentCache
from .repository import PaymentsRepository
from .models import PaymentCreate, PaymentResponse
from .settings import settings


router = APIRouter()


def get_cache(request: Request) -> PaymentCache:
    """Obtém o cache criado durante a inicialização da aplicação."""

    return request.app.state.cache


def get_payments_repository(request: Request) -> PaymentsRepository:
    """Obtém o repositório criado durante a inicialização da aplicação."""

    return request.app.state.payments_repository


@router.post(
    "/pagamentos",
    response_model=PaymentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={202: {"description": "Pagamento aceito para processamento"}},
)
async def request_payment(
    command: PaymentCreate,
    response: Response,
    repository: PaymentsRepository = Depends(get_payments_repository),
) -> PaymentResponse:
    """Salva a solicitação e responde imediatamente com processando."""

    # O repositório cria o UUID e grava o pagamento no PostgreSQL.
    payment = await repository.create(command)
    response.headers["Location"] = f"/pagamentos/{payment.id}"
    return PaymentResponse.from_record(payment, settings.payment_delay_seconds)


@router.get(
    "/pagamentos/{payment_id}",
    response_model=PaymentResponse,
    responses={404: {"description": "Pagamento não encontrado"}},
)
async def get_payment(
    payment_id: uuid.UUID,
    response: Response,
    cache: PaymentCache = Depends(get_cache),
    repository: PaymentsRepository = Depends(get_payments_repository),
) -> PaymentResponse:
    """Consulta o cache e, quando necessário, consulta o PostgreSQL."""

    cached_payment = await cache.get(payment_id)
    if cached_payment is not None:
        # Em um HIT, devolvemos exatamente a cópia armazenada. Ela pode ficar
        # desatualizada até o TTL expirar, que é uma desvantagem do cache.
        response.headers["X-Cache"] = "HIT"
        return cached_payment

    # Em um MISS, consultamos o PostgreSQL, que é a fonte persistente.
    payment = await repository.find(payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado",
        )

    current_payment = PaymentResponse.from_record(
        payment,
        settings.payment_delay_seconds,
    )
    await cache.set(current_payment)
    response.headers["X-Cache"] = "MISS"
    return current_payment

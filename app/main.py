"""Cria e configura a aplicação FastAPI."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from .api import router
from .cache import PaymentCache
from .repository import PaymentsRepository
from .settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Abre os recursos na inicialização e fecha no encerramento."""

    # PostgreSQL é a fonte persistente das solicitações de pagamento.
    repository = await PaymentsRepository.connect(settings.database_url)
    app.state.payments_repository = repository

    # O cliente Redis é criado 1 vez e compartilhado pelas requisições.
    redis = Redis.from_url(settings.redis_url, decode_responses=False)
    try:
        await redis.ping()
        app.state.cache = PaymentCache(redis, settings.payment_cache_ttl_seconds)

        yield

    finally:
        await redis.aclose()
        await repository.close()


app = FastAPI(
    title="Pagamentos assíncronos com caching",
    version="1.0.0",
    description="API didática com PostgreSQL, espera simulada e cache Redis.",
    lifespan=lifespan,
)

# Os endpoints ficam em api.py; main.py cuida apenas da composição.
app.include_router(router)

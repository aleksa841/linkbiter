from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from redis import asyncio as aioredis

from app.auth.users import fastapi_users, auth_backend
from app.api.router import router
from app.auth.schemas import UserRead, UserCreate
from app.db.config import REDIS_URL
from app.scheduler import scheduler, delete_expired_links

import uvicorn

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:

    # redis для кэширования
    redis = aioredis.from_url(REDIS_URL)
    FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')

    # scheduler для удаления expired_links
    scheduler.add_job(delete_expired_links, 'interval', minutes=2)
    scheduler.start()

    try:
        yield
    finally:
        scheduler.shutdown()
        await redis.close()

app = FastAPI(lifespan=lifespan)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix='/auth',
    tags=['auth']
    )

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix='/auth',
    tags=['auth'],
)

app.include_router(router)

if __name__ == '__main__':

    uvicorn.run(
        'app.main:app',
        host='127.0.0.1',
        port=8000,
        reload=True,
        log_level='info'
    )

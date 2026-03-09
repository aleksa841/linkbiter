from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import RedirectResponse
from fastapi_cache import FastAPICache
import secrets

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.links import LinkCreate, LinkCreateResponse, LinkStats, LinkUpdate
from app.db.session import get_async_session
from app.db.models import Link
from app.auth.db import User
from app.auth.users import fastapi_users
from app.redis_helper import clear_cache, get_cached_data, CLICKS_THRESHOLD, CACHE_TTL
from app.api.config import SHORT_CODE_TTL, BASE_URL

from datetime import datetime, timedelta, timezone

from pydantic import HttpUrl
from typing import Optional

router = APIRouter(
    prefix='/links',
    tags=['Links']
)


@router.post('/shorten', response_model=LinkCreateResponse, summary='Cоздать короткую ссылку')
async def create_short_link(
    payload: LinkCreate, 
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
    session: AsyncSession = Depends(get_async_session)
):
    # читаем алиас или создаем на бэке. Для примера генерим токен длиной 6
    short_code = payload.custom_alias or secrets.token_urlsafe(6)

    result = await session.execute(
        select(Link).where(Link.short_code == short_code)
    )

    # проверяем, что такого короткого кода нет в БД, если есть - возвращаем ошибку
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=f'{short_code} уже существует. Пожалуйста, выберите другой короткий код'
        ) 

    short_url = BASE_URL + short_code

    now = datetime.now(timezone.utc)
    expires_at = payload.expires_at or (
        now + timedelta(days=SHORT_CODE_TTL)
    )

    # формируем ответ и сохраняем в БД
    response = LinkCreateResponse(
        url=payload.url,
        short_code=short_code,
        short_url=short_url,
        expires_at=expires_at
    )

    link = Link(
        short_code=short_code,
        short_url=short_url,
        original_url=str(payload.url),
        expires_at=expires_at,
        created_by=user.id if user else None,
    )

    try:
        session.add(link)
        await session.commit()
        return response
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Ошибка при сохранении ссылки'
        ) from e

@router.get('/{short_code}/stats', response_model=LinkStats, summary='Получить статистику ссылки')
async def get_link_stats(
    short_code: str,
    session: AsyncSession = Depends(get_async_session)
):
    
    # сначала пробуем получить данные из кэша
    redis = FastAPICache.get_backend().redis
    cache_key = f'stats:{short_code}'

    cached_data = await get_cached_data(redis, cache_key, LinkStats)
    if cached_data:
        return cached_data

    result = await session.execute(
        select(Link).where(Link.short_code == short_code)
    )

    link = result.scalar_one_or_none()

    if link is None:
        raise HTTPException(
            status_code=404,
            detail='Ссылка не найдена'
        )
    
    elif link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=410,
            detail='Ссылка не действительна'
        )
    
    response = LinkStats(
        url=link.original_url,
        created_at=link.created_at,
        clicks=link.clicks,
        last_used_at=link.last_used_at
    )

    if link.clicks >= CLICKS_THRESHOLD:
        # сохраняем в кэш, если кликов больше 5, время хранения кэша - 5 минут для примера
        await redis.setex(cache_key, CACHE_TTL, response.model_dump_json())
            
    return response

@router.get(f'/search', response_model=LinkCreateResponse, summary='Найти ссылку по оригинальному URL')
async def search_link(
    original_url: HttpUrl,
    session: AsyncSession = Depends(get_async_session)
):
    
    # сначала пробуем получить данные из кэша
    redis = FastAPICache.get_backend().redis
    cache_key = f'search:{str(original_url)}'

    cached_data = await get_cached_data(redis, cache_key, LinkCreateResponse)
    if cached_data:
        return cached_data

    result = await session.execute(
        select(Link).where(Link.original_url == str(original_url))
    )

    link = result.scalars().first()

    if link is None:
        raise HTTPException(
            status_code=404,
            detail='Ссылка не найдена'
        )
    
    elif link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=410,
            detail='Ссылка не действительна'
        )
    
    response = LinkCreateResponse(
        url=link.original_url,
        short_code=link.short_code,
        short_url=link.short_url,
        expires_at=link.expires_at
    )

    if link.clicks >= CLICKS_THRESHOLD:
        # сохраняем в кэше, если кликов больше 5, время хранения 5 минут
        await redis.setex(cache_key, CACHE_TTL, response.model_dump_json())
    
    return response
    
@router.get('/{short_code}', summary='Перейти на сайт')
async def redirect(
    short_code: str,
    session: AsyncSession = Depends(get_async_session)
):
    
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Link).where(Link.short_code == short_code)
    )

    link = result.scalar_one_or_none()

    if link is None:
        raise HTTPException(
            status_code=404,
            detail='Ссылка не найдена'
        )
    
    elif link.expires_at and link.expires_at < now:
        raise HTTPException(
            status_code=410,
            detail='Ссылка не действительна'
        )
    
    # при каждом переходе увеличиваем счетчик кликов и обновляем время последнего использования
    # не кэшируем данные из-за счетчика кликов и времени последнего использования
    link.clicks += 1
    link.last_used_at = now
    await session.commit()
    
    return RedirectResponse(
        url=link.original_url,
        # временный редирект
        status_code=307
    )

@router.put('/{short_code}', summary='Обновить короткую ссылку')
async def update_link(
    short_code: str,
    payload: LinkUpdate,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session)
):

    result = await session.execute(
        select(Link).where(Link.short_code == short_code)
    )

    link = result.scalar_one_or_none()

    if user.id != link.created_by:
        raise HTTPException(
            status_code=403,
            detail='Вы не можете изменить эту ссылку'
        )

    if link is None:
        raise HTTPException(
            status_code=404,
            detail='Ссылка не найдена'
        )
    
    new_short_code = payload.new_short_code
    result = await session.execute(
        select(Link).where(Link.short_code == new_short_code)
    )

    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=f'{new_short_code} уже существует. Пожалуйста, выберите другой короткий код'
        ) 
    
    link.short_code = new_short_code
    link.short_url = BASE_URL + new_short_code
    
    response = LinkCreateResponse(
        url=link.original_url,
        short_code=link.short_code,
        short_url=link.short_url,
        expires_at=link.expires_at
    )

    await session.commit()
    await session.refresh(link)

    # чистим кэш
    await clear_cache(short_code, link.original_url)

    return response

@router.delete('/{short_code}', summary='Удалить короткую ссылку')
async def delete_link(
    short_code: str,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session)
):

    result = await session.execute(
        select(Link).where(Link.short_code == short_code)
    )

    link = result.scalar_one_or_none()

    if user.id != link.created_by:
        raise HTTPException(
            status_code=403,
            detail='Вы не можете удалить эту ссылку'
        )

    if link is None:
        raise HTTPException(
            status_code=404,
            detail='Ссылка не найдена'
        )

    await session.delete(link)
    await session.commit()

    # чистим кэш
    await clear_cache(short_code, link.original_url)

    return {'detail': 'Ссылка успешно удалена'}
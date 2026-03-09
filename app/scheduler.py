from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, delete
from app.db.session import async_session_maker
from app.db.models import Link
from app.redis_helper import clear_cache

from datetime import datetime, timezone

scheduler = AsyncIOScheduler()

# удаляем ссылки, у которых закончился срок действия
async def delete_expired_links():
    async with async_session_maker() as session:

        result = await session.execute(
            select(Link).where(Link.expires_at < datetime.now(timezone.utc))
        )

        expired_links = result.scalars().all()

        # удаляем из БД и кэша
        for link in expired_links:
            await clear_cache(link.short_code, link.original_url)
            await session.delete(link)

        await session.commit()
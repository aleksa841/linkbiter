from fastapi_cache import FastAPICache

# параметры для кеширования
CLICKS_THRESHOLD = 5
CACHE_TTL = 300

async def clear_cache(short_code: str, original_url: str):
    redis = FastAPICache.get_backend().redis

    await redis.delete(
        f'stats:{short_code}',
        f'search:{original_url}'
    )

async def get_cached_data(redis, cache_key: str, model):
   cached_data = await redis.get(cache_key)
   
   if cached_data:
        return model.model_validate_json(cached_data.decode())
   
   return None
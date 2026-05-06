from functools import lru_cache

import redis
from django.conf import settings


@lru_cache(maxsize=1)
def get_client() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)

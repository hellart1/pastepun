from celery import shared_task
from django.core.cache import cache
from django.db.models import F
from django_redis import get_redis_connection

from paste.models import Paste

# scan 1000 views per 1 task
SCAN_COUNT = 1000
# lock lifetime
LOCK_TTL = 30

@shared_task(ignore_result=True)
def flush_paste_views():
    redis = get_redis_connection("default")

    lock = redis.set(
        'views:scan:lock',
        1,
        nx=True,
        ex=LOCK_TTL,
    )
    if not lock:
        return

    try:
        cursor = redis.get('views:scan:cursor')
        cursor = int(cursor) if cursor else 0

        cursor, keys = redis.scan(
            cursor=cursor,
            match='counter:paste:*:views_pending',
            count=SCAN_COUNT
        )

        for key in keys:
            paste_hash = key.decode().split(':')[2]

            delta = redis.getset(key, 0)
            if not delta:
                continue

            delta = int(delta)

            redis.incrby(f'counter:paste:{paste_hash}:views_total', delta)

            Paste.objects.filter(hash=paste_hash).update(
                views=F('views') + delta
            )

            if cursor == 0:
                redis.delete('views:scan:cursor')
            else:
                redis.set('views:scan:cursor', cursor)
    finally:
        redis.delete('views:scan:lock')

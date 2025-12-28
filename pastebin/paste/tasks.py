from celery import shared_task
from django.core.cache import cache
from django.db.models import F
from django_redis import get_redis_connection

from paste.models import Paste


@shared_task(ignore_result=True)
def flush_paste_views():
    redis = get_redis_connection("default")

    for key in redis.scan_iter('paste:*:views_pending'):
        paste_hash = key.decode().split(':')[1]

        delta = redis.getset(key, 0)

        if delta is None:
            continue

        delta = int(delta)

        redis.incrby(f'paste:{paste_hash}:views_total', delta)

        Paste.objects.filter(hash=paste_hash).update(
            views=F('views') + delta
        )

    # key = f"paste:{paste_hash}:views"
    # views = redis.getset(key, 0)
    #
    # print(f"views: {int(views)}")
    # if views is None:
    #     return
    #
    # views = int(views)
    #
    # Paste.objects.filter(hash=paste_hash).update(views=F('views') + views)


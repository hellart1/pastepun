from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_redis import get_redis_connection

from paste.integrations import S3Storage
from paste.models import Paste


def get_paste_content(paste_hash: str, max_size=50000) -> str:
    key = f"cache:paste:{paste_hash}:text"
    data = cache.get(key)
    if data:
        return data

    storage = S3Storage()
    paste = storage.get_content(paste_hash)
    if storage.get_size(paste_hash) < max_size:
        cache.set(key=key, value=paste, timeout=600)
    return paste

def get_paste_by_hash(paste_hash: str) -> Paste:
    key = f"cache:paste:{paste_hash}"
    data = cache.get(key)
    if data:
        return data

    paste = get_object_or_404(Paste, hash=paste_hash)
    cache.set(key, paste, timeout=600)

    return paste

def get_paste_views(paste_hash):
    redis = get_redis_connection()
    total = redis.get(f"counter:paste:{paste_hash}:views_total")
    pending = redis.get(f"counter:paste:{paste_hash}:views_pending")

    return int(total or 0) + int(pending or 0)

def get_expires_pastes_queryset():
    return Paste.objects.filter(expires_at__lt=timezone.now())

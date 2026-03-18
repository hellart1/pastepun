import base64
import os
from datetime import timedelta

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django_redis import get_redis_connection

from paste.integrations import S3Storage
from paste.models import Paste
from paste.selectors import get_paste_by_hash, get_paste_content

class PasteService:
    def __init__(self):
        self.s3 = S3Storage()

    def create_paste(self, text, expiration, visibility, user):
        paste_hash = self.generate_hash()

        self.s3.upload_text(paste_hash, text)

        Paste.objects.create(
            hash=paste_hash,
            expiration_type=expiration,
            is_private=visibility,
            expires_at=self.calculate_expiration(expiration),
            owner=user if user.is_authenticated else None,
        )
        return paste_hash

    def calculate_expiration(self, expiration_type):
        mapping = {
            '10M': timedelta(minutes=10),
            '1H': timedelta(hours=1),
            '1D': timedelta(days=1)
        }

        expire_delta = mapping.get(expiration_type)

        if expire_delta is None:
            return None

        return timezone.localtime(timezone.now()) + expire_delta

    def update_paste_content(self, paste_hash, text):
        self.s3.upload_text(paste_hash, text)

        cache_key = f"cache:paste:{paste_hash}:text"
        cache.delete(cache_key)

    def delete_paste(self, paste_hash):
        self.s3.delete_object(paste_hash)

        cache.delete(f"cache:{paste_hash}:text")
        cache.delete(f"cache:{paste_hash}")
        cache.delete(f"counter:paste:{paste_hash}:views_total")
        cache.delete(f"counter:paste:{paste_hash}:pending")

        Paste.objects.filter(hash=paste_hash).delete()

    def generate_hash(self):
        #переделать
        for _ in range(100):
            random_bytes = os.urandom(10)
            coded_bytes = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
            coded_bytes.replace('=', '')
            _hash = coded_bytes[:7]

            if not Paste.objects.filter(hash=_hash).exists():
                return _hash

        raise ValueError("Не удалось найти уникальный хэш. Повторите позже")

class PasteViewService:
    def __init__(self, request, paste_hash):
        self.request = request
        self.paste_hash = paste_hash
        self.redis = get_redis_connection()

    def get_full_paste_content(self):
        paste = get_paste_by_hash(self.paste_hash)

        if paste.is_expired or (paste.is_private == 'private' and self.request.user != paste.owner):
            raise PermissionDenied

        paste.text = get_paste_content(self.paste_hash)

        self._increment_views()

        return paste

    def _increment_views(self):
        viewer_id = self._get_viewer_id()
        viewer_key = f"views:paste:{self.paste_hash}:viewer:{viewer_id}"

        if self.redis.set(viewer_key, 1, nx=True, ex=3600):
            self.redis.incr(f"counter:paste:{self.paste_hash}:views_pending")

    def _get_viewer_id(self):
        if self.request.user.is_authenticated:
            return f"user_id:{self.request.user.id}"
        else:
            if not self.request.session.session_key:
                self.request.session.create()
            session_key = self.request.session.session_key

            return f"session_key:{session_key}"


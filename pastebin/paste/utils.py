import base64
import os
from datetime import timedelta, datetime

import boto3
import django_redis
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.cache import cache
from django.forms import model_to_dict
from django.views.generic.detail import SingleObjectMixin
from rest_framework.response import Response

from paste.models import Paste


class S3ConnectMixin:
    def s3_client(self):
        return boto3.client(
            's3',
            endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
            region_name=os.getenv("ru-central1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

    def s3_resource(self):
        return boto3.resource(
            's3',
            endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
            region_name=os.getenv("ru-central1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )


class S3UtilsMixin(S3ConnectMixin):

    def put_object_in_s3(self, file_hash, text, resource=None, bucket_name=settings.AWS_STORAGE_BUCKET_NAME):
        resource = resource or self.s3_resource()
        bucket = resource.Bucket(bucket_name)
        try:
            return bucket.put_object(
                Key=f"{file_hash}.txt",
                Body=text
            )
        except Exception as e:
            print(f"Ошибка: {e}")
            return None

    def get_text_from_object_in_s3(self, object_name, client=None, bucket_name=settings.AWS_STORAGE_BUCKET_NAME):
        client = client or self.s3_client()

        response = client.get_object(Bucket=bucket_name, Key=f'{object_name}.txt')
        content = response['Body'].read().decode('utf-8')

        return content

    def get_object_size_from_s3(self, object_name, client=None, bucket_name=settings.AWS_STORAGE_BUCKET_NAME):
        client = client or self.s3_client()

        response = client.head_object(Bucket=bucket_name, Key=f'{object_name}.txt')

        return response['ContentLength']

    def get_or_set_cached_text(self, object_name, max_size=50000, client=None, bucket_name=settings.AWS_STORAGE_BUCKET_NAME):
        key = f"paste_text {object_name}"
        data = cache.get(key)
        if data:
            return data

        client = client or self.s3_client()

        size = self.get_object_size_from_s3(object_name, client=client)
        paste = self.get_text_from_object_in_s3(object_name, client=client)
        if size < max_size:
            cache.set(key=key, value=paste, timeout=600)

        return paste

    def get_or_set_cached_paste(self, paste_hash):
        key = f"paste {paste_hash}"
        data = cache.get(key)
        if data:
            return data
        paste = Paste.objects.get(hash=paste_hash)
        cache.set(key=f"paste {paste_hash}", value=paste, timeout=10)

        return paste

    def get_user_id_or_session_key(self, request):
        if request.user.is_authenticated:
            return f"user_id:{request.user.id}"
        else:
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key

            return f"session_key:{session_key}"

    def get_unique_hash(self):
        for attempts in range(100):
            random_bytes = os.urandom(10)
            coded_bytes = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
            coded_bytes.replace('=', '')
            _hash = coded_bytes[:7]

            if not Paste.objects.filter(hash=_hash).exists():
                return _hash

        raise ValueError("Не удалось найти уникальный хэш. Повторите позже")

class CacheConnect:
    def get_redis_connection(self):
        return django_redis.get_redis_connection()

class CacheMethods(CacheConnect):
    # def get_or_set_cached_text(self, object_name, max_size=50000, client=None, bucket_name=settings.AWS_STORAGE_BUCKET_NAME):
    #     key = f"paste_text {object_name}"
    #     data = cache.get(key)
    #     if data:
    #         return data
    #
    #     client = client or self.s3_client()
    #
    #     size = self.get_object_size_from_s3(object_name, client=client)
    #     paste = self.get_text_from_object_in_s3(object_name, client=client)
    #     if size < max_size:
    #         cache.set(key=key, value=paste, timeout=600)
    #
    #     return paste
    #
    # def get_or_set_cached_paste(self, paste_hash):
    #     key = f"paste {paste_hash}"
    #     data = cache.get(key)
    #     if data:
    #         return data
    #     paste = Paste.objects.get(hash=paste_hash)
    #     cache.set(key=f"paste {paste_hash}", value=paste, timeout=600)
    #
    #     return paste
    #
    # def get_user_id_or_session_key(self, request):
    #     if request.user.is_authenticated:
    #         return f"user_id:{request.user.id}"
    #     else:
    #         if not request.session.session_key:
    #             request.session.create()
    #         session_key = request.session.session_key
    #
    #         return f"session_key:{session_key}"

    def get_user_id_or_session_key(self, request):
        if request.user.is_authenticated:
            return f"user_id:{request.user.id}"
        else:
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key

            return f"session_key:{session_key}"


    def increment_paste_views_in_cache(self, request, paste_hash):
        redis = self.get_redis_connection()
        viewers = self.get_user_id_or_session_key(request)
        redis_key = f"paste:{paste_hash}:viewer:{viewers}"

        created = redis.set(
            redis_key,
            1,
            nx=True,
            ex=3600
        )

        if created:
            redis.incr(f"paste:{paste_hash}:views_pending")

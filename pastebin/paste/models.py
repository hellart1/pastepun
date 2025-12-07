from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Paste(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pastes',
        blank=True,
        null=True
    )
    hash = models.CharField(max_length=10, unique=True)
    expiration_type = models.CharField(max_length=15, default='N')
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.CharField(max_length=10, default='public')
    views = models.IntegerField(blank=True, null=True)

    @property
    def is_expired(self):
        if self.expiration_type == 'N' or self.expiration_type == 'B':
            return False

        mapping = {
            '10M': timedelta(minutes=10),
            '1H': timedelta(hours=1),
            '1D': timedelta(days=1)
        }

        expire_delta = mapping.get(self.expiration_type)

        if expire_delta is None:
            return False

        return timezone.now() > self.created_at + expire_delta


    def __str__(self):
        return self.hash



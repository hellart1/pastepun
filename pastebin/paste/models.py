from django.db import models
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
    expiration_type = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.CharField(max_length=10, default='public')
    views = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.hash



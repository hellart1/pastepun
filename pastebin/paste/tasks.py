from celery import shared_task
from django.core.cache import cache
from django.db.models import F

from paste.models import Paste


@shared_task
def update_counter_of_views(paste_hash):
    # paste = Paste.objects.get(hash=paste_hash)
    views = cache.get(key=f"paste:{paste_hash}:views")
    if views:
        Paste.objects.filter(hash=paste_hash).update(views=F('views') + views)
    # if paste.views != views:
        # paste.views += views
        # paste.save()

from celery import shared_task
from django.utils import timezone

from .models import Lead
from .notifications import notify_owner


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def notify_owner_task(lead_id: int) -> None:
    lead = Lead.objects.select_related("call__business").get(pk=lead_id)
    if lead.owner_notified_at:
        return
    notify_owner(lead.call.business, lead)
    lead.owner_notified_at = timezone.now()
    lead.save(update_fields=["owner_notified_at"])

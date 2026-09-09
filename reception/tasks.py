from celery import shared_task
from django.utils import timezone

from .models import NotificationDelivery
from .notifications import notify_owner


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def notify_owner_task(delivery_id: str) -> None:
    delivery = NotificationDelivery.objects.select_related(
        "business", "endpoint", "lead"
    ).get(pk=delivery_id)
    if delivery.status in {NotificationDelivery.Status.SENT, NotificationDelivery.Status.DELIVERED}:
        return
    delivery.status = NotificationDelivery.Status.SENDING
    delivery.attempt_count += 1
    delivery.save(update_fields=["status", "attempt_count", "updated_at"])
    try:
        notify_owner(delivery.endpoint, delivery.lead)
    except Exception as exc:
        delivery.status = NotificationDelivery.Status.FAILED
        delivery.last_error = str(exc)[:2000]
        delivery.save(update_fields=["status", "last_error", "updated_at"])
        raise
    delivery.status = NotificationDelivery.Status.SENT
    delivery.sent_at = timezone.now()
    delivery.last_error = ""
    delivery.save(update_fields=["status", "sent_at", "last_error", "updated_at"])

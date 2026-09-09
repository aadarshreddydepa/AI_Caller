from django.core.mail import send_mail


def notify_owner(business, lead):
    """Local default: Django console email. Production replaces only this adapter."""
    send_mail(
        subject=f"New callback request for {business.name}",
        message=lead.summary or "A caller requested a callback.",
        from_email=None,
        recipient_list=[business.owner_notification_target],
        fail_silently=False,
    )

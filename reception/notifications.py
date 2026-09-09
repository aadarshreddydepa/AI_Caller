from django.core.mail import send_mail


def notify_owner(endpoint, lead):
    """Local default: Django console email. Production replaces only this adapter."""
    if endpoint.channel != "email":
        raise NotImplementedError(f"Notification channel '{endpoint.channel}' is not configured")
    send_mail(
        subject=f"New callback request for {endpoint.business.name}",
        message=lead.summary or "A caller requested a callback.",
        from_email=None,
        recipient_list=[endpoint.destination],
        fail_silently=False,
    )

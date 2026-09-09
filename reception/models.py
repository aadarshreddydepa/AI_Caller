import uuid
from django.core.validators import MinValueValidator
from django.db import models


class Business(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=160)
    description = models.TextField()
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    business_hours = models.CharField(max_length=255, blank=True)
    service_area = models.CharField(max_length=255, blank=True)
    owner_notification_target = models.CharField(max_length=255, help_text="Email or future SMS/WhatsApp destination")
    escalation_instructions = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=160)
    description = models.TextField()
    price_from = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    price_note = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "name"], name="unique_business_service")]


class FAQ(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=500)
    answer = models.TextField()
    keywords = models.CharField(max_length=500, help_text="Comma-separated matching phrases")
    active = models.BooleanField(default=True)


class Call(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ESCALATED = "escalated", "Escalated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="calls")
    caller_phone = models.CharField(max_length=32, blank=True)
    caller_name = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)


class ConversationTurn(models.Model):
    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name="turns")
    speaker = models.CharField(max_length=10, choices=[("caller", "Caller"), ("agent", "Agent")])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Lead(models.Model):
    class Urgency(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"

    call = models.OneToOneField(Call, on_delete=models.CASCADE, related_name="lead")
    requirement = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    preferred_callback_time = models.CharField(max_length=255, blank=True)
    urgency = models.CharField(max_length=10, choices=Urgency.choices, default=Urgency.NORMAL)
    owner_callback_requested = models.BooleanField(default=False)
    summary = models.TextField(blank=True)
    owner_notified_at = models.DateTimeField(null=True, blank=True)

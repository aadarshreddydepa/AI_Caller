import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UUIDTimeStampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Business(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        ONBOARDING = "onboarding", "Onboarding"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        CLOSED = "closed", "Closed"

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=160)
    legal_name = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")
    default_language = models.CharField(max_length=16, default="en")
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    service_area = models.CharField(max_length=255, blank=True)
    escalation_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ONBOARDING, db_index=True)

    @property
    def active(self):
        return self.status == self.Status.ACTIVE

    def __str__(self):
        return self.name


class BusinessMembership(UUIDTimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        STAFF = "staff", "Staff"
        VIEWER = "viewer", "Viewer"

    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="business_memberships")
    role = models.CharField(max_length=16, choices=Role.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.INVITED)
    invited_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "user"], name="unique_business_member")]
        indexes = [models.Index(fields=["user", "status"])]


class BusinessLocation(UUIDTimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=160)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=24, blank=True)
    country = models.CharField(max_length=2, default="IN")
    phone = models.CharField(max_length=32, blank=True)
    is_primary = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "name"], name="unique_business_location")]


class BusinessHour(UUIDTimeStampedModel):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="hours")
    location = models.ForeignKey(BusinessLocation, on_delete=models.CASCADE, related_name="hours")
    day_of_week = models.PositiveSmallIntegerField(choices=Weekday.choices)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["location", "day_of_week"], name="unique_location_weekday")]


class BusinessHourException(UUIDTimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="hour_exceptions")
    location = models.ForeignKey(BusinessLocation, on_delete=models.CASCADE, related_name="hour_exceptions")
    date = models.DateField()
    is_closed = models.BooleanField(default=True)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["location", "date"], name="unique_location_date_exception")]


class Service(UUIDTimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="services")
    location = models.ForeignKey(BusinessLocation, null=True, blank=True, on_delete=models.SET_NULL, related_name="services")
    name = models.CharField(max_length=160)
    description = models.TextField()
    price_from = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    price_to = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    price_note = models.CharField(max_length=255, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "name"], name="unique_business_service")]


class FAQ(UUIDTimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=500)
    answer = models.TextField()
    keywords = models.CharField(max_length=500)
    category = models.CharField(max_length=100, blank=True)
    priority = models.PositiveSmallIntegerField(default=100)
    active = models.BooleanField(default=True)


class PhoneNumber(UUIDTimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="phone_numbers")
    provider = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=32, unique=True)
    provider_reference = models.CharField(max_length=255, blank=True)
    purpose = models.CharField(max_length=50, default="reception")
    status = models.CharField(max_length=20, default="inactive")
    configuration = models.JSONField(default=dict, blank=True)


class CallSession(UUIDTimeStampedModel):
    class Direction(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"

    class Status(models.TextChoices):
        RINGING = "ringing", "Ringing"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        MISSED = "missed", "Missed"
        TRANSFERRED = "transferred", "Transferred"

    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="calls")
    phone_number = models.ForeignKey(PhoneNumber, null=True, blank=True, on_delete=models.SET_NULL, related_name="calls")
    external_call_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    direction = models.CharField(max_length=10, choices=Direction.choices, default=Direction.INBOUND)
    caller_phone = models.CharField(max_length=32, blank=True)
    caller_name = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    detected_language = models.CharField(max_length=16, blank=True)
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    end_reason = models.CharField(max_length=100, blank=True)
    after_hours = models.BooleanField(default=False)
    escalated = models.BooleanField(default=False)
    recording_status = models.CharField(max_length=20, default="none")

    class Meta:
        indexes = [models.Index(fields=["business", "-started_at"]), models.Index(fields=["business", "status"])]


class ConversationTurn(UUIDTimeStampedModel):
    class Speaker(models.TextChoices):
        CALLER = "caller", "Caller"
        AGENT = "agent", "Agent"
        SYSTEM = "system", "System"
        HUMAN = "human", "Human"

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="conversation_turns")
    call = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name="turns")
    sequence_number = models.PositiveIntegerField()
    speaker = models.CharField(max_length=10, choices=Speaker.choices)
    text = models.TextField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    stt_confidence = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(1)])
    interrupted = models.BooleanField(default=False)

    class Meta:
        ordering = ["sequence_number"]
        constraints = [models.UniqueConstraint(fields=["call", "sequence_number"], name="unique_call_turn_sequence")]


class CallEvent(UUIDTimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="call_events")
    call = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=80, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at"]


class Lead(UUIDTimeStampedModel):
    class Urgency(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        CONVERTED = "converted", "Converted"
        CLOSED = "closed", "Closed"
        SPAM = "spam", "Spam"

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="leads")
    call = models.OneToOneField(CallSession, on_delete=models.CASCADE, related_name="lead")
    caller_name = models.CharField(max_length=160, blank=True)
    caller_phone = models.CharField(max_length=32, blank=True)
    requirement = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    preferred_callback_time = models.CharField(max_length=255, blank=True)
    urgency = models.CharField(max_length=10, choices=Urgency.choices, default=Urgency.NORMAL)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW, db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_leads")
    owner_callback_requested = models.BooleanField(default=False)
    summary = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["business", "status", "-created_at"])]


class LeadNote(UUIDTimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="lead_notes")
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="lead_notes")
    note = models.TextField()


class NotificationEndpoint(UUIDTimeStampedModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        WEBHOOK = "webhook", "Webhook"

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="notification_endpoints")
    channel = models.CharField(max_length=16, choices=Channel.choices)
    destination = models.CharField(max_length=255)
    label = models.CharField(max_length=100, blank=True)
    enabled = models.BooleanField(default=True)
    verified_at = models.DateTimeField(null=True, blank=True)


class NotificationDelivery(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="notification_deliveries")
    call = models.ForeignKey(CallSession, null=True, blank=True, on_delete=models.CASCADE, related_name="notification_deliveries")
    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.CASCADE, related_name="notification_deliveries")
    endpoint = models.ForeignKey(NotificationEndpoint, on_delete=models.PROTECT, related_name="deliveries")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED, db_index=True)
    provider_message_id = models.CharField(max_length=255, blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True)
    queued_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)


class AppointmentRequest(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        OWNER_REVIEW = "owner_review", "Owner review"
        CONFIRMED = "confirmed", "Confirmed"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"
        RESCHEDULED = "rescheduled", "Rescheduled"

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="appointment_requests")
    call = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name="appointment_requests")
    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name="appointment_requests")
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL, related_name="appointment_requests")
    location = models.ForeignKey(BusinessLocation, null=True, blank=True, on_delete=models.SET_NULL, related_name="appointment_requests")
    requested_date = models.DateField(null=True, blank=True)
    requested_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    confirmed_start = models.DateTimeField(null=True, blank=True)
    confirmed_end = models.DateTimeField(null=True, blank=True)


class IntegrationConnection(UUIDTimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="integrations")
    provider = models.CharField(max_length=80)
    integration_type = models.CharField(max_length=80)
    status = models.CharField(max_length=20, default="inactive")
    credentials_reference = models.CharField(max_length=255, blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "provider", "integration_type"], name="unique_business_integration")]


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs")
    action = models.CharField(max_length=100, db_index=True)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class UsageRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="usage_records")
    call = models.ForeignKey(CallSession, null=True, blank=True, on_delete=models.SET_NULL, related_name="usage_records")
    metric = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=16, decimal_places=4, validators=[MinValueValidator(0)])
    occurred_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [models.Index(fields=["business", "metric", "-occurred_at"])]

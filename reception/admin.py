from django.contrib import admin
from .models import (
    AppointmentRequest, AuditLog, Business, BusinessHour, BusinessHourException,
    BusinessLocation, BusinessMembership, CallEvent, CallSession,
    ConversationTurn, FAQ, IntegrationConnection, Lead, LeadNote,
    NotificationDelivery, NotificationEndpoint, PhoneNumber, Service, UsageRecord,
)

admin.site.register([
    Business, BusinessMembership, BusinessLocation, BusinessHour,
    BusinessHourException, Service, FAQ, PhoneNumber, CallSession,
    ConversationTurn, CallEvent, Lead, LeadNote, NotificationEndpoint,
    NotificationDelivery, AppointmentRequest, IntegrationConnection,
    AuditLog, UsageRecord,
])

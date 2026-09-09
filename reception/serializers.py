from rest_framework import serializers
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from accounts.models import User
from .models import (
    AppointmentRequest, Business, BusinessMembership, CallSession, ConversationTurn,
    FAQ, Lead, NotificationDelivery, NotificationEndpoint, Service,
)


class StartCallSerializer(serializers.Serializer):
    business_slug = serializers.SlugField()
    caller_phone = serializers.CharField(required=False, allow_blank=True, max_length=32)


class SignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    business_name = serializers.CharField(max_length=160)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10, max_length=128)
    password_confirm = serializers.CharField(write_only=True, max_length=128)

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        try:
            password_validation.validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs


class TurnSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=4000)


class LeadSerializer(serializers.Serializer):
    caller_name = serializers.CharField(required=False, allow_blank=True, max_length=160)
    caller_phone = serializers.CharField(required=False, allow_blank=True, max_length=32)
    requirement = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True, max_length=255)
    preferred_callback_time = serializers.CharField(required=False, allow_blank=True, max_length=255)
    urgency = serializers.ChoiceField(choices=Lead.Urgency.choices, required=False)
    owner_callback_requested = serializers.BooleanField(required=False)


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ["id", "slug", "name", "description", "phone", "service_area", "timezone", "default_language", "status"]


class MembershipSerializer(serializers.ModelSerializer):
    business = BusinessSerializer(read_only=True)

    class Meta:
        model = BusinessMembership
        fields = ["id", "role", "status", "business"]


class ConversationTurnSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationTurn
        fields = ["id", "sequence_number", "speaker", "text", "stt_confidence", "interrupted", "created_at"]


class CallSessionSerializer(serializers.ModelSerializer):
    lead_id = serializers.UUIDField(source="lead.id", read_only=True, allow_null=True)
    lead_requirement = serializers.CharField(source="lead.requirement", read_only=True, allow_null=True)
    lead_status = serializers.CharField(source="lead.status", read_only=True, allow_null=True)

    class Meta:
        model = CallSession
        fields = [
            "id", "direction", "caller_name", "caller_phone", "status", "started_at",
            "ended_at", "duration_seconds", "after_hours", "escalated", "lead_id",
            "lead_requirement", "lead_status",
        ]


class CallDetailSerializer(CallSessionSerializer):
    turns = ConversationTurnSerializer(many=True, read_only=True)

    class Meta(CallSessionSerializer.Meta):
        fields = CallSessionSerializer.Meta.fields + ["end_reason", "detected_language", "recording_status", "turns"]


class LeadListSerializer(serializers.ModelSerializer):
    call_started_at = serializers.DateTimeField(source="call.started_at", read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id", "call_id", "caller_name", "caller_phone", "requirement", "location",
            "preferred_callback_time", "urgency", "status", "owner_callback_requested",
            "summary", "call_started_at", "created_at",
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    caller_name = serializers.CharField(source="lead.caller_name", read_only=True, allow_null=True)
    service_name = serializers.CharField(source="service.name", read_only=True, allow_null=True)

    class Meta:
        model = AppointmentRequest
        fields = ["id", "call_id", "lead_id", "caller_name", "service_id", "service_name", "requested_date", "requested_time", "notes", "status", "confirmed_start", "confirmed_end", "created_at"]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "description", "price_from", "price_to", "price_note", "duration_minutes", "active", "created_at"]


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["id", "question", "answer", "keywords", "category", "priority", "active", "created_at"]


class NotificationEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationEndpoint
        fields = ["id", "channel", "destination", "label", "enabled", "verified_at", "created_at"]


class NotificationDeliverySerializer(serializers.ModelSerializer):
    destination = serializers.CharField(source="endpoint.destination", read_only=True)
    channel = serializers.CharField(source="endpoint.channel", read_only=True)

    class Meta:
        model = NotificationDelivery
        fields = ["id", "call_id", "lead_id", "channel", "destination", "status", "attempt_count", "last_error", "queued_at", "sent_at", "delivered_at"]


class BusinessSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ["id", "name", "legal_name", "description", "timezone", "default_language", "phone", "email", "website", "service_area", "escalation_instructions", "status"]
        read_only_fields = ["id", "status"]


class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, required=False, max_length=160)

    class Meta:
        model = User
        fields = ["id", "email", "name", "phone"]
        read_only_fields = ["id", "email"]

    def to_representation(self, instance):
        return {"id": str(instance.id), "email": instance.email, "name": instance.get_full_name(), "phone": instance.phone}

    def update(self, instance, validated_data):
        name = validated_data.pop("name", None)
        if name is not None:
            parts = name.strip().split(maxsplit=1)
            instance.first_name = parts[0] if parts else ""
            instance.last_name = parts[1] if len(parts) > 1 else ""
        return super().update(instance, validated_data)

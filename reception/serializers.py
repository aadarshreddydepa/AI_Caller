from rest_framework import serializers
from .models import Business, BusinessMembership, CallSession, ConversationTurn, Lead


class StartCallSerializer(serializers.Serializer):
    business_slug = serializers.SlugField()
    caller_phone = serializers.CharField(required=False, allow_blank=True, max_length=32)


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
        fields = ["id", "slug", "name", "description", "phone", "service_area", "timezone", "default_language"]


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

    class Meta:
        model = CallSession
        fields = [
            "id", "direction", "caller_name", "caller_phone", "status", "started_at",
            "ended_at", "duration_seconds", "after_hours", "escalated", "lead_id",
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

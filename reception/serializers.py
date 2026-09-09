from rest_framework import serializers
from .models import Business, Call, Lead


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
        fields = ["slug", "name", "description", "phone", "address", "business_hours", "service_area"]

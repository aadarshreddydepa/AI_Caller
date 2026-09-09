from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Business, Call
from .serializers import BusinessSerializer, LeadSerializer, StartCallSerializer, TurnSerializer
from .services import Receptionist, complete_call, create_or_update_lead


class BusinessDetail(APIView):
    def get(self, request, slug):
        return Response(BusinessSerializer(get_object_or_404(Business, slug=slug, active=True)).data)


class CallStart(APIView):
    def post(self, request):
        serializer = StartCallSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        business = get_object_or_404(Business, slug=serializer.validated_data["business_slug"], active=True)
        call = Call.objects.create(business=business, caller_phone=serializer.validated_data.get("caller_phone", ""))
        greeting = f"Thank you for calling {business.name}. How may I help you today?"
        return Response({"call_id": str(call.id), "reply": greeting}, status=status.HTTP_201_CREATED)


class CallTurn(APIView):
    def post(self, request, call_id):
        serializer = TurnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        call = get_object_or_404(Call, id=call_id, status__in=[Call.Status.ACTIVE, Call.Status.ESCALATED])
        reply = Receptionist().reply(call, serializer.validated_data["text"])
        return Response({"reply": reply.text, "capture_lead": reply.should_capture_lead, "escalated": reply.escalation_requested})


class CallLead(APIView):
    def post(self, request, call_id):
        serializer = LeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        call = get_object_or_404(Call, id=call_id)
        for field in ("caller_name", "caller_phone"):
            if field in serializer.validated_data:
                setattr(call, field, serializer.validated_data[field])
        call.save(update_fields=[field for field in ("caller_name", "caller_phone") if field in serializer.validated_data])
        lead = create_or_update_lead(call, serializer.validated_data)
        return Response({"lead_id": lead.id, "status": "captured"})


class CallComplete(APIView):
    def post(self, request, call_id):
        call = get_object_or_404(Call, id=call_id)
        lead = complete_call(call)
        return Response({"status": call.status, "owner_notification_target": call.business.owner_notification_target, "summary": lead.summary})

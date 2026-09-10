from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from datetime import timedelta
from django.db.models import Count, Q
from django.db import transaction
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.text import slugify
from accounts.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import AppointmentRequest, Business, BusinessMembership, CallSession, ConversationTurn, FAQ, Lead, NotificationDelivery, NotificationEndpoint, Service
from .rbac import business_for_user
from .serializers import (
    AppointmentSerializer, BusinessSerializer, BusinessSettingsSerializer, CallDetailSerializer,
    CallSessionSerializer, FAQSerializer, LeadListSerializer, LeadSerializer, MembershipSerializer,
    NotificationDeliverySerializer, NotificationEndpointSerializer, ProfileSerializer,
    ServiceSerializer, SignupSerializer, StartCallSerializer, TurnSerializer,
)
from .services import Receptionist, complete_call, create_or_update_lead
from .voice import VoiceAgent, ollama_status


class BusinessDetail(APIView):
    def get(self, request, slug):
        return Response(BusinessSerializer(get_object_or_404(Business, slug=slug, status=Business.Status.ACTIVE)).data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SessionInfo(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"authenticated": False, "google_enabled": bool(getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get("google"))})
        memberships = BusinessMembership.objects.filter(
            user=request.user, status=BusinessMembership.Status.ACTIVE
        ).select_related("business")
        return Response({
            "authenticated": True,
            "google_enabled": bool(getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get("google")),
            "user": {"id": str(request.user.id), "email": request.user.email, "name": request.user.get_full_name()},
            "memberships": MembershipSerializer(memberships, many=True).data,
        })


class SessionLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = authenticate(request, email=request.data.get("email", ""), password=request.data.get("password", ""))
        if not user or not user.is_active:
            return Response({"detail": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session.set_expiry(60 * 60 * 24 * 30 if request.data.get("remember_me") is True else 0)
        return Response({"authenticated": True, "email": user.email})


class SessionSignup(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        name_parts = data["name"].strip().split(maxsplit=1)
        user = User.objects.create_user(
            email=data["email"], password=data["password"],
            first_name=name_parts[0], last_name=name_parts[1] if len(name_parts) > 1 else "",
        )
        base_slug = slugify(data["business_name"])[:42] or "business"
        slug = base_slug
        counter = 2
        while Business.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        business = Business.objects.create(
            name=data["business_name"].strip(), slug=slug, description="",
            email=data["email"], status=Business.Status.ACTIVE,
        )
        BusinessMembership.objects.create(
            business=business, user=user, role=BusinessMembership.Role.OWNER,
            status=BusinessMembership.Status.ACTIVE, accepted_at=timezone.now(),
        )
        NotificationEndpoint.objects.create(
            business=business, channel=NotificationEndpoint.Channel.EMAIL,
            destination=data["email"], label="Owner email", enabled=True,
        )
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response({"authenticated": True, "business_id": str(business.id)}, status=status.HTTP_201_CREATED)


class SessionLogout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardSummary(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        business = business_for_user(request.user, business_id)
        calls = business.calls.all()
        leads = business.leads.all()
        call_stats = calls.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(status=CallSession.Status.COMPLETED)),
            escalated=Count("id", filter=Q(escalated=True)),
            after_hours=Count("id", filter=Q(after_hours=True)),
        )
        lead_stats = leads.aggregate(
            total=Count("id"),
            new=Count("id", filter=Q(status=Lead.Status.NEW)),
            converted=Count("id", filter=Q(status=Lead.Status.CONVERTED)),
        )
        start_date = timezone.localdate() - timedelta(days=6)
        activity_rows = (
            calls.filter(started_at__date__gte=start_date)
            .annotate(day=TruncDate("started_at"))
            .values("day").annotate(count=Count("id")).order_by("day")
        )
        activity_by_day = {row["day"]: row["count"] for row in activity_rows}
        activity = [
            {"date": (start_date + timedelta(days=offset)).isoformat(), "count": activity_by_day.get(start_date + timedelta(days=offset), 0)}
            for offset in range(7)
        ]
        return Response({
            "business": BusinessSerializer(business).data,
            "calls": call_stats,
            "leads": lead_stats,
            "activity": activity,
            "recent_calls": CallSessionSerializer(calls.order_by("-started_at")[:8], many=True).data,
        })


class BusinessCalls(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        business = business_for_user(request.user, business_id)
        return Response(CallSessionSerializer(business.calls.order_by("-started_at")[:100], many=True).data)


class BusinessCallDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id, call_id):
        business = business_for_user(request.user, business_id)
        call = get_object_or_404(business.calls.prefetch_related("turns"), id=call_id)
        return Response(CallDetailSerializer(call).data)


class BusinessLeads(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        business = business_for_user(request.user, business_id)
        return Response(LeadListSerializer(business.leads.select_related("call").order_by("-created_at")[:100], many=True).data)


class BusinessAppointments(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        business = business_for_user(request.user, business_id)
        rows = business.appointment_requests.select_related("lead", "service").order_by("-created_at")[:100]
        return Response(AppointmentSerializer(rows, many=True).data)


class BusinessKnowledge(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        business = business_for_user(request.user, business_id)
        return Response({
            "services": ServiceSerializer(business.services.order_by("name"), many=True).data,
            "faqs": FAQSerializer(business.faqs.order_by("priority", "question"), many=True).data,
        })


class BusinessNotifications(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        business = business_for_user(request.user, business_id)
        return Response({
            "endpoints": NotificationEndpointSerializer(business.notification_endpoints.order_by("channel", "label"), many=True).data,
            "deliveries": NotificationDeliverySerializer(business.notification_deliveries.select_related("endpoint").order_by("-queued_at")[:100], many=True).data,
        })


class BusinessSearch(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        business = business_for_user(request.user, business_id)
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"query": query, "calls": [], "leads": [], "services": [], "faqs": []})
        calls = business.calls.filter(
            Q(caller_name__icontains=query) | Q(caller_phone__icontains=query) |
            Q(lead__requirement__icontains=query)
        ).select_related("lead").order_by("-started_at")[:6]
        leads = business.leads.filter(
            Q(caller_name__icontains=query) | Q(caller_phone__icontains=query) |
            Q(requirement__icontains=query) | Q(summary__icontains=query)
        ).select_related("call").order_by("-created_at")[:6]
        services = business.services.filter(
            Q(name__icontains=query) | Q(description__icontains=query), active=True
        ).order_by("name")[:6]
        faqs = business.faqs.filter(
            Q(question__icontains=query) | Q(answer__icontains=query) |
            Q(keywords__icontains=query), active=True
        ).order_by("priority")[:6]
        return Response({
            "query": query,
            "calls": CallSessionSerializer(calls, many=True).data,
            "leads": LeadListSerializer(leads, many=True).data,
            "services": ServiceSerializer(services, many=True).data,
            "faqs": FAQSerializer(faqs, many=True).data,
        })


class BusinessSettings(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        return Response(BusinessSettingsSerializer(business_for_user(request.user, business_id)).data)

    def patch(self, request, business_id):
        business = business_for_user(request.user, business_id, "manage_content")
        serializer = BusinessSettingsSerializer(business, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class VoiceAgentStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        business_for_user(request.user, business_id)
        return Response(ollama_status())


class VoiceCallStart(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, business_id):
        business = business_for_user(request.user, business_id)
        call = CallSession.objects.create(business=business, status=CallSession.Status.ACTIVE)
        greeting = VoiceAgent().greeting(business)
        VoiceAgent._create_turn(call, ConversationTurn.Speaker.AGENT, greeting)
        return Response({"call_id": str(call.id), "reply": greeting}, status=status.HTTP_201_CREATED)


class VoiceCallTurn(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, business_id, call_id):
        serializer = TurnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        business = business_for_user(request.user, business_id)
        call = get_object_or_404(CallSession, id=call_id, business=business, status=CallSession.Status.ACTIVE)
        answer = VoiceAgent().reply(call, serializer.validated_data["text"])
        return Response({"reply": answer})


class VoiceCallComplete(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, business_id, call_id):
        business = business_for_user(request.user, business_id)
        call = get_object_or_404(CallSession, id=call_id, business=business)
        lead = complete_call(call)
        return Response({"status": call.status, "lead_id": str(lead.id)})


class Profile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(ProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CallStart(APIView):
    def post(self, request):
        serializer = StartCallSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        business = get_object_or_404(Business, slug=serializer.validated_data["business_slug"], status=Business.Status.ACTIVE)
        call = CallSession.objects.create(business=business, caller_phone=serializer.validated_data.get("caller_phone", ""))
        greeting = f"Thank you for calling {business.name}. How may I help you today?"
        return Response({"call_id": str(call.id), "reply": greeting}, status=status.HTTP_201_CREATED)


class CallTurn(APIView):
    def post(self, request, call_id):
        serializer = TurnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        call = get_object_or_404(CallSession, id=call_id, status=CallSession.Status.ACTIVE)
        reply = Receptionist().reply(call, serializer.validated_data["text"])
        return Response({"reply": reply.text, "capture_lead": reply.should_capture_lead, "escalated": reply.escalation_requested})


class CallLead(APIView):
    def post(self, request, call_id):
        serializer = LeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        call = get_object_or_404(CallSession, id=call_id)
        for field in ("caller_name", "caller_phone"):
            if field in serializer.validated_data:
                setattr(call, field, serializer.validated_data[field])
        call.save(update_fields=[field for field in ("caller_name", "caller_phone") if field in serializer.validated_data])
        lead = create_or_update_lead(call, serializer.validated_data)
        return Response({"lead_id": lead.id, "status": "captured"})


class CallComplete(APIView):
    def post(self, request, call_id):
        call = get_object_or_404(CallSession, id=call_id)
        lead = complete_call(call)
        return Response({"status": call.status, "notifications_queued": call.notification_deliveries.count(), "summary": lead.summary})

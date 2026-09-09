from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Business, BusinessMembership, CallSession, Lead
from .rbac import business_for_user
from .serializers import (
    BusinessSerializer, CallDetailSerializer, CallSessionSerializer, LeadListSerializer,
    LeadSerializer, MembershipSerializer, StartCallSerializer, TurnSerializer,
)
from .services import Receptionist, complete_call, create_or_update_lead


class BusinessDetail(APIView):
    def get(self, request, slug):
        return Response(BusinessSerializer(get_object_or_404(Business, slug=slug, status=Business.Status.ACTIVE)).data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SessionInfo(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"authenticated": False})
        memberships = BusinessMembership.objects.filter(
            user=request.user, status=BusinessMembership.Status.ACTIVE
        ).select_related("business")
        return Response({
            "authenticated": True,
            "user": {"id": str(request.user.id), "email": request.user.email, "name": request.user.get_full_name()},
            "memberships": MembershipSerializer(memberships, many=True).data,
        })


class SessionLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = authenticate(request, email=request.data.get("email", ""), password=request.data.get("password", ""))
        if not user or not user.is_active:
            return Response({"detail": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response({"authenticated": True, "email": user.email})


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
        return Response({
            "business": BusinessSerializer(business).data,
            "calls": call_stats,
            "leads": lead_stats,
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

from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from accounts.models import User
from .models import Business, BusinessMembership, CallSession, FAQ, NotificationEndpoint


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class ReceptionFlowTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            slug="test-repairs", name="Test Repairs", description="Repairs", status=Business.Status.ACTIVE
        )
        NotificationEndpoint.objects.create(
            business=self.business, channel=NotificationEndpoint.Channel.EMAIL,
            destination="owner@example.com", label="Owner",
        )
        FAQ.objects.create(business=self.business, question="Hours", answer="We are open 9 to 6.", keywords="hours,open")
        self.client = APIClient()

    def test_caller_is_answered_and_owner_receives_summary(self):
        start = self.client.post("/api/v1/calls/", {"business_slug": self.business.slug, "caller_phone": "+919999999999"}, format="json")
        self.assertEqual(start.status_code, 201)
        call_id = start.data["call_id"]
        turn = self.client.post(f"/api/v1/calls/{call_id}/turns/", {"text": "What are your hours?"}, format="json")
        self.assertEqual(turn.data["reply"], "We are open 9 to 6.")
        lead = self.client.post(f"/api/v1/calls/{call_id}/lead/", {"caller_name": "Priya", "requirement": "AC repair", "preferred_callback_time": "after 5 PM"}, format="json")
        self.assertEqual(lead.status_code, 200)
        complete = self.client.post(f"/api/v1/calls/{call_id}/complete/", format="json")
        self.assertEqual(complete.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Priya", mail.outbox[0].body)


class TenantRBACTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner-a@example.com", password="safe-test-password")
        self.business_a = Business.objects.create(slug="business-a", name="Business A", description="A", status=Business.Status.ACTIVE)
        self.business_b = Business.objects.create(slug="business-b", name="Business B", description="B", status=Business.Status.ACTIVE)
        BusinessMembership.objects.create(
            business=self.business_a, user=self.owner,
            role=BusinessMembership.Role.OWNER, status=BusinessMembership.Status.ACTIVE,
        )
        CallSession.objects.create(business=self.business_a, caller_name="Allowed caller")
        CallSession.objects.create(business=self.business_b, caller_name="Private caller")
        self.client = APIClient()
        self.client.force_login(self.owner)

    def test_owner_can_read_own_dashboard(self):
        response = self.client.get(f"/api/v1/businesses/{self.business_a.id}/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["calls"]["total"], 1)

    def test_owner_cannot_read_another_business(self):
        response = self.client.get(f"/api/v1/businesses/{self.business_b.id}/dashboard/")
        self.assertEqual(response.status_code, 404)

from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .models import Business, FAQ


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class ReceptionFlowTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            slug="test-repairs", name="Test Repairs", description="Repairs", owner_notification_target="owner@example.com"
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

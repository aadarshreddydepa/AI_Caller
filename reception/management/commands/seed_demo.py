from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from reception.models import (
    Business, BusinessLocation, BusinessMembership, CallSession, ConversationTurn,
    FAQ, Lead, NotificationEndpoint, Service,
)


class Command(BaseCommand):
    help = "Create or update a safe demo business for local receptionist testing."

    def handle(self, *args, **options):
        business, _ = Business.objects.update_or_create(
            slug="bright-repairs",
            defaults={
                "name": "Bright Home Repairs",
                "description": "Local home repair and maintenance service.",
                "phone": "+91 90000 00000",
                "service_area": "Hyderabad",
                "escalation_instructions": "Escalate emergencies, complaints, price negotiations, and owner requests.",
                "status": Business.Status.ACTIVE,
            },
        )
        owner, _ = User.objects.get_or_create(email="owner@example.com", defaults={"first_name": "Demo", "last_name": "Owner"})
        owner.set_password("demo-owner-local")
        owner.save(update_fields=["password"])
        BusinessMembership.objects.update_or_create(
            business=business, user=owner,
            defaults={"role": BusinessMembership.Role.OWNER, "status": BusinessMembership.Status.ACTIVE},
        )
        location, _ = BusinessLocation.objects.update_or_create(
            business=business, name="Madhapur",
            defaults={"address_line_1": "Madhapur", "city": "Hyderabad", "state": "Telangana", "is_primary": True},
        )
        NotificationEndpoint.objects.update_or_create(
            business=business, channel=NotificationEndpoint.Channel.EMAIL, destination="owner@example.com",
            defaults={"label": "Owner email", "enabled": True},
        )
        Service.objects.update_or_create(
            business=business,
            name="AC repair",
            defaults={"location": location, "description": "Inspection and repair for home air conditioners.", "price_from": 499, "price_note": "Final price depends on inspection."},
        )
        FAQ.objects.update_or_create(
            business=business,
            question="What are your working hours?",
            defaults={"answer": "We are open Monday to Saturday, from 9 AM to 6 PM.", "keywords": "hours,open,close,timing,time"},
        )
        FAQ.objects.update_or_create(
            business=business,
            question="Where do you provide service?",
            defaults={"answer": "We currently provide service across Hyderabad.", "keywords": "area,location,serve,service area,hyderabad"},
        )
        demo_calls = [
            ("Priya Sharma", "+919800004210", "AC repair", 0, True, False),
            ("Rahul Verma", "+919700001184", "Service pricing", 0, False, False),
            ("Unknown caller", "+918800009032", "Owner requested", 0, True, True),
            ("Ananya Rao", "+919900007208", "Service area", 1, False, False),
            ("Vikram Singh", "+919600002801", "AC installation", 1, True, False),
            ("Meera Joshi", "+919500006019", "Working hours", 2, False, False),
            ("Karan Shah", "+919400008312", "Emergency repair", 2, True, True),
            ("Sneha Iyer", "+919300004551", "Maintenance plan", 3, True, False),
            ("Arjun Nair", "+919200007743", "Service pricing", 4, False, False),
            ("Divya Patel", "+919100003928", "AC repair", 4, True, False),
            ("Nikhil Kumar", "+919000006144", "Service area", 5, False, False),
            ("Fatima Khan", "+918900002556", "AC repair", 6, True, False),
        ]
        now = timezone.now()
        for index, (caller, phone, requirement, days_ago, has_lead, escalated) in enumerate(demo_calls, start=1):
            call, _ = CallSession.objects.update_or_create(
                external_call_id=f"demo-call-{index}",
                defaults={
                    "business": business, "caller_name": caller, "caller_phone": phone,
                    "status": CallSession.Status.COMPLETED, "duration_seconds": 74 + index * 11,
                    "escalated": escalated, "after_hours": index in {3, 7, 12},
                    "ended_at": now - timedelta(days=days_ago, minutes=index * 9),
                },
            )
            started_at = now - timedelta(days=days_ago, minutes=index * 9 + 2)
            CallSession.objects.filter(pk=call.pk).update(started_at=started_at)
            ConversationTurn.objects.update_or_create(
                call=call, sequence_number=1,
                defaults={"business": business, "speaker": ConversationTurn.Speaker.CALLER, "text": f"I am calling about {requirement.lower()}."},
            )
            ConversationTurn.objects.update_or_create(
                call=call, sequence_number=2,
                defaults={"business": business, "speaker": ConversationTurn.Speaker.AGENT, "text": "I can help with that and arrange an owner callback if needed."},
            )
            if has_lead:
                Lead.objects.update_or_create(
                    call=call,
                    defaults={
                        "business": business, "caller_name": caller, "caller_phone": phone,
                        "requirement": requirement, "location": "Hyderabad",
                        "preferred_callback_time": "Today after 5 PM",
                        "urgency": Lead.Urgency.HIGH if escalated else Lead.Urgency.NORMAL,
                        "owner_callback_requested": True,
                        "summary": f"{caller} requested help with {requirement.lower()} and asked for a callback.",
                    },
                )
        self.stdout.write(self.style.SUCCESS(f"Demo business ready: {business.slug}"))

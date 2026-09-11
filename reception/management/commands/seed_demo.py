from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from reception.models import (
    AppointmentRequest, Business, BusinessHour, BusinessLocation,
    BusinessMembership, CallSession, ConversationTurn, FAQ, Lead,
    NotificationDelivery, NotificationEndpoint, Service,
)


SERVICES = [
    ("AC inspection and repair", "Diagnosis and repair for split and window air conditioners.", 499, 60, "Parts and gas refill are charged separately."),
    ("AC installation", "Installation of split and window air-conditioning units.", 1499, 120, "A site inspection may be required."),
    ("Plumbing repair", "Repairs for taps, sinks, toilets, blocked drains, and household pipe leaks.", 399, 60, "Replacement materials are charged separately."),
    ("Electrical inspection", "Safety inspection and diagnosis of common household electrical faults.", 349, 45, "The final price depends on the issue found."),
    ("Water-tank cleaning", "Mechanised cleaning and sanitisation of household water tanks.", 1299, 180, "Starting price applies to tanks up to 1,000 litres."),
    ("Annual home-maintenance plan", "Four scheduled preventive inspections across the year.", 4999, None, "One-year plan; repair parts are not included."),
]

FAQS = [
    ("What are your working hours?", "We are open Monday to Saturday from 9 AM to 6 PM. On Sundays, we only collect emergency callback requests.", "hours,open,close,timing,sunday", "Hours"),
    ("Where do you provide service?", "We serve Hyderabad, Secunderabad, Madhapur, Kondapur, Gachibowli, and Jubilee Hills.", "area,location,serve,coverage,hyderabad", "Coverage"),
    ("Do you provide same-day service?", "Same-day service may be available, but the owner must confirm technician availability and timing.", "same day,today,available,availability", "Booking"),
    ("Is there a visiting charge?", "Inspection starts at 349 rupees for electrical work and 499 rupees for AC service. The final cost depends on the work required.", "visiting,inspection,charge,fee", "Pricing"),
    ("Do you provide a warranty?", "Completed labour has a 30-day service warranty. Replacement parts follow the manufacturer warranty.", "warranty,guarantee", "Policy"),
    ("Can I cancel an appointment?", "Please contact us at least two hours before the requested visit to cancel or reschedule.", "cancel,reschedule,change appointment", "Booking"),
    ("Which payment methods do you accept?", "We accept UPI, cards, and cash after the service is completed.", "payment,pay,upi,card,cash", "Payment"),
    ("Do you service commercial properties?", "We support small offices and retail properties. Larger commercial jobs need an owner callback before they can be accepted.", "commercial,office,shop,retail", "Coverage"),
]

CALLS = [
    ("Priya Sharma", "+91 98765 43210", "AC repair - unit is not cooling", "Kondapur", "Tomorrow between 9 and 11 AM", 0, "new", "normal", "AC inspection and repair", False, False, 1),
    ("Rahul Verma", "+91 97000 11840", "Plumbing repair for a leaking kitchen tap", "Madhapur", "Today after 5 PM", 0, "contacted", "normal", "Plumbing repair", False, False, None),
    ("Karan Shah", "+91 94000 83120", "Urgent burning smell from switchboard", "Gachibowli", "Immediately", 1, "new", "high", "Electrical inspection", True, True, None),
    ("Ananya Rao", "+91 99000 72080", "Water-tank cleaning for a 1,000-litre tank", "Jubilee Hills", "Saturday morning", 1, "qualified", "normal", "Water-tank cleaning", False, False, 3),
    ("Vikram Singh", "+91 96000 28010", "New split AC installation", "Secunderabad", "Weekday afternoon", 2, "converted", "normal", "AC installation", False, False, 2),
    ("Meera Joshi", "+91 95000 60190", "Asked about working hours and service coverage", "Hyderabad", "", 2, "closed", "low", None, False, False, None),
    ("Sneha Iyer", "+91 93000 45510", "Annual maintenance plan for a three-bedroom flat", "Madhapur", "Tomorrow after 4 PM", 3, "qualified", "normal", "Annual home-maintenance plan", False, False, None),
    ("Arjun Nair", "+91 92000 77430", "Requested a discount on an AC inspection", "Kondapur", "Today before 6 PM", 4, "new", "normal", "AC inspection and repair", True, False, None),
    ("Divya Patel", "+91 91000 39280", "Bathroom drain is blocked", "Jubilee Hills", "Tomorrow morning", 4, "contacted", "normal", "Plumbing repair", False, False, None),
    ("Fatima Khan", "+91 89000 25560", "Sunday pipe burst causing water ingress", "Gachibowli", "Immediately", 5, "converted", "high", "Plumbing repair", True, True, None),
    ("Nikhil Kumar", "+91 90000 61440", "Refrigerator repair enquiry - unsupported service", "Madhapur", "Evening", 6, "closed", "low", None, True, False, None),
    ("Lakshmi Menon", "+91 98850 44321", "Electrical safety inspection before moving into a flat", "Kondapur", "Friday after 2 PM", 6, "converted", "normal", "Electrical inspection", False, False, 4),
]


class Command(BaseCommand):
    help = "Create the complete Bright Home Repairs demonstration workspace."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Remove existing business demo records first.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            demo_business = Business.objects.filter(slug="bright-repairs").first()
            if demo_business:
                # Calls use PROTECT for their business, so remove this demo's calls first.
                CallSession.objects.filter(business=demo_business).delete()
                demo_business.delete()
            demo_owner = User.objects.filter(email="owner@example.com").first()
            if demo_owner and not demo_owner.business_memberships.exists():
                demo_owner.delete()
            self.stdout.write("Removed the existing Bright Home Repairs demo data.")

        business, _ = Business.objects.update_or_create(
            slug="bright-repairs",
            defaults={
                "name": "Bright Home Repairs",
                "legal_name": "Bright Home Repairs Private Limited",
                "description": "A trusted Hyderabad home-maintenance company providing AC, plumbing, electrical, water-tank cleaning, and preventive maintenance services.",
                "timezone": "Asia/Kolkata",
                "default_language": "en-IN",
                "phone": "+91 40 4567 8900",
                "email": "support@brighthomerepairs.in",
                "website": "https://brighthomerepairs.in",
                "service_area": "Hyderabad, Secunderabad, Madhapur, Kondapur, Gachibowli, and Jubilee Hills",
                "escalation_instructions": "Request an immediate owner callback for safety emergencies, serious complaints, refunds, price negotiations, commercial jobs, unsupported services, or an explicit request for a human. Never promise technician availability or an arrival time.",
                "status": Business.Status.ACTIVE,
            },
        )
        owner, _ = User.objects.get_or_create(email="owner@example.com")
        owner.first_name, owner.last_name, owner.phone = "Aarav", "Reddy", "+91 98490 12012"
        owner.set_password("demo-owner-local")
        owner.save()
        BusinessMembership.objects.update_or_create(
            business=business, user=owner,
            defaults={"role": "owner", "status": "active", "accepted_at": timezone.now()},
        )
        location, _ = BusinessLocation.objects.update_or_create(
            business=business, name="Madhapur Service Centre",
            defaults={"address_line_1": "Plot 24, Hitech City Road", "city": "Hyderabad", "state": "Telangana", "postal_code": "500081", "country": "IN", "phone": "+91 40 4567 8900", "is_primary": True, "active": True},
        )
        for weekday in range(7):
            closed = weekday == BusinessHour.Weekday.SUNDAY
            BusinessHour.objects.update_or_create(
                business=business, location=location, day_of_week=weekday,
                defaults={"opens_at": None if closed else time(9), "closes_at": None if closed else time(18), "is_closed": closed},
            )
        endpoint, _ = NotificationEndpoint.objects.update_or_create(
            business=business, channel="email", destination="owner@example.com",
            defaults={"label": "Owner email", "enabled": True, "verified_at": timezone.now()},
        )
        services = {}
        for name, description, price, duration, note in SERVICES:
            services[name], _ = Service.objects.update_or_create(
                business=business, name=name,
                defaults={"location": location, "description": description, "price_from": price, "price_note": note, "duration_minutes": duration, "active": True},
            )
        for priority, (question, answer, keywords, category) in enumerate(FAQS, start=1):
            FAQ.objects.update_or_create(
                business=business, question=question,
                defaults={"answer": answer, "keywords": keywords, "category": category, "priority": priority * 10, "active": True},
            )

        # Replace the scenario rows even without --reset, keeping normal reseeds idempotent.
        CallSession.objects.filter(business=business, external_call_id__startswith="bright-demo-").delete()
        now = timezone.now()
        for index, row in enumerate(CALLS, start=1):
            name, phone, requirement, area, callback, days, lead_status, urgency, service_name, escalated, after_hours, appointment_days = row
            started_at = now - timedelta(days=days, minutes=index * 13)
            duration = 72 + index * 17
            call = CallSession.objects.create(
                business=business, external_call_id=f"bright-demo-{index}", caller_name=name,
                caller_phone=phone, status="completed", detected_language="en-IN",
                duration_seconds=duration, ended_at=started_at + timedelta(seconds=duration),
                escalated=escalated, after_hours=after_hours, end_reason="caller_completed",
            )
            CallSession.objects.filter(pk=call.pk).update(started_at=started_at, answered_at=started_at)
            turns = [
                ("agent", f"Hello, thank you for calling {business.name}. How may I help you today?"),
                ("caller", f"Hello, I am {name}. I am calling about {requirement.lower()} in {area}."),
                ("agent", self._agent_reply(service_name, escalated)),
            ]
            if callback:
                turns.append(("caller", f"Please call me back {callback.lower()}. My number is {phone}."))
            for sequence, (speaker, text) in enumerate(turns, start=1):
                ConversationTurn.objects.create(business=business, call=call, sequence_number=sequence, speaker=speaker, text=text)
            lead = Lead.objects.create(
                business=business, call=call, caller_name=name, caller_phone=phone,
                requirement=requirement, location=area, preferred_callback_time=callback,
                urgency=urgency, status=lead_status, assigned_to=owner if lead_status != "closed" else None,
                owner_callback_requested=bool(callback or escalated),
                summary=f"{name} called from {area} about {requirement.lower()}. Preferred callback: {callback or 'not requested'}.",
            )
            if appointment_days:
                AppointmentRequest.objects.create(
                    business=business, call=call, lead=lead, service=services[service_name], location=location,
                    requested_date=timezone.localdate() + timedelta(days=appointment_days),
                    requested_time=time(10 + index % 5), notes=f"Customer requested {service_name.lower()} at {area}.",
                    status="confirmed" if lead_status == "converted" else "owner_review",
                )
            if lead.owner_callback_requested:
                NotificationDelivery.objects.create(
                    business=business, call=call, lead=lead, endpoint=endpoint,
                    status="sent", attempt_count=1, sent_at=started_at + timedelta(minutes=3),
                )

        self.stdout.write(self.style.SUCCESS(
            "Fresh Bright Home Repairs demo ready: 6 services, 8 FAQs, 12 calls, 12 leads, and 4 appointments."
        ))

    @staticmethod
    def _agent_reply(service_name, escalated):
        if escalated:
            return "I understand, and I’m sorry you’re dealing with this. I’ll mark this for an owner callback. I won’t promise an arrival time, but I’ll make sure your details and urgency are recorded."
        if service_name:
            return f"Of course, I’d be happy to help. We provide {service_name.lower()}. I’ll record your details and preferred time so the owner can confirm the visit with you."
        return "Certainly. I can help with those approved details, and I’ll keep a record of your enquiry for the team."

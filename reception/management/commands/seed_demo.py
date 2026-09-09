from django.core.management.base import BaseCommand
from reception.models import Business, FAQ, Service


class Command(BaseCommand):
    help = "Create or update a safe demo business for local receptionist testing."

    def handle(self, *args, **options):
        business, _ = Business.objects.update_or_create(
            slug="bright-repairs",
            defaults={
                "name": "Bright Home Repairs",
                "description": "Local home repair and maintenance service.",
                "phone": "+91 90000 00000",
                "address": "Madhapur, Hyderabad",
                "business_hours": "Monday-Saturday, 9 AM-6 PM",
                "service_area": "Hyderabad",
                "owner_notification_target": "owner@example.com",
                "escalation_instructions": "Escalate emergencies, complaints, price negotiations, and owner requests.",
            },
        )
        Service.objects.update_or_create(
            business=business,
            name="AC repair",
            defaults={"description": "Inspection and repair for home air conditioners.", "price_from": 499, "price_note": "Final price depends on inspection."},
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
        self.stdout.write(self.style.SUCCESS(f"Demo business ready: {business.slug}"))

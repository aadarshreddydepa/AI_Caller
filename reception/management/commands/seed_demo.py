from django.core.management.base import BaseCommand
from accounts.models import User
from reception.models import (
    Business, BusinessLocation, BusinessMembership, FAQ, NotificationEndpoint, Service,
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
        owner.set_unusable_password()
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
        self.stdout.write(self.style.SUCCESS(f"Demo business ready: {business.slug}"))

from django.shortcuts import get_object_or_404

from .models import Business, BusinessMembership


ROLE_PERMISSIONS = {
    BusinessMembership.Role.OWNER: {"view", "manage_leads", "manage_content", "manage_members", "manage_integrations", "export"},
    BusinessMembership.Role.MANAGER: {"view", "manage_leads", "manage_content", "manage_integrations", "export"},
    BusinessMembership.Role.STAFF: {"view", "manage_leads"},
    BusinessMembership.Role.VIEWER: {"view"},
}


def business_for_user(user, business_id, permission="view") -> Business:
    if user.is_staff:
        return get_object_or_404(Business, id=business_id)
    membership = get_object_or_404(
        BusinessMembership.objects.select_related("business"),
        business_id=business_id,
        user=user,
        status=BusinessMembership.Status.ACTIVE,
    )
    if permission not in ROLE_PERMISSIONS.get(membership.role, set()):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Your business role does not allow this action.")
    return membership.business

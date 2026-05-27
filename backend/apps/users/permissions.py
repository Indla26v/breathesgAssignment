from rest_framework.permissions import BasePermission
from apps.users.models import User

class IsAnalyst(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [User.ANALYST, User.TENANT_ADMIN, User.PLATFORM_ADMIN]
        )

class IsTenantAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [User.TENANT_ADMIN, User.PLATFORM_ADMIN]
        )

class IsPlatformAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.PLATFORM_ADMIN
        )

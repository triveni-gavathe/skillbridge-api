from rest_framework.permissions import BasePermission


class IsRole(BasePermission):
    """Base helper. Subclass and set allowed_roles."""
    allowed_roles = []

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in self.allowed_roles
        )


class IsStudent(IsRole):
    allowed_roles = ['student']

class IsTrainer(IsRole):
    allowed_roles = ['trainer']

class IsInstitution(IsRole):
    allowed_roles = ['institution']

class IsTrainerOrInstitution(IsRole):
    allowed_roles = ['trainer', 'institution']

class IsProgrammeManager(IsRole):
    allowed_roles = ['programme_manager']

class IsMonitoringOfficer(BasePermission):
    """Monitoring officer must supply the scoped monitoring token, not standard login token."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != 'monitoring_officer':
            return False
        # Must be the special monitoring token, not the standard one
        if getattr(request, 'token_type', 'standard') != 'monitoring':
            return False
        return True
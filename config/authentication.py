from typing import Any

from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from accounts.models import Tenant, User

HEADER_USER_ID = "HTTP_X_USER_ID"
HEADER_TENANT_ID = "HTTP_X_TENANT_ID"
HEADER_ROLE = "HTTP_X_ROLE"


class GatewayAuthentication(BaseAuthentication):
    def authenticate_header(self, request: Request) -> str:
        return "Gateway"

    def authenticate(self, request: Request) -> tuple[User, dict[str, Any]] | None:
        user_id = request.META.get(HEADER_USER_ID)
        tenant_id = request.META.get(HEADER_TENANT_ID)
        role = request.META.get(HEADER_ROLE)
        if not user_id or not tenant_id or not role:
            raise AuthenticationFailed("Missing required gateway headers.")

        user = (
            User.objects.select_related("tenant")
            .filter(
                auth0_user_id=user_id,
                tenant__auth0_organization_id=tenant_id,
                role=role,
            )
            .first()
        )
        if not user:
            raise AuthenticationFailed("User not found.")

        return user, {"role": role, "tenant_id": tenant_id}


class InternalTenantAuthentication(BaseAuthentication):
    """
    Authentication for internal service-to-service calls.

    Resolves a tenant from `X-Tenant-Id` and does not require an end-user identity.
    """

    def authenticate_header(self, request: Request) -> str:
        return "InternalTenant"

    def authenticate(
        self, request: Request
    ) -> tuple[AnonymousUser, dict[str, Any]] | None:
        tenant_id = request.META.get(HEADER_TENANT_ID)
        if not tenant_id:
            raise AuthenticationFailed("Missing required internal tenant header.")

        tenant = Tenant.objects.filter(auth0_organization_id=tenant_id).first()
        if not tenant:
            raise AuthenticationFailed("Tenant not found.")

        return AnonymousUser(), {"tenant": tenant, "tenant_id": tenant_id}

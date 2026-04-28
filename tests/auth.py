from __future__ import annotations

from accounts.models import User


def gateway_headers(user: User) -> dict[str, str]:
    return {
        "X-User-Id": user.auth0_user_id,
        "X-Tenant-Id": user.tenant.auth0_organization_id if user.tenant else "",
        "X-Role": user.role,
    }

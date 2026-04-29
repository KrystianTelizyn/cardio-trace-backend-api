from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from config.authentication import (
    HEADER_ROLE,
    HEADER_TENANT_ID,
    HEADER_USER_ID,
    GatewayAuthentication,
    InternalTenantAuthentication,
)
from tests.mixins import TenantUsersMixin


class GatewayAuthenticationTests(TenantUsersMixin, TestCase):
    tenant_auth0_organization_id = "org_auth_test"
    tenant_name = "Auth Clinic"
    doctor_auth0_user_id = "auth0|auth_doc"
    doctor_email = "authdoc@example.com"
    doctor_profile_name = "Auth Doc"

    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.auth = GatewayAuthentication()
        self.user = self.doctor_user

    def test_raises_when_all_headers_absent(self) -> None:
        request = self.factory.get("/me/profile")
        with self.assertRaisesRegex(AuthenticationFailed, "Missing required gateway"):
            self.auth.authenticate(request)

    def test_raises_when_tenant_header_missing(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{HEADER_USER_ID: self.user.auth0_user_id, HEADER_ROLE: "doctor"},  # type: ignore[arg-type]
        )
        with self.assertRaisesRegex(AuthenticationFailed, "Missing required gateway"):
            self.auth.authenticate(request)

    def test_raises_when_roles_header_missing(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{
                HEADER_USER_ID: self.user.auth0_user_id,
                HEADER_TENANT_ID: self.tenant.auth0_organization_id,
            },  # type: ignore[arg-type]
        )
        with self.assertRaisesRegex(AuthenticationFailed, "Missing required gateway"):
            self.auth.authenticate(request)

    def test_raises_when_user_not_found(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{  # type: ignore[arg-type]
                HEADER_USER_ID: "auth0|nonexistent",
                HEADER_TENANT_ID: self.tenant.auth0_organization_id,
                HEADER_ROLE: "doctor",
            },
        )
        with self.assertRaisesRegex(AuthenticationFailed, "User not found"):
            self.auth.authenticate(request)

    def test_raises_on_tenant_mismatch(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{  # type: ignore[arg-type]
                HEADER_USER_ID: "auth0|auth_doc",
                HEADER_TENANT_ID: "org_wrong",
                HEADER_ROLE: "doctor",
            },
        )
        with self.assertRaisesRegex(AuthenticationFailed, "User not found"):
            self.auth.authenticate(request)

    def test_raises_on_role_mismatch(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{  # type: ignore[arg-type]
                HEADER_USER_ID: "auth0|auth_doc",
                HEADER_TENANT_ID: self.tenant.auth0_organization_id,
                HEADER_ROLE: "patient",
            },
        )
        with self.assertRaisesRegex(AuthenticationFailed, "User not found"):
            self.auth.authenticate(request)

    def test_returns_user_and_auth_on_success(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{  # type: ignore[arg-type]
                HEADER_USER_ID: self.user.auth0_user_id,
                HEADER_TENANT_ID: self.tenant.auth0_organization_id,
                HEADER_ROLE: "doctor",
            },
        )
        result = self.auth.authenticate(request)

        self.assertIsNotNone(result)
        user, auth_info = result
        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(auth_info["role"], "doctor")
        self.assertEqual(auth_info["tenant_id"], self.tenant.auth0_organization_id)


class InternalTenantAuthenticationTests(TenantUsersMixin, TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.auth = InternalTenantAuthentication()

    def test_raises_when_tenant_header_missing(self) -> None:
        request = self.factory.get("/measurements")
        with self.assertRaisesRegex(
            AuthenticationFailed, "Missing required internal tenant header"
        ):
            self.auth.authenticate(request)

    def test_raises_when_unknown_tenant(self) -> None:
        request = self.factory.get("/measurements", **{HEADER_TENANT_ID: "org_missing"})  # type: ignore[arg-type]
        with self.assertRaisesRegex(AuthenticationFailed, "Tenant not found"):
            self.auth.authenticate(request)

    def test_returns_anonymous_user_and_tenant_on_success(self) -> None:
        request = self.factory.get(
            "/measurements",
            **{  # type: ignore[arg-type]
                HEADER_TENANT_ID: self.tenant.auth0_organization_id,
            },
        )
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)

        user, auth_info = result
        self.assertFalse(user.is_authenticated)
        self.assertEqual(auth_info["tenant"].pk, self.tenant.pk)
        self.assertEqual(auth_info["tenant_id"], self.tenant.auth0_organization_id)

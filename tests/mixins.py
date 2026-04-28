from __future__ import annotations

from rest_framework.test import APIClient

from accounts.models import User
from tests.auth import gateway_headers
from tests.factories import (
    DeviceFactory,
    DoctorProfileFactory,
    DoctorUserFactory,
    PatientProfileFactory,
    PatientUserFactory,
    TenantFactory,
)


class ApiClientMixin:
    client: APIClient

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()


class GatewayAuthMixin:
    def headers_for(self, user: User) -> dict[str, str]:
        return gateway_headers(user)


class TenantUsersMixin:
    tenant = None
    doctor_user = None
    patient_user = None
    doctor_profile = None
    patient_profile = None

    @classmethod
    def setUpTestData(cls) -> None:
        slug = getattr(cls, "fixture_slug", cls.__name__).lower()

        tenant_org_id = getattr(cls, "tenant_auth0_organization_id", f"org_{slug}")
        tenant_name = getattr(cls, "tenant_name", f"Tenant {cls.__name__}")

        doctor_auth0_user_id = getattr(
            cls, "doctor_auth0_user_id", f"auth0|doctor_{slug}"
        )
        doctor_email = getattr(cls, "doctor_email", f"doctor_{slug}@example.com")

        patient_auth0_user_id = getattr(
            cls, "patient_auth0_user_id", f"auth0|patient_{slug}"
        )
        patient_email = getattr(cls, "patient_email", f"patient_{slug}@example.com")

        doctor_profile_name = getattr(cls, "doctor_profile_name", "Doc")
        patient_profile_name = getattr(cls, "patient_profile_name", "Pat")

        cls.tenant = TenantFactory(
            auth0_organization_id=tenant_org_id,
            name=tenant_name,
        )
        cls.doctor_user = DoctorUserFactory(
            auth0_user_id=doctor_auth0_user_id,
            email=doctor_email,
            tenant=cls.tenant,
        )
        cls.patient_user = PatientUserFactory(
            auth0_user_id=patient_auth0_user_id,
            email=patient_email,
            tenant=cls.tenant,
        )
        cls.doctor_profile = DoctorProfileFactory(
            user=cls.doctor_user,
            name=doctor_profile_name,
        )
        cls.patient_profile = PatientProfileFactory(
            user=cls.patient_user,
            name=patient_profile_name,
        )
        super().setUpTestData()


class WrongTenantMixin:
    other_tenant = None
    other_doctor_user = None
    other_patient_user = None
    other_patient_profile = None

    @classmethod
    def setUpTestData(cls) -> None:
        cls.other_tenant = TenantFactory()
        cls.other_doctor_user = DoctorUserFactory(tenant=cls.other_tenant)
        cls.other_patient_user = PatientUserFactory(tenant=cls.other_tenant)
        cls.other_patient_profile = PatientProfileFactory(user=cls.other_patient_user)
        super().setUpTestData()


class DevicesFixtureMixin:
    device = None

    @classmethod
    def setUpTestData(cls) -> None:
        cls.device = DeviceFactory(tenant=cls.tenant)
        super().setUpTestData()

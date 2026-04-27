import datetime

import pytest
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient, APIRequestFactory

from accounts.exceptions import TenantNotFound
from accounts.models import DoctorProfile, PatientProfile, Tenant, User
from accounts.use_cases import ProvisionUser, UpdateProfile
from config.authentication import (
    HEADER_ROLE,
    HEADER_TENANT_ID,
    HEADER_USER_ID,
    GatewayAuthentication,
)


class ProvisionUserUseCaseTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            auth0_organization_id="org_test123",
            name="Test Clinic",
        )
        self.use_case = ProvisionUser()

    def test_creates_doctor_with_profile(self):
        user, created = self.use_case.execute(
            auth0_user_id="auth0|doctor1",
            auth0_org_id="org_test123",
            role="doctor",
            email="doc@example.com",
            name="Alice",
        )

        assert created is True
        assert user.auth0_user_id == "auth0|doctor1"
        assert user.email == "doc@example.com"
        assert user.role == User.Role.DOCTOR
        assert user.tenant == self.tenant
        assert user.doctor_profile.name == "Alice"

    def test_creates_patient_with_profile(self):
        user, created = self.use_case.execute(
            auth0_user_id="auth0|patient1",
            auth0_org_id="org_test123",
            role="patient",
            email="pat@example.com",
            name="Bob",
        )

        assert created is True
        assert user.role == User.Role.PATIENT
        assert user.patient_profile.name == "Bob"

    def test_idempotent_returns_existing_user(self):
        user1, created1 = self.use_case.execute(
            auth0_user_id="auth0|repeat",
            auth0_org_id="org_test123",
            role="doctor",
            email="repeat@example.com",
        )
        user2, created2 = self.use_case.execute(
            auth0_user_id="auth0|repeat",
            auth0_org_id="org_test123",
            role="doctor",
            email="repeat@example.com",
        )

        assert created1 is True
        assert created2 is False
        assert user1.pk == user2.pk

    def test_raises_tenant_not_found(self):
        with pytest.raises(TenantNotFound) as exc_info:
            self.use_case.execute(
                auth0_user_id="auth0|orphan",
                auth0_org_id="org_nonexistent",
                role="doctor",
                email="orphan@example.com",
            )
        assert "org_nonexistent" in str(exc_info.value)

    def test_name_defaults_to_empty_string(self):
        user, _ = self.use_case.execute(
            auth0_user_id="auth0|noname",
            auth0_org_id="org_test123",
            role="patient",
            email="noname@example.com",
        )

        assert user.patient_profile.name == ""


class UserProvisionViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            auth0_organization_id="org_view_test",
            name="View Test Clinic",
        )
        self.valid_payload = {
            "auth0_user_id": "auth0|view_doc",
            "auth0_org_id": "org_view_test",
            "role": "doctor",
            "email": "viewdoc@example.com",
            "name": "Dr. View",
        }

    def test_create_user_returns_201(self):
        response = self.client.post("/users", self.valid_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["auth0_user_id"] == "auth0|view_doc"
        assert data["email"] == "viewdoc@example.com"
        assert data["role"] == "doctor"
        assert data["profile"]["name"] == "Dr. View"
        assert "id" in data["profile"]

    def test_existing_user_returns_200(self):
        self.client.post("/users", self.valid_payload, format="json")
        response = self.client.post("/users", self.valid_payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["auth0_user_id"] == "auth0|view_doc"

    def test_invalid_role_returns_400(self):
        payload = {**self.valid_payload, "role": "admin"}
        response = self.client.post("/users", payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_required_field_returns_400(self):
        payload = {
            "auth0_user_id": "auth0|incomplete",
            "role": "doctor",
        }
        response = self.client.post("/users", payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unknown_tenant_returns_404(self):
        payload = {**self.valid_payload, "auth0_org_id": "org_does_not_exist"}
        response = self.client.post("/users", payload, format="json")
        print(response.json())
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "org_does_not_exist" in response.json()["error"]["message"]

    def test_patient_creation_returns_patient_profile(self):
        payload = {
            "auth0_user_id": "auth0|view_pat",
            "auth0_org_id": "org_view_test",
            "role": "patient",
            "email": "viewpat@example.com",
            "name": "Pat View",
        }
        response = self.client.post("/users", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        profile = response.json()["profile"]
        assert profile["name"] == "Pat View"
        assert "dob" in profile
        assert "medical_id" in profile


# ---------------------------------------------------------------------------
# GatewayAuthentication tests
# ---------------------------------------------------------------------------


class GatewayAuthenticationTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.auth = GatewayAuthentication()
        self.tenant = Tenant.objects.create(
            auth0_organization_id="org_auth_test",
            name="Auth Clinic",
        )
        self.user = User.objects.create_user(
            auth0_user_id="auth0|auth_doc",
            email="authdoc@example.com",
            tenant=self.tenant,
            role="doctor",
        )
        DoctorProfile.objects.create(user=self.user, name="Auth Doc")

    def test_raises_when_all_headers_absent(self) -> None:
        request = self.factory.get("/me/profile")
        with pytest.raises(AuthenticationFailed, match="Missing required gateway"):
            self.auth.authenticate(request)

    def test_raises_when_tenant_header_missing(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{HEADER_USER_ID: "auth0|auth_doc", HEADER_ROLE: "doctor"},  # type: ignore[arg-type]
        )
        with pytest.raises(AuthenticationFailed, match="Missing required gateway"):
            self.auth.authenticate(request)

    def test_raises_when_roles_header_missing(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{HEADER_USER_ID: "auth0|auth_doc", HEADER_TENANT_ID: "org_auth_test"},  # type: ignore[arg-type]
        )
        with pytest.raises(AuthenticationFailed, match="Missing required gateway"):
            self.auth.authenticate(request)

    def test_raises_when_user_not_found(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{  # type: ignore[arg-type]
                HEADER_USER_ID: "auth0|nonexistent",
                HEADER_TENANT_ID: "org_auth_test",
                HEADER_ROLE: "doctor",
            },
        )
        with pytest.raises(AuthenticationFailed, match="User not found"):
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
        with pytest.raises(AuthenticationFailed, match="User not found"):
            self.auth.authenticate(request)

    def test_raises_on_role_mismatch(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{  # type: ignore[arg-type]
                HEADER_USER_ID: "auth0|auth_doc",
                HEADER_TENANT_ID: "org_auth_test",
                HEADER_ROLE: "patient",
            },
        )
        with pytest.raises(AuthenticationFailed, match="User not found"):
            self.auth.authenticate(request)

    def test_returns_user_and_auth_on_success(self) -> None:
        request = self.factory.get(
            "/me/profile",
            **{  # type: ignore[arg-type]
                HEADER_USER_ID: "auth0|auth_doc",
                HEADER_TENANT_ID: "org_auth_test",
                HEADER_ROLE: "doctor",
            },
        )
        result = self.auth.authenticate(request)

        assert result is not None
        user, auth_info = result
        assert user.pk == self.user.pk
        assert auth_info["role"] == "doctor"
        assert auth_info["tenant_id"] == "org_auth_test"


# ---------------------------------------------------------------------------
# UpdateProfile use case tests
# ---------------------------------------------------------------------------


class UpdateProfileUseCaseTests(TestCase):
    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            auth0_organization_id="org_profile_test",
            name="Profile Clinic",
        )
        self.doctor = User.objects.create_user(
            auth0_user_id="auth0|profile_doc",
            email="profiledoc@example.com",
            tenant=self.tenant,
            role="doctor",
        )
        DoctorProfile.objects.create(user=self.doctor, name="Doc")
        self.patient = User.objects.create_user(
            auth0_user_id="auth0|profile_pat",
            email="profilepat@example.com",
            tenant=self.tenant,
            role="patient",
        )
        PatientProfile.objects.create(user=self.patient, name="Pat")
        self.use_case = UpdateProfile()

    def test_updates_doctor_fields(self) -> None:
        profile = self.use_case.execute(
            user=self.doctor,
            name="Updated",
            surname="Smith",
            specialization="Cardiology",
            license_number="LIC-001",
        )

        assert profile.name == "Updated"
        assert profile.surname == "Smith"
        assert profile.specialization == "Cardiology"
        assert profile.license_number == "LIC-001"

    def test_updates_patient_fields(self) -> None:
        profile = self.use_case.execute(
            user=self.patient,
            name="Updated Pat",
            surname="Jones",
            dob=datetime.date(1990, 5, 15),
            gender="male",
            medical_id="MED-123",
        )

        assert profile.name == "Updated Pat"
        assert profile.surname == "Jones"
        assert profile.dob == datetime.date(1990, 5, 15)
        assert profile.gender == "male"
        assert profile.medical_id == "MED-123"

    def test_noop_when_no_fields_provided(self) -> None:
        profile = self.use_case.execute(user=self.doctor)

        assert profile.name == "Doc"


# ---------------------------------------------------------------------------
# ProfileUpdateView integration tests
# ---------------------------------------------------------------------------


class ProfileUpdateViewTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            auth0_organization_id="org_patch_test",
            name="Patch Clinic",
        )
        self.doctor = User.objects.create_user(
            auth0_user_id="auth0|patch_doc",
            email="patchdoc@example.com",
            tenant=self.tenant,
            role="doctor",
        )
        DoctorProfile.objects.create(user=self.doctor, name="PatchDoc")
        self.patient = User.objects.create_user(
            auth0_user_id="auth0|patch_pat",
            email="patchpat@example.com",
            tenant=self.tenant,
            role="patient",
        )
        PatientProfile.objects.create(user=self.patient, name="PatchPat")

    def _gateway_headers(self, user: User) -> dict[str, str]:
        return {
            HEADER_USER_ID: user.auth0_user_id,
            HEADER_TENANT_ID: user.tenant.auth0_organization_id,
            HEADER_ROLE: user.role,
        }

    def test_doctor_profile_update_returns_200(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"name": "New Name", "specialization": "Cardiology"},
            format="json",
            **self._gateway_headers(self.doctor),  # type: ignore[arg-type]
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
        assert data["specialization"] == "Cardiology"

    def test_patient_profile_update_returns_200(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"name": "New Pat", "dob": "1990-05-15", "gender": "female"},
            format="json",
            **self._gateway_headers(self.patient),  # type: ignore[arg-type]
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Pat"
        assert data["dob"] == "1990-05-15"
        assert data["gender"] == "female"

    def test_unauthenticated_returns_401(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"name": "Hacker"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_tenant_header_returns_401(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"name": "Hacker"},
            format="json",
            **{HEADER_USER_ID: self.doctor.auth0_user_id, HEADER_ROLE: "doctor"},  # type: ignore[arg-type]
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_dob_returns_400(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"dob": "not-a-date"},
            format="json",
            **self._gateway_headers(self.patient),  # type: ignore[arg-type]
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unknown_fields_ignored_for_patient(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"license_number": "LIC-999"},
            format="json",
            **self._gateway_headers(self.patient),  # type: ignore[arg-type]
        )

        assert response.status_code == status.HTTP_200_OK
        assert "license_number" not in response.json()

    def test_unknown_fields_ignored_for_doctor(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"medical_id": "MED-999"},
            format="json",
            **self._gateway_headers(self.doctor),  # type: ignore[arg-type]
        )

        assert response.status_code == status.HTTP_200_OK
        assert "medical_id" not in response.json()

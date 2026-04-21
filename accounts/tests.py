import pytest
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.exceptions import TenantNotFound
from accounts.models import Tenant, User
from accounts.use_cases import ProvisionUser


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

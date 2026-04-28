from django.test import TestCase
from rest_framework import status

from tests.mixins import ApiClientMixin, TenantUsersMixin


class UserProvisionViewTests(ApiClientMixin, TenantUsersMixin, TestCase):
    tenant_auth0_organization_id = "org_view_test"
    tenant_name = "View Test Clinic"

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.valid_payload = {
            "auth0_user_id": "auth0|view_doc",
            "auth0_org_id": cls.tenant.auth0_organization_id,
            "role": "doctor",
            "email": "viewdoc@example.com",
            "name": "Dr. View",
        }

    def test_create_user_returns_201(self) -> None:
        response = self.client.post("/users", self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["auth0_user_id"], "auth0|view_doc")
        self.assertEqual(data["email"], "viewdoc@example.com")
        self.assertEqual(data["role"], "doctor")
        self.assertEqual(data["profile"]["name"], "Dr. View")
        self.assertIn("id", data["profile"])

    def test_existing_user_returns_200(self) -> None:
        self.client.post("/users", self.valid_payload, format="json")
        response = self.client.post("/users", self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["auth0_user_id"], "auth0|view_doc")

    def test_invalid_role_returns_400(self) -> None:
        payload = {**self.valid_payload, "role": "admin"}
        response = self.client.post("/users", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_field_returns_400(self) -> None:
        payload = {
            "auth0_user_id": "auth0|incomplete",
            "role": "doctor",
        }
        response = self.client.post("/users", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_tenant_returns_404(self) -> None:
        payload = {**self.valid_payload, "auth0_org_id": "org_does_not_exist"}
        response = self.client.post("/users", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("org_does_not_exist", response.json()["error"]["message"])

    def test_patient_creation_returns_patient_profile(self) -> None:
        payload = {
            "auth0_user_id": "auth0|view_pat",
            "auth0_org_id": self.tenant.auth0_organization_id,
            "role": "patient",
            "email": "viewpat@example.com",
            "name": "Pat View",
        }
        response = self.client.post("/users", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        profile = response.json()["profile"]
        self.assertEqual(profile["name"], "Pat View")
        self.assertIn("dob", profile)
        self.assertIn("medical_id", profile)

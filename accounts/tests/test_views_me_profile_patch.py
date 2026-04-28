from django.test import TestCase
from rest_framework import status

from tests.mixins import ApiClientMixin, GatewayAuthMixin, TenantUsersMixin


class ProfileUpdateViewTests(
    ApiClientMixin, GatewayAuthMixin, TenantUsersMixin, TestCase
):
    tenant_auth0_organization_id = "org_patch_test"
    tenant_name = "Patch Clinic"
    doctor_auth0_user_id = "auth0|patch_doc"
    doctor_email = "patchdoc@example.com"
    patient_auth0_user_id = "auth0|patch_pat"
    patient_email = "patchpat@example.com"
    doctor_profile_name = "PatchDoc"
    patient_profile_name = "PatchPat"

    def test_doctor_profile_update_returns_200(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"name": "New Name", "specialization": "Cardiology"},
            format="json",
            headers=self.headers_for(self.doctor_user),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "New Name")
        self.assertEqual(data["specialization"], "Cardiology")

    def test_patient_profile_update_returns_200(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"name": "New Pat", "dob": "1990-05-15", "gender": "female"},
            format="json",
            headers=self.headers_for(self.patient_user),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "New Pat")
        self.assertEqual(data["dob"], "1990-05-15")
        self.assertEqual(data["gender"], "female")

    def test_unauthenticated_returns_401(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"name": "Hacker"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_tenant_header_returns_401(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"name": "Hacker"},
            format="json",
            headers={"X-User-Id": self.doctor_user.auth0_user_id, "X-Role": "doctor"},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_dob_returns_400(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"dob": "not-a-date"},
            format="json",
            headers=self.headers_for(self.patient_user),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_fields_ignored_for_patient(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"license_number": "LIC-999"},
            format="json",
            headers=self.headers_for(self.patient_user),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("license_number", response.json())

    def test_unknown_fields_ignored_for_doctor(self) -> None:
        response = self.client.patch(
            "/me/profile",
            {"medical_id": "MED-999"},
            format="json",
            headers=self.headers_for(self.doctor_user),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("medical_id", response.json())

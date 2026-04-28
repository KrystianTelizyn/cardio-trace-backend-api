from django.test import TestCase
from rest_framework import status

from devices.models import DeviceAssignment
from tests.mixins import (
    ApiClientMixin,
    DevicesFixtureMixin,
    GatewayAuthMixin,
    TenantUsersMixin,
)


class AssignDeviceViewTests(
    ApiClientMixin,
    GatewayAuthMixin,
    TenantUsersMixin,
    DevicesFixtureMixin,
    TestCase,
):
    def test_assigns_device_201(self) -> None:
        response = self.client.post(
            "/device-assignments",
            data={
                "device_id": self.device.id,
                "patient_profile_id": self.patient_profile.id,
            },
            headers=self.headers_for(self.doctor_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assignment = DeviceAssignment.objects.get(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )
        self.assertEqual(assignment.device_id, self.device.id)
        self.assertEqual(assignment.patient_id, self.patient_profile.id)
        self.assertEqual(assignment.doctor_id, self.doctor_profile.id)
        self.assertEqual(assignment.tenant_id, self.tenant.id)

    def test_returns_401_for_unauthenticated_request(self) -> None:
        response = self.client.post(
            "/device-assignments",
            data={
                "device_id": self.device.id,
                "patient_profile_id": self.patient_profile.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_400_for_invalid_payload(self) -> None:
        response = self.client.post(
            "/device-assignments",
            data={"device_id": self.device.id},
            headers=self.headers_for(self.doctor_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_400_for_unknown_device(self) -> None:
        response = self.client.post(
            "/device-assignments",
            data={
                "device_id": 999999999,
                "patient_profile_id": self.patient_profile.id,
            },
            headers=self.headers_for(self.doctor_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_400_for_unknown_patient(self) -> None:
        response = self.client.post(
            "/device-assignments",
            data={
                "device_id": self.device.id,
                "patient_profile_id": 999999999,
            },
            headers=self.headers_for(self.doctor_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

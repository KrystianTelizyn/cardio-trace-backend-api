from django.test import TestCase
from rest_framework import status

from devices.models import DeviceAssignment
from tests.mixins import (
    ApiClientMixin,
    DevicesFixtureMixin,
    GatewayAuthMixin,
    TenantUsersMixin,
    WrongTenantMixin,
)


class DeleteDeviceAssignmentViewTests(
    ApiClientMixin,
    GatewayAuthMixin,
    TenantUsersMixin,
    WrongTenantMixin,
    DevicesFixtureMixin,
    TestCase,
):
    def test_deletes_device_assignment_204(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )

        response = self.client.delete(
            f"/device-assignments/{assignment.id}",
            headers=self.headers_for(self.doctor_user),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DeviceAssignment.objects.filter(id=assignment.id).exists())

    def test_returns_404_for_assignment_in_other_tenant(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )

        response = self.client.delete(
            f"/device-assignments/{assignment.id}",
            headers=self.headers_for(self.other_doctor_user),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json()["error"]["code"],
            "device_assignment_not_found",
        )
        self.assertTrue(DeviceAssignment.objects.filter(id=assignment.id).exists())

    def test_after_delete_device_can_be_assigned_again(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )

        delete_response = self.client.delete(
            f"/device-assignments/{assignment.id}",
            headers=self.headers_for(self.doctor_user),
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        # Re-assign should succeed now that the previous assignment row is gone.
        assign_response = self.client.post(
            "/device-assignments",
            data={
                "device_id": self.device.id,
                "patient_profile_id": self.patient_profile.id,
            },
            headers=self.headers_for(self.doctor_user),
            format="json",
        )
        self.assertEqual(assign_response.status_code, status.HTTP_201_CREATED)

    def test_returns_401_for_unauthenticated_request(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )
        response = self.client.delete(f"/device-assignments/{assignment.id}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

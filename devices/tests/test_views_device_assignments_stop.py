from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from devices.models import DeviceAssignment
from tests.mixins import (
    ApiClientMixin,
    DevicesFixtureMixin,
    GatewayAuthMixin,
    TenantUsersMixin,
    WrongTenantMixin,
)


class StopDeviceAssignmentViewTests(
    ApiClientMixin,
    GatewayAuthMixin,
    TenantUsersMixin,
    WrongTenantMixin,
    DevicesFixtureMixin,
    TestCase,
):
    def test_stops_device_assignment_200(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )

        response = self.client.patch(
            f"/device-assignments/{assignment.id}",
            headers=self.headers_for(self.doctor_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignment.refresh_from_db()
        self.assertIsNotNone(assignment.unassigned_at)

    def test_returns_404_for_assignment_in_other_tenant(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )

        response = self.client.patch(
            f"/device-assignments/{assignment.id}",
            headers=self.headers_for(self.other_doctor_user),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json()["error"]["code"],
            "device_assignment_not_found",
        )
        assignment.refresh_from_db()
        self.assertIsNone(assignment.unassigned_at)

    def test_after_stop_device_can_be_assigned_again(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )

        stop_response = self.client.patch(
            f"/device-assignments/{assignment.id}",
            headers=self.headers_for(self.doctor_user),
        )
        self.assertEqual(stop_response.status_code, status.HTTP_200_OK)

        # Re-assign should succeed now that the previous assignment is stopped.
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

    def test_returns_409_for_already_stopped_assignment(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=timezone.now(),
        )
        response = self.client.patch(
            f"/device-assignments/{assignment.id}",
            headers=self.headers_for(self.doctor_user),
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.json()["error"]["code"],
            "device_assignment_already_stopped",
        )

    def test_returns_401_for_unauthenticated_request(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )
        response = self.client.patch(f"/device-assignments/{assignment.id}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

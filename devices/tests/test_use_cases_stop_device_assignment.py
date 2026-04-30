from django.test import TestCase
from django.utils import timezone

from devices.exceptions import (
    DeviceAssignmentAlreadyStoppedError,
    DeviceAssignmentNotFoundError,
)
from devices.models import DeviceAssignment
from devices.use_cases import StopDeviceAssignment
from tests.factories import TenantFactory
from tests.mixins import DevicesFixtureMixin, TenantUsersMixin


class StopDeviceAssignmentUseCaseTests(
    TenantUsersMixin,
    DevicesFixtureMixin,
    TestCase,
):
    def test_stops_device_assignment(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )

        updated = StopDeviceAssignment().execute(
            assignment_id=assignment.id,
            tenant=self.tenant,
        )

        self.assertIsNotNone(updated.unassigned_at)

    def test_raises_not_found_for_assignment_in_other_tenant(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )

        other_tenant = TenantFactory()

        with self.assertRaises(DeviceAssignmentNotFoundError):
            StopDeviceAssignment().execute(
                assignment_id=assignment.id,
                tenant=other_tenant,
            )

        assignment.refresh_from_db()
        self.assertIsNone(assignment.unassigned_at)

    def test_raises_when_assignment_already_stopped(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=timezone.now(),
        )

        with self.assertRaises(DeviceAssignmentAlreadyStoppedError):
            StopDeviceAssignment().execute(
                assignment_id=assignment.id,
                tenant=self.tenant,
            )

from django.test import TestCase

from devices.exceptions import DeviceAssignmentNotFoundError
from devices.models import DeviceAssignment
from devices.use_cases import DeleteDeviceAssignment
from tests.factories import TenantFactory
from tests.mixins import DevicesFixtureMixin, TenantUsersMixin


class DeleteDeviceAssignmentUseCaseTests(
    TenantUsersMixin,
    DevicesFixtureMixin,
    TestCase,
):
    def test_deletes_device_assignment(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )

        DeleteDeviceAssignment().execute(
            assignment_id=assignment.id,
            tenant=self.tenant,
        )

        self.assertFalse(DeviceAssignment.objects.filter(id=assignment.id).exists())

    def test_raises_not_found_for_assignment_in_other_tenant(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )

        other_tenant = TenantFactory()

        with self.assertRaises(DeviceAssignmentNotFoundError):
            DeleteDeviceAssignment().execute(
                assignment_id=assignment.id,
                tenant=other_tenant,
            )

        self.assertTrue(DeviceAssignment.objects.filter(id=assignment.id).exists())

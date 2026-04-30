from django.test import TestCase
from django.utils import timezone

from devices.exceptions import (
    DeviceAlreadyActivelyAssignedError,
    DeviceNotFoundError,
    PatientAlreadyHasActiveDeviceAssignmentError,
    PatientProfileNotFoundError,
)
from devices.use_cases import AssignDevice
from tests.mixins import DevicesFixtureMixin, TenantUsersMixin
from tests.factories import DeviceFactory, PatientProfileFactory, PatientUserFactory


class AssignDeviceUseCaseTests(TenantUsersMixin, DevicesFixtureMixin, TestCase):
    def test_assigns_device_to_patient(self) -> None:
        device_assignment = AssignDevice().execute(
            device_id=self.device.id,
            patient_profile_id=self.patient_profile.id,
            doctor_profile=self.doctor_profile,
            tenant=self.tenant,
        )
        self.assertEqual(device_assignment.device, self.device)
        self.assertEqual(device_assignment.patient, self.patient_profile)
        self.assertEqual(device_assignment.doctor, self.doctor_profile)
        self.assertEqual(device_assignment.tenant, self.tenant)
        self.assertIsNotNone(device_assignment.assigned_at)
        self.assertIsNone(device_assignment.unassigned_at)

    def test_raises_exception_on_invalid_device(self) -> None:
        with self.assertRaises(DeviceNotFoundError):
            AssignDevice().execute(
                device_id=9999999999,
                patient_profile_id=self.patient_profile.id,
                doctor_profile=self.doctor_profile,
                tenant=self.tenant,
            )

    def test_raises_exception_on_invalid_patient_profile(self) -> None:
        with self.assertRaises(PatientProfileNotFoundError):
            AssignDevice().execute(
                device_id=self.device.id,
                patient_profile_id=9999999999,
                doctor_profile=self.doctor_profile,
                tenant=self.tenant,
            )

    def test_raises_exception_when_device_already_has_active_assignment(self) -> None:
        AssignDevice().execute(
            device_id=self.device.id,
            patient_profile_id=self.patient_profile.id,
            doctor_profile=self.doctor_profile,
            tenant=self.tenant,
        )

        other_patient_user = PatientUserFactory(tenant=self.tenant)
        other_patient_profile = PatientProfileFactory(user=other_patient_user)
        with self.assertRaises(DeviceAlreadyActivelyAssignedError):
            AssignDevice().execute(
                device_id=self.device.id,
                patient_profile_id=other_patient_profile.id,
                doctor_profile=self.doctor_profile,
                tenant=self.tenant,
            )

    def test_raises_exception_when_patient_already_has_active_assignment(self) -> None:
        other_device = DeviceFactory(tenant=self.tenant)
        AssignDevice().execute(
            device_id=self.device.id,
            patient_profile_id=self.patient_profile.id,
            doctor_profile=self.doctor_profile,
            tenant=self.tenant,
        )

        with self.assertRaises(PatientAlreadyHasActiveDeviceAssignmentError):
            AssignDevice().execute(
                device_id=other_device.id,
                patient_profile_id=self.patient_profile.id,
                doctor_profile=self.doctor_profile,
                tenant=self.tenant,
            )

    def test_allows_reassignment_when_existing_assignment_is_stopped(self) -> None:
        first_assignment = AssignDevice().execute(
            device_id=self.device.id,
            patient_profile_id=self.patient_profile.id,
            doctor_profile=self.doctor_profile,
            tenant=self.tenant,
        )
        first_assignment.unassigned_at = timezone.now()
        first_assignment.save(update_fields=["unassigned_at"])

        reassigned = AssignDevice().execute(
            device_id=self.device.id,
            patient_profile_id=self.patient_profile.id,
            doctor_profile=self.doctor_profile,
            tenant=self.tenant,
        )

        self.assertNotEqual(first_assignment.id, reassigned.id)

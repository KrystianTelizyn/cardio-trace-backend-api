from django.test import TestCase

from devices.exceptions import (
    DeviceAssignmentAlreadyExistsError,
    DeviceNotFoundError,
    PatientProfileNotFoundError,
)
from devices.use_cases import AssignDevice
from tests.mixins import DevicesFixtureMixin, TenantUsersMixin
from tests.factories import PatientProfileFactory, PatientUserFactory


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

    def test_raises_exception_on_duplicate_assignment(self) -> None:
        AssignDevice().execute(
            device_id=self.device.id,
            patient_profile_id=self.patient_profile.id,
            doctor_profile=self.doctor_profile,
            tenant=self.tenant,
        )

        with self.assertRaises(DeviceAssignmentAlreadyExistsError):
            AssignDevice().execute(
                device_id=self.device.id,
                patient_profile_id=self.patient_profile.id,
                doctor_profile=self.doctor_profile,
                tenant=self.tenant,
            )

    def test_raises_exception_on_duplicate_assignment_for_different_patient(
        self,
    ) -> None:
        AssignDevice().execute(
            device_id=self.device.id,
            patient_profile_id=self.patient_profile.id,
            doctor_profile=self.doctor_profile,
            tenant=self.tenant,
        )

        other_patient_user = PatientUserFactory(tenant=self.tenant)
        other_patient_profile = PatientProfileFactory(user=other_patient_user)

        with self.assertRaises(DeviceAssignmentAlreadyExistsError):
            AssignDevice().execute(
                device_id=self.device.id,
                patient_profile_id=other_patient_profile.id,
                doctor_profile=self.doctor_profile,
                tenant=self.tenant,
            )

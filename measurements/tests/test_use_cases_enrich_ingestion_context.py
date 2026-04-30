from django.test import TestCase

from devices.exceptions import DeviceIdentityNotFoundError
from measurements.use_cases import EnrichIngestionContext
from tests.factories import DeviceFactory, DoctorProfileFactory
from tests.mixins import (
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TenantUsersMixin,
    WrongTenantMixin,
)


class EnrichIngestionContextUseCaseTests(
    TenantUsersMixin,
    WrongTenantMixin,
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TestCase,
):
    def test_returns_device_uid_and_active_session_uid(self) -> None:
        assignment = self.create_active_assignment()
        session = self.create_measurement_session(device_assignment=assignment)

        device_uid, session_uid = EnrichIngestionContext().execute(
            tenant=self.tenant,
            serial_number=self.device.serial_number,
            brand=self.device.brand,
        )

        self.assertEqual(device_uid, self.device.uid)
        self.assertEqual(session_uid, session.id)

    def test_returns_null_session_uid_when_no_active_session(self) -> None:
        device_uid, session_uid = EnrichIngestionContext().execute(
            tenant=self.tenant,
            serial_number=self.device.serial_number,
            brand=self.device.brand,
        )

        self.assertEqual(device_uid, self.device.uid)
        self.assertIsNone(session_uid)

    def test_raises_for_unknown_device_identity(self) -> None:
        with self.assertRaises(DeviceIdentityNotFoundError):
            EnrichIngestionContext().execute(
                tenant=self.tenant,
                serial_number="missing-sn",
                brand="missing-brand",
            )

    def test_is_tenant_scoped_for_same_serial_and_brand(self) -> None:
        other_device = DeviceFactory(
            tenant=self.other_tenant,
            serial_number=self.device.serial_number,
            brand=self.device.brand,
            name="Other Tenant Device",
        )
        other_doctor_profile = DoctorProfileFactory(user=self.other_doctor_user)
        other_assignment = self.create_active_assignment(
            device=other_device,
            patient=self.other_patient_profile,
            doctor=other_doctor_profile,
            tenant=self.other_tenant,
        )
        other_session = self.create_measurement_session(
            tenant=self.other_tenant,
            device_assignment=other_assignment,
        )

        device_uid, session_uid = EnrichIngestionContext().execute(
            tenant=self.tenant,
            serial_number=self.device.serial_number,
            brand=self.device.brand,
        )

        self.assertEqual(device_uid, self.device.uid)
        self.assertNotEqual(device_uid, other_device.uid)
        self.assertNotEqual(session_uid, other_session.id)

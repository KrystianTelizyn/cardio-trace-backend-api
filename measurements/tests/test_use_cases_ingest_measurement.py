from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase

from devices.models import DeviceAssignment
from measurements.exceptions import (
    DeviceBySerialNotFoundError,
    DeviceHasNoActiveAssignmentError,
)
from measurements.use_cases import IngestMeasurement
from tests.factories import (
    DeviceFactory,
    DoctorProfileFactory,
    PatientProfileFactory,
    PatientUserFactory,
)
from tests.mixins import DevicesFixtureMixin, TenantUsersMixin, WrongTenantMixin


class IngestMeasurementUseCaseTests(
    TenantUsersMixin, WrongTenantMixin, DevicesFixtureMixin, TestCase
):
    def test_creates_measurement_for_device_assignment(self) -> None:
        DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )

        timestamp = datetime(2026, 1, 10, 12, 30, tzinfo=ZoneInfo("UTC"))
        measurement = IngestMeasurement().execute(
            serial_number=self.device.serial_number,
            brand=self.device.brand,
            tenant=self.tenant,
            timestamp=timestamp,
            heart_rate=75.5,
            hrv=42.3,
        )

        self.assertEqual(measurement.device, self.device)
        self.assertEqual(measurement.patient, self.patient_profile)
        self.assertEqual(measurement.tenant, self.tenant)
        self.assertEqual(measurement.timestamp, timestamp)
        self.assertEqual(measurement.heart_rate, 75.5)
        self.assertEqual(measurement.hrv, 42.3)

    def test_raises_device_not_found_for_unknown_serial_number(self) -> None:
        with self.assertRaises(DeviceBySerialNotFoundError):
            IngestMeasurement().execute(
                serial_number="UNKNOWN-SN",
                brand=self.device.brand,
                tenant=self.tenant,
                timestamp=datetime.now(tz=ZoneInfo("UTC")),
                heart_rate=70.0,
                hrv=30.0,
            )

    def test_raises_conflict_when_device_has_no_assignment(self) -> None:
        with self.assertRaises(DeviceHasNoActiveAssignmentError):
            IngestMeasurement().execute(
                serial_number=self.device.serial_number,
                brand=self.device.brand,
                tenant=self.tenant,
                timestamp=datetime.now(tz=ZoneInfo("UTC")),
                heart_rate=70.0,
                hrv=30.0,
            )

    def test_resolves_device_assignment_within_tenant(self) -> None:
        # Primary tenant assignment
        DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )

        # Another tenant with a device using the same serial number
        other_device = DeviceFactory(
            tenant=self.other_tenant,
            serial_number=self.device.serial_number,
            brand=self.device.brand,
            name="Other Device",
        )
        other_doctor_profile = DoctorProfileFactory(
            user=self.other_doctor_user,
            name="Other Doc",
        )
        DeviceAssignment.objects.create(
            device=other_device,
            patient=self.other_patient_profile,
            doctor=other_doctor_profile,
            tenant=self.other_tenant,
        )

        timestamp = datetime(2026, 1, 10, 12, 30, tzinfo=ZoneInfo("UTC"))
        measurement = IngestMeasurement().execute(
            serial_number=self.device.serial_number,
            brand=self.device.brand,
            tenant=self.tenant,
            timestamp=timestamp,
            heart_rate=75.5,
            hrv=42.3,
        )

        self.assertEqual(measurement.tenant, self.tenant)
        self.assertEqual(measurement.patient, self.patient_profile)

    def test_resolves_device_assignment_by_brand_within_tenant(self) -> None:
        """
        The same `serial_number` can exist across different brands inside a tenant.
        In that case, ingestion must resolve the device/assignment by both fields.
        """

        # Brand under test (brand1): uses the fixture device + patient
        DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )

        # Another brand (brand2) using the same serial_number
        brand2_device = DeviceFactory(
            tenant=self.tenant,
            serial_number=self.device.serial_number,
            brand="Brand-2",
            name="Other Brand Device",
        )
        brand2_patient_user = PatientUserFactory(tenant=self.tenant)
        brand2_patient_profile = PatientProfileFactory(
            user=brand2_patient_user, name="Brand2 Patient"
        )

        DeviceAssignment.objects.create(
            device=brand2_device,
            patient=brand2_patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
        )

        timestamp = datetime(2026, 1, 10, 12, 30, tzinfo=ZoneInfo("UTC"))
        measurement = IngestMeasurement().execute(
            serial_number=self.device.serial_number,
            brand=self.device.brand,
            tenant=self.tenant,
            timestamp=timestamp,
            heart_rate=75.5,
            hrv=42.3,
        )

        self.assertEqual(measurement.tenant, self.tenant)
        self.assertEqual(measurement.patient, self.patient_profile)

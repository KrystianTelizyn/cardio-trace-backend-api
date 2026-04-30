from datetime import datetime
import uuid
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone

from devices.models import DeviceAssignment
from measurements.exceptions import (
    MeasurementDroppedSessionStopped,
    MeasurementSessionNotFoundError,
)
from measurements.models import MeasurementSession
from measurements.use_cases import IngestMeasurement
from tests.factories import DeviceFactory, DoctorProfileFactory
from tests.mixins import DevicesFixtureMixin, TenantUsersMixin, WrongTenantMixin


class IngestMeasurementUseCaseTests(
    TenantUsersMixin, WrongTenantMixin, DevicesFixtureMixin, TestCase
):
    def test_creates_measurement_for_session(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )
        measurement_session = MeasurementSession.objects.create(
            tenant=self.tenant,
            device_assignment=assignment,
            started_at=timezone.now(),
        )

        timestamp = datetime(2026, 1, 10, 12, 30, tzinfo=ZoneInfo("UTC"))
        measurement = IngestMeasurement().execute(
            measurement_session_id=measurement_session.id,
            tenant=self.tenant,
            timestamp=timestamp,
            heart_rate=75.5,
            hrv=42.3,
        )

        self.assertIsInstance(measurement.id, uuid.UUID)
        self.assertEqual(measurement.measurement_session, measurement_session)
        self.assertEqual(measurement.tenant, self.tenant)
        self.assertEqual(measurement.timestamp, timestamp)
        self.assertEqual(measurement.heart_rate, 75.5)
        self.assertEqual(measurement.hrv, 42.3)

    def test_raises_session_not_found_for_unknown_id(self) -> None:
        with self.assertRaises(MeasurementSessionNotFoundError):
            IngestMeasurement().execute(
                measurement_session_id="01JZZZZZZZZZZZZZZZZZZZZZZZ",
                tenant=self.tenant,
                timestamp=datetime.now(tz=ZoneInfo("UTC")),
                heart_rate=70.0,
                hrv=30.0,
            )

    def test_raises_accepted_drop_when_session_is_stopped(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )
        measurement_session = MeasurementSession.objects.create(
            tenant=self.tenant,
            device_assignment=assignment,
            started_at=timezone.now(),
            stopped_at=timezone.now(),
        )

        with self.assertRaises(MeasurementDroppedSessionStopped):
            IngestMeasurement().execute(
                measurement_session_id=measurement_session.id,
                tenant=self.tenant,
                timestamp=datetime.now(tz=ZoneInfo("UTC")),
                heart_rate=70.0,
                hrv=30.0,
            )

    def test_resolves_measurement_session_within_tenant(self) -> None:
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )
        measurement_session = MeasurementSession.objects.create(
            tenant=self.tenant,
            device_assignment=assignment,
            started_at=timezone.now(),
        )

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
        other_assignment = DeviceAssignment.objects.create(
            device=other_device,
            patient=self.other_patient_profile,
            doctor=other_doctor_profile,
            tenant=self.other_tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )
        MeasurementSession.objects.create(
            tenant=self.other_tenant,
            device_assignment=other_assignment,
            started_at=timezone.now(),
        )

        timestamp = datetime(2026, 1, 10, 12, 30, tzinfo=ZoneInfo("UTC"))
        measurement = IngestMeasurement().execute(
            measurement_session_id=measurement_session.id,
            tenant=self.tenant,
            timestamp=timestamp,
            heart_rate=75.5,
            hrv=42.3,
        )

        self.assertEqual(measurement.tenant, self.tenant)
        self.assertEqual(measurement.measurement_session, measurement_session)

from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase

from measurements.exceptions import (
    ActiveMeasurementSessionAlreadyExistsError,
    MeasurementSessionAssignmentNotFoundError,
    MeasurementSessionStartOutsideAssignmentWindowError,
)
from measurements.use_cases import StartMeasurementSession
from tests.mixins import DevicesFixtureMixin, MeasurementFixturesMixin, TenantUsersMixin


class StartMeasurementSessionUseCaseTests(
    TenantUsersMixin,
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TestCase,
):
    def test_starts_measurement_session(self) -> None:
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC")),
        )

        started_at = datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC"))
        session = StartMeasurementSession().execute(
            device_assignment_id=assignment.id,
            tenant=self.tenant,
            started_at=started_at,
        )

        self.assertEqual(session.tenant, self.tenant)
        self.assertEqual(session.device_assignment, assignment)
        self.assertEqual(session.started_at, started_at)
        self.assertIsNone(session.stopped_at)
        self.assertEqual(session.status, "active")

    def test_raises_not_found_for_unknown_assignment(self) -> None:
        with self.assertRaises(MeasurementSessionAssignmentNotFoundError):
            StartMeasurementSession().execute(
                device_assignment_id=999999999,
                tenant=self.tenant,
            )

    def test_raises_bad_request_for_start_before_assignment(self) -> None:
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC")),
        )

        with self.assertRaises(MeasurementSessionStartOutsideAssignmentWindowError):
            StartMeasurementSession().execute(
                device_assignment_id=assignment.id,
                tenant=self.tenant,
                started_at=datetime(2026, 1, 10, 9, 59, tzinfo=ZoneInfo("UTC")),
            )

    def test_raises_conflict_for_existing_active_session(self) -> None:
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC")),
        )
        StartMeasurementSession().execute(
            device_assignment_id=assignment.id,
            tenant=self.tenant,
            started_at=datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC")),
        )

        with self.assertRaises(ActiveMeasurementSessionAlreadyExistsError):
            StartMeasurementSession().execute(
                device_assignment_id=assignment.id,
                tenant=self.tenant,
                started_at=datetime(2026, 1, 10, 12, 0, tzinfo=ZoneInfo("UTC")),
            )

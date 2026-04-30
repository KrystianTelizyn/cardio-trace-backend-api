from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase

from measurements.exceptions import (
    MeasurementSessionInvalidStopTimeError,
    MeasurementSessionNotFoundError,
)
from measurements.use_cases import StopMeasurementSession
from tests.mixins import DevicesFixtureMixin, MeasurementFixturesMixin, TenantUsersMixin


class StopMeasurementSessionUseCaseTests(
    TenantUsersMixin,
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TestCase,
):
    def test_stops_active_measurement_session(self) -> None:
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC"))
        )
        session = self.create_measurement_session(
            device_assignment=assignment,
            started_at=datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC")),
        )

        stopped = StopMeasurementSession().execute(
            measurement_session_id=session.id,
            tenant=self.tenant,
            stopped_at=datetime(2026, 1, 10, 12, 0, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(stopped.id, session.id)
        self.assertEqual(
            stopped.stopped_at,
            datetime(2026, 1, 10, 12, 0, tzinfo=ZoneInfo("UTC")),
        )
        self.assertEqual(stopped.status, "stopped")

    def test_returns_existing_session_when_already_stopped(self) -> None:
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC"))
        )
        session = self.create_measurement_session(
            device_assignment=assignment,
            started_at=datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC")),
            stopped_at=datetime(2026, 1, 10, 11, 30, tzinfo=ZoneInfo("UTC")),
        )

        result = StopMeasurementSession().execute(
            measurement_session_id=session.id,
            tenant=self.tenant,
            stopped_at=datetime(2026, 1, 10, 12, 0, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(result.id, session.id)
        self.assertEqual(
            result.stopped_at,
            datetime(2026, 1, 10, 11, 30, tzinfo=ZoneInfo("UTC")),
        )

    def test_raises_not_found_for_unknown_session(self) -> None:
        with self.assertRaises(MeasurementSessionNotFoundError):
            StopMeasurementSession().execute(
                measurement_session_id="01JZZZZZZZZZZZZZZZZZZZZZZZ",
                tenant=self.tenant,
            )

    def test_raises_bad_request_for_invalid_stop_time(self) -> None:
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC"))
        )
        session = self.create_measurement_session(
            device_assignment=assignment,
            started_at=datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC")),
        )

        with self.assertRaises(MeasurementSessionInvalidStopTimeError):
            StopMeasurementSession().execute(
                measurement_session_id=session.id,
                tenant=self.tenant,
                stopped_at=datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC")),
            )

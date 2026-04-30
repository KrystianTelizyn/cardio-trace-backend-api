from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase
from rest_framework import status

from tests.mixins import (
    ApiClientMixin,
    DevicesFixtureMixin,
    GatewayAuthMixin,
    MeasurementFixturesMixin,
    TenantUsersMixin,
)


class MeasurementSessionStopViewTests(
    ApiClientMixin,
    GatewayAuthMixin,
    TenantUsersMixin,
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TestCase,
):
    def setUp(self) -> None:
        super().setUp()
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC"))
        )
        self.active_session = self.create_measurement_session(
            device_assignment=assignment,
            started_at=datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC")),
        )

    def test_stops_measurement_session_200(self) -> None:
        response = self.client.patch(
            f"/measurement-sessions/{self.active_session.id}",
            data={"stopped_at": "2026-01-10T12:00:00Z"},
            headers=self.headers_for(self.patient_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["id"], self.active_session.id)
        self.assertEqual(data["started_at"], "2026-01-10T11:00:00Z")
        self.assertEqual(data["stopped_at"], "2026-01-10T12:00:00Z")
        self.assertEqual(data["status"], "stopped")

    def test_returns_200_for_already_stopped_session(self) -> None:
        self.client.patch(
            f"/measurement-sessions/{self.active_session.id}",
            data={"stopped_at": "2026-01-10T11:30:00Z"},
            headers=self.headers_for(self.patient_user),
            format="json",
        )
        response = self.client.patch(
            f"/measurement-sessions/{self.active_session.id}",
            data={"stopped_at": "2026-01-10T12:00:00Z"},
            headers=self.headers_for(self.patient_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], self.active_session.id)
        self.assertEqual(response.json()["stopped_at"], "2026-01-10T11:30:00Z")
        self.assertEqual(response.json()["status"], "stopped")

    def test_returns_404_for_unknown_session(self) -> None:
        response = self.client.patch(
            "/measurement-sessions/01JZZZZZZZZZZZZZZZZZZZZZZZ",
            data={"stopped_at": "2026-01-10T12:00:00Z"},
            headers=self.headers_for(self.patient_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json()["error"]["code"],
            "measurement_session_not_found",
        )

    def test_returns_400_for_invalid_stop_time(self) -> None:
        response = self.client.patch(
            f"/measurement-sessions/{self.active_session.id}",
            data={"stopped_at": "2026-01-10T11:00:00Z"},
            headers=self.headers_for(self.patient_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["error"]["code"],
            "measurement_session_invalid_stop_time",
        )

    def test_returns_401_for_unauthenticated_request(self) -> None:
        response = self.client.patch(
            f"/measurement-sessions/{self.active_session.id}",
            data={"stopped_at": "2026-01-10T12:00:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

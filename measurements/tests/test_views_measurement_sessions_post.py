from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase
from rest_framework import status

from measurements.models import MeasurementSession
from tests.mixins import (
    ApiClientMixin,
    DevicesFixtureMixin,
    GatewayAuthMixin,
    MeasurementFixturesMixin,
    TenantUsersMixin,
)


class MeasurementSessionStartViewTests(
    ApiClientMixin,
    GatewayAuthMixin,
    TenantUsersMixin,
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TestCase,
):
    def setUp(self) -> None:
        super().setUp()
        self.assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC")),
        )
        self.valid_payload = {
            "device_assignment_id": self.assignment.id,
            "started_at": "2026-01-10T11:00:00Z",
        }

    def test_starts_measurement_session_201(self) -> None:
        response = self.client.post(
            "/measurement-sessions",
            data=self.valid_payload,
            headers=self.headers_for(self.patient_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["started_at"], self.valid_payload["started_at"])
        self.assertEqual(data["status"], "active")

        session = MeasurementSession.objects.get(id=data["id"])
        self.assertEqual(session.tenant, self.tenant)
        self.assertEqual(session.device_assignment, self.assignment)

    def test_starts_measurement_session_when_started_at_missing(self) -> None:
        response = self.client.post(
            "/measurement-sessions",
            data={"device_assignment_id": self.assignment.id},
            headers=self.headers_for(self.patient_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("id", data)
        self.assertIsNotNone(data["started_at"])
        self.assertEqual(data["status"], "active")

        session = MeasurementSession.objects.get(id=data["id"])
        self.assertEqual(session.tenant, self.tenant)
        self.assertEqual(session.device_assignment, self.assignment)
        self.assertIsNotNone(session.started_at)
        self.assertIsNone(session.stopped_at)

    def test_returns_400_for_invalid_payload(self) -> None:
        response = self.client.post(
            "/measurement-sessions",
            data={},
            headers=self.headers_for(self.patient_user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_404_for_unknown_assignment(self) -> None:
        response = self.client.post(
            "/measurement-sessions",
            data={"device_assignment_id": 999999999},
            headers=self.headers_for(self.patient_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json()["error"]["code"],
            "measurement_session_assignment_not_found",
        )

    def test_returns_400_for_started_at_outside_assignment_window(self) -> None:
        response = self.client.post(
            "/measurement-sessions",
            data={
                "device_assignment_id": self.assignment.id,
                "started_at": "2026-01-10T09:59:00Z",
            },
            headers=self.headers_for(self.patient_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["error"]["code"],
            "measurement_session_start_outside_assignment_window",
        )

    def test_returns_409_for_existing_active_session(self) -> None:
        self.client.post(
            "/measurement-sessions",
            data=self.valid_payload,
            headers=self.headers_for(self.patient_user),
            format="json",
        )
        response = self.client.post(
            "/measurement-sessions",
            data=self.valid_payload,
            headers=self.headers_for(self.patient_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.json()["error"]["code"],
            "active_measurement_session_already_exists",
        )

    def test_returns_401_for_unauthenticated_request(self) -> None:
        response = self.client.post(
            "/measurement-sessions",
            data=self.valid_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

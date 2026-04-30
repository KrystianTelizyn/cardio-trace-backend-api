from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase
from rest_framework import status

from measurements.models import Measurement, MeasurementSession
from tests.mixins import (
    ApiClientMixin,
    DevicesFixtureMixin,
    GatewayAuthMixin,
    MeasurementFixturesMixin,
    TenantUsersMixin,
)


class MeasurementSessionLifecycleFlowTests(
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
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC"))
        )

    def test_start_ingest_stop_and_drop_after_stop(self) -> None:
        start_response = self.client.post(
            "/measurement-sessions",
            data={
                "device_assignment_id": self.assignment.id,
                "started_at": "2026-01-10T11:00:00Z",
            },
            headers=self.headers_for(self.patient_user),
            format="json",
        )
        self.assertEqual(start_response.status_code, status.HTTP_201_CREATED)
        session_id = start_response.json()["id"]
        self.assertEqual(start_response.json()["status"], "active")

        session = MeasurementSession.objects.get(id=session_id)
        self.assertIsNone(session.stopped_at)

        ingest_response_1 = self.client.post(
            "/measurements",
            data={
                "measurement_session_id": session_id,
                "timestamp": "2026-01-10T11:10:00Z",
                "heart_rate": 72.5,
                "hrv": 39.1,
            },
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )
        self.assertEqual(ingest_response_1.status_code, status.HTTP_201_CREATED)

        ingest_response_2 = self.client.post(
            "/measurements",
            data={
                "measurement_session_id": session_id,
                "timestamp": "2026-01-10T11:12:00Z",
                "heart_rate": 73.8,
                "hrv": 38.6,
            },
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )
        self.assertEqual(ingest_response_2.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            Measurement.objects.filter(measurement_session_id=session_id).count(),
            2,
        )

        stop_response = self.client.patch(
            f"/measurement-sessions/{session_id}",
            data={"stopped_at": "2026-01-10T11:15:00Z"},
            headers=self.headers_for(self.patient_user),
            format="json",
        )
        self.assertEqual(stop_response.status_code, status.HTTP_200_OK)
        self.assertEqual(stop_response.json()["status"], "stopped")
        self.assertEqual(stop_response.json()["id"], session_id)

        session.refresh_from_db()
        self.assertEqual(
            session.stopped_at,
            datetime(2026, 1, 10, 11, 15, tzinfo=ZoneInfo("UTC")),
        )

        ingest_after_stop = self.client.post(
            "/measurements",
            data={
                "measurement_session_id": session_id,
                "timestamp": "2026-01-10T11:16:00Z",
                "heart_rate": 75.2,
                "hrv": 37.4,
            },
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )
        self.assertEqual(ingest_after_stop.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(
            ingest_after_stop.json()["error"]["code"],
            "measurement_dropped_session_stopped",
        )
        self.assertEqual(
            Measurement.objects.filter(measurement_session_id=session_id).count(),
            2,
        )

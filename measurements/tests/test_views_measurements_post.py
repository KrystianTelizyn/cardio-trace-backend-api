import uuid

from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from devices.models import DeviceAssignment
from measurements.models import Measurement, MeasurementSession
from tests.mixins import ApiClientMixin, DevicesFixtureMixin, TenantUsersMixin


class MeasurementIngestViewTests(
    ApiClientMixin,
    TenantUsersMixin,
    DevicesFixtureMixin,
    TestCase,
):
    def setUp(self) -> None:
        super().setUp()
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )
        self.measurement_session = MeasurementSession.objects.create(
            tenant=self.tenant,
            device_assignment=assignment,
            started_at=timezone.now(),
        )
        self.valid_payload = {
            "measurement_session_id": self.measurement_session.id,
            "timestamp": "2026-01-10T12:30:00Z",
            "heart_rate": 74.2,
            "hrv": 40.1,
        }

    def test_ingests_measurement_201(self) -> None:
        response = self.client.post(
            "/measurements",
            data=self.valid_payload,
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["measurement_session_id"], self.measurement_session.id)
        self.assertEqual(data["heart_rate"], self.valid_payload["heart_rate"])
        self.assertEqual(data["hrv"], self.valid_payload["hrv"])
        self.assertIsInstance(uuid.UUID(data["id"]), uuid.UUID)

        measurement = Measurement.objects.get(id=data["id"])
        self.assertEqual(
            measurement.measurement_session_id, self.measurement_session.id
        )
        self.assertEqual(measurement.tenant_id, self.tenant.id)

    def test_returns_400_for_invalid_payload(self) -> None:
        response = self.client.post(
            "/measurements",
            data={"measurement_session_id": self.measurement_session.id},
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_404_for_unknown_measurement_session(self) -> None:
        payload = {
            **self.valid_payload,
            "measurement_session_id": "01JZZZZZZZZZZZZZZZZZZZZZZZ",
        }
        response = self.client.post(
            "/measurements",
            data=payload,
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json()["error"]["code"],
            "measurement_session_not_found",
        )

    def test_returns_202_for_stopped_session(self) -> None:
        self.measurement_session.stopped_at = timezone.now()
        self.measurement_session.save(update_fields=["stopped_at"])

        response = self.client.post(
            "/measurements",
            data=self.valid_payload,
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(
            response.json()["error"]["code"],
            "measurement_dropped_session_stopped",
        )

    def test_returns_401_for_missing_tenant_header(self) -> None:
        response = self.client.post(
            "/measurements", data=self.valid_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_401_for_unknown_tenant(self) -> None:
        response = self.client.post(
            "/measurements",
            data=self.valid_payload,
            format="json",
            HTTP_X_TENANT_ID="org_missing",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

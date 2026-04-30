from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from devices.models import DeviceAssignment
from measurements.models import Measurement
from tests.mixins import ApiClientMixin, DevicesFixtureMixin, TenantUsersMixin


class MeasurementIngestViewTests(
    ApiClientMixin,
    TenantUsersMixin,
    DevicesFixtureMixin,
    TestCase,
):
    def setUp(self) -> None:
        super().setUp()
        DeviceAssignment.objects.create(
            device=self.device,
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tenant=self.tenant,
            assigned_at=timezone.now(),
            unassigned_at=None,
        )
        self.valid_payload = {
            "serial_number": self.device.serial_number,
            "brand": self.device.brand,
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
        self.assertEqual(data["device_id"], self.device.id)
        self.assertEqual(data["patient_id"], self.patient_profile.id)
        self.assertEqual(data["tenant_id"], self.tenant.id)
        self.assertEqual(data["heart_rate"], self.valid_payload["heart_rate"])
        self.assertEqual(data["hrv"], self.valid_payload["hrv"])

        measurement = Measurement.objects.get(id=data["id"])
        self.assertEqual(measurement.device_id, self.device.id)
        self.assertEqual(measurement.patient_id, self.patient_profile.id)
        self.assertEqual(measurement.tenant_id, self.tenant.id)

    def test_returns_400_for_invalid_payload(self) -> None:
        response = self.client.post(
            "/measurements",
            data={"serial_number": self.device.serial_number},
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_404_for_unknown_serial_number(self) -> None:
        payload = {**self.valid_payload, "serial_number": "missing"}
        response = self.client.post(
            "/measurements",
            data=payload,
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error"]["code"], "device_not_found")

    def test_returns_409_for_unassigned_device(self) -> None:
        DeviceAssignment.objects.all().delete()

        response = self.client.post(
            "/measurements",
            data=self.valid_payload,
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.json()["error"]["code"],
            "device_has_no_active_assignment",
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

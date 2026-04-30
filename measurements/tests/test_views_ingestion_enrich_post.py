from django.test import TestCase
from rest_framework import status

from tests.mixins import (
    ApiClientMixin,
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TenantUsersMixin,
)


class IngestionEnrichViewTests(
    ApiClientMixin,
    TenantUsersMixin,
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TestCase,
):
    def setUp(self) -> None:
        super().setUp()
        self.valid_payload = {
            "serial_number": self.device.serial_number,
            "brand": self.device.brand,
        }

    def test_returns_200_with_device_uid_and_active_session_uid(self) -> None:
        assignment = self.create_active_assignment()
        session = self.create_measurement_session(device_assignment=assignment)

        response = self.client.post(
            "/ingestion/enrich",
            data=self.valid_payload,
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["device_uid"], self.device.uid)
        self.assertEqual(response.json()["session_uid"], session.id)

    def test_returns_200_with_null_session_when_no_active_session(self) -> None:
        response = self.client.post(
            "/ingestion/enrich",
            data=self.valid_payload,
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["device_uid"], self.device.uid)
        self.assertIsNone(response.json()["session_uid"])

    def test_returns_400_for_invalid_payload(self) -> None:
        response = self.client.post(
            "/ingestion/enrich",
            data={"serial_number": self.device.serial_number},
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_404_for_unknown_device_identity(self) -> None:
        payload = {
            "serial_number": "unknown-serial",
            "brand": "unknown-brand",
        }
        response = self.client.post(
            "/ingestion/enrich",
            data=payload,
            format="json",
            HTTP_X_TENANT_ID=self.tenant.auth0_organization_id,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error"]["code"], "device_identity_not_found")

    def test_returns_401_for_missing_tenant_header(self) -> None:
        response = self.client.post(
            "/ingestion/enrich",
            data=self.valid_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_401_for_unknown_tenant_header(self) -> None:
        response = self.client.post(
            "/ingestion/enrich",
            data=self.valid_payload,
            format="json",
            HTTP_X_TENANT_ID="org_missing",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

from django.test import TestCase
from rest_framework import status

from devices.models import Device
from tests.mixins import ApiClientMixin, GatewayAuthMixin, TenantUsersMixin


class CreateDeviceViewTests(
    ApiClientMixin, GatewayAuthMixin, TenantUsersMixin, TestCase
):
    def test_creates_device_201(self) -> None:
        response = self.client.post(
            "/devices",
            data={
                "serial_number": "1234567890",
                "brand": "Test Brand",
                "name": "Test Device",
            },
            headers=self.headers_for(self.doctor_user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        device = Device.objects.get(serial_number="1234567890")
        self.assertEqual(device.brand, "Test Brand")
        self.assertEqual(device.name, "Test Device")
        self.assertEqual(device.tenant, self.tenant)

    def test_returns_401_for_unauthenticated_request(self) -> None:
        response = self.client.post(
            "/devices",
            data={
                "serial_number": "1234567890",
                "brand": "Test Brand",
                "name": "Test Device",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_400_for_duplicate_device(self) -> None:
        request_args = {
            "path": "/devices",
            "data": {
                "serial_number": "1234567890",
                "brand": "Test Brand",
                "name": "Test Device",
            },
            "headers": self.headers_for(self.doctor_user),
            "format": "json",
        }
        good_response = self.client.post(**request_args)
        self.assertEqual(good_response.status_code, status.HTTP_201_CREATED)
        bad_response = self.client.post(**request_args)
        self.assertEqual(bad_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            bad_response.json()["error"]["code"],
            "device_already_exists",
        )

    def test_returns_400_for_invalid_data(self) -> None:
        request_args = {
            "path": "/devices",
            "data": {
                "serial_number": "1234567890",
                "brand": "Test Brand",
            },
            "headers": self.headers_for(self.doctor_user),
            "format": "json",
        }
        response = self.client.post(**request_args)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

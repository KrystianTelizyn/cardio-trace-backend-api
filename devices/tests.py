# Create your tests here.
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from devices.models import Device
from devices.use_cases import CreateDevice
from devices.exceptions import DeviceAlreadyExistsError
from accounts.models import Tenant
from accounts.models import User


class CreateDeviceUseCaseTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant", auth0_organization_id="test_org_id"
        )
        self.existing_device = Device.objects.create(
            serial_number="1234567890",
            brand="Test Brand",
            name="Test Device",
            tenant=self.tenant,
        )
        self.use_case = CreateDevice()

    def test_creates_new_device(self):
        device = self.use_case.execute(
            serial_number="xyz", brand="Apple", name="Watch", tenant=self.tenant
        )
        self.assertEqual(device.serial_number, "xyz")
        self.assertEqual(device.brand, "Apple")
        self.assertEqual(device.name, "Watch")
        self.assertEqual(device.tenant, self.tenant)

    def test_raises_exception_on_duplicate(self):
        with self.assertRaises(DeviceAlreadyExistsError):
            self.use_case.execute(
                serial_number="1234567890",
                brand="Test Brand",
                name="Test Device",
                tenant=self.tenant,
            )


class CreateDeviceViewTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant", auth0_organization_id="test_org_id"
        )
        self.user = User.objects.create(
            email="test@example.com",
            tenant=self.tenant,
            role="doctor",
            auth0_user_id="auth0|1234567890",
        )
        self.client = APIClient()

    def _gateway_headers(self, user: User) -> dict[str, str]:
        return {
            "X-User-Id": user.auth0_user_id,
            "X-Tenant-Id": user.tenant.auth0_organization_id,
            "X-Role": user.role,
        }

    def test_creates_device_201(self):
        response = self.client.post(
            "/devices",
            data={
                "serial_number": "1234567890",
                "brand": "Test Brand",
                "name": "Test Device",
            },
            headers=self._gateway_headers(self.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        device = Device.objects.get(serial_number="1234567890")
        self.assertEqual(device.brand, "Test Brand")
        self.assertEqual(device.name, "Test Device")
        self.assertEqual(device.tenant, self.tenant)

    def test_returns_401_for_unauthenticated_request(self):
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

    def test_returns_400_for_duplicate_device(self):
        request_args = {
            "path": "/devices",
            "data": {
                "serial_number": "1234567890",
                "brand": "Test Brand",
                "name": "Test Device",
            },
            "headers": self._gateway_headers(self.user),
            "format": "json",
        }
        good_response = self.client.post(**request_args)
        self.assertEqual(good_response.status_code, status.HTTP_201_CREATED)
        bad_response = self.client.post(**request_args)
        self.assertEqual(bad_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_400_for_invalid_data(self):
        request_args = {
            "path": "/devices",
            "data": {
                "serial_number": "1234567890",
                "brand": "Test Brand",
            },
            "headers": self._gateway_headers(self.user),
            "format": "json",
        }
        response = self.client.post(**request_args)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

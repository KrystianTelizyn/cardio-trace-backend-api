from django.test import TestCase

from devices.exceptions import DeviceAlreadyExistsError
from devices.use_cases import CreateDevice
from tests.factories import DeviceFactory
from tests.mixins import TenantUsersMixin


class CreateDeviceUseCaseTests(TenantUsersMixin, TestCase):
    tenant_auth0_organization_id = "test_org_id"
    tenant_name = "Test Tenant"

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.existing_device = DeviceFactory(
            serial_number="1234567890",
            brand="Test Brand",
            name="Test Device",
            tenant=cls.tenant,
        )

    def test_creates_new_device(self) -> None:
        device = CreateDevice().execute(
            serial_number="xyz",
            brand="Apple",
            name="Watch",
            tenant=self.tenant,
        )
        self.assertEqual(device.serial_number, "xyz")
        self.assertEqual(device.brand, "Apple")
        self.assertEqual(device.name, "Watch")
        self.assertEqual(device.tenant, self.tenant)

    def test_raises_exception_on_duplicate(self) -> None:
        with self.assertRaises(DeviceAlreadyExistsError):
            CreateDevice().execute(
                serial_number="1234567890",
                brand="Test Brand",
                name="Test Device",
                tenant=self.tenant,
            )

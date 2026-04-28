from devices.models import Device
from accounts.models import Tenant
from devices.exceptions import DeviceAlreadyExistsError


class CreateDevice:
    def execute(
        self, *, serial_number: str, brand: str, name: str, tenant: Tenant
    ) -> tuple[Device, bool]:
        if Device.objects.filter(
            serial_number=serial_number, tenant=tenant, brand=brand
        ).exists():
            raise DeviceAlreadyExistsError(serial_number)

        return Device.objects.create(
            serial_number=serial_number, brand=brand, name=name, tenant=tenant
        )

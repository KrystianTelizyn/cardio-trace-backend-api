from datetime import datetime

from measurements.exceptions import (
    DeviceBySerialNotFoundError,
    DeviceHasNoActiveAssignmentError,
)
from accounts.models import Tenant
from measurements.models import Measurement
from devices.models import Device, DeviceAssignment


class IngestMeasurement:
    def execute(
        self,
        *,
        serial_number: str,
        brand: str,
        tenant: Tenant,
        timestamp: datetime,
        heart_rate: float,
        hrv: float,
    ) -> Measurement:
        device = Device.objects.filter(
            serial_number=serial_number,
            brand=brand,
            tenant=tenant,
        ).first()
        if not device:
            raise DeviceBySerialNotFoundError(
                serial_number=serial_number,
                brand=brand,
                tenant_id=tenant.id,
            )

        assignment = (
            DeviceAssignment.objects.filter(device=device, tenant=tenant)
            .select_related("patient", "tenant")
            .order_by("-created_at")
            .first()
        )
        if not assignment:
            raise DeviceHasNoActiveAssignmentError(
                serial_number=serial_number,
                brand=brand,
                tenant_id=tenant.id,
            )

        return Measurement.objects.create(
            device=device,
            patient=assignment.patient,
            tenant=tenant,
            timestamp=timestamp,
            heart_rate=heart_rate,
            hrv=hrv,
        )

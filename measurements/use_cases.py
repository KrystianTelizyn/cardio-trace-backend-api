from datetime import datetime
from django.utils import timezone

from accounts.models import Tenant
from devices.models import DeviceAssignment
from devices.exceptions import DeviceIdentityNotFoundError
from devices.models import Device
from measurements.exceptions import (
    ActiveMeasurementSessionAlreadyExistsError,
    MeasurementDroppedSessionStopped,
    MeasurementSessionAssignmentNotFoundError,
    MeasurementSessionInvalidStopTimeError,
    MeasurementSessionNotFoundError,
    MeasurementSessionStartOutsideAssignmentWindowError,
)
from measurements.models import Measurement, MeasurementSession


class IngestMeasurement:
    def execute(
        self,
        *,
        measurement_session_id: str,
        tenant: Tenant,
        timestamp: datetime,
        heart_rate: float,
        hrv: float,
    ) -> Measurement:
        measurement_session = MeasurementSession.objects.filter(
            id=measurement_session_id,
            tenant=tenant,
        ).first()
        if not measurement_session:
            raise MeasurementSessionNotFoundError(
                measurement_session_id=measurement_session_id,
                tenant_id=tenant.id,
            )
        if not measurement_session.is_active:
            raise MeasurementDroppedSessionStopped(
                measurement_session_id=measurement_session_id
            )

        return Measurement.objects.create(
            tenant=tenant,
            measurement_session=measurement_session,
            timestamp=timestamp,
            heart_rate=heart_rate,
            hrv=hrv,
        )


class EnrichIngestionContext:
    def execute(
        self,
        *,
        tenant: Tenant,
        serial_number: str,
        brand: str,
    ) -> tuple[str, str | None]:
        device = Device.objects.filter(
            tenant=tenant,
            serial_number=serial_number,
            brand=brand,
        ).first()
        if not device:
            raise DeviceIdentityNotFoundError(
                tenant_id=tenant.id,
                serial_number=serial_number,
                brand=brand,
            )

        active_session = MeasurementSession.objects.filter(
            tenant=tenant,
            device_assignment__device=device,
            stopped_at__isnull=True,
        ).first()
        session_uid = active_session.id if active_session else None
        return device.uid, session_uid


class StartMeasurementSession:
    def execute(
        self,
        *,
        device_assignment_id: int,
        tenant: Tenant,
        started_at: datetime | None = None,
    ) -> MeasurementSession:
        effective_started_at = started_at or timezone.now()

        assignment = DeviceAssignment.objects.filter(
            id=device_assignment_id,
            tenant=tenant,
            unassigned_at__isnull=True,
        ).first()
        if not assignment:
            raise MeasurementSessionAssignmentNotFoundError(
                device_assignment_id=device_assignment_id,
                tenant_id=tenant.id,
            )

        if effective_started_at < assignment.assigned_at:
            raise MeasurementSessionStartOutsideAssignmentWindowError(
                started_at=effective_started_at.isoformat(),
                device_assignment_id=device_assignment_id,
            )

        has_active_session = MeasurementSession.objects.filter(
            tenant=tenant,
            device_assignment=assignment,
            stopped_at__isnull=True,
        ).exists()
        if has_active_session:
            raise ActiveMeasurementSessionAlreadyExistsError(
                device_assignment_id=device_assignment_id
            )

        return MeasurementSession.objects.create(
            tenant=tenant,
            device_assignment=assignment,
            started_at=effective_started_at,
        )


class StopMeasurementSession:
    def execute(
        self,
        *,
        measurement_session_id: str,
        tenant: Tenant,
        stopped_at: datetime | None = None,
    ) -> MeasurementSession:
        measurement_session = MeasurementSession.objects.filter(
            id=measurement_session_id,
            tenant=tenant,
        ).first()
        if not measurement_session:
            raise MeasurementSessionNotFoundError(
                measurement_session_id=measurement_session_id,
                tenant_id=tenant.id,
            )

        if not measurement_session.is_active:
            return measurement_session

        effective_stopped_at = stopped_at or timezone.now()
        if effective_stopped_at <= measurement_session.started_at:
            raise MeasurementSessionInvalidStopTimeError(
                measurement_session_id=measurement_session_id,
                stopped_at=effective_stopped_at.isoformat(),
            )

        measurement_session.stopped_at = effective_stopped_at
        measurement_session.save(update_fields=["stopped_at"])
        return measurement_session

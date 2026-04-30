from datetime import datetime

from measurements.exceptions import (
    MeasurementDroppedSessionStopped,
    MeasurementSessionNotFoundError,
)
from accounts.models import Tenant
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

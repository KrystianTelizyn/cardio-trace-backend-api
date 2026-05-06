from datetime import datetime
import logging
from collections.abc import Generator
from contextlib import contextmanager

import redis
from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from accounts.models import Tenant
from devices.models import DeviceAssignment
from devices.models import Device
from measurements.cache import (
    IngestionRoutingStore,
    build_ingestion_routing_store,
)
from measurements.exceptions import (
    ActiveMeasurementSessionAlreadyExistsError,
    MeasurementDuplicateFrameDropped,
    MeasurementDroppedSessionStopped,
    MeasurementSessionAssignmentNotFoundError,
    MeasurementSessionInvalidStopTimeError,
    MeasurementSessionNotFoundError,
    MeasurementSessionStartOutsideAssignmentWindowError,
)
from measurements.models import Measurement, MeasurementSession

logger = logging.getLogger(__name__)


@contextmanager
def suppress_cache_errors() -> Generator[None, None, None]:
    try:
        yield
    except redis.RedisError as exc:
        logger.warning("Redis cache operation failed, skipping: %s", exc)


class IngestMeasurement:
    def execute(
        self,
        *,
        measurement_session_id: str,
        tenant: Tenant,
        timestamp: datetime,
        heart_rate: float | None,
        rmssd: float | None,
        sdnn: float | None,
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

        try:
            return Measurement.objects.create(
                tenant=tenant,
                measurement_session=measurement_session,
                timestamp=timestamp,
                heart_rate=heart_rate,
                rmssd=rmssd,
                sdnn=sdnn,
            )
        except IntegrityError:
            raise MeasurementDuplicateFrameDropped(
                measurement_session_id=measurement_session_id,
                timestamp=timestamp.isoformat(),
            ) from None


class EnrichIngestionContext:
    def __init__(self, *, routing_store: IngestionRoutingStore | None = None) -> None:
        self.routing_store = routing_store or build_ingestion_routing_store()

    def execute(
        self,
        *,
        tenant: Tenant,
        serial_number: str,
        brand: str,
    ) -> tuple[str | None, str | None]:
        device = Device.objects.filter(
            tenant=tenant,
            serial_number=serial_number,
            brand=brand,
        ).first()
        if not device:
            with suppress_cache_errors():
                self.routing_store.set_device_map_not_found(
                    tenant_id=tenant.auth0_organization_id,
                    brand=brand,
                    serial_number=serial_number,
                    ttl=settings.CACHE_TTL_DEVICE_NOT_FOUND,
                )
            return None, None

        active_session = MeasurementSession.objects.filter(
            tenant=tenant,
            device_assignment__device=device,
            stopped_at__isnull=True,
        ).first()
        session_uid = active_session.id if active_session else None

        with suppress_cache_errors():
            self.routing_store.set_device_map(
                tenant_id=tenant.auth0_organization_id,
                brand=brand,
                serial_number=serial_number,
                device_uid=device.uid,
                ttl=settings.CACHE_TTL_DEVICE_SESSION_ACTIVE,
            )
        with suppress_cache_errors():
            if session_uid:
                self.routing_store.set_device_session(
                    tenant_id=tenant.auth0_organization_id,
                    device_uid=device.uid,
                    session_uid=session_uid,
                    ttl=settings.CACHE_TTL_DEVICE_SESSION_ACTIVE,
                )
            else:
                self.routing_store.set_device_session_not_found(
                    tenant_id=tenant.auth0_organization_id,
                    device_uid=device.uid,
                    ttl=settings.CACHE_TTL_SESSION_NOT_FOUND,
                )

        return device.uid, session_uid


class StartMeasurementSession:
    def __init__(self, *, routing_store: IngestionRoutingStore | None = None) -> None:
        self.routing_store = routing_store or build_ingestion_routing_store()

    def execute(
        self,
        *,
        device_assignment_id: int,
        tenant: Tenant,
        started_at: datetime | None = None,
    ) -> MeasurementSession:
        effective_started_at = started_at or timezone.now()

        assignment = (
            DeviceAssignment.objects.filter(
                id=device_assignment_id,
                tenant=tenant,
                unassigned_at__isnull=True,
            )
            .select_related("device")
            .first()
        )
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

        session = MeasurementSession.objects.create(
            tenant=tenant,
            device_assignment=assignment,
            started_at=effective_started_at,
        )

        with suppress_cache_errors():
            self.routing_store.set_device_session(
                tenant_id=tenant.auth0_organization_id,
                device_uid=assignment.device.uid,
                session_uid=session.id,
                ttl=settings.CACHE_TTL_DEVICE_SESSION_ACTIVE,
            )

        return session


class StopMeasurementSession:
    def __init__(self, *, routing_store: IngestionRoutingStore | None = None) -> None:
        self.routing_store = routing_store or build_ingestion_routing_store()

    def execute(
        self,
        *,
        measurement_session_id: str,
        tenant: Tenant,
        stopped_at: datetime | None = None,
    ) -> MeasurementSession:
        measurement_session = (
            MeasurementSession.objects.filter(
                id=measurement_session_id,
                tenant=tenant,
            )
            .select_related("device_assignment__device")
            .first()
        )
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

        with suppress_cache_errors():
            self.routing_store.set_device_session_not_found(
                tenant_id=tenant.auth0_organization_id,
                device_uid=measurement_session.device_assignment.device.uid,
                ttl=settings.CACHE_TTL_SESSION_NOT_FOUND,
            )

        return measurement_session

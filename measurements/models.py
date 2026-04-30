from django.db import models

from accounts.models import PatientProfile, Tenant
from devices.models import Device, DeviceAssignment
import ulid


def generate_ulid_str() -> str:
    return str(ulid.new())


class MeasurementSession(models.Model):
    id = models.CharField(
        max_length=26,
        primary_key=True,
        default=generate_ulid_str,
        editable=False,
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="measurement_sessions",
    )
    device_assignment = models.ForeignKey(
        DeviceAssignment,
        on_delete=models.CASCADE,
        related_name="measurement_sessions",
    )
    started_at = models.DateTimeField()
    stopped_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "device_assignment"],
                condition=models.Q(stopped_at__isnull=True),
                name="uniq_active_session_per_assignment",
            ),
            models.CheckConstraint(
                condition=models.Q(stopped_at__isnull=True)
                | models.Q(stopped_at__gt=models.F("started_at")),
                name="measurement_session_stopped_after_started",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "device_assignment", "started_at"],
                name="measurement_session_assignment_idx",
            ),
        ]

    @property
    def is_active(self) -> bool:
        return self.stopped_at is None

    @property
    def status(self) -> str:
        return "active" if self.is_active else "stopped"


class Measurement(models.Model):
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="measurements",
    )
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="measurements",
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="measurements",
    )
    timestamp = models.DateTimeField()
    heart_rate = models.FloatField()
    hrv = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

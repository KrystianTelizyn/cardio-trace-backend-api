from django.db import models

from accounts.models import PatientProfile, Tenant
from devices.models import Device


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

from django.db import models
import secrets
import string

from accounts.models import PatientProfile, Tenant, DoctorProfile


def generate_device_uid() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


class Device(models.Model):
    uid = models.CharField(max_length=8, unique=True, default=generate_device_uid)
    serial_number = models.CharField(max_length=255)
    brand = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="devices",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["serial_number", "tenant", "brand"],
                name="unique_device_per_tenant",
            )
        ]

    def __str__(self):
        return f"{self.brand}|{self.name}|{self.serial_number}"


class DeviceAssignment(models.Model):
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="device_assignments"
    )
    patient = models.ForeignKey(
        PatientProfile, on_delete=models.CASCADE, related_name="device_assignments"
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="device_assignments"
    )
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="device_assignments"
    )
    assigned_at = models.DateTimeField()
    unassigned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "patient"],
                condition=models.Q(unassigned_at__isnull=True),
                name="uniq_active_assign_per_patient",
            ),
            models.UniqueConstraint(
                fields=["tenant", "device"],
                condition=models.Q(unassigned_at__isnull=True),
                name="uniq_active_assign_per_device",
            ),
            models.CheckConstraint(
                condition=models.Q(unassigned_at__isnull=True)
                | models.Q(unassigned_at__gt=models.F("assigned_at")),
                name="device_assignment_unassigned_after_assigned",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "device", "assigned_at"],
                name="dev_assign_device_hist_idx",
            ),
            models.Index(
                fields=["tenant", "patient", "assigned_at"],
                name="dev_assign_patient_hist_idx",
            ),
        ]

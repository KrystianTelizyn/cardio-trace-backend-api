from django.db import models

from accounts.models import PatientProfile, Tenant, DoctorProfile


class Device(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["device", "tenant"],
                name="unique_active_device_assignment_per_tenant",
            ),
        ]

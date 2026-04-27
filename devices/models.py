from django.db import models

from accounts.models import Tenant


class Device(models.Model):
    serial_number = models.CharField(max_length=255)
    brand = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="devices",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["serial_number", "tenant", "brand"],
                name="unique_device_per_tenant",
            )
        ]

    def __str__(self):
        return f"{self.brand}|{self.name}|{self.serial_number}"

from __future__ import annotations

import devices.models
from django.db import migrations, models


def backfill_device_uid(apps, schema_editor) -> None:
    Device = apps.get_model("devices", "Device")
    for device in Device.objects.filter(uid__isnull=True):
        device.uid = devices.models.generate_device_uid()
        device.save(update_fields=["uid"])


def noop_reverse(apps, schema_editor) -> None:
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("devices", "0004_deviceassignment_valid_window_and_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="uid",
            field=models.CharField(max_length=8, null=True, unique=True),
        ),
        migrations.RunPython(backfill_device_uid, noop_reverse),
        migrations.AlterField(
            model_name="device",
            name="uid",
            field=models.CharField(
                default=devices.models.generate_device_uid,
                max_length=8,
                unique=True,
            ),
        ),
    ]

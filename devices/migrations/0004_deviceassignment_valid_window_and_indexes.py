import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "devices",
            "0003_remove_deviceassignment_unique_device_assignment_per_tenant_and_more",
        ),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="deviceassignment",
            name="unique_active_device_assignment_per_tenant",
        ),
        migrations.AddField(
            model_name="deviceassignment",
            name="assigned_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="deviceassignment",
            name="unassigned_at",
            field=models.DateTimeField(blank=True, null=True),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="deviceassignment",
            constraint=models.UniqueConstraint(
                condition=models.Q(unassigned_at__isnull=True),
                fields=("tenant", "patient"),
                name="uniq_active_assign_per_patient",
            ),
        ),
        migrations.AddConstraint(
            model_name="deviceassignment",
            constraint=models.UniqueConstraint(
                condition=models.Q(unassigned_at__isnull=True),
                fields=("tenant", "device"),
                name="uniq_active_assign_per_device",
            ),
        ),
        migrations.AddConstraint(
            model_name="deviceassignment",
            constraint=models.CheckConstraint(
                condition=models.Q(unassigned_at__isnull=True)
                | models.Q(unassigned_at__gt=models.F("assigned_at")),
                name="device_assignment_unassigned_after_assigned",
            ),
        ),
        migrations.AddIndex(
            model_name="deviceassignment",
            index=models.Index(
                fields=["tenant", "device", "assigned_at"],
                name="dev_assign_device_hist_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="deviceassignment",
            index=models.Index(
                fields=["tenant", "patient", "assigned_at"],
                name="dev_assign_patient_hist_idx",
            ),
        ),
    ]

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("measurements", "0002_measurementsession"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="measurement",
            name="device",
        ),
        migrations.RemoveField(
            model_name="measurement",
            name="patient",
        ),
        migrations.AddField(
            model_name="measurement",
            name="measurement_session",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="measurements",
                to="measurements.measurementsession",
            ),
        ),
        migrations.AlterField(
            model_name="measurement",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]

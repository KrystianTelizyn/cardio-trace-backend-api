from django.db import migrations


def create_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("accounts", "Tenant")
    Tenant.objects.get_or_create(
        auth0_organization_id="org_nBep3mlTxl2DlaNs",
        defaults={"name": "cardio-trace-clinic"},
    )


def remove_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("accounts", "Tenant")
    Tenant.objects.filter(
        auth0_organization_id="org_nBep3mlTxl2DlaNs",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_tenant, remove_default_tenant),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_approvalsignature"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="details",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="response_status",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]

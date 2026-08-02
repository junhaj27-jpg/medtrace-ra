from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0004_auditlog_details_response_status")]
    operations = [
        migrations.CreateModel(
            name="ApprovalEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event", models.CharField(choices=[("approved", "승인"), ("revoked", "승인 취소")], max_length=20)),
                ("comment", models.TextField(blank=True)),
                ("content_hash", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="approval_events", to="auth.user")),
                ("change_request", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="approval_events", to="core.changerequest")),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]

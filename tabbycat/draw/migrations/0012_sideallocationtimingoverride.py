from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("draw", "0011_byteteamoverride"),
    ]

    operations = [
        migrations.CreateModel(
            name="SideAllocationTimingOverride",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timing", models.CharField(choices=[("before", "Before pairing"), ("after", "After pairing")], default="before", max_length=16, verbose_name="timing")),
                ("round", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="side_allocation_timing_override", to="tournaments.round", verbose_name="round")),
            ],
            options={
                "verbose_name": "side allocation timing override",
                "verbose_name_plural": "side allocation timing overrides",
            },
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0079_deployment_time_zone"),
    ]

    operations = [
        migrations.AddField(
            model_name="sourceimage",
            name="time_zone",
            field=models.CharField(blank=True, help_text="IANA time zone for this capture", max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="sourceimage",
            name="utc_offset_minutes",
            field=models.IntegerField(blank=True, help_text="Offset from UTC in minutes at capture time", null=True),
        ),
    ]

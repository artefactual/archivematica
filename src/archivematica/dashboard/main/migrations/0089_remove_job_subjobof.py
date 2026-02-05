from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0088_job_createdtime_microseconds"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="job",
            name="subjobof",
        ),
    ]

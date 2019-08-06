# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models


def data_migration(apps, schema_editor):
    Job = apps.get_model("main", "Job")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )

    # I can't rely on the model registry neither the current model.
    replacements = {
        "Unknown": 0,
        "Awaiting decision": 1,
        "Completed successfully": 2,
        "Executing command(s)": 3,
        "Failed": 4,
    }

    for key, value in replacements.items():
        Job.objects.filter(currentstep=key).update(currentstep=value)
        MicroServiceChainLink.objects.filter(defaultexitmessage=key).update(
            defaultexitmessage=value
        )
        MicroServiceChainLinkExitCode.objects.filter(exitmessage=key).update(
            exitmessage=value
        )


class Migration(migrations.Migration):

    dependencies = [("main", "0030_rights_import")]

    operations = [
        # Migrate the data before the field is alterned and filter() only accept integers
        migrations.RunPython(data_migration),
        migrations.AlterField(
            model_name="job",
            name="currentstep",
            field=models.IntegerField(
                default=0,
                db_column="currentStep",
                choices=[
                    (0, "Unknown"),
                    (1, "Awaiting decision"),
                    (2, "Completed successfully"),
                    (3, "Executing command(s)"),
                    (4, "Failed"),
                ],
            ),
        ),
    ]

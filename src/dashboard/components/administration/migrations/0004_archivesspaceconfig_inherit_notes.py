from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [("administration", "0003_archivesspace_help_text")]

    operations = [
        migrations.AddField(
            model_name="archivesspaceconfig",
            name="inherit_notes",
            field=models.BooleanField(
                default=False,
                verbose_name=b"Inherit digital object notes from the parent component",
            ),
            preserve_default=True,
        )
    ]

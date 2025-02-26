import uuid

import main.models
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [("main", "0002_initial_data")]

    operations = [
        migrations.CreateModel(
            name="ArchivesSpaceDIPObjectResourcePairing",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "dipuuid",
                    main.models.UUIDField(
                        max_length=50, db_column="dipUUID", default=uuid.uuid4
                    ),
                ),
                (
                    "fileuuid",
                    main.models.UUIDField(
                        max_length=50, db_column="fileUUID", default=uuid.uuid4
                    ),
                ),
                (
                    "resourceid",
                    models.CharField(max_length=150, db_column="resourceId"),
                ),
            ],
            options={
                "db_table": "ArchivesSpaceDIPObjectResourcePairing",
                "verbose_name": "ASDIPObjectResourcePairing",
            },
            bases=(models.Model,),
        )
    ]

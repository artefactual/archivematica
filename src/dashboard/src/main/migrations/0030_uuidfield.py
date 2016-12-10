# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import main.models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0029_backlog_removal_event'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='event_id',
            field=models.UUIDField(default=None, unique=True, null=True, db_column=b'eventIdentifierUUID'),
        ),
        migrations.AlterField(
            model_name='job',
            name='jobuuid',
            field=models.UUIDField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'jobUUID'),
        ),
        migrations.AlterField(
            model_name='levelofdescription',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='metadataappliestotype',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='microservicechain',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='microservicechainchoice',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='microservicechainlink',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='microservicechainlinkexitcode',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='microservicechoicereplacementdic',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='siparrange',
            name='file_uuid',
            field=models.UUIDField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='siparrange',
            name='transfer_uuid',
            field=models.UUIDField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='standardtaskconfig',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='taskconfig',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='taskconfigassignmagiclink',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='taskconfigsetunitvariable',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='taskconfigunitvariablelinkpull',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='tasktype',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='taxonomy',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='taxonomyterm',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='transfermetadatafield',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='transfermetadatafieldvalue',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='transfermetadataset',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='unitvariable',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='watcheddirectory',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
        migrations.AlterField(
            model_name='watcheddirectoryexpectedtype',
            name='id',
            field=main.models.UUIDPkField(default=uuid.uuid4, serialize=False, primary_key=True, db_column=b'pk'),
        ),
    ]

# -*- coding: utf-8 -*-

"""Delete workflow-related content types left behind by migration 0067."""

from __future__ import unicode_literals

from django.db import migrations


CONTENT_TYPES = (
    ('main', 'taskconfigunitvariablelinkpull'),
    ('main', 'taskconfig'),
    ('main', 'watcheddirectoryexpectedtype'),
    ('main', 'microservicechainlinkexitcode'),
    ('main', 'microservicechainchoice'),
    ('main', 'standardtaskconfig'),
    ('main', 'taskconfigsetunitvariable'),
    ('main', 'microservicechainlink'),
    ('main', 'watcheddirectory'),
    ('main', 'microservicechoicereplacementdic'),
    ('main', 'tasktype'),
    ('main', 'microservicechain'),
)


def data_migration_up(apps, schema_editor):
    ContentTypes = apps.get_model('contenttypes', 'contenttype')
    for app, model in CONTENT_TYPES:
        ContentTypes.objects.filter(app_label=app, model=model).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0067_delete_workflow_models'),
    ]

    operations = [
        migrations.RunPython(data_migration_up, migrations.RunPython.noop)
    ]

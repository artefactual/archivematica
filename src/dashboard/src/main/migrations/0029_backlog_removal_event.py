# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


BCKLG_RMVL_EVT_UUID = "463e5d1c-d680-47fa-a27a-7efd4f702355"


def data_migration(apps, schema_editor):
    """Cause the "Create removal from backlog PREMIS events" micro-service to
    no longer restrict itself to files in an objects/ directory. Essentially,
    run this SQL::

        UPDATE StandardTasksConfigs
            SET filterSubDir=NULL
            WHERE pk='463e5d1c-d680-47fa-a27a-7efd4f702355';
    """
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    StandardTaskConfig.objects.filter(id=BCKLG_RMVL_EVT_UUID).update(filter_subdir=None)


class Migration(migrations.Migration):

    dependencies = [("main", "0028_version_number")]

    operations = [migrations.RunPython(data_migration)]

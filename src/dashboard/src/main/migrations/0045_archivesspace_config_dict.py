# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


_AS_DICTNAME = "upload-archivesspace_v0.0"


def data_migration_up(apps, schema_editor):
    """
    Update ASpace config dict:

    The ASpace config dict is used in linkTaskManagerReplacementDicFromChoice
    to set the parameters sent to the upload-archivesspace script, which is
    expecting "restrictions" instead of "premis". This field doesn't seem to
    be used anywhere else, so it only needs to be updated in the related form
    fields that are used to update the config dict.
    """
    DashboardSetting = apps.get_model("main", "DashboardSetting")
    as_dict = DashboardSetting.objects.get_dict(_AS_DICTNAME)
    # Get 'premis' value removing it from the dict
    value = as_dict.pop("premis", None)
    # Add default value if not present
    if value is None:
        value = "yes"
    # Set it in the new field
    as_dict.update({"restrictions": value})
    DashboardSetting.objects.set_dict(_AS_DICTNAME, as_dict)


def data_migration_down(apps, schema_editor):
    """
    Restore ASpace config dict:

    Restore previous dict state with "premis" field instead of "restrictions"
    """
    DashboardSetting = apps.get_model("main", "DashboardSetting")
    as_dict = DashboardSetting.objects.get_dict(_AS_DICTNAME)
    # Get 'restrictions' value removing it from the dict
    value = as_dict.pop("restrictions", None)
    # Add default value if not present
    if value is None:
        value = "yes"
    # Set it in the new field
    as_dict.update({"premis": value})
    DashboardSetting.objects.set_dict(_AS_DICTNAME, as_dict)


class Migration(migrations.Migration):

    dependencies = [("main", "0044_update_idtools")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

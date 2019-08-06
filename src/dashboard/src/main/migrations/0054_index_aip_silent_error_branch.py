# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations

# Can't use apps.get_model for this model as we need to access class attributes.
from main.models import Job


NEW_EXIT_CODE_PK = "c2638a7b-3308-4a0b-895a-001e09fd407a"


def data_migration_up(apps, schema_editor):
    """Add new branch to Index AIP chain link to continue on errors.

    It is up to the client script to use this exit code when desired. It is
    useful when you want to mark the job status as failing but you still want
    to continue processing the package - which is something that we allow users
    to do via configuration.
    """
    clean_up_after_storing_aip_pk = "b7cf0d9a-504f-4f4e-9930-befa817d67ff"
    index_aip_pk = "48703fad-dc44-4c8e-8f47-933df3ef6179"

    apps.get_model("main", "MicroServiceChainLinkExitCode").objects.create(
        id=NEW_EXIT_CODE_PK,
        microservicechainlink_id=index_aip_pk,
        exitcode=179,
        nextmicroservicechainlink_id=clean_up_after_storing_aip_pk,
        exitmessage=Job.STATUS_FAILED,
    )


def data_migration_down(apps, schema_editor):
    """Unapply migration."""
    apps.get_model("main", "MicroServiceChainLinkExitCode").objects.get(
        pk=NEW_EXIT_CODE_PK
    ).delete()


class Migration(migrations.Migration):

    dependencies = [("main", "0053_remove_mcp_unused_field")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

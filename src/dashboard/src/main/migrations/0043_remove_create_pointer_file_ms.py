# -*- coding: utf-8 -*-
"""Migration to remove the "Create AIP Pointer File" micro-service."""
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """This migration removes the "Create AIP Pointer File" micro-services.
    This functionality will be moved to the Storage Service (SS). The
    motivation for this is that pointer files need to be created in the SS for
    a different purpose, namely for the replica packages that are created when
    an AIP Storage location has a mirror location; the replicas need their own
    pointer files with replica-specific information.
    """

    ###########################################################################
    # Model Classes
    ###########################################################################

    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")

    ###########################################################################
    # Useful Model Instances
    ###########################################################################

    copy_submission_docs_cl_uuid = "0a63befa-327d-4655-a021-341b639ee9ed"
    create_pointer_file_cl_uuid = "0915f727-0bc3-47c8-b9b2-25dc2ecef2bb"
    set_bag_file_permissions_cl_uuid = "5fbc344c-19c8-48be-a753-02dac987428c"

    ###########################################################################
    # 1. Set "Copy submission documentation" to exit to "Set bag file perm"
    ###########################################################################

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id=copy_submission_docs_cl_uuid
    ).update(nextmicroservicechainlink_id=set_bag_file_permissions_cl_uuid)
    MicroServiceChainLink.objects.filter(id=copy_submission_docs_cl_uuid).update(
        defaultnextchainlink_id=set_bag_file_permissions_cl_uuid
    )

    ###########################################################################
    # 2. Destroy "Create AIP Pointer File" link and dependent mdl instances
    ###########################################################################

    # Deleting just the related ``TaskConfig`` and StandardTaskConfig`` model
    # instances task config models is sufficient to delete the relevant "Create
    # AIP Pointer File" chain link because of Django's default cascading
    # delete behaviour for foreign keys.
    # See https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.CASCADE
    create_pointer_file_cl = MicroServiceChainLink.objects.get(
        id=create_pointer_file_cl_uuid
    )
    create_pointer_file_tc = create_pointer_file_cl.currenttask
    create_pointer_file_stc_uuid = create_pointer_file_tc.tasktypepkreference
    create_pointer_file_stc = StandardTaskConfig.objects.get(
        id=create_pointer_file_stc_uuid
    )
    create_pointer_file_stc.delete()
    create_pointer_file_tc.delete()


class Migration(migrations.Migration):

    dependencies = [("main", "0042_directory_uuids_all_transfer_types")]

    operations = [migrations.RunPython(data_migration)]

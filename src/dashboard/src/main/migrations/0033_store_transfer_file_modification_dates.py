# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations
from django.db import models

# Can't use apps.get_model for this model as we need to access class attributes
from main.models import Job


def data_migration(apps, schema_editor):
    """Workflow migrations for storing file modification dates in transfers.

    Changes workflow so that, at a high-level, the following micro-services are
    created:

    1. "Store File Modification Dates" micro-service

    Specifics:

    1. Store File Modification Dates

       i.   Standard Tasks Config
            - references ``storeFileModificationDates_v0.0`` executable
       ii.  Task Config
            - configures ``storeFileModificationDates`` as a "one instance" type
       iii. Chain Link ``set_transfer_file_mod_dates_cl``
            - puts storing of file modification dates in the "Characterize and
              extract metadata" group
       iv.  Creates a one instance TaskConfig micro-service for the storing of file
            modification dates.
    """

    ###########################################################################
    # Model Classes
    ###########################################################################

    TaskType = apps.get_model("main", "TaskType")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    TaskConfig = apps.get_model("main", "TaskConfig")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )

    ###########################################################################
    # Get Existing Model Instances
    ###########################################################################

    one_instance_type = TaskType.objects.get(description="one instance")

    ###########################################################################
    # Store file modification dates CHAIN LINKs, etc.
    ###########################################################################

    # Store File Modification Dates Standard Task Config.
    set_file_mod_dates_stc_pk = "102edcd9-3d0c-47d1-be1e-137875d73765"
    StandardTaskConfig.objects.create(
        id=set_file_mod_dates_stc_pk,
        requires_output_lock=False,
        execute="storeFileModificationDates_v0.0",
        arguments='"%SIPUUID%" "%sharedPath%"',
    )

    # Store File Modification Dates Task Config.
    set_file_mod_dates_tc_pk = "fc64dc4c-e245-402b-b572-2dc027b414d1"
    TaskConfig.objects.create(
        id=set_file_mod_dates_tc_pk,
        tasktype=one_instance_type,
        tasktypepkreference=set_file_mod_dates_stc_pk,
        description="Store file modification dates",
    )

    # Store File Modification Dates Chain Link.
    set_transfer_file_mod_dates_cl_pk = "f8ef02c4-f585-4b0d-9b6f-3cef6fbe527f"
    fail_cl_pk = "61c316a6-0a50-4f65-8767-1f44b1eeb6dd"
    MicroServiceChainLink.objects.create(
        id=set_transfer_file_mod_dates_cl_pk,
        currenttask_id=set_file_mod_dates_tc_pk,
        microservicegroup="Characterize and extract metadata",
        defaultnextchainlink_id=fail_cl_pk,
        defaultexitmessage=Job.STATUS_FAILED,
    )

    # Make "Policy checks for preservation derivatives" exit to the "Load
    # Rights" chain link.
    load_rights_cl_pk = "1a136608-ae7b-42b4-bf2f-de0e514cfd47"
    MicroServiceChainLinkExitCode.objects.create(
        id="4eaba00b-30bc-4508-84e4-d9871cd39fc7",
        microservicechainlink_id=set_transfer_file_mod_dates_cl_pk,
        nextmicroservicechainlink_id=load_rights_cl_pk,
        exitcode=0,
        exitmessage=Job.STATUS_COMPLETED_SUCCESSFULLY,
    )

    # Introduce between "Add processed structMap to METS.xml document" and "Characterize and extract"
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="307edcde-ad10-401c-92c4-652917c993ed"
    ).update(nextmicroservicechainlink_id=set_transfer_file_mod_dates_cl_pk)


class Migration(migrations.Migration):

    dependencies = [("main", "0032_dashboardsetting_scope")]

    operations = [
        migrations.AddField(
            model_name="file",
            name="modificationtime",
            field=models.DateTimeField(
                auto_now_add=True, null=True, db_column="modificationTime"
            ),
        ),
        migrations.RunPython(data_migration),
    ]

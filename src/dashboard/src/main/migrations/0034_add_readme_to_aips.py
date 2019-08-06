# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations

# Can't use apps.get_model for this model as we need to access class attributes
from main.models import Job


def data_migration(apps, schema_editor):
    """Workflow migrations for adding README file to AIPs.

    Changes workflow so that, at a high-level, the following micro-services are
    created:

    1. "Add README file" micro-service

    Specifics:

    1. Add README File

       i.   Standard Tasks Config
            - references ``copy_v0.0`` executable
       ii.  Task Config
            - configures ``copy`` as a "one instance" type
       iii. Chain Link ``add_readme_file_cl``
            - puts adding of README file in the "Add README file" group
       iv.  Creates a one instance TaskConfig micro-service for the adding of
            the README file.
       v.   Chain ``add_readme_file_c_pk``
            - "Add README File" chain
    """

    ###########################################################################
    # Model Classes
    ###########################################################################

    TaskType = apps.get_model("main", "TaskType")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    TaskConfig = apps.get_model("main", "TaskConfig")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )

    ###########################################################################
    # Get Existing Model Instances
    ###########################################################################

    one_instance_type = TaskType.objects.get(description="one instance")

    ###########################################################################
    # Add README file CHAIN LINKs, etc.
    ###########################################################################

    # Add README File Standard Task Config.
    add_readme_file_stc_pk = "acb6b747-54b5-4d53-920d-85746cb453a4"
    StandardTaskConfig.objects.create(
        id=add_readme_file_stc_pk,
        requires_output_lock=False,
        execute="copy_v0.0",
        arguments='"%clientAssetsDirectory%README/README.html" "%SIPDirectory%README.html"',
    )

    # Add README File Task Config.
    add_readme_file_tc_pk = "5bf6bc93-fa3d-4c3e-9ae0-8e714e8fedba"
    TaskConfig.objects.create(
        id=add_readme_file_tc_pk,
        tasktype=one_instance_type,
        tasktypepkreference=add_readme_file_stc_pk,
        description="Add README file",
    )

    # Add README File Chain Link.
    add_readme_file_cl_pk = "523c97cc-b267-4cfb-8209-d99e523bf4b3"
    fail_cl_pk = "61c316a6-0a50-4f65-8767-1f44b1eeb6dd"
    add_readme_file_cl = MicroServiceChainLink.objects.create(
        id=add_readme_file_cl_pk,
        currenttask_id=add_readme_file_tc_pk,
        defaultnextchainlink_id=fail_cl_pk,
        microservicegroup="Add README file",
        defaultexitmessage=Job.STATUS_FAILED,
    )

    # Add README File Chain.
    add_readme_file_c_pk = "f1311d19-54c9-4484-9b3c-9bda40457559"
    MicroServiceChain.objects.create(
        id=add_readme_file_c_pk,
        startinglink=add_readme_file_cl,
        description="Add README file",
    )

    # Make "Add README to AIP" exit to the "Generate DIP" chain link.
    generate_dip_cl_pk = "61a8de9c-7b25-4f0f-b218-ad4dde261eed"
    MicroServiceChainLinkExitCode.objects.create(
        id="8c019161-2229-4fc9-be8b-db304525e647",
        microservicechainlink=add_readme_file_cl,
        nextmicroservicechainlink_id=generate_dip_cl_pk,
        exitcode=0,
        exitmessage=Job.STATUS_COMPLETED_SUCCESSFULLY,
    )

    # Introduce after "Generate METS.xml document"
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0"
    ).update(nextmicroservicechainlink_id=add_readme_file_cl_pk)

    # Modify "Prepare AIP" chain link to include README.html in call to bagit_v0.0
    StandardTaskConfig.objects.filter(id="045f84de-2669-4dbc-a31b-43a4954d0481").update(
        arguments='create "%SIPDirectory%%SIPName%-%SIPUUID%" '
        '"%SIPDirectory%" "logs/" "objects/" '
        '"METS.%SIPUUID%.xml" "README.html" "thumbnails/" '
        '"metadata/" --writer filesystem'
    )


class Migration(migrations.Migration):

    dependencies = [("main", "0033_store_transfer_file_modification_dates")]

    operations = [migrations.RunPython(data_migration)]

# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """Workflow migrations for file validation using MediaConch.

    Changes workflow so that, at a high-level the following micro-services are
    created:

    1. "Validate Preservation Derivatives" micro-service
    2. "Validate Access Derivatives" micro-service

    Specifics:

    1. "Validate Preservation Derivatives" chain link after "Normalize for
       Preservation" chain link.

       i.   Standard Tasks Config
            - references ``validateFile_v1.0`` executable with
              preservation-specific command-line args.
       ii.  Task Config
            - configures validate preservation derivative as a "for each
              file" type
       iii. Chain Link ``vldt_prsrvtn_drvtv_cl``
            - puts validate preservation derivative in the "Normalize" group
            - sets the next chain link to the link that was the next link after
              "Normalize for preservation".
       iv.  Exit Codes
            - "Validate preservation derivatives" continues on to the link that
              was previously the next link after "Normalize for preservation",
              no matter what the exit code (0, 1, or 2).

    2. "Validate Access Derivatives" chain link after "Normalize for Access"
       chain link.

       i.   Standard Tasks Config
            - references ``validateFile_v1.0`` executable with access-specific
              command-line args.
       ii.  Task Config
            - configures validate access derivative as a "for each file" type
       iii. Chain Link ``vldt_ccss_drvtv_cl``
            - puts validate access derivative in the "Normalize" group
            - sets the next chain link to the link that was the next link after
              "Normalize for access".
       iv.  Exit Codes
            - "Validate access derivatives" continues on to the link that
              was previously the next link after "Normalize for access",
              no matter what the exit code (0, 1, or 2).
    """

    ###########################################################################
    # Model Classes
    ###########################################################################

    TaskType = apps.get_model("main", "TaskType")
    TaskConfig = apps.get_model("main", "TaskConfig")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )

    ###########################################################################
    # Get Existing Model Instances
    ###########################################################################

    for_each_file_type = TaskType.objects.get(description="for each file")

    # There are two chain links with the task config description 'Normalize for
    # preservation'. However, all of them exit to the same next chain link.
    nrmlz_prsrvtn_cl_1, nrmlz_prsrvtn_cl_2 = MicroServiceChainLink.objects.filter(
        currenttask__description="Normalize for preservation"
    ).all()
    nrmlz_prsrvtn_next_link = (
        nrmlz_prsrvtn_cl_1.exit_codes.first().nextmicroservicechainlink
    )

    # Similarly, there are two chain links with the task config description
    # 'Normalize for access'. However, in this case, they exit to different
    # next chain links.
    nrmlz_ccss_cl_1, nrmlz_ccss_cl_2 = MicroServiceChainLink.objects.filter(
        currenttask__description="Normalize for access"
    ).all()
    nrmlz_ccss_1_next_link = (
        nrmlz_ccss_cl_1.exit_codes.first().nextmicroservicechainlink
    )
    nrmlz_ccss_2_next_link = (
        nrmlz_ccss_cl_2.exit_codes.first().nextmicroservicechainlink
    )

    ###########################################################################
    # Validate PRESERVATION Derivatives CHAIN LINK, etc.
    ###########################################################################

    # Validate Preservation Derivatives Standard Task Config.
    vldt_prsrvtn_drvtv_stc_pk = "f8bc7b43-8bd4-4db8-88dc-d6f55732fb63"
    StandardTaskConfig.objects.create(
        id=vldt_prsrvtn_drvtv_stc_pk,
        execute="validateFile_v1.0",
        arguments=(
            '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"'
            ' "%sharedPath%" "preservation"'
        ),
        filter_subdir="objects/",
    )

    # Validate Preservation Derivatives Task Config.
    vldt_prsrvtn_drvtv_tc_pk = "b6479474-159d-47aa-a10f-40495cb0e273"
    vldt_prsrvtn_drvtv_tc = TaskConfig.objects.create(
        id=vldt_prsrvtn_drvtv_tc_pk,
        tasktype=for_each_file_type,
        tasktypepkreference=vldt_prsrvtn_drvtv_stc_pk,
        description="Validate preservation derivatives",
    )

    # Validate Preservation Derivatives Chain Link.
    vldt_prsrvtn_drvtv_cl_pk = "5b0042a2-2244-475c-85d5-41e4b11e65d6"
    vldt_prsrvtn_drvtv_cl = MicroServiceChainLink.objects.create(
        id=vldt_prsrvtn_drvtv_cl_pk,
        currenttask=vldt_prsrvtn_drvtv_tc,
        defaultnextchainlink=nrmlz_prsrvtn_next_link,
        microservicegroup="Normalize",
    )

    # Fix default next links for "Normalize for Preservation" links
    nrmlz_prsrvtn_cl_1.defaultnextchainlink = vldt_prsrvtn_drvtv_cl
    nrmlz_prsrvtn_cl_2.defaultnextchainlink = vldt_prsrvtn_drvtv_cl

    # Update the six chain link exit code rows for the 'Normalize for
    # preservation' chain links so that they exit to the 'Validate preservation
    # derivatives' chain link.
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink__in=[nrmlz_prsrvtn_cl_1, nrmlz_prsrvtn_cl_2]
    ).update(nextmicroservicechainlink=vldt_prsrvtn_drvtv_cl)

    # Create three new chain link exit code rows that cause the Validate
    # Preservation Derivatives chain link to exit to whatever chain link that
    # Normalize for Preservation used to exit to.
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully'
    # and 4 is 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
        ("f574f94f-c431-4442-a554-ac0934ccac93", 0, 2),
        ("d922a98b-2d65-4d75-bae0-9e8a446cb289", 1, 4),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=vldt_prsrvtn_drvtv_cl,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=nrmlz_prsrvtn_next_link,
        )

    ###########################################################################
    # Validate ACCESS Derivatives CHAIN LINK, etc.
    ###########################################################################

    # Validate Access Derivatives Standard Task Config.
    vldt_ccss_drvtv_stc_pk = "52e7912e-2ce9-4192-9ba4-19a75b2a2807"
    StandardTaskConfig.objects.create(
        id=vldt_ccss_drvtv_stc_pk,
        execute="validateFile_v1.0",
        arguments=(
            '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"' ' "%sharedPath%" "access"'
        ),
        filter_subdir="DIP/objects/",
    )

    # Validate Access Derivatives Task Config.
    vldt_ccss_drvtv_tc_pk = "b597753f-0b36-484f-ae78-4ae95951fd90"
    vldt_ccss_drvtv_tc = TaskConfig.objects.create(
        id=vldt_ccss_drvtv_tc_pk,
        tasktype=for_each_file_type,
        tasktypepkreference=vldt_ccss_drvtv_stc_pk,
        description="Validate access derivatives",
    )

    # Validate Access Derivatives Chain Link # 1.
    vldt_ccss_drvtv_cl_1_pk = "286bbb36-6a38-41d5-bf7a-a8ba58aa71ce"
    vldt_ccss_drvtv_cl_1 = MicroServiceChainLink.objects.create(
        id=vldt_ccss_drvtv_cl_1_pk,
        currenttask=vldt_ccss_drvtv_tc,
        defaultnextchainlink=nrmlz_ccss_1_next_link,
        microservicegroup="Normalize",
    )

    # Validate Access Derivatives Chain Link # 2.
    vldt_ccss_drvtv_cl_2_pk = "a7c18fee-c8c1-4713-ba74-9705c45efbce"
    vldt_ccss_drvtv_cl_2 = MicroServiceChainLink.objects.create(
        id=vldt_ccss_drvtv_cl_2_pk,
        currenttask=vldt_ccss_drvtv_tc,
        defaultnextchainlink=nrmlz_ccss_2_next_link,
        microservicegroup="Normalize",
    )

    # Fix default next links for "Normalize for Access" links
    nrmlz_ccss_cl_1.defaultnextchainlink = vldt_ccss_drvtv_cl_1
    nrmlz_ccss_cl_2.defaultnextchainlink = vldt_ccss_drvtv_cl_2

    # Update the three chain link exit code rows for the FIRST 'Normalize for
    # access' chain link so that they exit to the FIRST 'Validate access
    # derivatives' chain link.
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink=nrmlz_ccss_cl_1
    ).update(nextmicroservicechainlink=vldt_ccss_drvtv_cl_1)

    # Update the three chain link exit code rows for the SECOND 'Normalize for
    # access' chain link so that they exit to the SECOND 'Validate access
    # derivatives' chain link.
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink=nrmlz_ccss_cl_2
    ).update(nextmicroservicechainlink=vldt_ccss_drvtv_cl_2)

    # Create three new MSCL exit code rows that cause the Validate
    # Access Derivatives CL 1 to exit to whatever Normalize for Access 1 used
    # to exit to. Note: in ``exit_message_codes`` 2 is 'Completed successfully'
    # and 4 is 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
        ("9bbaafd6-9954-4f1f-972a-4f7eb0a60de7", 0, 2),
        ("de1dabdd-93ca-4f3b-accf-b9096aa494ba", 1, 4),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=vldt_ccss_drvtv_cl_1,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=nrmlz_ccss_1_next_link,
        )

    # Create three new MSCL exit code rows that cause the Validate
    # Access Derivatives CL 2 to exit to whatever Normalize for Access 2 used
    # to exit to.
    for pk, exit_code in (
        ("09df34f7-31ff-4107-82e7-1db36351acd3", 0),
        ("0e92980d-2545-42f6-9d62-b506ac2ceecb", 1),
        ("41a2ab1e-6804-4228-9f6c-ae6259839348", 2),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=vldt_ccss_drvtv_cl_2,
            exitcode=exit_code,
            exitmessage=2,  # 2 is "Completed successfully"
            nextmicroservicechainlink=nrmlz_ccss_2_next_link,
        )


class Migration(migrations.Migration):

    dependencies = [("main", "0035_fix_workflow_dip_generation")]

    operations = [migrations.RunPython(data_migration)]

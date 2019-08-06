# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """Workflow migrations for policy checks on files using MediaConch.

    Changes workflow so that, at a high-level the following micro-services are
    created:

    1. "Policy Checks on Preservation Derivatives" micro-service
    2. "Policy Checks on Access Derivatives" micro-service
    3. "Policy Checks on Originals" micro-service

    Specifics:

    1. Policy Checks on Preservation Derivatives

       i.   Standard Tasks Config
            - references ``policyCheckPreservationDerivative_v0.0`` executable
       ii.  Task Config
            - configures ``policyCheckPreservationDerivative`` as a "for each file" type
       iii. Chain Link ``prsrvtn_drvtv_policy_check_cl``
            - puts policy check on access derivatives in the "Policy checks for
              derivatives" group
       iv.  Creates a choice point TaskConfig micro-service for letting the
            user choose whether to perform policy checks on preservation derivatives.

    2. Policy Checks on Access Derivatives

       i.   Standard Tasks Config
            - references ``policyCheckAccessDerivative_v0.0`` executable
       ii.  Task Config
            - configures ``policyCheckPreservationDerivative`` as a "for each file" type
       iii. Chain Link ``ccss_drvtv_policy_check_cl``
            - puts policy check on access derivatives in the "Policy checks for
              derivatives" group
            - sets the next chain link to "Add final metadata > Move to
              metadata reminder"
       iv.  Creates a choice point TaskConfig micro-service for letting the
            user choose whether to perform policy checks on access derivatives.

    3. Policy Checks on Originals during Transfer

       i.   Standard Tasks Config
            - references ``policyCheckOriginal_v0.0`` executable
       ii.  Task Config
            - configures ``policyCheckOriginal`` as a "for each file" type
       iii. Chain Link ``prsrvtn_drvtv_policy_check_cl``
            - puts policy check on originals in the "Validation" group
       iv.  Creates a choice point TaskConfig micro-service for letting the
            user choose whether to perform policy checks on originals.
    """

    ###########################################################################
    # Model Classes
    ###########################################################################

    TaskType = apps.get_model("main", "TaskType")
    TaskConfig = apps.get_model("main", "TaskConfig")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    MicroServiceChainChoice = apps.get_model("main", "MicroServiceChainChoice")

    ###########################################################################
    # Get Existing Model Instances
    ###########################################################################

    for_each_file_type = TaskType.objects.get(description="for each file")
    user_choice_type = TaskType.objects.get(
        description="get user choice to proceed with"
    )

    ###########################################################################
    # Policy Check for Derivative CHAIN LINKs, etc.
    ###########################################################################

    # Preservation Derivative Policy Check Standard Task Config.
    prsrvtn_drvtv_policy_check_stc_pk = "0dc703b8-780a-4643-a427-bb60bd5879a8"
    StandardTaskConfig.objects.create(
        id=prsrvtn_drvtv_policy_check_stc_pk,
        execute="policyCheck_v0.0",
        arguments=(
            '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"'
            ' "%sharedPath%" "preservation"'
        ),
    )

    # Access Derivative Policy Check Standard Task Config.
    ccss_drvtv_policy_check_stc_pk = "0872e8ff-5b1b-4c00-a5ea-72efc498fcbf"
    StandardTaskConfig.objects.create(
        id=ccss_drvtv_policy_check_stc_pk,
        execute="policyCheck_v0.0",
        arguments=(
            '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"' ' "%sharedPath%" "access"'
        ),
    )

    # Preservation Derivative Policy Check Task Config.
    prsrvtn_drvtv_policy_check_tc_pk = "1dd8e61f-0579-4a87-bfec-60bedb355048"
    prsrvtn_drvtv_policy_check_tc = TaskConfig.objects.create(
        id=prsrvtn_drvtv_policy_check_tc_pk,
        tasktype=for_each_file_type,
        tasktypepkreference=prsrvtn_drvtv_policy_check_stc_pk,
        description="Policy checks for preservation derivatives",
    )

    # Access Derivative Policy Check Task Config.
    ccss_drvtv_policy_check_tc_pk = "4a8d87e2-4a9a-4ad7-9b4c-d433c9281539"
    ccss_drvtv_policy_check_tc = TaskConfig.objects.create(
        id=ccss_drvtv_policy_check_tc_pk,
        tasktype=for_each_file_type,
        tasktypepkreference=ccss_drvtv_policy_check_stc_pk,
        description="Policy checks for access derivatives",
    )

    # Access Derivative Policy Check Chain Link.
    # It is positioned before the "Move to metadata reminder" chain link.
    move_metadata_cl = MicroServiceChainLink.objects.filter(
        currenttask__description="Move to metadata reminder"
    ).first()
    ccss_drvtv_policy_check_cl_pk = "3bbfbd27-ba41-4e36-8b7f-b4f02676bda3"
    ccss_drvtv_policy_check_cl = MicroServiceChainLink.objects.create(
        id=ccss_drvtv_policy_check_cl_pk,
        currenttask=ccss_drvtv_policy_check_tc,
        defaultnextchainlink=move_metadata_cl,
        microservicegroup="Policy checks for derivatives",
    )

    ###########################################################################
    # BEGIN Micro-service that asks "Do you want to do policy checks on ACCESS
    # derivatives?"
    ###########################################################################

    # Access Derivative Policy Check CHOICE POINT Task Config
    ccss_drvtv_plcy_chck_choice_tc_pk = "a91ad9f6-1027-409c-8e66-4c8769ff9f06"
    ccss_drvtv_plcy_chck_choice_tc = TaskConfig.objects.create(
        id=ccss_drvtv_plcy_chck_choice_tc_pk,
        tasktype=user_choice_type,
        tasktypepkreference=None,
        description="Perform policy checks on access derivatives?",
    )

    # "Perform policy checks on access derivatives?" CHOICE chain link.
    ccss_drvtv_policy_check_choice_cl_pk = "8ce07e94-6130-4987-96f0-2399ad45c5c2"
    ccss_drvtv_policy_check_choice_cl = MicroServiceChainLink.objects.create(
        id=ccss_drvtv_policy_check_choice_cl_pk,
        currenttask=ccss_drvtv_plcy_chck_choice_tc,
        defaultnextchainlink=None,
        microservicegroup="Policy checks for derivatives",
    )

    # MS Chain Choice and Chain that say "Yes, I do want to do policy checks on
    # access derivatives"
    chain_yes_ccss_drvtv_plcy_chck_msc_pk = "d9760427-b488-4381-832a-de10106de6fe"
    chain_yes_ccss_drvtv_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_yes_ccss_drvtv_plcy_chck_msc_pk,
        startinglink=ccss_drvtv_policy_check_cl,
        description="Yes",  # Yes, policy checks on access derivatives please!'
    )

    choice_yes_ccss_drvtv_plcy_chck_mscc_pk = "6cf8bb30-e2f3-4db8-ad7b-81fd6fc05199"
    MicroServiceChainChoice.objects.create(
        id=choice_yes_ccss_drvtv_plcy_chck_mscc_pk,
        chainavailable=chain_yes_ccss_drvtv_plcy_chck_msc,
        choiceavailableatlink=ccss_drvtv_policy_check_choice_cl,
    )

    # MS Chain Choice and Chain that say "No, I do not want to do policy checks
    # on access derivatives"
    chain_no_ccss_drvtv_plcy_chck_msc_pk = "76befd52-14c3-44f9-838f-15a4e01624b0"
    chain_no_ccss_drvtv_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_no_ccss_drvtv_plcy_chck_msc_pk,
        startinglink=move_metadata_cl,  # crucially points to whatever Access
        # Policy checks points to when done.
        description="No",  # No policy checks on access derivatives please!'
    )

    choice_no_ccss_drvtv_plcy_chck_mscc_pk = "b4bf70d2-aa37-44f5-b3fa-04ad2961e979"
    MicroServiceChainChoice.objects.create(
        id=choice_no_ccss_drvtv_plcy_chck_mscc_pk,
        chainavailable=chain_no_ccss_drvtv_plcy_chck_msc,
        choiceavailableatlink=ccss_drvtv_policy_check_choice_cl,
    )

    ###########################################################################
    # END Micro-service that asks "Do you want to do policy checks on ACCESS
    # derivatives?"
    ###########################################################################

    # "Policy checks for preservation derivatives" chain link.
    # It is positioned before the "Policy checks for access derivatives"
    # CHOICE chain link.
    prsrvtn_drvtv_policy_check_cl_pk = "0fd20984-db3c-492b-a512-eedd74bacc82"
    prsrvtn_drvtv_policy_check_cl = MicroServiceChainLink.objects.create(
        id=prsrvtn_drvtv_policy_check_cl_pk,
        currenttask=prsrvtn_drvtv_policy_check_tc,
        defaultnextchainlink=ccss_drvtv_policy_check_choice_cl,
        microservicegroup="Policy checks for derivatives",
    )

    # Make "Policy checks for preservation derivatives" exit to the "Policy
    # checks for access derivatives" CHOICE chain link.
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully' and 4 is
    # 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
        ("088ef391-3c7c-4dff-be9b-34af19f3d38b", 0, 2),
        ("150d2b36-6262-4c7b-9dbc-5b0606dd5a48", 1, 4),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=prsrvtn_drvtv_policy_check_cl,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=ccss_drvtv_policy_check_choice_cl,
        )

    ###########################################################################
    # BEGIN Micro-service that asks "Do you want to do policy checks on
    # PRESERVATION derivatives?"
    ###########################################################################

    # Preservation Derivative Policy Check CHOICE POINT Task Config
    prsrvtn_drvtv_plcy_chck_choice_tc_pk = "a4aad773-480a-422a-8e61-124fc7487572"
    prsrvtn_drvtv_plcy_chck_choice_tc = TaskConfig.objects.create(
        id=prsrvtn_drvtv_plcy_chck_choice_tc_pk,
        tasktype=user_choice_type,
        tasktypepkreference=None,
        description="Perform policy checks on preservation derivatives?",
    )

    # "Perform policy checks on preservation derivatives?" CHOICE chain link.
    prsrvtn_drvtv_policy_check_choice_cl_pk = "153c5f41-3cfb-47ba-9150-2dd44ebc27df"
    prsrvtn_drvtv_policy_check_choice_cl = MicroServiceChainLink.objects.create(
        id=prsrvtn_drvtv_policy_check_choice_cl_pk,
        currenttask=prsrvtn_drvtv_plcy_chck_choice_tc,
        defaultnextchainlink=None,
        microservicegroup="Policy checks for derivatives",
    )

    # MS Chain Choice and Chain that say "Yes, I do want to do policy checks on
    # preservation derivatives"
    chain_yes_prsrvtn_drvtv_plcy_chck_msc_pk = "3a55f688-eca3-4ebc-a012-4ce68290e7b0"
    chain_yes_prsrvtn_drvtv_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_yes_prsrvtn_drvtv_plcy_chck_msc_pk,
        startinglink=prsrvtn_drvtv_policy_check_cl,
        description="Yes"  # Yes, policy checks on preservation derivatives
        # please!'
    )

    choice_yes_prsrvtn_drvtv_plcy_chck_mscc_pk = "06aad779-758b-4791-81ef-2342c6af3109"
    MicroServiceChainChoice.objects.create(
        id=choice_yes_prsrvtn_drvtv_plcy_chck_mscc_pk,
        chainavailable=chain_yes_prsrvtn_drvtv_plcy_chck_msc,
        choiceavailableatlink=prsrvtn_drvtv_policy_check_choice_cl,
    )

    # MS Chain Choice and Chain that say "No, I do not want to do policy checks
    # on preservation derivatives"
    chain_no_prsrvtn_drvtv_plcy_chck_msc_pk = "b7ce05f0-9d94-4b3e-86cc-d4b2c6dba546"
    chain_no_prsrvtn_drvtv_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_no_prsrvtn_drvtv_plcy_chck_msc_pk,
        startinglink=ccss_drvtv_policy_check_choice_cl,
        description="No"  # No policy checks on preservation derivatives
        # please!'
    )

    choice_no_prsrvtn_drvtv_plcy_chck_mscc_pk = "4fca61c6-3314-4f3a-8284-6db5590cc736"
    MicroServiceChainChoice.objects.create(
        id=choice_no_prsrvtn_drvtv_plcy_chck_mscc_pk,
        chainavailable=chain_no_prsrvtn_drvtv_plcy_chck_msc,
        choiceavailableatlink=prsrvtn_drvtv_policy_check_choice_cl,
    )

    ###########################################################################
    # END Micro-service that asks "Do you want to do policy checks on
    # PRESERVATION derivatives?"
    ###########################################################################

    # Configure any links that exit to "Move to metadata reminder" to now exit
    # to the "Policy checks for preservation derivatives" choice point.
    MicroServiceChainLinkExitCode.objects.filter(
        nextmicroservicechainlink=move_metadata_cl
    ).update(nextmicroservicechainlink=prsrvtn_drvtv_policy_check_choice_cl)
    MicroServiceChainLink.objects.filter(defaultnextchainlink=move_metadata_cl).update(
        defaultnextchainlink=prsrvtn_drvtv_policy_check_choice_cl
    )

    # Make "Policy checks for access derivatives" exit to "Move to metadata
    # reminder". (Note: this crucially must follow the above update!)
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully' and 4 is
    # 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
        ("a9c2f8b8-e21f-4bf2-af22-e304c23b0143", 0, 2),
        ("db44f68e-259a-4ff0-a122-d3281d6f2c7d", 1, 4),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=ccss_drvtv_policy_check_cl,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=move_metadata_cl,
        )

    ###########################################################################
    # Policy Checking on Originals during Transfer
    ###########################################################################

    # Policy Checks Originals Standard Task Config.
    rgnl_policy_check_stc_pk = "cd5c8bbe-3699-4caf-a134-0e77c8ccc84a"
    StandardTaskConfig.objects.create(
        id=rgnl_policy_check_stc_pk,
        execute="policyCheck_v0.0",
        arguments=(
            '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"' ' "%sharedPath%" "original"'
        )
        # filter_subdir='objects/'  <- not needed during transfer, I believe ...
    )

    # Policy Checks Originals Task Config.
    rgnl_policy_check_tc_pk = "0f9f9634-275f-4460-aceb-09dcf37049c4"
    rgnl_policy_check_tc = TaskConfig.objects.create(
        id=rgnl_policy_check_tc_pk,
        tasktype=for_each_file_type,
        tasktypepkreference=rgnl_policy_check_stc_pk,
        description="Policy checks for originals",
    )

    # Policy Checks Originals Chain Link.
    # It is positioned before the "Move to examine contents" chain link.
    move_examine_contents_cl = MicroServiceChainLink.objects.filter(
        currenttask__description="Move to examine contents"
    ).first()
    rgnl_policy_check_cl_pk = "6c147aeb-20c5-47ce-9f40-7f22683cea1f"
    rgnl_policy_check_cl = MicroServiceChainLink.objects.create(
        id=rgnl_policy_check_cl_pk,
        currenttask=rgnl_policy_check_tc,
        defaultnextchainlink=move_examine_contents_cl,
        microservicegroup="Validation",
    )

    # Make "Policy checks for originals" exit to "Move to examine
    # contents". (Note: this crucially must follow the above update!)
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully' and 4 is
    # 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
        ("24b40a16-819e-4748-b886-c05d7829615b", 0, 2),
        ("103b22f4-7495-4c08-8233-8389ed300e68", 1, 4),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=rgnl_policy_check_cl,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=move_examine_contents_cl,
        )

    ###########################################################################
    # BEGIN Micro-service that asks "Do you want to do policy checks on
    # ORIGINALS during transfer?"
    ###########################################################################

    # Originals Policy Check CHOICE POINT Task Config
    rgnl_plcy_chck_choice_tc_pk = "3aaabae1-c329-4bbd-a25d-b07e0f7a6d08"
    rgnl_plcy_chck_choice_tc = TaskConfig.objects.create(
        id=rgnl_plcy_chck_choice_tc_pk,
        tasktype=user_choice_type,
        tasktypepkreference=None,
        description="Perform policy checks on originals?",
    )

    # "Perform policy checks on originals?" CHOICE chain link.
    rgnl_policy_check_choice_cl_pk = "70fc7040-d4fb-4d19-a0e6-792387ca1006"
    rgnl_policy_check_choice_cl = MicroServiceChainLink.objects.create(
        id=rgnl_policy_check_choice_cl_pk,
        currenttask=rgnl_plcy_chck_choice_tc,
        defaultnextchainlink=None,
        microservicegroup="Validation",
    )

    # MS Chain Choice and Chain that say "Yes, I do want to do policy checks on
    # originals"
    chain_yes_rgnl_plcy_chck_msc_pk = "c611a6ff-dfdb-46d1-b390-f366a6ea6f66"
    chain_yes_rgnl_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_yes_rgnl_plcy_chck_msc_pk,
        startinglink=rgnl_policy_check_cl,
        description="Yes",  # Yes, policy checks on originals please!'
    )

    choice_yes_rgnl_plcy_chck_mscc_pk = "c4bdc313-3389-49db-a8f1-a0f1b81a8dd2"
    MicroServiceChainChoice.objects.create(
        id=choice_yes_rgnl_plcy_chck_mscc_pk,
        chainavailable=chain_yes_rgnl_plcy_chck_msc,
        choiceavailableatlink=rgnl_policy_check_choice_cl,
    )

    # MS Chain Choice and Chain that say "No, I do not want to do policy checks
    # on originals"
    chain_no_rgnl_plcy_chck_msc_pk = "3e891cc4-39d2-4989-a001-5107a009a223"
    chain_no_rgnl_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_no_rgnl_plcy_chck_msc_pk,
        startinglink=move_examine_contents_cl,  # must crucially point to "Move
        # to examine contents", i.e.,
        # what "Validate formats" used
        # to point to.
        description="No",  # No policy checks on originals please!'
    )

    choice_no_rgnl_plcy_chck_mscc_pk = "7c7feef9-34e9-4745-a5e9-dfb7ba82eba2"
    MicroServiceChainChoice.objects.create(
        id=choice_no_rgnl_plcy_chck_mscc_pk,
        chainavailable=chain_no_rgnl_plcy_chck_msc,
        choiceavailableatlink=rgnl_policy_check_choice_cl,
    )

    ###########################################################################
    # END Micro-service that asks "Do you want to do policy checks on ACCESS
    # derivatives?"
    ###########################################################################

    # 'Validate formats' exits to 'Policy checks for originals'
    # CHOICE cl.
    validate_formats_cl = MicroServiceChainLink.objects.filter(
        currenttask__description="Validate formats"
    ).first()
    validate_formats_cl.defaultnextchainlink = rgnl_policy_check_choice_cl
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink=validate_formats_cl
    ).update(nextmicroservicechainlink=rgnl_policy_check_choice_cl)


class Migration(migrations.Migration):

    dependencies = [("main", "0036_mediaconch_validation")]

    operations = [migrations.RunPython(data_migration)]

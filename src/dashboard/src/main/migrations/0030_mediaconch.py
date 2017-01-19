# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import os

from django.db import migrations


HERE = os.path.dirname(os.path.abspath(__file__))
MIGR_DATA = os.path.join(os.path.dirname(HERE), 'migrations-data')
VALIDATE_CMD_FNM = os.path.join(MIGR_DATA, 'mc_validate_cmd.py')
POLICY_CHECK_CMD_FNM = os.path.join(MIGR_DATA, 'mc_policy_check_cmd.py')


def data_migration(apps, schema_editor):
    """Migrations for MediaConch integration.

    Changes workflow so that, at a high-level the following things happen:

    1. MediaConch is available for validation (in particular for validating
       .mkv files)
    2. Creates a "Validate Preservation Derivatives" micro-service (in
       particular, so that MediaConch can be used for conformance-checking of
       .mkv files created during "Normalize for preservation")
    3. Creates a "Validate Access Derivatives" micro-service (in particular, so
       that MediaConch can be used for conformance-checking of .mkv files
       created during "Normalize for access")

    Specifics:

    a. MediaConch Tool (command-line program)
    b. MediaConch Command (Python wrapper, "client script")
    c. MediaConch-against-MKV-for-validate Rule
    d. MediaConch-against-MKV-for-validatePreservationDerivative Rule
    e. MediaConch-against-MKV-for-validateAccessDerivative Rule

    f. "Validate Preservation Derivatives" chain link after "Normalize for
       Preservation" chain link.

       i.   Standard Tasks Config
            - references ``validatePreservationDerivative_v0.0`` executable
       ii.  Task Config
            - configures ``validatePreservationDerivative`` as a "for each
              file" type
       iii. Chain Link ``vldt_prsrvtn_drvtv_cl``
            - puts validate preservation derivative in the "Normalize" group
            - sets the next chain link to the link that was the next link after
              "Normalize for preservation".
       iv.  Exit Codes
            - "Validate preservation derivatives" continues on to the link that
              was previously the next link after "Normalize for preservation",
              no matter what the exit code (0, 1, or 2).

    g. "Validate Access Derivatives" chain link after "Normalize for Access"
       chain link.

       i.   Standard Tasks Config
            - references ``validateAccessDerivative_v0.0`` executable
       ii.  Task Config
            - configures ``validateAccessDerivative`` as a "for each file" type
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

    FPTool = apps.get_model('fpr', 'FPTool')
    FPCommand = apps.get_model('fpr', 'FPCommand')
    FPRule = apps.get_model('fpr', 'FPRule')
    FormatVersion = apps.get_model('fpr', 'FormatVersion')
    TaskType = apps.get_model('main', 'TaskType')
    TaskConfig = apps.get_model('main', 'TaskConfig')
    StandardTaskConfig = apps.get_model('main', 'StandardTaskConfig')
    MicroServiceChain = apps.get_model('main', 'MicroServiceChain')
    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')
    MicroServiceChainLinkExitCode = apps.get_model(
        'main', 'MicroServiceChainLinkExitCode')
    MicroServiceChainChoice = apps.get_model('main', 'MicroServiceChainChoice')

    ###########################################################################
    # Get Existing Model Instances
    ###########################################################################

    mkv_format = FormatVersion.objects.get(description='Generic MKV')
    for_each_file_type = TaskType.objects.get(description='for each file')
    user_choice_type = TaskType.objects.get(
        description='get user choice to proceed with')

    # There are two chain links with the task config description 'Normalize for
    # preservation'. However, all of them exit to the same next chain link.
    nrmlz_prsrvtn_cl_1, nrmlz_prsrvtn_cl_2 = MicroServiceChainLink.objects\
        .filter(currenttask__description='Normalize for preservation').all()
    nrmlz_prsrvtn_next_link = nrmlz_prsrvtn_cl_1\
        .exit_codes.first().nextmicroservicechainlink

    # Similarly, there are two chain links with the task config description
    # 'Normalize for access'. However, in this case, they exit to different
    # next chain links.
    nrmlz_ccss_cl_1, nrmlz_ccss_cl_2 = MicroServiceChainLink.objects\
        .filter(currenttask__description='Normalize for access').all()
    nrmlz_ccss_1_next_link = nrmlz_ccss_cl_1\
        .exit_codes.first().nextmicroservicechainlink
    nrmlz_ccss_2_next_link = nrmlz_ccss_cl_2\
        .exit_codes.first().nextmicroservicechainlink

    ###########################################################################
    # Create MediaConch Tool and Command
    ###########################################################################

    # MediaConch Tool
    mediaconch_tool_uuid = 'f79c56f1-2d42-440a-8a1f-f40888e24bca'
    mediaconch_tool = FPTool.objects.create(
        uuid=mediaconch_tool_uuid,
        description='MediaConch',
        version='16.12',
        enabled=True,
        slug='mediaconch-1612'
    )

    with open(VALIDATE_CMD_FNM) as filei:
        mediaconch_command_script = filei.read()

    # MediaConch Command
    mediaconch_command_uuid = '287656fb-e58f-4967-bf72-0bae3bbb5ca8'
    mediaconch_command = FPCommand.objects.create(
        uuid=mediaconch_command_uuid,
        tool=mediaconch_tool,
        description='Validate using MediaConch',
        command=mediaconch_command_script,
        script_type='pythonScript',
        command_usage='validation'
    )

    ###########################################################################
    # MediaConch Rules
    ###########################################################################

    # MediaConch-against-MKV-for-validate Rule.
    mediaconch_mkv_rule_uuid = 'a2fb0477-6cde-43f8-a1c9-49834913d588'
    FPRule.objects.create(
        uuid=mediaconch_mkv_rule_uuid,
        purpose='validation',
        command=mediaconch_command,
        format=mkv_format
    )

    # MediaConch-against-MKV-for-validatePreservationDerivative Rule.
    # Create the FPR rule that causes 'Validate using MediaConch' command to be
    # used on for-preservation-derived 'Generic MKV' files in the "Validate
    # Preservation Derivatives" micro-service.
    vldt_prsrvtn_drvtv_rule_pk = '3fcbf5d2-c908-4ec4-b618-8c7dc0f4117e'
    FPRule.objects.create(
        uuid=vldt_prsrvtn_drvtv_rule_pk,
        purpose='validatePreservationDerivative',
        command=mediaconch_command,
        format=mkv_format
    )

    # MediaConch-against-MKV-for-validateAccessDerivative Rule.
    # Create the FPR rule that causes 'Validate using MediaConch' command to be
    # used on for-access-derived 'Generic MKV' files in the "Validate
    # Access Derivatives" micro-service.
    vldt_ccss_drvtv_rule_pk = '0ada4f48-d8a6-4762-8a20-c04cb4e58676'
    FPRule.objects.create(
        uuid=vldt_ccss_drvtv_rule_pk,
        purpose='validateAccessDerivative',
        command=mediaconch_command,
        format=mkv_format
    )

    ###########################################################################
    # Validate PRESERVATION Derivatives CHAIN LINK, etc.
    ###########################################################################

    # Validate Preservation Derivatives Standard Task Config.
    vldt_prsrvtn_drvtv_stc_pk = 'f8bc7b43-8bd4-4db8-88dc-d6f55732fb63'
    StandardTaskConfig.objects.create(
        id=vldt_prsrvtn_drvtv_stc_pk,
        execute='validatePreservationDerivative_v0.0',
        arguments=('"%relativeLocation%" "%fileUUID%" "%SIPUUID%"'
                   ' "%sharedPath%"'),
        filter_subdir='objects/'
    )

    # Validate Preservation Derivatives Task Config.
    vldt_prsrvtn_drvtv_tc_pk = 'b6479474-159d-47aa-a10f-40495cb0e273'
    vldt_prsrvtn_drvtv_tc = TaskConfig.objects.create(
        id=vldt_prsrvtn_drvtv_tc_pk,
        tasktype=for_each_file_type,
        tasktypepkreference=vldt_prsrvtn_drvtv_stc_pk,
        description='Validate preservation derivatives'
    )

    # Validate Preservation Derivatives Chain Link.
    vldt_prsrvtn_drvtv_cl_pk = '5b0042a2-2244-475c-85d5-41e4b11e65d6'
    vldt_prsrvtn_drvtv_cl = MicroServiceChainLink.objects.create(
        id=vldt_prsrvtn_drvtv_cl_pk,
        currenttask=vldt_prsrvtn_drvtv_tc,
        defaultnextchainlink=nrmlz_prsrvtn_next_link,
        microservicegroup='Normalize'
    )


    # Fix default next links for "Normalize for Preservation" links
    nrmlz_prsrvtn_cl_1.defaultnextchainlink = vldt_prsrvtn_drvtv_cl
    nrmlz_prsrvtn_cl_2.defaultnextchainlink = vldt_prsrvtn_drvtv_cl

    # Update the six chain link exit code rows for the 'Normalize for
    # preservation' chain links so that they exit to the 'Validate preservation
    # derivatives' chain link.
    MicroServiceChainLinkExitCode.objects\
        .filter(microservicechainlink__in=[nrmlz_prsrvtn_cl_1,
                                           nrmlz_prsrvtn_cl_2])\
        .update(nextmicroservicechainlink=vldt_prsrvtn_drvtv_cl)

    # Create three new chain link exit code rows that cause the Validate
    # Preservation Derivatives chain link to exit to whatever chain link that
    # Normalize for Preservation used to exit to.
    for pk, exit_code, exit_message in (
            ('f574f94f-c431-4442-a554-ac0934ccac93', 0,
             'Completed successfully'),
            ('d922a98b-2d65-4d75-bae0-9e8a446cb289', 1, 'Failed')):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=vldt_prsrvtn_drvtv_cl,
            exitcode=exit_code,
            exitmessage=exit_message,
            nextmicroservicechainlink=nrmlz_prsrvtn_next_link
        )

    ###########################################################################
    # Validate ACCESS Derivatives CHAIN LINK, etc.
    ###########################################################################

    # Validate Access Derivatives Standard Task Config.
    vldt_ccss_drvtv_stc_pk = '52e7912e-2ce9-4192-9ba4-19a75b2a2807'
    StandardTaskConfig.objects.create(
        id=vldt_ccss_drvtv_stc_pk,
        execute='validateAccessDerivative_v0.0',
        arguments=('"%relativeLocation%" "%fileUUID%" "%SIPUUID%"'
                   ' "%sharedPath%"'),
        filter_subdir='DIP/objects/'
    )

    # Validate Access Derivatives Task Config.
    vldt_ccss_drvtv_tc_pk = 'b597753f-0b36-484f-ae78-4ae95951fd90'
    vldt_ccss_drvtv_tc = TaskConfig.objects.create(
        id=vldt_ccss_drvtv_tc_pk,
        tasktype=for_each_file_type,
        tasktypepkreference=vldt_ccss_drvtv_stc_pk,
        description='Validate access derivatives'
    )

    # Validate Access Derivatives Chain Link # 1.
    vldt_ccss_drvtv_cl_1_pk = '286bbb36-6a38-41d5-bf7a-a8ba58aa71ce'
    vldt_ccss_drvtv_cl_1 = MicroServiceChainLink.objects.create(
        id=vldt_ccss_drvtv_cl_1_pk,
        currenttask=vldt_ccss_drvtv_tc,
        defaultnextchainlink=nrmlz_ccss_1_next_link,
        microservicegroup='Normalize'
    )

    # Validate Access Derivatives Chain Link # 2.
    vldt_ccss_drvtv_cl_2_pk = 'a7c18fee-c8c1-4713-ba74-9705c45efbce'
    vldt_ccss_drvtv_cl_2 = MicroServiceChainLink.objects.create(
        id=vldt_ccss_drvtv_cl_2_pk,
        currenttask=vldt_ccss_drvtv_tc,
        defaultnextchainlink=nrmlz_ccss_2_next_link,
        microservicegroup='Normalize'
    )

    # Fix default next links for "Normalize for Access" links
    nrmlz_ccss_cl_1.defaultnextchainlink = vldt_ccss_drvtv_cl_1
    nrmlz_ccss_cl_2.defaultnextchainlink = vldt_ccss_drvtv_cl_2

    # Update the three chain link exit code rows for the FIRST 'Normalize for
    # access' chain link so that they exit to the FIRST 'Validate access
    # derivatives' chain link.
    MicroServiceChainLinkExitCode.objects\
        .filter(microservicechainlink=nrmlz_ccss_cl_1)\
        .update(nextmicroservicechainlink=vldt_ccss_drvtv_cl_1)

    # Update the three chain link exit code rows for the SECOND 'Normalize for
    # access' chain link so that they exit to the SECOND 'Validate access
    # derivatives' chain link.
    MicroServiceChainLinkExitCode.objects\
        .filter(microservicechainlink=nrmlz_ccss_cl_2)\
        .update(nextmicroservicechainlink=vldt_ccss_drvtv_cl_2)

    # Create three new MSCL exit code rows that cause the Validate
    # Access Derivatives CL 1 to exit to whatever Normalize for Access 1 used
    # to exit to.
    for pk, exit_code, exit_message in (
            ('9bbaafd6-9954-4f1f-972a-4f7eb0a60de7', 0,
             'Completed successfully'),
            ('de1dabdd-93ca-4f3b-accf-b9096aa494ba', 1, 'Failed')):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=vldt_ccss_drvtv_cl_1,
            exitcode=exit_code,
            exitmessage=exit_message,
            nextmicroservicechainlink=nrmlz_ccss_1_next_link
        )

    # Create three new MSCL exit code rows that cause the Validate
    # Access Derivatives CL 2 to exit to whatever Normalize for Access 2 used
    # to exit to.
    for pk, exit_code in (
            ('09df34f7-31ff-4107-82e7-1db36351acd3', 0),
            ('0e92980d-2545-42f6-9d62-b506ac2ceecb', 1),
            ('41a2ab1e-6804-4228-9f6c-ae6259839348', 2)):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=vldt_ccss_drvtv_cl_2,
            exitcode=exit_code,
            nextmicroservicechainlink=nrmlz_ccss_2_next_link
        )

    ###########################################################################
    # Policy Check for Derivative CHAIN LINKs, etc.
    ###########################################################################

    # Preservation Derivative Policy Check Standard Task Config.
    prsrvtn_drvtv_policy_check_stc_pk = '0dc703b8-780a-4643-a427-bb60bd5879a8'
    StandardTaskConfig.objects.create(
        id=prsrvtn_drvtv_policy_check_stc_pk,
        execute='policyCheckPreservationDerivative_v0.0',
        arguments=('"%relativeLocation%" "%fileUUID%" "%SIPUUID%"'
                   ' "%sharedPath%"')
    )

    # Access Derivative Policy Check Standard Task Config.
    ccss_drvtv_policy_check_stc_pk = '0872e8ff-5b1b-4c00-a5ea-72efc498fcbf'
    StandardTaskConfig.objects.create(
        id=ccss_drvtv_policy_check_stc_pk,
        execute='policyCheckAccessDerivative_v0.0',
        arguments=('"%relativeLocation%" "%fileUUID%" "%SIPUUID%"'
                   ' "%sharedPath%"')
    )

    # Preservation Derivative Policy Check Task Config.
    prsrvtn_drvtv_policy_check_tc_pk = '1dd8e61f-0579-4a87-bfec-60bedb355048'
    prsrvtn_drvtv_policy_check_tc = TaskConfig.objects.create(
        id=prsrvtn_drvtv_policy_check_tc_pk,
        tasktype=for_each_file_type,
        tasktypepkreference=prsrvtn_drvtv_policy_check_stc_pk,
        description='Policy checks for preservation derivatives'
    )

    # Access Derivative Policy Check Task Config.
    ccss_drvtv_policy_check_tc_pk = '4a8d87e2-4a9a-4ad7-9b4c-d433c9281539'
    ccss_drvtv_policy_check_tc = TaskConfig.objects.create(
        id=ccss_drvtv_policy_check_tc_pk,
        tasktype=for_each_file_type,
        tasktypepkreference=ccss_drvtv_policy_check_stc_pk,
        description='Policy checks for access derivatives'
    )

    # Access Derivative Policy Check Chain Link.
    # It is positioned before the "Move to metadata reminder" chain link.
    move_metadata_cl = MicroServiceChainLink.objects.filter(
        currenttask__description='Move to metadata reminder').first()
    ccss_drvtv_policy_check_cl_pk = '3bbfbd27-ba41-4e36-8b7f-b4f02676bda3'
    ccss_drvtv_policy_check_cl = MicroServiceChainLink.objects.create(
        id=ccss_drvtv_policy_check_cl_pk,
        currenttask=ccss_drvtv_policy_check_tc,
        defaultnextchainlink=move_metadata_cl,
        microservicegroup='Policy checks for derivatives'
    )

    ###########################################################################
    # BEGIN Micro-service that asks "Do you want to do policy checks on ACCESS
    # derivatives?"
    ###########################################################################

    # Access Derivative Policy Check CHOICE POINT Task Config
    ccss_drvtv_plcy_chck_choice_tc_pk = 'a91ad9f6-1027-409c-8e66-4c8769ff9f06'
    ccss_drvtv_plcy_chck_choice_tc = TaskConfig.objects.create(
        id=ccss_drvtv_plcy_chck_choice_tc_pk,
        tasktype=user_choice_type,
        tasktypepkreference=None,
        description='Perform policy checks on access derivatives?'
    )

    # "Perform policy checks on access derivatives?" CHOICE chain link.
    ccss_drvtv_policy_check_choice_cl_pk = \
        '8ce07e94-6130-4987-96f0-2399ad45c5c2'
    ccss_drvtv_policy_check_choice_cl = MicroServiceChainLink.objects.create(
        id=ccss_drvtv_policy_check_choice_cl_pk,
        currenttask=ccss_drvtv_plcy_chck_choice_tc,
        defaultnextchainlink=None,
        microservicegroup='Policy checks for derivatives'
    )

    # MS Chain Choice and Chain that say "Yes, I do want to do policy checks on
    # access derivatives"
    chain_yes_ccss_drvtv_plcy_chck_msc_pk = \
        'd9760427-b488-4381-832a-de10106de6fe'
    chain_yes_ccss_drvtv_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_yes_ccss_drvtv_plcy_chck_msc_pk,
        startinglink=ccss_drvtv_policy_check_cl,
        description='Yes'  # Yes, policy checks on access derivatives please!'
    )

    choice_yes_ccss_drvtv_plcy_chck_mscc_pk = \
        '6cf8bb30-e2f3-4db8-ad7b-81fd6fc05199'
    MicroServiceChainChoice.objects.create(
        id=choice_yes_ccss_drvtv_plcy_chck_mscc_pk,
        chainavailable=chain_yes_ccss_drvtv_plcy_chck_msc,
        choiceavailableatlink=ccss_drvtv_policy_check_choice_cl
    )

    # MS Chain Choice and Chain that say "No, I do not want to do policy checks
    # on access derivatives"
    chain_no_ccss_drvtv_plcy_chck_msc_pk = \
        '76befd52-14c3-44f9-838f-15a4e01624b0'
    chain_no_ccss_drvtv_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_no_ccss_drvtv_plcy_chck_msc_pk,
        startinglink=move_metadata_cl,  # crucially points to whatever Access
                                        # Policy checks points to when done.
        description='No'  # No policy checks on access derivatives please!'
    )

    choice_no_ccss_drvtv_plcy_chck_mscc_pk = \
        'b4bf70d2-aa37-44f5-b3fa-04ad2961e979'
    MicroServiceChainChoice.objects.create(
        id=choice_no_ccss_drvtv_plcy_chck_mscc_pk,
        chainavailable=chain_no_ccss_drvtv_plcy_chck_msc,
        choiceavailableatlink=ccss_drvtv_policy_check_choice_cl
    )

    ###########################################################################
    # END Micro-service that asks "Do you want to do policy checks on ACCESS
    # derivatives?"
    ###########################################################################

    # "Policy checks for preservation derivatives" chain link.
    # It is positioned before the "Policy checks for access derivatives"
    # CHOICE chain link.
    prsrvtn_drvtv_policy_check_cl_pk = '0fd20984-db3c-492b-a512-eedd74bacc82'
    prsrvtn_drvtv_policy_check_cl = MicroServiceChainLink.objects.create(
        id=prsrvtn_drvtv_policy_check_cl_pk,
        currenttask=prsrvtn_drvtv_policy_check_tc,
        defaultnextchainlink=ccss_drvtv_policy_check_choice_cl,
        microservicegroup='Policy checks for derivatives'
    )

    # Make "Policy checks for preservation derivatives" exit to the "Policy
    # checks for access derivatives" CHOICE chain link.
    for pk, exit_code, exit_message in (
            ('088ef391-3c7c-4dff-be9b-34af19f3d38b', 0,
             'Completed successfully'),
            ('150d2b36-6262-4c7b-9dbc-5b0606dd5a48', 1,
             'Failed')):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=prsrvtn_drvtv_policy_check_cl,
            exitcode=exit_code,
            exitmessage=exit_message,
            nextmicroservicechainlink=ccss_drvtv_policy_check_choice_cl
        )

    ###########################################################################
    # BEGIN Micro-service that asks "Do you want to do policy checks on
    # PRESERVATION derivatives?"
    ###########################################################################

    # Preservation Derivative Policy Check CHOICE POINT Task Config
    prsrvtn_drvtv_plcy_chck_choice_tc_pk = \
        'a4aad773-480a-422a-8e61-124fc7487572'
    prsrvtn_drvtv_plcy_chck_choice_tc = TaskConfig.objects.create(
        id=prsrvtn_drvtv_plcy_chck_choice_tc_pk,
        tasktype=user_choice_type,
        tasktypepkreference=None,
        description='Perform policy checks on preservation derivatives?'
    )

    # "Perform policy checks on preservation derivatives?" CHOICE chain link.
    prsrvtn_drvtv_policy_check_choice_cl_pk = \
        '153c5f41-3cfb-47ba-9150-2dd44ebc27df'
    prsrvtn_drvtv_policy_check_choice_cl = \
        MicroServiceChainLink.objects.create(
            id=prsrvtn_drvtv_policy_check_choice_cl_pk,
            currenttask=prsrvtn_drvtv_plcy_chck_choice_tc,
            defaultnextchainlink=None,
            microservicegroup='Policy checks for derivatives'
        )

    # MS Chain Choice and Chain that say "Yes, I do want to do policy checks on
    # preservation derivatives"
    chain_yes_prsrvtn_drvtv_plcy_chck_msc_pk = \
        '3a55f688-eca3-4ebc-a012-4ce68290e7b0'
    chain_yes_prsrvtn_drvtv_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_yes_prsrvtn_drvtv_plcy_chck_msc_pk,
        startinglink=prsrvtn_drvtv_policy_check_cl,
        description='Yes'  # Yes, policy checks on preservation derivatives
                           # please!'
    )

    choice_yes_prsrvtn_drvtv_plcy_chck_mscc_pk = \
        '06aad779-758b-4791-81ef-2342c6af3109'
    MicroServiceChainChoice.objects.create(
        id=choice_yes_prsrvtn_drvtv_plcy_chck_mscc_pk,
        chainavailable=chain_yes_prsrvtn_drvtv_plcy_chck_msc,
        choiceavailableatlink=prsrvtn_drvtv_policy_check_choice_cl
    )

    # MS Chain Choice and Chain that say "No, I do not want to do policy checks
    # on preservation derivatives"
    chain_no_prsrvtn_drvtv_plcy_chck_msc_pk = \
        'b7ce05f0-9d94-4b3e-86cc-d4b2c6dba546'
    chain_no_prsrvtn_drvtv_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_no_prsrvtn_drvtv_plcy_chck_msc_pk,
        startinglink=ccss_drvtv_policy_check_choice_cl,
        description='No'  # No policy checks on preservation derivatives
                          # please!'
    )

    choice_no_prsrvtn_drvtv_plcy_chck_mscc_pk = \
        '4fca61c6-3314-4f3a-8284-6db5590cc736'
    MicroServiceChainChoice.objects.create(
        id=choice_no_prsrvtn_drvtv_plcy_chck_mscc_pk,
        chainavailable=chain_no_prsrvtn_drvtv_plcy_chck_msc,
        choiceavailableatlink=prsrvtn_drvtv_policy_check_choice_cl
    )

    ###########################################################################
    # END Micro-service that asks "Do you want to do policy checks on
    # PRESERVATION derivatives?"
    ###########################################################################

    # Configure any links that exit to "Move to metadata reminder" to now exit
    # to the "Policy checks for preservation derivatives" choice point.
    MicroServiceChainLinkExitCode.objects\
        .filter(nextmicroservicechainlink=move_metadata_cl)\
        .update(nextmicroservicechainlink=prsrvtn_drvtv_policy_check_choice_cl)
    MicroServiceChainLink.objects\
        .filter(defaultnextchainlink=move_metadata_cl)\
        .update(defaultnextchainlink=prsrvtn_drvtv_policy_check_choice_cl)

    # Make "Policy checks for access derivatives" exit to "Move to metadata
    # reminder". (Note: this crucially must follow the above update!)
    for pk, exit_code, exit_message in (
            ('a9c2f8b8-e21f-4bf2-af22-e304c23b0143', 0,
             'Completed successfully'),
            ('db44f68e-259a-4ff0-a122-d3281d6f2c7d', 1,
             'Failed')):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=ccss_drvtv_policy_check_cl,
            exitcode=exit_code,
            exitmessage=exit_message,
            nextmicroservicechainlink=move_metadata_cl
        )

    ###########################################################################
    # Create MediaConch Command for Policy Checking
    ###########################################################################

    with open(POLICY_CHECK_CMD_FNM) as filei:
        mediaconch_policy_check_command_script = filei.read()

    # MediaConch Command
    # NOTE: this command is disabled by default because it references a
    # dummy/non-existent policy file.
    mediaconch_policy_check_command_uuid = \
        '9ef290f7-5320-4d69-821a-3156fc184b4e'
    mediaconch_policy_check_command = FPCommand.objects.create(
        uuid=mediaconch_policy_check_command_uuid,
        tool=mediaconch_tool,
        description=('Check against policy PLACEHOLDER_FOR_POLICY_FILE_NAME'
                     ' using MediaConch'),
        command=mediaconch_policy_check_command_script,
        script_type='pythonScript',
        command_usage='validation',
        enabled=False
    )

    # MediaConch-against-MKV-for-policyCheckingPreservationFile Rule.
    # Create the FPR rule that causes 'Check against policy using MediaConch'
    # command to be used on 'Generic MKV' files intended for preservation in
    # the "Policy check" micro-service.
    # NOTE: this rule is disabled by default because it references a disabled
    # command that, in turn, references a non-existent MediaConch policy file.
    policy_check_preservation_rule_pk = 'aaaf34ef-c00f-4bb9-85c1-01c0ad5f3a8c'
    FPRule.objects.create(
        uuid=policy_check_preservation_rule_pk,
        purpose='checkingPresDerivativePolicy',
        command=mediaconch_policy_check_command,
        format=mkv_format,
        enabled=False
    )


    ###########################################################################
    # Policy Checking on Originals during Transfer
    ###########################################################################

    # Policy Checks Originals Standard Task Config.
    rgnl_policy_check_stc_pk = 'cd5c8bbe-3699-4caf-a134-0e77c8ccc84a'
    StandardTaskConfig.objects.create(
        id=rgnl_policy_check_stc_pk,
        execute='policyCheckOriginal_v0.0',
        arguments=('"%relativeLocation%" "%fileUUID%" "%SIPUUID%"'
                   ' "%sharedPath%"')
        # filter_subdir='objects/'  <- not needed during transfer, I believe ...
    )

    # Policy Checks Originals Task Config.
    rgnl_policy_check_tc_pk = '0f9f9634-275f-4460-aceb-09dcf37049c4'
    rgnl_policy_check_tc = TaskConfig.objects.create(
        id=rgnl_policy_check_tc_pk,
        tasktype=for_each_file_type,
        tasktypepkreference=rgnl_policy_check_stc_pk,
        description='Policy checks for originals'
    )

    # Policy Checks Originals Chain Link.
    # It is positioned before the "Move to examine contents" chain link.
    move_examine_contents_cl = MicroServiceChainLink.objects.filter(
        currenttask__description='Move to examine contents').first()
    rgnl_policy_check_cl_pk = '6c147aeb-20c5-47ce-9f40-7f22683cea1f'
    rgnl_policy_check_cl = MicroServiceChainLink.objects.create(
        id=rgnl_policy_check_cl_pk,
        currenttask=rgnl_policy_check_tc,
        defaultnextchainlink=move_examine_contents_cl,
        microservicegroup='Validation'
    )

    # Make "Policy checks for originals" exit to "Move to examine
    # contents". (Note: this crucially must follow the above update!)
    for pk, exit_code, exit_message in (
            ('24b40a16-819e-4748-b886-c05d7829615b', 0,
             'Completed successfully'),
            ('103b22f4-7495-4c08-8233-8389ed300e68', 1,
             'Failed')):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=rgnl_policy_check_cl,
            exitcode=exit_code,
            exitmessage=exit_message,
            nextmicroservicechainlink=move_examine_contents_cl
        )


    ###########################################################################
    # BEGIN Micro-service that asks "Do you want to do policy checks on
    # ORIGINALS during transfer?"
    ###########################################################################

    # Originals Policy Check CHOICE POINT Task Config
    rgnl_plcy_chck_choice_tc_pk = '3aaabae1-c329-4bbd-a25d-b07e0f7a6d08'
    rgnl_plcy_chck_choice_tc = TaskConfig.objects.create(
        id=rgnl_plcy_chck_choice_tc_pk,
        tasktype=user_choice_type,
        tasktypepkreference=None,
        description='Perform policy checks on originals?'
    )

    # "Perform policy checks on originals?" CHOICE chain link.
    rgnl_policy_check_choice_cl_pk = \
        '70fc7040-d4fb-4d19-a0e6-792387ca1006'
    rgnl_policy_check_choice_cl = MicroServiceChainLink.objects.create(
        id=rgnl_policy_check_choice_cl_pk,
        currenttask=rgnl_plcy_chck_choice_tc,
        defaultnextchainlink=None,
        microservicegroup='Validation'
    )

    # MS Chain Choice and Chain that say "Yes, I do want to do policy checks on
    # originals"
    chain_yes_rgnl_plcy_chck_msc_pk = \
        'c611a6ff-dfdb-46d1-b390-f366a6ea6f66'
    chain_yes_rgnl_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_yes_rgnl_plcy_chck_msc_pk,
        startinglink=rgnl_policy_check_cl,
        description='Yes'  # Yes, policy checks on originals please!'
    )

    choice_yes_rgnl_plcy_chck_mscc_pk = \
        'c4bdc313-3389-49db-a8f1-a0f1b81a8dd2'
    MicroServiceChainChoice.objects.create(
        id=choice_yes_rgnl_plcy_chck_mscc_pk,
        chainavailable=chain_yes_rgnl_plcy_chck_msc,
        choiceavailableatlink=rgnl_policy_check_choice_cl
    )

    # MS Chain Choice and Chain that say "No, I do not want to do policy checks
    # on originals"
    chain_no_rgnl_plcy_chck_msc_pk = \
        '3e891cc4-39d2-4989-a001-5107a009a223'
    chain_no_rgnl_plcy_chck_msc = MicroServiceChain.objects.create(
        id=chain_no_rgnl_plcy_chck_msc_pk,
        startinglink=move_examine_contents_cl,  # must crucially point to "Move
                                                # to examine contents", i.e.,
                                                # what "Validate formats" used
                                                # to point to.
        description='No'  # No policy checks on originals please!'
    )

    choice_no_rgnl_plcy_chck_mscc_pk = \
        '7c7feef9-34e9-4745-a5e9-dfb7ba82eba2'
    MicroServiceChainChoice.objects.create(
        id=choice_no_rgnl_plcy_chck_mscc_pk,
        chainavailable=chain_no_rgnl_plcy_chck_msc,
        choiceavailableatlink=rgnl_policy_check_choice_cl
    )

    ###########################################################################
    # END Micro-service that asks "Do you want to do policy checks on ACCESS
    # derivatives?"
    ###########################################################################

    # 'Validate formats' exits to 'Policy checks for originals'
    # CHOICE cl.
    validate_formats_cl = MicroServiceChainLink.objects.filter(
        currenttask__description='Validate formats').first()
    validate_formats_cl.defaultnextchainlink = rgnl_policy_check_choice_cl
    MicroServiceChainLinkExitCode.objects\
        .filter(microservicechainlink=validate_formats_cl)\
        .update(nextmicroservicechainlink=rgnl_policy_check_choice_cl)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0029_backlog_removal_event'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]

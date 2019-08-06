# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations

# Can't use apps.get_model for this model as we need to access class attributes
from main.models import Job


def data_migration(apps, schema_editor):
    """Workflow migrations making METS normative structMap optional to include.

    Changes workflow, adding the choice as to whether or not a normative
    structMap is created when METS XML is generated

    1. Add normative structMap chain choice
    2. Add link to generate METS XML with normative structMap
    3. Add chain/chain choice to generate METS XML with normative structMap
    4. Add chain/chain choice to generate METS XML with no normative structMap
    5. Put normative structMap choice where "Generate METS.xml document" was

    Specifics:

    1. Add normative structMap chain choice

       i.   Tasks Config
            - configures link to be a "get user choice to proceed with" type
            - specifies text user will be shown to describe choice
       ii.  Chain Link ``normative_choice_cl``
            - puts link in the "Generate AIP METS" group

    2. Add link to generate METS XML with normative structMap

       i.   Standard Tasks Config
            - specifies that link should execute "createMETS_v2.0"
            - specifies that execute arguments should include creation of
              normative structMap
       ii.  Tasks Config
            - configures link to be a "one instance" type
            - specifies "Generate METS.xml document" will describe link
       iii. Chain Link ``normative_mets_cl``
            - puts link in the "Generate AIP METS" group
       iv.  Exit Code
            - specifies that next link is "Add README file"

    3. Add chain/chain choice to generate METS XML with normative structMap

       i.   Chain
            - specifies that chain should start with ``normative_mets_cl``
            - specifies that chain should be described in choice as "Yes"
       ii.  Chain Choice
            - specifies choice should be available at ``normative_choice_cl``

    4. Add chain/chain choice to generate METS XML with no normative structMap

       i.   Chain
            - specifies that the chain should start with existing METS XML
              generation link
            - specifies that chain should be described in choice as "No"
       ii.  Chain Choice
            - specifies choice should be available at ``normative_choice_cl``

    5. Put normative structMap choice where "Generate METS.xml document" was

       i.   Update "Bind PIDs" link to progress to ``normative_choice_cl``
            rather than existing "Generate METS.xml document" link
    """

    ###########################################################################
    # Model Classes
    ###########################################################################

    TaskType = apps.get_model("main", "TaskType")
    TaskConfig = apps.get_model("main", "TaskConfig")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainChoice = apps.get_model("main", "MicroServiceChainChoice")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )

    ###########################################################################
    # Get Existing Model Instances
    ###########################################################################

    one_instance_type = TaskType.objects.get(description="one instance")
    user_choice_type = TaskType.objects.get(
        description="get user choice to proceed with"
    )

    ###########################################################################
    # Add normative structMap choice link, etc.
    ###########################################################################

    # Add normative structMap chain choice link (and task config)
    normative_choice_tc = TaskConfig.objects.create(
        id="b9613953-9f2d-474b-b8b4-2e17f0b0239d",
        tasktype=user_choice_type,
        tasktypepkreference=None,
        description="Document empty directories?",
    )

    normative_choice_cl = MicroServiceChainLink.objects.create(
        id="d0dfa5fc-e3c2-4638-9eda-f96eea1070e0",
        currenttask=normative_choice_tc,
        defaultnextchainlink=None,
        microservicegroup="Generate AIP METS",
    )

    # Add link/related entities to generate METS XML with normative structMap
    normative_mets_stc_pk = "07d6dff8-20ee-4346-88da-6dfe549eddb1"
    StandardTaskConfig.objects.create(
        id=normative_mets_stc_pk,
        execute="createMETS_v2.0",
        arguments='--amdSec --baseDirectoryPath "%SIPDirectory%" --baseDirectoryPathString "SIPDirectory" --fileGroupIdentifier "%SIPUUID%" --fileGroupType "sip_id" --xmlFile "%SIPDirectory%METS.%SIPUUID%.xml" --sipType "%SIPType%" --createNormativeStructmap',
    )

    normative_mets_tc = TaskConfig.objects.create(
        id="5ba69f6a-1605-42a5-a53a-4d5179613e12",
        tasktype=one_instance_type,
        tasktypepkreference=normative_mets_stc_pk,
        description="Generate METS.xml document",
    )

    normative_mets_cl = MicroServiceChainLink.objects.create(
        id="18c37bff-fce9-4b40-a50a-022ea0386f1a",
        currenttask=normative_mets_tc,
        defaultexitmessage=4,
        defaultnextchainlink_id="7d728c39-395f-4892-8193-92f086c0546f",
        microservicegroup="Generate AIP METS",
    )

    add_readme_file_link_pk = "523c97cc-b267-4cfb-8209-d99e523bf4b3"
    MicroServiceChainLinkExitCode.objects.create(
        id="7038781d-fb5c-4c24-99a3-9f6c4846940d",
        microservicechainlink=normative_mets_cl,
        nextmicroservicechainlink_id=add_readme_file_link_pk,
        exitcode=0,
        exitmessage=Job.STATUS_COMPLETED_SUCCESSFULLY,
    )

    # Add "Yes" (generate METS with normative structMap) chain and chain choice
    normative_yes_choice_msc = MicroServiceChain.objects.create(
        id="29881c21-3548-454a-9637-ebc5fd46aee0",
        startinglink=normative_mets_cl,
        description="Yes",
    )

    MicroServiceChainChoice.objects.create(
        id="ab896ca3-2caf-4cbe-86d3-f61166728a13",
        chainavailable=normative_yes_choice_msc,
        choiceavailableatlink=normative_choice_cl,
    )

    # Add "No" (generate METS with no normative structMap) chain andchain choice
    normative_no_choice_msc = MicroServiceChain.objects.create(
        id="65273f18-5b4e-4944-af4f-09be175a88e8",
        startinglink_id="ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0",
        description="No",
    )

    MicroServiceChainChoice.objects.create(
        id="cee3fef4-ac99-4086-8ce9-7ed95c4bda9a",
        chainavailable=normative_no_choice_msc,
        choiceavailableatlink=normative_choice_cl,
    )

    # Put normative structMap choice where "Generate METS.xml document" was
    bind_pids_link_pk = "7677d1cd-2211-4969-8c10-5ec2a93d5c2f"
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id=bind_pids_link_pk
    ).update(nextmicroservicechainlink=normative_choice_cl)


class Migration(migrations.Migration):

    dependencies = [("main", "0045_archivesspace_config_dict")]

    operations = [migrations.RunPython(data_migration)]

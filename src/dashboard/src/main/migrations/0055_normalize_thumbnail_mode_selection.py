# -*- coding: utf-8 -*-
"""Add a new mode selection prior to generating thumbnails. The user can
choose to generate thumbnails (the previous default), skip generating thumbnails
entirely, or to only generate thumbnails if there is an active FPRule for the
given file type.
"""
from __future__ import absolute_import, unicode_literals

from django.db import migrations
from dateutil.parser import parse as parse_date
from django.db.models.functions import Concat
from django.db.models import Value, Func, F


def data_migration_down(apps, schema_editor):
    """
    Remove thumbnail mode selection prior to the links that run normalize
    thumbnails.
    """
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    MicroServiceChoiceReplacementDic = apps.get_model(
        "main", "MicroServiceChoiceReplacementDic"
    )
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    TaskConfig = apps.get_model("main", "TaskConfig")
    TaskConfigSetUnitVariable = apps.get_model("main", "TaskConfigSetUnitVariable")
    TaskConfigUnitVariableLinkPull = apps.get_model(
        "main", "TaskConfigUnitVariableLinkPull"
    )

    StandardTaskConfig.objects.filter(execute="normalize_v1.0").update(
        arguments=Func(
            F("arguments"),
            Value(' --thumbnail_mode "%ThumbnailMode%"'),
            Value(""),
            function="replace",
        )
    )

    MicroServiceChainLinkExitCode.objects.filter(
        pk="e1a92dc8-a10f-4023-bd98-f6b1214cfc6e"
    ).delete()

    MicroServiceChoiceReplacementDic.objects.filter(
        pk="972fce6c-52c8-4c00-99b9-d6814e377974"
    ).delete()

    MicroServiceChoiceReplacementDic.objects.filter(
        pk="89f098ef-1cb2-4a97-ad67-4c0f14d0546b"
    ).delete()

    MicroServiceChoiceReplacementDic.objects.filter(
        pk="c318b224-b718-4535-a911-494b1af6ff26"
    ).delete()

    MicroServiceChainLink.objects.filter(
        pk="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65"
    ).delete()

    TaskConfig.objects.filter(pk="48358662-79d2-494d-9689-a5c9a1e563c4").delete()

    MicroServiceChainLink.objects.filter(
        pk="6e5126be-76ac-4c8f-9754-fc25a234a751"
    ).delete()

    TaskConfigUnitVariableLinkPull.objects.filter(
        pk="c6977cda-2ef0-460c-bb1c-6368eab52b24"
    ).delete()

    TaskConfig.objects.filter(pk="73bd7787-7358-4fb1-aac7-d151d4495107").delete()

    StandardTaskConfig.objects.filter(pk="d12b6b59-1f1c-47c2-b1a3-2bf898740eae").update(
        execute="remove_v0.0",
        arguments='-R "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"',
    )

    StandardTaskConfig.objects.filter(pk="6abefa8d-387d-4f23-9978-bea7e6657a57").update(
        execute="copy_v0.0",
        arguments='-R "%SIPDirectory%thumbnails" "%SIPDirectory%DIP/."',
    )

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="4103a5b0-e473-4198-8ff7-aaa6fec34749"
    ).update(nextmicroservicechainlink_id="092b47db-6f77-4072-aed3-eb248ab69e9c")

    MicroServiceChainLink.objects.filter(
        pk="4103a5b0-e473-4198-8ff7-aaa6fec34749"
    ).update(defaultnextchainlink_id="092b47db-6f77-4072-aed3-eb248ab69e9c")

    MicroServiceChainLinkExitCode.objects.filter(
        pk="52b8af47-f938-4ede-8a41-c4ded3a404a5"
    ).delete()
    MicroServiceChainLink.objects.filter(
        pk="d951628f-e2c2-40b2-8bc0-7b9a7d1ef3d3"
    ).delete()
    TaskConfigSetUnitVariable.objects.filter(
        pk="8fd545ec-161c-4190-9091-17b42b41dd1e"
    ).delete()
    TaskConfig.objects.filter(pk="a59cd3fe-06ec-485e-9757-16d2068b8d6e").delete()

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="35c8763a-0430-46be-8198-9ecb23f895c8"
    ).update(nextmicroservicechainlink_id="180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21")

    MicroServiceChainLink.objects.filter(
        pk="35c8763a-0430-46be-8198-9ecb23f895c8"
    ).update(defaultnextchainlink_id="180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21")

    MicroServiceChainLinkExitCode.objects.filter(
        pk="18ea6b41-68ee-4b03-af1d-0bbd803129f1"
    ).delete()
    MicroServiceChainLink.objects.filter(
        pk="b33c9544-145c-4525-8a80-d686b4d1c3fa"
    ).delete()
    TaskConfigSetUnitVariable.objects.filter(
        pk="319f4a1a-c6d5-4ddf-9f29-74a2d72e7d1c"
    ).delete()
    TaskConfig.objects.filter(pk="860f535c-60c3-4622-8dca-73719b7e2d8c").delete()

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="31abe664-745e-4fef-a669-ff41514e0083"
    ).update(nextmicroservicechainlink_id="09b85517-e5f5-415b-a950-1a60ee285242")

    MicroServiceChainLink.objects.filter(
        pk="31abe664-745e-4fef-a669-ff41514e0083"
    ).update(defaultnextchainlink_id="09b85517-e5f5-415b-a950-1a60ee285242")

    MicroServiceChainLinkExitCode.objects.filter(
        pk="70a5eadd-84bc-4bb1-a62e-b8dc7fe8f690"
    ).delete()
    MicroServiceChainLink.objects.filter(
        pk="3505acc1-2b03-45df-93e2-626e6885e907"
    ).delete()
    TaskConfigSetUnitVariable.objects.filter(
        pk="6fdfd777-86a5-4bc5-ae5a-ac3400df6ab2"
    ).delete()
    TaskConfig.objects.filter(pk="dd0127bb-c15a-4dc0-a80c-405b2fb81bb7").delete()

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="0b92a510-a290-44a8-86d8-6b7139be29df"
    ).update(nextmicroservicechainlink_id="f6fdd1a7-f0c5-4631-b5d3-19421155bd7a")

    MicroServiceChainLink.objects.filter(
        pk="0b92a510-a290-44a8-86d8-6b7139be29df"
    ).update(defaultnextchainlink_id="f6fdd1a7-f0c5-4631-b5d3-19421155bd7a")

    MicroServiceChainLinkExitCode.objects.filter(
        pk="ac94d44a-cb16-4791-9361-b1c3d56a3252"
    ).delete()
    MicroServiceChainLink.objects.filter(
        pk="c7122b0b-e036-4551-b7cd-2eca6ebba53f"
    ).delete()
    TaskConfigSetUnitVariable.objects.filter(
        pk="e04c035a-da9a-4908-9f46-a20dcd10f5fd"
    ).delete()
    TaskConfig.objects.filter(pk="eccaafcc-1793-4ac3-81f8-935e4ce49595").delete()

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="56da7758-913a-4cd2-a815-be140ed09357"
    ).update(nextmicroservicechainlink_id="8ce130d4-3f7e-46ec-868a-505cf9033d96")

    MicroServiceChainLink.objects.filter(
        pk="56da7758-913a-4cd2-a815-be140ed09357"
    ).update(defaultnextchainlink_id="8ce130d4-3f7e-46ec-868a-505cf9033d96")

    MicroServiceChainLinkExitCode.objects.filter(
        pk="1ca2172a-8570-4499-8acd-218bf2c9f746"
    ).delete()
    MicroServiceChainLink.objects.filter(
        pk="4ca2c28a-8962-412b-9ec3-37c105cc47d9"
    ).delete()
    TaskConfigSetUnitVariable.objects.filter(
        pk="cd8f0eec-7c40-46a9-8716-457a7c8b0adb"
    ).delete()
    TaskConfig.objects.filter(pk="99b10a95-eebd-40b5-beee-985bee5da5a4").delete()

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="6b931965-d5f6-4611-a536-39d5901f8f70"
    ).update(nextmicroservicechainlink_id="0a6558cf-cf5f-4646-977e-7d6b4fde47e8")

    MicroServiceChainLink.objects.filter(
        pk="6b931965-d5f6-4611-a536-39d5901f8f70"
    ).update(defaultnextchainlink_id="0a6558cf-cf5f-4646-977e-7d6b4fde47e8")

    MicroServiceChainLinkExitCode.objects.filter(
        pk="6b2a81c6-8671-460d-9f25-1ef19e42a4fa"
    ).delete()
    MicroServiceChainLink.objects.filter(
        pk="62e0adc0-87f6-4162-acfa-f560c93d181d"
    ).delete()
    TaskConfigSetUnitVariable.objects.filter(
        pk="1b599511-0193-48a1-b9f3-0f28afaf8f33"
    ).delete()
    TaskConfig.objects.filter(pk="9ce16ae3-a87c-4b9d-8584-b0118e1e2b1f").delete()

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="f3a39155-d655-4336-8227-f8c88e4b7669"
    ).update(nextmicroservicechainlink_id="e950cd98-574b-4e57-9ef8-c2231e1ce451")

    MicroServiceChainLink.objects.filter(
        pk="f3a39155-d655-4336-8227-f8c88e4b7669"
    ).update(defaultnextchainlink_id="e950cd98-574b-4e57-9ef8-c2231e1ce451")

    MicroServiceChainLinkExitCode.objects.filter(
        pk="004c5e3f-04b6-476b-9289-d3755ebd8a7f"
    ).delete()
    MicroServiceChainLink.objects.filter(
        pk="8bcbca9c-91f6-4377-b064-b41751fb98ba"
    ).delete()
    TaskConfigSetUnitVariable.objects.filter(
        pk="6cfc8e17-b3f6-481e-ba1d-9b1f32c1256b"
    ).delete()
    TaskConfig.objects.filter(pk="884d8849-19c6-47c7-947f-ad349a483f44").delete()


def data_migration_up(apps, schema_editor):
    """
    Add a normalize thumbnail mode selection prior to the links that run
    normalize thumbnails.
    """
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    MicroServiceChoiceReplacementDic = apps.get_model(
        "main", "MicroServiceChoiceReplacementDic"
    )
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    TaskConfig = apps.get_model("main", "TaskConfig")
    TaskConfigSetUnitVariable = apps.get_model("main", "TaskConfigSetUnitVariable")
    TaskConfigUnitVariableLinkPull = apps.get_model(
        "main", "TaskConfigUnitVariableLinkPull"
    )

    # Return home once the selection has been made
    TaskConfig.objects.create(
        pk="73bd7787-7358-4fb1-aac7-d151d4495107",
        tasktypepkreference="c6977cda-2ef0-460c-bb1c-6368eab52b24",
        description="Return to normalization step",
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        replaces=None,
        tasktype_id="c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
    )

    TaskConfigUnitVariableLinkPull.objects.create(
        pk="c6977cda-2ef0-460c-bb1c-6368eab52b24",
        variable="normalizationThumbnailProcessing",
        variablevalue=None,
        createdtime=parse_date("2018-06-28T00:00:00+00:00"),
        updatedtime=None,
        defaultmicroservicechainlink=None,
    )

    MicroServiceChainLink.objects.create(
        pk="6e5126be-76ac-4c8f-9754-fc25a234a751",
        microservicegroup="Normalize",
        reloadfilelist=1,
        defaultexitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        currenttask_id="73bd7787-7358-4fb1-aac7-d151d4495107",
        defaultnextchainlink=None,
        replaces=None,
    )

    TaskConfig.objects.create(
        pk="48358662-79d2-494d-9689-a5c9a1e563c4",
        tasktypepkreference=None,
        description="Choose thumbnail mode",
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        replaces=None,
        tasktype_id="9c84b047-9a6d-463f-9836-eafa49743b84",
    )

    MicroServiceChainLink.objects.create(
        pk="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        microservicegroup="Normalize",
        reloadfilelist=1,
        defaultexitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        currenttask_id="48358662-79d2-494d-9689-a5c9a1e563c4",
        defaultnextchainlink=None,
        replaces=None,
    )

    MicroServiceChoiceReplacementDic.objects.create(
        pk="c318b224-b718-4535-a911-494b1af6ff26",
        description="Yes",
        replacementdic='{"%ThumbnailMode%": "generate"}',
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        choiceavailableatlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        replaces=None,
    )

    MicroServiceChoiceReplacementDic.objects.create(
        pk="89f098ef-1cb2-4a97-ad67-4c0f14d0546b",
        description="Yes, without default",
        replacementdic='{"%ThumbnailMode%": "generate_non_default"}',
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        choiceavailableatlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        replaces=None,
    )

    MicroServiceChoiceReplacementDic.objects.create(
        pk="972fce6c-52c8-4c00-99b9-d6814e377974",
        description="No",
        replacementdic='{"%ThumbnailMode%": "do_not_generate"}',
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        choiceavailableatlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        replaces=None,
    )

    MicroServiceChainLinkExitCode.objects.create(
        pk="e1a92dc8-a10f-4023-bd98-f6b1214cfc6e",
        exitcode=0,
        exitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        microservicechainlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        nextmicroservicechainlink_id="6e5126be-76ac-4c8f-9754-fc25a234a751",
        replaces=None,
    )

    StandardTaskConfig.objects.filter(
        execute="normalize_v1.0", arguments__startswith="thumbnail"
    ).update(
        arguments=Concat("arguments", Value(' --thumbnail_mode "%ThumbnailMode%"'))
    )

    # Update 'Remove bagged files' to use new removeDirectories_v0.0 script
    StandardTaskConfig.objects.filter(pk="d12b6b59-1f1c-47c2-b1a3-2bf898740eae").update(
        execute="removeDirectories_v0.0",
        arguments='"%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"',
    )

    # Update 'Copy thumbnails to DIP directory' to use new copyThumbnailsToDIPDirectory_v0.0 script
    StandardTaskConfig.objects.filter(pk="6abefa8d-387d-4f23-9978-bea7e6657a57").update(
        execute="copyThumbnailsToDIPDirectory_v0.0",
        arguments='"%SIPDirectory%thumbnails" "%SIPDirectory%DIP"',
    )

    TaskConfig.objects.create(
        pk="a59cd3fe-06ec-485e-9757-16d2068b8d6e",
        tasktypepkreference="8fd545ec-161c-4190-9091-17b42b41dd1e",
        description="Set normalize path",
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        replaces=None,
        tasktype_id="6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
    )

    TaskConfigSetUnitVariable.objects.create(
        pk="8fd545ec-161c-4190-9091-17b42b41dd1e",
        updatedtime=None,
        microservicechainlink_id="092b47db-6f77-4072-aed3-eb248ab69e9c",
        createdtime=parse_date("2018-06-28T00:00:00+00:00"),
        variablevalue=None,
        variable="normalizationThumbnailProcessing",
    )

    MicroServiceChainLink.objects.create(
        pk="d951628f-e2c2-40b2-8bc0-7b9a7d1ef3d3",
        microservicegroup="Normalize",
        reloadfilelist=1,
        defaultexitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        currenttask_id="a59cd3fe-06ec-485e-9757-16d2068b8d6e",
        defaultnextchainlink=None,
        replaces=None,
    )

    MicroServiceChainLinkExitCode.objects.create(
        pk="52b8af47-f938-4ede-8a41-c4ded3a404a5",
        exitcode=0,
        exitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        microservicechainlink_id="d951628f-e2c2-40b2-8bc0-7b9a7d1ef3d3",
        nextmicroservicechainlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        replaces=None,
    )

    MicroServiceChainLink.objects.filter(
        pk="4103a5b0-e473-4198-8ff7-aaa6fec34749"
    ).update(defaultnextchainlink_id="d951628f-e2c2-40b2-8bc0-7b9a7d1ef3d3")

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="4103a5b0-e473-4198-8ff7-aaa6fec34749"
    ).update(nextmicroservicechainlink_id="d951628f-e2c2-40b2-8bc0-7b9a7d1ef3d3")

    TaskConfig.objects.create(
        pk="860f535c-60c3-4622-8dca-73719b7e2d8c",
        tasktypepkreference="319f4a1a-c6d5-4ddf-9f29-74a2d72e7d1c",
        description="Set normalize path",
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        replaces=None,
        tasktype_id="6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
    )

    TaskConfigSetUnitVariable.objects.create(
        pk="319f4a1a-c6d5-4ddf-9f29-74a2d72e7d1c",
        updatedtime=None,
        microservicechainlink_id="180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21",
        createdtime=parse_date("2018-06-28T00:00:00+00:00"),
        variablevalue=None,
        variable="normalizationThumbnailProcessing",
    )

    MicroServiceChainLink.objects.create(
        pk="b33c9544-145c-4525-8a80-d686b4d1c3fa",
        microservicegroup="Normalize",
        reloadfilelist=1,
        defaultexitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        currenttask_id="860f535c-60c3-4622-8dca-73719b7e2d8c",
        defaultnextchainlink=None,
        replaces=None,
    )

    MicroServiceChainLinkExitCode.objects.create(
        pk="18ea6b41-68ee-4b03-af1d-0bbd803129f1",
        exitcode=0,
        exitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        microservicechainlink_id="b33c9544-145c-4525-8a80-d686b4d1c3fa",
        nextmicroservicechainlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        replaces=None,
    )

    MicroServiceChainLink.objects.filter(
        pk="35c8763a-0430-46be-8198-9ecb23f895c8"
    ).update(defaultnextchainlink_id="b33c9544-145c-4525-8a80-d686b4d1c3fa")

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="35c8763a-0430-46be-8198-9ecb23f895c8"
    ).update(nextmicroservicechainlink_id="b33c9544-145c-4525-8a80-d686b4d1c3fa")

    TaskConfig.objects.create(
        pk="dd0127bb-c15a-4dc0-a80c-405b2fb81bb7",
        tasktypepkreference="6fdfd777-86a5-4bc5-ae5a-ac3400df6ab2",
        description="Set normalize path",
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        replaces=None,
        tasktype_id="6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
    )

    TaskConfigSetUnitVariable.objects.create(
        pk="6fdfd777-86a5-4bc5-ae5a-ac3400df6ab2",
        updatedtime=None,
        microservicechainlink_id="09b85517-e5f5-415b-a950-1a60ee285242",
        createdtime=parse_date("2018-06-28T00:00:00+00:00"),
        variablevalue=None,
        variable="normalizationThumbnailProcessing",
    )

    MicroServiceChainLink.objects.create(
        pk="3505acc1-2b03-45df-93e2-626e6885e907",
        microservicegroup="Normalize",
        reloadfilelist=1,
        defaultexitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        currenttask_id="dd0127bb-c15a-4dc0-a80c-405b2fb81bb7",
        defaultnextchainlink=None,
        replaces=None,
    )

    MicroServiceChainLinkExitCode.objects.create(
        pk="70a5eadd-84bc-4bb1-a62e-b8dc7fe8f690",
        exitcode=0,
        exitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        microservicechainlink_id="3505acc1-2b03-45df-93e2-626e6885e907",
        nextmicroservicechainlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        replaces=None,
    )

    MicroServiceChainLink.objects.filter(
        pk="31abe664-745e-4fef-a669-ff41514e0083"
    ).update(defaultnextchainlink_id="3505acc1-2b03-45df-93e2-626e6885e907")

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="31abe664-745e-4fef-a669-ff41514e0083"
    ).update(nextmicroservicechainlink_id="3505acc1-2b03-45df-93e2-626e6885e907")

    TaskConfig.objects.create(
        pk="eccaafcc-1793-4ac3-81f8-935e4ce49595",
        tasktypepkreference="e04c035a-da9a-4908-9f46-a20dcd10f5fd",
        description="Set normalize path",
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        replaces=None,
        tasktype_id="6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
    )

    TaskConfigSetUnitVariable.objects.create(
        pk="e04c035a-da9a-4908-9f46-a20dcd10f5fd",
        updatedtime=None,
        microservicechainlink_id="f6fdd1a7-f0c5-4631-b5d3-19421155bd7a",
        createdtime=parse_date("2018-06-28T00:00:00+00:00"),
        variablevalue=None,
        variable="normalizationThumbnailProcessing",
    )

    MicroServiceChainLink.objects.create(
        pk="c7122b0b-e036-4551-b7cd-2eca6ebba53f",
        microservicegroup="Normalize",
        reloadfilelist=1,
        defaultexitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        currenttask_id="eccaafcc-1793-4ac3-81f8-935e4ce49595",
        defaultnextchainlink=None,
        replaces=None,
    )

    MicroServiceChainLinkExitCode.objects.create(
        pk="ac94d44a-cb16-4791-9361-b1c3d56a3252",
        exitcode=0,
        exitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        microservicechainlink_id="c7122b0b-e036-4551-b7cd-2eca6ebba53f",
        nextmicroservicechainlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        replaces=None,
    )

    MicroServiceChainLink.objects.filter(
        pk="0b92a510-a290-44a8-86d8-6b7139be29df"
    ).update(defaultnextchainlink_id="c7122b0b-e036-4551-b7cd-2eca6ebba53f")

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="0b92a510-a290-44a8-86d8-6b7139be29df"
    ).update(nextmicroservicechainlink_id="c7122b0b-e036-4551-b7cd-2eca6ebba53f")

    TaskConfig.objects.create(
        pk="99b10a95-eebd-40b5-beee-985bee5da5a4",
        tasktypepkreference="cd8f0eec-7c40-46a9-8716-457a7c8b0adb",
        description="Set normalize path",
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        replaces=None,
        tasktype_id="6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
    )

    TaskConfigSetUnitVariable.objects.create(
        pk="cd8f0eec-7c40-46a9-8716-457a7c8b0adb",
        updatedtime=None,
        microservicechainlink_id="8ce130d4-3f7e-46ec-868a-505cf9033d96",
        createdtime=parse_date("2018-06-28T00:00:00+00:00"),
        variablevalue=None,
        variable="normalizationThumbnailProcessing",
    )

    MicroServiceChainLink.objects.create(
        pk="4ca2c28a-8962-412b-9ec3-37c105cc47d9",
        microservicegroup="Normalize",
        reloadfilelist=1,
        defaultexitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        currenttask_id="99b10a95-eebd-40b5-beee-985bee5da5a4",
        defaultnextchainlink=None,
        replaces=None,
    )

    MicroServiceChainLinkExitCode.objects.create(
        pk="1ca2172a-8570-4499-8acd-218bf2c9f746",
        exitcode=0,
        exitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        microservicechainlink_id="4ca2c28a-8962-412b-9ec3-37c105cc47d9",
        nextmicroservicechainlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        replaces=None,
    )

    MicroServiceChainLink.objects.filter(
        pk="56da7758-913a-4cd2-a815-be140ed09357"
    ).update(defaultnextchainlink_id="4ca2c28a-8962-412b-9ec3-37c105cc47d9")

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="56da7758-913a-4cd2-a815-be140ed09357"
    ).update(nextmicroservicechainlink_id="4ca2c28a-8962-412b-9ec3-37c105cc47d9")

    TaskConfig.objects.create(
        pk="9ce16ae3-a87c-4b9d-8584-b0118e1e2b1f",
        tasktypepkreference="1b599511-0193-48a1-b9f3-0f28afaf8f33",
        description="Set normalize path",
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        replaces=None,
        tasktype_id="6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
    )

    TaskConfigSetUnitVariable.objects.create(
        pk="1b599511-0193-48a1-b9f3-0f28afaf8f33",
        updatedtime=None,
        microservicechainlink_id="0a6558cf-cf5f-4646-977e-7d6b4fde47e8",
        createdtime=parse_date("2018-06-28T00:00:00+00:00"),
        variablevalue=None,
        variable="normalizationThumbnailProcessing",
    )

    MicroServiceChainLink.objects.create(
        pk="62e0adc0-87f6-4162-acfa-f560c93d181d",
        microservicegroup="Normalize",
        reloadfilelist=1,
        defaultexitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        currenttask_id="9ce16ae3-a87c-4b9d-8584-b0118e1e2b1f",
        defaultnextchainlink=None,
        replaces=None,
    )

    MicroServiceChainLinkExitCode.objects.create(
        pk="6b2a81c6-8671-460d-9f25-1ef19e42a4fa",
        exitcode=0,
        exitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        microservicechainlink_id="62e0adc0-87f6-4162-acfa-f560c93d181d",
        nextmicroservicechainlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        replaces=None,
    )

    MicroServiceChainLink.objects.filter(
        pk="6b931965-d5f6-4611-a536-39d5901f8f70"
    ).update(defaultnextchainlink_id="62e0adc0-87f6-4162-acfa-f560c93d181d")

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="6b931965-d5f6-4611-a536-39d5901f8f70"
    ).update(nextmicroservicechainlink_id="62e0adc0-87f6-4162-acfa-f560c93d181d")

    TaskConfig.objects.create(
        pk="884d8849-19c6-47c7-947f-ad349a483f44",
        tasktypepkreference="6cfc8e17-b3f6-481e-ba1d-9b1f32c1256b",
        description="Set normalize path",
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        replaces=None,
        tasktype_id="6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
    )

    TaskConfigSetUnitVariable.objects.create(
        pk="6cfc8e17-b3f6-481e-ba1d-9b1f32c1256b",
        updatedtime=None,
        microservicechainlink_id="e950cd98-574b-4e57-9ef8-c2231e1ce451",
        createdtime=parse_date("2018-06-28T00:00:00+00:00"),
        variablevalue=None,
        variable="normalizationThumbnailProcessing",
    )

    MicroServiceChainLink.objects.create(
        pk="8bcbca9c-91f6-4377-b064-b41751fb98ba",
        microservicegroup="Normalize",
        reloadfilelist=1,
        defaultexitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        currenttask_id="884d8849-19c6-47c7-947f-ad349a483f44",
        defaultnextchainlink=None,
        replaces=None,
    )

    MicroServiceChainLinkExitCode.objects.create(
        pk="004c5e3f-04b6-476b-9289-d3755ebd8a7f",
        exitcode=0,
        exitmessage=2,
        lastmodified=parse_date("2018-06-28T00:00:00+00:00"),
        microservicechainlink_id="8bcbca9c-91f6-4377-b064-b41751fb98ba",
        nextmicroservicechainlink_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
        replaces=None,
    )

    MicroServiceChainLink.objects.filter(
        pk="f3a39155-d655-4336-8227-f8c88e4b7669"
    ).update(defaultnextchainlink_id="8bcbca9c-91f6-4377-b064-b41751fb98ba")

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="f3a39155-d655-4336-8227-f8c88e4b7669"
    ).update(nextmicroservicechainlink_id="8bcbca9c-91f6-4377-b064-b41751fb98ba")


class Migration(migrations.Migration):
    """Entry point for the migration."""

    dependencies = [("main", "0054_index_aip_silent_error_branch")]
    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

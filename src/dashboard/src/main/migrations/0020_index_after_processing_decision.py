# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    TaskConfig = apps.get_model("main", "TaskConfig")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    TaskConfigUnitVariableLinkPull = apps.get_model(
        "main", "TaskConfigUnitVariableLinkPull"
    )

    # Remove the original "index transfer contents" microservice during ingest

    update_transfer_index = "d46f6af8-bc4e-4369-a808-c0fedb439fef"
    send_to_backlog = "abd6d60c-d50f-4660-a189-ac1b34fafe85"

    index_transfer_contents = "eb52299b-9ae6-4a1f-831e-c7eee0de829f"
    create_transfer_metadata_xml = "db99ab43-04d7-44ab-89ec-e09d7bbdc39d"

    # "Check for specialized processing" should point at the chainlink after indexing
    TaskConfigUnitVariableLinkPull.objects.filter(
        defaultmicroservicechainlink=index_transfer_contents
    ).update(defaultmicroservicechainlink=create_transfer_metadata_xml)

    # "Identify DSpace METS file" should point at the chainlink after indexing
    MicroServiceChainLink.objects.filter(
        id="8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc"
    ).update(defaultnextchainlink=create_transfer_metadata_xml)
    MicroServiceChainLinkExitCode.objects.filter(
        nextmicroservicechainlink=index_transfer_contents
    ).update(nextmicroservicechainlink=create_transfer_metadata_xml)

    # Delete STC from the old indexing MSCL, and exit codes rows
    StandardTaskConfig.objects.filter(
        id="2c9fd8e4-a4f9-4aa6-b443-de8a9a49e396"
    ).delete()
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink=index_transfer_contents
    ).delete()

    # Instead of updating the status of the file in the backlog,
    # index the files freshly with a "backlog" status
    TaskConfig.objects.filter(id="d6a0dec1-63e7-4c7c-b4c0-e68f0afcedd3").update(
        description="Index transfer contents"
    )
    StandardTaskConfig.objects.filter(id="16ce41d9-7bfa-4167-bca8-49fe358f53ba").update(
        execute="elasticSearchIndex_v0.0",
        arguments='"%SIPDirectory%" "%SIPUUID%" "backlog"',
    )

    # Also move this MSCL to the beginning of the "send to backlog" chain,
    # since it requires having the files still physically accessible
    MicroServiceChain.objects.filter(startinglink=send_to_backlog).update(
        startinglink=update_transfer_index
    )
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink=update_transfer_index
    ).update(nextmicroservicechainlink=send_to_backlog)

    # Finally, mark nextMicroServiceChainLink as null for the new last link
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink="561bbb52-d95c-4004-b0d3-739c0a65f406"
    ).update(nextmicroservicechainlink=None)


class Migration(migrations.Migration):

    dependencies = [("main", "0019_normalization_report")]

    operations = [migrations.RunPython(data_migration)]

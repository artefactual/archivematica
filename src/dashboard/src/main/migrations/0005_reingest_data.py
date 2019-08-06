# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    TaskConfig = apps.get_model("main", "TaskConfig")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainChoice = apps.get_model("main", "MicroServiceChainChoice")
    WatchedDirectory = apps.get_model("main", "WatchedDirectory")

    # Only one exit code for determine version
    MicroServiceChainLinkExitCode.objects.filter(
        id="7f2d5239-b464-4837-8e01-0fc43e31395d"
    ).delete()
    MicroServiceChainLinkExitCode.objects.filter(
        id="6e06fd5e-3892-4e79-b64f-069876bd95a1"
    ).update(exitcode=0)

    # Update DIPfromAIP to Reingest
    MicroServiceChainLink.objects.filter(
        id__in=(
            "9520386f-bb6d-4fb9-a6b6-5845ef39375f",
            "77c722ea-5a8f-48c0-ae82-c66a3fa8ca77",
            "c103b2fb-9a6b-4b68-8112-b70597a6cd14",
            "60b0e812-ebbe-487e-810f-56b1b6fdd819",
            "31fc3f66-34e9-478f-8d1b-c29cd0012360",
            "e4e19c32-16cc-4a7f-a64d-a1f180bdb164",
            "83d5e887-6f7c-48b0-bd81-e3f00a9da772",
        )
    ).update(microservicegroup="Reingest AIP")

    # Update Watched Directory
    WatchedDirectory.objects.filter(
        watched_directory_path="%watchDirectoryPath%system/createDIPFromAIP/"
    ).update(watched_directory_path="%watchDirectoryPath%system/reingestAIP/")
    # Rename DIPfromAIP
    TaskConfig.objects.filter(id="c450501a-251f-4de7-acde-91c47cf62e36").update(
        description="Approve AIP reingest"
    )
    MicroServiceChain.objects.filter(
        startinglink_id="77c722ea-5a8f-48c0-ae82-c66a3fa8ca77"
    ).update(description="Approve AIP reingest")
    MicroServiceChain.objects.filter(
        startinglink_id="9520386f-bb6d-4fb9-a6b6-5845ef39375f"
    ).update(description="AIP reingest approval chain")

    # Add processingMCP
    MicroServiceChainLink.objects.create(
        id="ff516d0b-2bba-414c-88d4-f3575ebf050a",
        microservicegroup="Reingest AIP",
        defaultexitmessage="Failed",
        currenttask_id="f89b9e0f-8789-4292-b5d0-4a330c0205e1",
        defaultnextchainlink_id="7d728c39-395f-4892-8193-92f086c0546f",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="545f54cc-475c-4980-9dff-8f7e65ebaeba",
        microservicechainlink_id="ff516d0b-2bba-414c-88d4-f3575ebf050a",
        exitcode=0,
        nextmicroservicechainlink_id="60b0e812-ebbe-487e-810f-56b1b6fdd819",
        exitmessage="Completed successfully",
    )
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="c103b2fb-9a6b-4b68-8112-b70597a6cd14"
    ).update(nextmicroservicechainlink_id="ff516d0b-2bba-414c-88d4-f3575ebf050a")
    # Redirect to typical normalization node
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink__in=(
            "83d5e887-6f7c-48b0-bd81-e3f00a9da772",
            "e4e19c32-16cc-4a7f-a64d-a1f180bdb164",
        ),
        exitcode=0,
    ).update(nextmicroservicechainlink_id="5d6a103c-9a5d-4010-83a8-6f4c61eb1478")

    # Reject SIP should be the SIP chain, not transfer
    MicroServiceChainChoice.objects.filter(
        choiceavailableatlink_id="9520386f-bb6d-4fb9-a6b6-5845ef39375f",
        chainavailable_id="1b04ec43-055c-43b7-9543-bd03c6a778ba",
    ).update(chainavailable_id="a6ed697e-6189-4b4e-9f80-29209abc7937")

    # Add parse METS to DB MSCL
    repopulateSTC = "12fcbb37-499b-4e1c-8164-3beb1657b6dd"
    repopulateTC = "507c13db-63c9-476b-9a16-0c3a05aff1cb"
    repopulateMSCL = "33533fbb-1607-434f-a82b-cf938c05f60b"
    StandardTaskConfig.objects.create(
        id=repopulateSTC,
        requires_output_lock=False,
        execute="parseMETStoDB_v1.0",
        arguments="%SIPUUID% %SIPDirectory%",
    )
    TaskConfig.objects.create(
        id=repopulateTC,
        tasktype_id="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        tasktypepkreference=repopulateSTC,
        description="Populate database with reingested AIP data",
    )
    MicroServiceChainLink.objects.create(
        id=repopulateMSCL,
        microservicegroup="Reingest AIP",
        defaultexitmessage="Failed",
        currenttask_id=repopulateTC,
        defaultnextchainlink_id="7d728c39-395f-4892-8193-92f086c0546f",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="7ec3b34f-7505-4459-a139-9d7f5738984c",
        microservicechainlink_id=repopulateMSCL,
        exitcode=0,
        nextmicroservicechainlink_id="e4e19c32-16cc-4a7f-a64d-a1f180bdb164",
        exitmessage="Completed successfully",
    )
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="31fc3f66-34e9-478f-8d1b-c29cd0012360"
    ).update(nextmicroservicechainlink_id=repopulateMSCL)

    # Add SIP type to createMETS2
    StandardTaskConfig.objects.filter(id="0aec05d4-7222-4c28-89f4-043d20a812cc").update(
        arguments='''--amdSec --baseDirectoryPath "%SIPDirectory%" --baseDirectoryPathString "SIPDirectory" --fileGroupIdentifier "%SIPUUID%" --fileGroupType "sip_id" --xmlFile "%SIPDirectory%METS.%SIPUUID%.xml" --sipType "%SIPType%"'''
    )

    # METS failure should result in a failed SIP
    failed_sip_link = "7d728c39-395f-4892-8193-92f086c0546f"
    MicroServiceChainLink.objects.filter(
        id="ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0"
    ).update(defaultnextchainlink_id=failed_sip_link)

    # Don't use weird normalization node, remove unitVars for that
    d1 = "29dece8e-55a4-4f2c-b4c2-365ab6376ceb"
    d2 = "635ba89d-0ad6-4fc9-acc3-e6069dffdcd5"
    try:
        MicroServiceChainLinkExitCode.objects.filter(id__in=(d1, d2)).delete()
        MicroServiceChainLink.objects.filter(id__in=(d1, d2)).delete()
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [("main", "0005_reingest")]

    operations = [migrations.RunPython(data_migration)]

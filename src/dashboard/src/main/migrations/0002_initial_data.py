# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import contextlib

from dateutil.parser import parse as parse_date
from django.db import migrations, connection


@contextlib.contextmanager
def suppress_autotime(model, fields):
    """Turn off auto_now and auto_now_add.
    Credits to @soulseekah - http://stackoverflow.com/a/35943149.
    """
    _original_values = {}
    for field in model._meta.local_fields:
        if field.name in fields:
            _original_values[field.name] = {
                "auto_now": field.auto_now,
                "auto_now_add": field.auto_now_add,
            }
            field.auto_now = False
            field.auto_now_add = False
    try:
        yield
    finally:
        for field in model._meta.local_fields:
            if field.name in fields:
                field.auto_now = _original_values[field.name]["auto_now"]
                field.auto_now_add = _original_values[field.name]["auto_now_add"]


def load_fixtures(apps, schema_editor):
    Agent = apps.get_model("main", "Agent")
    MetadataAppliesToType = apps.get_model("main", "MetadataAppliesToType")
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainChoice = apps.get_model("main", "MicroServiceChainChoice")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    MicroServiceChoiceReplacementDic = apps.get_model(
        "main", "MicroServiceChoiceReplacementDic"
    )
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    TaskConfig = apps.get_model("main", "TaskConfig")
    TaskConfigAssignMagicLink = apps.get_model("main", "TaskConfigAssignMagicLink")
    TaskConfigSetUnitVariable = apps.get_model("main", "TaskConfigSetUnitVariable")
    TaskConfigUnitVariableLinkPull = apps.get_model(
        "main", "TaskConfigUnitVariableLinkPull"
    )
    TaskType = apps.get_model("main", "TaskType")
    Taxonomy = apps.get_model("main", "Taxonomy")
    TaxonomyTerm = apps.get_model("main", "TaxonomyTerm")
    TransferMetadataField = apps.get_model("main", "TransferMetadataField")
    WatchedDirectory = apps.get_model("main", "WatchedDirectory")
    WatchedDirectoryExpectedType = apps.get_model(
        "main", "WatchedDirectoryExpectedType"
    )

    with connection.constraint_checks_disabled():
        props = {
            "pk": 1,
            "agenttype": "software",
            "identifiervalue": "Archivematica-1.4.1",
            "name": "Archivematica",
            "identifiertype": "preservation system",
        }
        Agent.objects.create(**props)
        props = {
            "pk": 2,
            "agenttype": "organization",
            "identifiervalue": "ORG",
            "name": "Your Organization Name Here",
            "identifiertype": "repository code",
        }
        Agent.objects.create(**props)

        with suppress_autotime(MetadataAppliesToType, ["lastmodified"]):
            props = {
                "pk": "3e48343d-e2d2-4956-aaa3-b54d26eb9761",
                "replaces": None,
                "description": "SIP",
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MetadataAppliesToType.objects.create(**props)
            props = {
                "pk": "45696327-44c5-4e78-849b-e027a189bf4d",
                "replaces": None,
                "description": "Transfer",
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MetadataAppliesToType.objects.create(**props)
            props = {
                "pk": "7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17",
                "replaces": None,
                "description": "File",
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MetadataAppliesToType.objects.create(**props)

        with suppress_autotime(MicroServiceChain, ["lastmodified"]):
            props = {
                "pk": "01d80b27-4ad1-4bd1-8f8d-f819f18bf685",
                "description": "Yes",
                "startinglink_id": "f19926dd-8fb5-4c79-8ade-c83f61f55b40",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "06f03bb3-121d-4c85-bec7-abbc5320a409",
                "description": "Examine contents",
                "startinglink_id": "100a75f4-9d2a-41bf-8dd0-aec811ae1077",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "0766af55-a950-44d0-a79b-9f2bb65f92c8",
                "description": "Create AIC",
                "startinglink_id": "6404ce13-8619-48ba-b12f-aa7a034153ac",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "082fa7d6-68e1-431c-9216-899aec92cfa7",
                "description": "Attempt restructure for compliance",
                "startinglink_id": "5cf308fd-a6dc-4033-bda1-61689bb55ce2",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "0ea3a6f9-ff37-4f32-ac01-eec5393f008a",
                "description": "Pre-normalize identify file format",
                "startinglink_id": "7a024896-c4f7-4808-a240-44c87c762bc5",
                "replaces": None,
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "0fe9842f-9519-4067-a691-8a363132ae24",
                "description": "Upload DIP to Atom",
                "startinglink_id": "651236d2-d77f-4ca7-bfe9-6332e96608ff",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "167dc382-4ab1-4051-8e22-e7f1c1bf3e6f",
                "description": "Approve transfer",
                "startinglink_id": "f052432c-d4e7-4379-8d86-f2a08f0ae509",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "169a5448-c756-4705-a920-737de6b8d595",
                "description": "Reject",
                "startinglink_id": "19c94543-14cb-4158-986b-1d2b55723cd8",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "191914db-119e-4b91-8422-c77805ad8249",
                "description": "Move transfer back to activeTransfers directory",
                "startinglink_id": "89071669-3bb6-4e03-90a3-3c8b20c7f6fe",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "description": "Reject transfer",
                "startinglink_id": "333532b9-b7c2-4478-9415-28a3056d58df",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "1cb2ef0e-afe8-45b5-8d8f-a1e120f06605",
                "description": "Approve transfer",
                "startinglink_id": "5b7a48e1-32ed-43f9-8ffa-e374010fcf76",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "1e0df175-d56d-450d-8bee-7df1dc7ae815",
                "description": "Approve",
                "startinglink_id": "0f0c1f33-29f2-49ae-b413-3e043da5df61",
                "replaces": None,
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "252ceb42-cc61-4833-a048-97fc0bda4759",
                "description": "Skip quarantine",
                "startinglink_id": "0e379b19-771e-4d90-a7e5-1583e4893c56",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "260ef4ea-f87d-4acf-830d-d0de41e6d2af",
                "description": "Create DIP from AIP",
                "startinglink_id": "77c722ea-5a8f-48c0-ae82-c66a3fa8ca77",
                "replaces": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "2748bedb-12aa-4b10-a556-66e7205580a4",
                "description": "Store DIP",
                "startinglink_id": "ed5d8475-3793-4fb0-a8df-94bd79b26a4c",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "27cf6ca9-11b4-41ac-9014-f8018bcbad5e",
                "description": "Compress AIP",
                "startinglink_id": "01d64f58-8295-4b7b-9cab-8f1b153a504f",
                "replaces": None,
                "lastmodified": parse_date("2013-11-07T22:51:34+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "28a4322d-b8a5-4bae-b2dd-71cc9ff99e73",
                "description": "uploadDIP",
                "startinglink_id": "92879a29-45bf-4f0b-ac43-e64474f0f2f9",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "2ba94783-d073-4372-9bd1-8316ada02635",
                "description": "Quarantine",
                "startinglink_id": "2872d007-6146-4359-b554-6e9fe7a8eca6",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "2eae85d6-da2f-4f1c-8c33-3810b55e23aa",
                "description": "SIP Creation complete",
                "startinglink_id": "36609513-6502-4aca-886a-6c4ae03a9f05",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "333643b7-122a-4019-8bef-996443f3ecc5",
                "description": "Unquarantine",
                "startinglink_id": "4430077a-92c5-4d86-b0f8-0d31bdb731fb",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "39682d0c-8d81-4fdd-8e10-85114b9eb2dd",
                "description": "approveNormalization",
                "startinglink_id": "de909a42-c5b5-46e1-9985-c031b50e9d30",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T07:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "4171636c-e013-4ecc-ae45-60b5458c208b",
                "description": "Transfers In progress",
                "startinglink_id": "998044bb-6260-452f-a742-cfb19e80125b",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "433f4e6b-1ef4-49f8-b1e4-49693791a806",
                "description": "Reject AIP",
                "startinglink_id": "f2e784a0-356b-4b92-9a5a-11887aa3cf48",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "498795c7-06f2-4f3f-95bf-57f1b35964ad",
                "description": "Check transfer directory for objects",
                "startinglink_id": "032cdc54-0b9b-4caf-86e8-10d63efbaec0",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "526eded3-2280-4f10-ac86-eff6c464cc81",
                "description": "Upload DIP to CONTENTdm",
                "startinglink_id": "f12ece2c-fb7e-44de-ba87-7e3c5b6feb74",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "55fa7084-3b64-48ca-be64-08949227f85d",
                "description": "DSpace Transfers In progress",
                "startinglink_id": "b963a646-0569-43c4-89a2-e3b814c5c08e",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "5727faac-88af-40e8-8c10-268644b0142d",
                "description": "Continue",
                "startinglink_id": "77a7fa46-92b9-418e-aa88-fbedd4114c9f",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "5f34245e-5864-4199-aafc-bc0ada01d4cd",
                "description": "Approve AIC",
                "startinglink_id": "f8cb20e6-27aa-44f6-b5a1-dd53b5fc71f6",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "612e3609-ce9a-4df6-a9a3-63d634d2d934",
                "description": "Normalize for preservation",
                "startinglink_id": "6b39088b-683e-48bd-ab89-9dab47f4e9e0",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "61cfa825-120e-4b17-83e6-51a42b67d969",
                "description": "Create single SIP and continue processing",
                "startinglink_id": "8f639582-8881-4a8b-8574-d2f86dc4db3d",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "6953950b-c101-4f4c-a0c3-0cd0684afe5e",
                "description": "Approve transfer",
                "startinglink_id": "f95a3ac5-47bc-4df9-a49c-d47abd1e05f3",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "69f4a4b9-93e2-481c-99a0-fa92d68c3ebd",
                "description": "SIP Creation complete",
                "startinglink_id": "01fd7a29-deb9-4dd1-8e28-1c48fc1ac41b",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "6f0f35fb-6831-4842-9512-4a263700a29b",
                "description": "storeAIP",
                "startinglink_id": "2d32235c-02d4-4686-88a6-96f4d6c7b1c3",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "7030f152-398a-470b-b045-f5dfa9013671",
                "description": "quarantineSIP ?",
                "startinglink_id": "55de1490-f3a0-4e1e-a25b-38b75f4f05e3",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "7065d256-2f47-4b7d-baec-2c4699626121",
                "description": "Send to backlog",
                "startinglink_id": "abd6d60c-d50f-4660-a189-ac1b34fafe85",
                "replaces": None,
                "lastmodified": parse_date("2013-04-05T23:08:30+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "79f1f5af-7694-48a4-b645-e42790bbf870",
                "description": "No",
                "startinglink_id": "307edcde-ad10-401c-92c4-652917c993ed",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "816f28cd-6af1-4d26-97f3-e61645eb881b",
                "description": "baggitDirectory Transfers In progress",
                "startinglink_id": "f6bcc82a-d629-4a78-8643-bf6e3cb39fe6",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "86fbea68-d08c-440f-af2c-dac68556db12",
                "description": "Move to metadata reminder",
                "startinglink_id": "eeb23509-57e2-4529-8857-9d62525db048",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "89cb80dd-0636-464f-930d-57b61e3928b2",
                "description": "Do not normalize",
                "startinglink_id": "0b92a510-a290-44a8-86d8-6b7139be29df",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "94f764ad-805a-4d4e-8a2b-a6f2515b30c7",
                "description": "TRIM Ingest",
                "startinglink_id": "8db10a7b-924f-4561-87b4-cb6078c65aab",
                "replaces": None,
                "lastmodified": parse_date("2012-11-30T19:55:49+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "96b49116-b114-47e8-95d0-b3c6ae4e80f5",
                "description": "Examine contents?",
                "startinglink_id": "accea2bf-ba74-4a3a-bb97-614775c74459",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "97ea7702-e4d5-48bc-b4b5-d15d897806ab",
                "description": "Quarantine",
                "startinglink_id": "46dcf7b1-3750-4f49-a9be-a4bf076e304f",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "9918b64c-b898-407b-bce4-a65aa3c11b89",
                "description": "createDIPFromAIP-wdChain",
                "startinglink_id": "9520386f-bb6d-4fb9-a6b6-5845ef39375f",
                "replaces": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "9efab23c-31dc-4cbd-a39d-bb1665460cbe",
                "description": "Store AIP",
                "startinglink_id": "49cbcc4d-067b-4cd5-b52e-faf50857b35a",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "a2e19764-b373-4093-b0dd-11d61580f180",
                "description": "SIP Creation",
                "startinglink_id": "ab69c494-23b7-4f50-acff-2e00cf7bffda",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "a6ed697e-6189-4b4e-9f80-29209abc7937",
                "description": "Reject SIP",
                "startinglink_id": "19c94543-14cb-4158-986b-1d2b55723cd8",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "ad37288a-162c-4562-8532-eb4050964c73",
                "description": "Unquarantine",
                "startinglink_id": "fbc3857b-bb02-425b-89ce-2d6a39eaa542",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "b0e0bf75-6b7e-44b6-a0d0-189eea7605dd",
                "description": "baggitZippedFile Transfers In progress",
                "startinglink_id": "15402367-2d3f-475e-b251-55532347a3c2",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "b93cecd4-71f2-4e28-bc39-d32fd62c5a94",
                "description": "Normalize for preservation and access",
                "startinglink_id": "424ee8f1-6cdd-4960-8641-ed82361d3ad7",
                "replaces": None,
                "lastmodified": parse_date("2012-12-04T22:56:32+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "bd94cc9b-7990-45a2-a255-a1b70936f9f2",
                "description": "Identify file format",
                "startinglink_id": "f09847c2-ee51-429a-9478-a860477f6b8d",
                "replaces": None,
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "c34bd22a-d077-4180-bf58-01db35bdb644",
                "description": "Normalize manually",
                "startinglink_id": "31abe664-745e-4fef-a669-ff41514e0083",
                "replaces": None,
                "lastmodified": parse_date("2013-01-05T01:09:13+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "c622426e-190e-437b-aa1a-4be9c9a7680d",
                "description": "Unquarantine",
                "startinglink_id": "01fd7a29-deb9-4dd1-8e28-1c48fc1ac41b",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "c75ef451-2040-4511-95ac-3baa0f019b48",
                "description": "Approve transfer",
                "startinglink_id": "45f4a7e3-87cf-4fb4-b4f9-e36ad8c853b1",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "c868840c-cf0b-49db-a684-af4248702954",
                "description": "Extract packages",
                "startinglink_id": "b944ec7f-7f99-491f-986d-58914c9bb4fa",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "cbe9b4a3-e4e6-4a32-8d7c-3adfc409cb6f",
                "description": "Redo",
                "startinglink_id": "b15c0ba6-e247-4512-8b56-860fd2b6299d",
                "replaces": None,
                "lastmodified": parse_date("2012-10-24T17:04:11+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "cc38912d-6520-44e1-92ff-76bb4881a55e",
                "description": "Failed compliance",
                "startinglink_id": "a98ba456-3dcd-4f45-804c-a40220ddc6cb",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "d381cf76-9313-415f-98a1-55c91e4d78e0",
                "description": "Approve transfer",
                "startinglink_id": "22c0f074-07b1-445f-9e8b-bf75ac7f0b48",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e",
                "description": "Skip quarantine",
                "startinglink_id": "d7e6404a-a186-4806-a130-7e6d27179a15",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "d4ff46d4-5c57-408c-943b-fed63c1a9d75",
                "description": "SIP Creation complete",
                "startinglink_id": "4430077a-92c5-4d86-b0f8-0d31bdb731fb",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "df54fec1-dae1-4ea6-8d17-a839ee7ac4a7",
                "description": "Yes",
                "startinglink_id": "4efe00da-6ed0-45dd-89ca-421b78c4b6be",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "e0a39199-c62a-4a2f-98de-e9d1116460a8",
                "description": "Skip examine contents",
                "startinglink_id": "192315ea-a1bf-44cf-8cb4-0b3edd1522a6",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "e4a59e3e-3dba-4eb5-9cf1-c1fb3ae61fa9",
                "description": "Approve transfer",
                "startinglink_id": "3868c8b8-977d-4162-a319-dc487de20f11",
                "replaces": None,
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "e600b56d-1a43-4031-9d7c-f64f123e5662",
                "description": "Normalize service files for access",
                "startinglink_id": "b20ff203-1472-40db-b879-0e59d17de867",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "e8544c5e-9cbb-4b8f-a68b-6d9b4d7f7362",
                "description": "Do not normalize",
                "startinglink_id": "70f41678-baa5-46e6-a71c-4b6b4d99f4a6",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "e9eaef1e-c2e0-4e3b-b942-bfb537162795",
                "description": "No",
                "startinglink_id": "2584b25c-8d98-44b7-beca-2b3ea2ea2505",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "eea54915-2a85-49b7-a370-b1a250dd29ce",
                "description": "Reject DIP",
                "startinglink_id": "f2a1faaf-7322-4d9c-aff9-f809e7a6a6a2",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "f11409ad-cf3c-4e7f-b0d5-4be32d98229b",
                "description": "Upload DIP to Archivists Toolkit",
                "startinglink_id": "7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1",
                "replaces": None,
                "lastmodified": parse_date("2013-03-26T03:25:01+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "f6df8882-d076-441e-bb00-2f58d5eda098",
                "description": "Generate transfer structure report",
                "startinglink_id": "6eca2676-b4ed-48d9-adb0-374e1d5c6e71",
                "replaces": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "fb7a326e-1e50-4b48-91b9-4917ff8d0ae8",
                "description": "Normalize for access",
                "startinglink_id": "6327fdf9-9673-42a8-ace5-cccad005818b",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "fefdcee4-dd84-4b55-836f-99ef880ecdb6",
                "description": "Automatic SIP Creation complete",
                "startinglink_id": "db6d3830-9eb4-4996-8f3a-18f4f998e07f",
                "replaces": None,
                "lastmodified": parse_date("2013-08-22T23:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)
            props = {
                "pk": "fffd5342-2337-463f-857a-b2c8c3778c6d",
                "description": "Transfers In progress",
                "startinglink_id": "0c94e6b5-4714-4bec-82c8-e187e0c04d77",
                "replaces": None,
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
            }
            MicroServiceChain.objects.create(**props)

        with suppress_autotime(MicroServiceChainChoice, ["lastmodified"]):
            props = {
                "pk": "00ed2cf8-c301-4de9-a80b-f00f2cae3667",
                "choiceavailableatlink_id": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                "chainavailable_id": "b93cecd4-71f2-4e28-bc39-d32fd62c5a94",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "06183294-4c2a-4763-9262-c2ab0fbdf36f",
                "choiceavailableatlink_id": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                "chainavailable_id": "612e3609-ce9a-4df6-a9a3-63d634d2d934",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "15525b8f-a6b6-4c2d-98d0-943b2fb106ec",
                "choiceavailableatlink_id": "2d32235c-02d4-4686-88a6-96f4d6c7b1c3",
                "chainavailable_id": "433f4e6b-1ef4-49f8-b1e4-49693791a806",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "15e370a2-1381-42b0-aab7-baf6095cee39",
                "choiceavailableatlink_id": "05f99ffd-abf2-4f5a-9ec8-f80a59967b89",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "171c7418-53c1-4d00-bcac-f77012050d1b",
                "choiceavailableatlink_id": "56eebd45-5600-4768-a8c2-ec0114555a3d",
                "chainavailable_id": "df54fec1-dae1-4ea6-8d17-a839ee7ac4a7",
                "replaces_id": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "176ee50a-0a9b-455b-bd60-ea2e95de9d4e",
                "choiceavailableatlink_id": "f3a58cbb-20a8-4c6d-9ae4-1a5f02c1a28e",
                "chainavailable_id": "333643b7-122a-4019-8bef-996443f3ecc5",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "1786f77e-4035-49c1-b966-32dbb6b189eb",
                "choiceavailableatlink_id": "998044bb-6260-452f-a742-cfb19e80125b",
                "chainavailable_id": "d381cf76-9313-415f-98a1-55c91e4d78e0",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "1b408994-ac47-4166-8a9b-4ef4bde09474",
                "choiceavailableatlink_id": "92879a29-45bf-4f0b-ac43-e64474f0f2f9",
                "chainavailable_id": "526eded3-2280-4f10-ac86-eff6c464cc81",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "1e350acc-b9c3-4845-8521-24b041495df3",
                "choiceavailableatlink_id": "ab69c494-23b7-4f50-acff-2e00cf7bffda",
                "chainavailable_id": "a6ed697e-6189-4b4e-9f80-29209abc7937",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "25bab081-384f-4462-be01-9dfef2dd6f30",
                "choiceavailableatlink_id": "dec97e3c-5598-4b99-b26e-f87a435a6b7f",
                "chainavailable_id": "01d80b27-4ad1-4bd1-8f8d-f819f18bf685",
                "replaces_id": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "29797e14-9528-455f-87d1-2026d54cf1bd",
                "choiceavailableatlink_id": "bb194013-597c-4e4a-8493-b36d190f8717",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "2df531df-339d-49c0-a5fe-5e655596b566",
                "choiceavailableatlink_id": "b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3",
                "chainavailable_id": "c34bd22a-d077-4180-bf58-01db35bdb644",
                "replaces_id": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "2e0a75d8-5f76-44d6-b5c3-e7d6ff5be58d",
                "choiceavailableatlink_id": "b963a646-0569-43c4-89a2-e3b814c5c08e",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "2e8ca13c-00f6-4610-b76c-13ba94d0e75d",
                "choiceavailableatlink_id": "15402367-2d3f-475e-b251-55532347a3c2",
                "chainavailable_id": "167dc382-4ab1-4051-8e22-e7f1c1bf3e6f",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "320440c5-d0c0-40a0-9659-7fa811ece50a",
                "choiceavailableatlink_id": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                "chainavailable_id": "c34bd22a-d077-4180-bf58-01db35bdb644",
                "replaces_id": None,
                "lastmodified": parse_date("2013-01-05T01:09:14+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "35c8e6a3-42c3-411a-b6b5-3d83d1759db7",
                "choiceavailableatlink_id": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                "chainavailable_id": "89cb80dd-0636-464f-930d-57b61e3928b2",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "399293b8-0d58-41b5-89c5-5edde497448b",
                "choiceavailableatlink_id": "b963a646-0569-43c4-89a2-e3b814c5c08e",
                "chainavailable_id": "1cb2ef0e-afe8-45b5-8d8f-a1e120f06605",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "399982e9-ebba-43da-b815-cddbeef3b551",
                "choiceavailableatlink_id": "7509e7dc-1e1b-4dce-8d21-e130515fce73",
                "chainavailable_id": "a6ed697e-6189-4b4e-9f80-29209abc7937",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "39bcba03-d251-4974-8a7b-45b2444e19a8",
                "choiceavailableatlink_id": "92879a29-45bf-4f0b-ac43-e64474f0f2f9",
                "chainavailable_id": "eea54915-2a85-49b7-a370-b1a250dd29ce",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "3fab588e-58dd-4d86-a5ce-2e4b67774c28",
                "choiceavailableatlink_id": "dec97e3c-5598-4b99-b26e-f87a435a6b7f",
                "chainavailable_id": "79f1f5af-7694-48a4-b645-e42790bbf870",
                "replaces_id": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "4197199a-897a-47eb-b573-59c90ba1373a",
                "choiceavailableatlink_id": "92879a29-45bf-4f0b-ac43-e64474f0f2f9",
                "chainavailable_id": "f11409ad-cf3c-4e7f-b0d5-4be32d98229b",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T07:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "41d23044-2616-445d-aa3e-7db0a9e05813",
                "choiceavailableatlink_id": "15402367-2d3f-475e-b251-55532347a3c2",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "47d090b7-f0c6-472f-84a1-fc9809dfa00f",
                "choiceavailableatlink_id": "b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3",
                "chainavailable_id": "fb7a326e-1e50-4b48-91b9-4917ff8d0ae8",
                "replaces_id": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "4a266d37-6c3d-49f7-b1ac-b93c0906945f",
                "choiceavailableatlink_id": "bb194013-597c-4e4a-8493-b36d190f8717",
                "chainavailable_id": "7065d256-2f47-4b7d-baec-2c4699626121",
                "replaces_id": None,
                "lastmodified": parse_date("2013-04-05T23:08:30+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "54d5f6a8-174c-4dd8-8698-546253c8043a",
                "choiceavailableatlink_id": "5c459c1a-f998-404d-a0dd-808709510b72",
                "chainavailable_id": "082fa7d6-68e1-431c-9216-899aec92cfa7",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "58a48e1d-b317-47b5-b4d4-996c98e0534a",
                "choiceavailableatlink_id": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                "chainavailable_id": "a6ed697e-6189-4b4e-9f80-29209abc7937",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "5c149b3b-8fb3-431c-a577-11cf349cfb38",
                "choiceavailableatlink_id": "eeb23509-57e2-4529-8857-9d62525db048",
                "chainavailable_id": "5727faac-88af-40e8-8c10-268644b0142d",
                "replaces_id": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "5cfaab52-dbdb-442c-82ee-310840330613",
                "choiceavailableatlink_id": "92879a29-45bf-4f0b-ac43-e64474f0f2f9",
                "chainavailable_id": "0fe9842f-9519-4067-a691-8a363132ae24",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "61452cbf-f3ad-4fd4-b602-bd6f1ba303f7",
                "choiceavailableatlink_id": "19adb668-b19a-4fcb-8938-f49d7485eaf3",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "63f0e429-1435-48e2-8eb0-dcb68e507168",
                "choiceavailableatlink_id": "56eebd45-5600-4768-a8c2-ec0114555a3d",
                "chainavailable_id": "e9eaef1e-c2e0-4e3b-b942-bfb537162795",
                "replaces_id": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "64e33508-c51d-4d96-9523-1a0c3b0809b1",
                "choiceavailableatlink_id": "accea2bf-ba74-4a3a-bb97-614775c74459",
                "chainavailable_id": "e0a39199-c62a-4a2f-98de-e9d1116460a8",
                "replaces_id": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "7131abac-d1e9-4dfc-b48a-36461485c240",
                "choiceavailableatlink_id": "0c94e6b5-4714-4bec-82c8-e187e0c04d77",
                "chainavailable_id": "6953950b-c101-4f4c-a0c3-0cd0684afe5e",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "73671d95-dfcc-4b77-91b6-ca7f194f8def",
                "choiceavailableatlink_id": "9520386f-bb6d-4fb9-a6b6-5845ef39375f",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "75258260-40c1-4162-8d5b-47a6417fbbc1",
                "choiceavailableatlink_id": "755b4177-c587-41a7-8c52-015277568302",
                "chainavailable_id": "97ea7702-e4d5-48bc-b4b5-d15d897806ab",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "7915624c-a235-44d0-8baf-307cd3f1ded9",
                "choiceavailableatlink_id": "f3a58cbb-20a8-4c6d-9ae4-1a5f02c1a28e",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "79858774-a10d-4bcb-b5d2-abf96c169cac",
                "choiceavailableatlink_id": "f6bcc82a-d629-4a78-8643-bf6e3cb39fe6",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "8001468a-1cc6-44fe-ad33-1b5c85bf2fcf",
                "choiceavailableatlink_id": "f6bcc82a-d629-4a78-8643-bf6e3cb39fe6",
                "chainavailable_id": "c75ef451-2040-4511-95ac-3baa0f019b48",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "913ee4f7-35f4-44a0-9249-eb1cfc270d4e",
                "choiceavailableatlink_id": "accea2bf-ba74-4a3a-bb97-614775c74459",
                "chainavailable_id": "06f03bb3-121d-4c85-bec7-abbc5320a409",
                "replaces_id": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "91d8699a-9fa3-4956-ad3c-d993da05efe7",
                "choiceavailableatlink_id": "b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3",
                "chainavailable_id": "e600b56d-1a43-4031-9d7c-f64f123e5662",
                "replaces_id": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "92bb65f8-3eab-484e-aae4-4d2a311358bb",
                "choiceavailableatlink_id": "bb194013-597c-4e4a-8493-b36d190f8717",
                "chainavailable_id": "61cfa825-120e-4b17-83e6-51a42b67d969",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "9b3bb1a8-86a8-498b-8fd1-e0e260a84a90",
                "choiceavailableatlink_id": "8db10a7b-924f-4561-87b4-cb6078c65aab",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-11-30T19:55:49+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "9d932c28-da5a-4e1b-b711-bea05cadac8a",
                "choiceavailableatlink_id": "05f99ffd-abf2-4f5a-9ec8-f80a59967b89",
                "chainavailable_id": "2ba94783-d073-4372-9bd1-8316ada02635",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "9edb1021-60b1-4c97-8d8d-b84bd163d452",
                "choiceavailableatlink_id": "5c459c1a-f998-404d-a0dd-808709510b72",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "a053c274-3047-40fa-b004-9f320ce0bb22",
                "choiceavailableatlink_id": "de909a42-c5b5-46e1-9985-c031b50e9d30",
                "chainavailable_id": "cbe9b4a3-e4e6-4a32-8d7c-3adfc409cb6f",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-24T17:04:11+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "a431002e-5ac5-44c8-82ac-27e426f3e07e",
                "choiceavailableatlink_id": "0c94e6b5-4714-4bec-82c8-e187e0c04d77",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "a69e8ead-dff3-4e12-9560-2cc4928e28e9",
                "choiceavailableatlink_id": "998044bb-6260-452f-a742-cfb19e80125b",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "bcb2db4e-881f-4726-a2ad-922818c9897b",
                "choiceavailableatlink_id": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                "chainavailable_id": "e600b56d-1a43-4031-9d7c-f64f123e5662",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "bebc5174-09b8-49e6-8dd6-4896e49fdc5e",
                "choiceavailableatlink_id": "6404ce13-8619-48ba-b12f-aa7a034153ac",
                "chainavailable_id": "5f34245e-5864-4199-aafc-bc0ada01d4cd",
                "replaces_id": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "bf622d91-0bbb-491b-b3d6-7dec6bf73b72",
                "choiceavailableatlink_id": "19adb668-b19a-4fcb-8938-f49d7485eaf3",
                "chainavailable_id": "c622426e-190e-437b-aa1a-4be9c9a7680d",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "c6d19691-c697-44e4-b718-3d82a10efaed",
                "choiceavailableatlink_id": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                "chainavailable_id": "fb7a326e-1e50-4b48-91b9-4917ff8d0ae8",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "c7bbb25e-599b-4511-8392-151088f87dce",
                "choiceavailableatlink_id": "9520386f-bb6d-4fb9-a6b6-5845ef39375f",
                "chainavailable_id": "260ef4ea-f87d-4acf-830d-d0de41e6d2af",
                "replaces_id": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "cb15da43-5c1b-478a-b25c-2ef69eff1dbf",
                "choiceavailableatlink_id": "92879a29-45bf-4f0b-ac43-e64474f0f2f9",
                "chainavailable_id": "2748bedb-12aa-4b10-a556-66e7205580a4",
                "replaces_id": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "cf0b6ef5-6bda-4f3a-a300-bf696c0a9940",
                "choiceavailableatlink_id": "755b4177-c587-41a7-8c52-015277568302",
                "chainavailable_id": "252ceb42-cc61-4833-a048-97fc0bda4759",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "d0fc8557-2ba2-4047-8b86-0a953900de5d",
                "choiceavailableatlink_id": "5c459c1a-f998-404d-a0dd-808709510b72",
                "chainavailable_id": "191914db-119e-4b91-8422-c77805ad8249",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "dc81c760-546d-4a90-85c2-b15aa3f5f27b",
                "choiceavailableatlink_id": "de909a42-c5b5-46e1-9985-c031b50e9d30",
                "chainavailable_id": "1e0df175-d56d-450d-8bee-7df1dc7ae815",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "e1ebb8eb-2f59-4e0e-bb7b-9bef930bf482",
                "choiceavailableatlink_id": "ab69c494-23b7-4f50-acff-2e00cf7bffda",
                "chainavailable_id": "2eae85d6-da2f-4f1c-8c33-3810b55e23aa",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "e584eca5-52bb-46c8-9ca0-f8ed3a1e3719",
                "choiceavailableatlink_id": "7509e7dc-1e1b-4dce-8d21-e130515fce73",
                "chainavailable_id": "e8544c5e-9cbb-4b8f-a68b-6d9b4d7f7362",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "e5c0da9a-8c16-41f7-8798-c90b04ac5541",
                "choiceavailableatlink_id": "de909a42-c5b5-46e1-9985-c031b50e9d30",
                "chainavailable_id": "169a5448-c756-4705-a920-737de6b8d595",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "e5e040db-2bc0-487b-a080-a9699cb5f05a",
                "choiceavailableatlink_id": "2d32235c-02d4-4686-88a6-96f4d6c7b1c3",
                "chainavailable_id": "9efab23c-31dc-4cbd-a39d-bb1665460cbe",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "e698d95e-4303-41e1-a0aa-c0b18866e3d0",
                "choiceavailableatlink_id": "8db10a7b-924f-4561-87b4-cb6078c65aab",
                "chainavailable_id": "e4a59e3e-3dba-4eb5-9cf1-c1fb3ae61fa9",
                "replaces_id": None,
                "lastmodified": parse_date("2012-11-30T19:55:49+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "e981fb29-7f93-4719-99ba-f2d22455f3ed",
                "choiceavailableatlink_id": "6404ce13-8619-48ba-b12f-aa7a034153ac",
                "chainavailable_id": "169a5448-c756-4705-a920-737de6b8d595",
                "replaces_id": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "f68b9e34-2808-4943-919d-9aab95eae460",
                "choiceavailableatlink_id": "7509e7dc-1e1b-4dce-8d21-e130515fce73",
                "chainavailable_id": "612e3609-ce9a-4df6-a9a3-63d634d2d934",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "fb06f370-24dc-4a3e-8900-6fad0159a0ab",
                "choiceavailableatlink_id": "755b4177-c587-41a7-8c52-015277568302",
                "chainavailable_id": "1b04ec43-055c-43b7-9543-bd03c6a778ba",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)
            props = {
                "pk": "fe49358d-e270-451a-b7e5-c12558b9c06f",
                "choiceavailableatlink_id": "05f99ffd-abf2-4f5a-9ec8-f80a59967b89",
                "chainavailable_id": "d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:05+00:00"),
            }
            MicroServiceChainChoice.objects.create(**props)

        with suppress_autotime(MicroServiceChainLink, ["lastmodified"]):
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:34+00:00"),
                "currenttask_id": "18dceb0a-dfb1-4b18-81a7-c6c5c578c5f1",
                "replaces_id": None,
                "pk": "002716a1-ae29-4f36-98ab-0d97192669c4",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "c2c7edcc-0e65-4df7-812f-a2ee5b5d52b6",
                "replaces_id": None,
                "pk": "01b30826-bfc4-4e07-8ca2-4263debad642",
                "defaultnextchainlink_id": "e19f8eed-faf9-4e04-bf1f-e9418f2b2b11",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "2f6947ee-5d92-416a-bade-b1079767e641",
                "replaces_id": None,
                "pk": "01c651cb-c174-4ba4-b985-1d87a44d6754",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "8a291152-729c-42f2-ab2e-c53b9f357799",
                "replaces_id": None,
                "pk": "01d64f58-8295-4b7b-9cab-8f1b153a504f",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "01fd7a29-deb9-4dd1-8e28-1c48fc1ac41b",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "8cda5b7a-fb44-4a61-a865-6ad01af5a150",
                "replaces_id": None,
                "pk": "032cdc54-0b9b-4caf-86e8-10d63efbaec0",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "3e70f50d-5056-413e-a3d1-7b4b13d2b821",
                "replaces_id": None,
                "pk": "03ee1136-f6ad-4184-8dcb-34872f843e14",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process metadata directory",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "6511ac58-d68e-4381-9cf3-01f2637acb4c",
                "replaces_id": None,
                "pk": "04493ab2-6cad-400d-8832-06941f121a96",
                "defaultnextchainlink_id": "75fb5d67-5efa-4232-b00b-d85236de0d3f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "48929c19-c0c7-41b2-8bd0-552b22e2d86f",
                "replaces_id": None,
                "pk": "045c43ae-d6cf-44f7-97d6-c8a602748565",
                "defaultnextchainlink_id": "50b67418-cb8d-434d-acc9-4a8324e7fdd2",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "f3567a6d-8a45-4174-b302-a629cdbfbe92",
                "replaces_id": None,
                "pk": "05f99ffd-abf2-4f5a-9ec8-f80a59967b89",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "0c95f944-837f-4ada-a396-2c7a818806c6",
                "replaces_id": None,
                "pk": "087d27be-c719-47d8-9bbb-9a7d8b609c44",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "a20c5353-9e23-4b5d-bb34-09f2efe1e54d",
                "replaces_id": None,
                "pk": "0915f727-0bc3-47c8-b9b2-25dc2ecef2bb",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "currenttask_id": "a8489361-b731-4d4a-861d-f4da1767665f",
                "replaces_id": None,
                "pk": "092b47db-6f77-4072-aed3-eb248ab69e9c",
                "defaultnextchainlink_id": "bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-10T22:49:48+00:00"),
                "currenttask_id": "21f8f2b6-d285-490a-9276-bfa87a0a4fb9",
                "replaces_id": None,
                "pk": "09b85517-e5f5-415b-a950-1a60ee285242",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "currenttask_id": "2894f4ea-0d11-431f-a7de-c2f765bd55a6",
                "replaces_id": None,
                "pk": "0a63befa-327d-4655-a021-341b639ee9ed",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "21f8f2b6-d285-490a-9276-bfa87a0a4fb9",
                "replaces_id": None,
                "pk": "0a6558cf-cf5f-4646-977e-7d6b4fde47e8",
                "defaultnextchainlink_id": "54b73077-a062-41cc-882c-4df1eba447d9",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "acd5e136-11ed-46fe-bf67-dc108f115d6b",
                "replaces_id": None,
                "pk": "0b92a510-a290-44a8-86d8-6b7139be29df",
                "defaultnextchainlink_id": "f6fdd1a7-f0c5-4631-b5d3-19421155bd7a",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIC",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "3ae4931e-886e-4e0a-9a85-9b047c9983ac",
                "replaces_id": None,
                "pk": "0c2c9c9a-25b2-4a2d-a790-103da79f9604",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "1b8b596f-b6ee-440f-b59c-5e8b39a2b46d",
                "replaces_id": None,
                "pk": "0c94e6b5-4714-4bec-82c8-e187e0c04d77",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Include default Transfer processingMCP.xml",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "a73b3690-ac75-4030-bb03-0c07576b649b",
                "replaces_id": None,
                "pk": "0c96c798-9ace-4c05-b3cf-243cdad796b7",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Reject AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-03-27T20:12:26+00:00"),
                "currenttask_id": "be4e3ee6-9be3-465f-93f0-77a4ccdfd1db",
                "replaces_id": None,
                "pk": "0d7f5dc2-b9af-43bf-b698-10fdcc5b014d",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "0e06d968-4b5b-4084-aab4-053a2a8d1679",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "0e1a8a6b-abcc-4ed6-b4fb-cbccfdc23ef5",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Clean up names",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "0e379b19-771e-4d90-a7e5-1583e4893c56",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Identify file format",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "a75ee667-3a1c-4950-9194-e07d0e6bf545",
                "replaces_id": None,
                "pk": "0e41c244-6c3e-46b9-a554-65e66e5c9324",
                "defaultnextchainlink_id": "95616c10-a79f-48ca-a352-234cc91eaf08",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "0f0c1f33-29f2-49ae-b413-3e043da5df61",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-30T19:55:47+00:00"),
                "currenttask_id": "0b90715c-50bc-4cb7-a390-771a7cc8180f",
                "replaces_id": None,
                "pk": "0fc3c795-dc68-4aa0-86fc-cbd6af3302fa",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Examine contents",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "869c4c44-6e7d-4473-934d-80c7b95a8310",
                "replaces_id": None,
                "pk": "100a75f4-9d2a-41bf-8dd0-aec811ae1077",
                "defaultnextchainlink_id": "192315ea-a1bf-44cf-8cb4-0b3edd1522a6",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process manually normalized files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "currenttask_id": "68920df3-66aa-44fc-b221-710dbe97680a",
                "replaces_id": None,
                "pk": "10c40e41-fb10-48b5-9d01-336cd958afe8",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "f23a22b8-a3b0-440b-bf4e-fb6e8e6e6b14",
                "replaces_id": None,
                "pk": "11033dbd-e4d4-4dd6-8bcf-48c424e222e3",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "currenttask_id": "8ed6f0e4-cd5c-4c4b-bce0-e8949ea696cd",
                "replaces_id": None,
                "pk": "1401c4d0-fb6f-42ef-94d3-c884c25800b2",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIC",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "741a09ee-8143-4216-8919-1046571af3e9",
                "replaces_id": None,
                "pk": "142d0a36-2b88-4b98-8a33-d809f667ecef",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "243b67e9-4d0b-4c38-8fa4-0fa3df8a5b86",
                "replaces_id": None,
                "pk": "15402367-2d3f-475e-b251-55532347a3c2",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "76729a40-dfa1-4c1a-adbf-01fb362324f5",
                "replaces_id": None,
                "pk": "154dd501-a344-45a9-97e3-b30093da35f5",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-02-19T00:52:52+00:00"),
                "currenttask_id": "602e9b26-5839-4940-b230-0264bb873fe7",
                "replaces_id": None,
                "pk": "15a2df8a-7b45-4c11-b6fa-884c9b7e5c67",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-12-04T22:46:47+00:00"),
                "currenttask_id": "9371ba25-b600-485d-b2d8-cef2f39c35ed",
                "replaces_id": None,
                "pk": "16415d2f-5642-496d-a46d-00028ef6eb0a",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "73e12d44-ec3d-41a9-b138-80ec7e31ede5",
                "replaces_id": None,
                "pk": "173d310c-8e40-4669-9a69-6d4c8ffd0396",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "currenttask_id": "a8489361-b731-4d4a-861d-f4da1767665f",
                "replaces_id": None,
                "pk": "180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21",
                "defaultnextchainlink_id": "8ce378a5-1418-4184-bf02-328a06e1d3be",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Examine contents",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "3649f0f4-2174-44af-aef9-31ebeddeb73b",
                "replaces_id": None,
                "pk": "192315ea-a1bf-44cf-8cb4-0b3edd1522a6",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad1f1ae6-658f-4281-abc2-fe2f6c5d5e8e",
                "replaces_id": None,
                "pk": "19adb668-b19a-4fcb-8938-f49d7485eaf3",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Reject SIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "2d8f4aa1-76ad-4c88-af81-f7f494780628",
                "replaces_id": None,
                "pk": "19c94543-14cb-4158-986b-1d2b55723cd8",
                "defaultnextchainlink_id": "3467d003-1603-49e3-b085-e58aa693afed",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Characterize and extract metadata",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7beb3689-02a7-4f56-a6d1-9c9399f06842",
                "replaces_id": None,
                "pk": "1b1a4565-b501-407b-b40f-2f20889423f1",
                "defaultnextchainlink_id": "a536828c-be65-4088-80bd-eb511a0a063d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "currenttask_id": "256e18ca-1bcd-4b14-b3d5-4efbad5663fc",
                "replaces_id": None,
                "pk": "1b737a9b-b4c0-4230-aa92-1e88067534b9",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "fecb3fe4-5c5c-4796-b9dc-c7d7cf33a9f3",
                "replaces_id": None,
                "pk": "1ba589db-88d1-48cf-bb1a-a5f9d2b17378",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Scan for viruses",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "3c002fb6-a511-461e-ad16-0d2c46649374",
                "replaces_id": None,
                "pk": "1c2550f1-3fc0-45d8-8bc4-4c06d720283b",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Completed successfully",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "09f73737-f7ca-4ea2-9676-d369f390e650",
                "replaces_id": None,
                "pk": "1cb7e228-6e94-4c93-bf70-430af99b9264",
                "defaultnextchainlink_id": "307edcde-ad10-401c-92c4-652917c993ed",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "5a3d244e-c7a1-4cd9-b1a8-2890bf1f254c",
                "replaces_id": None,
                "pk": "1cd3b36a-5252-4a69-9b1c-3b36829288ab",
                "defaultnextchainlink_id": "67b44f8f-bc97-4cb3-b6dd-09dba3c99d30",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "28e8e81c-3380-47f6-a973-e48f94104692",
                "replaces_id": None,
                "pk": "1dce8e21-7263-4cc4-aa59-968d9793b5f2",
                "defaultnextchainlink_id": "33d7ac55-291c-43ae-bb42-f599ef428325",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-12-06T18:58:24+00:00"),
                "currenttask_id": "eb14ba91-20cb-4b0e-ab5d-c30bfea4dbc8",
                "replaces_id": None,
                "pk": "20129b22-8f28-429b-a3f2-0648090fa305",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Store AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "bf71562c-bc87-4fd0-baa6-1d85ff751ea2",
                "replaces_id": None,
                "pk": "20515483-25ed-4133-b23e-5bb14cab8e22",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify SIP compliance",
                "defaultexitmessage": "Completed successfully",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "e82c3c69-3799-46fd-afc1-f479f960a362",
                "replaces_id": None,
                "pk": "208d441b-6938-44f9-b54a-bd73f05bc764",
                "defaultnextchainlink_id": "7d0616b2-afed-41a6-819a-495032e86291",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Include default Transfer processingMCP.xml",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "cfc7f6be-3984-4727-a71a-02ce27bef791",
                "replaces_id": None,
                "pk": "209400c1-5619-4acc-b091-b9d9c8fbb1c0",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-12-12T21:25:31+00:00"),
                "currenttask_id": "f6fbbf4f-bf8d-49f2-a978-8d689380cafc",
                "replaces_id": None,
                "pk": "214f1004-2748-4bed-a38d-48fe500c41b9",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Scan for viruses",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "9a0f8eac-6a9d-4b85-8049-74954fbd6594",
                "replaces_id": None,
                "pk": "21d6d597-b876-4b3f-ab85-f97356f10507",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename with transfer UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "22c0f074-07b1-445f-9e8b-bf75ac7f0b48",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "a75ee667-3a1c-4950-9194-e07d0e6bf545",
                "replaces_id": None,
                "pk": "22ded604-6cc0-444b-b320-f96afb15d581",
                "defaultnextchainlink_id": "bd382151-afd0-41bf-bb7a-b39aef728a32",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-12-04T20:13:09+00:00"),
                "currenttask_id": "13aaa76e-41db-4bff-8519-1f9ba8ca794f",
                "replaces_id": None,
                "pk": "2483c25a-ade8-4566-a259-c6c37350d0d6",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Identify file format",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "currenttask_id": "8558d885-d6c2-4d74-af46-20da45487ae7",
                "replaces_id": None,
                "pk": "2522d680-c7d9-4d06-8b11-a28d8bd8a71f",
                "defaultnextchainlink_id": "cc16178b-b632-4624-9091-822dd802a2c6",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Clean up names",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "9dd95035-e11b-4438-a6c6-a03df302933c",
                "replaces_id": None,
                "pk": "2584b25c-8d98-44b7-beca-2b3ea2ea2505",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Assign file UUIDs and checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "25b8ddff-4074-4803-a0dc-bbb3acd48a97",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-06T01:03:43+00:00"),
                "currenttask_id": "80ebef4c-0dd1-45eb-b993-1db56a077db8",
                "replaces_id": None,
                "pk": "26bf24c9-9139-4923-bf99-aa8648b1692b",
                "defaultnextchainlink_id": "f2a019ea-0601-419c-a475-1b96a927a2fb",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Assign file UUIDs and checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "bf5a1f0c-1b3e-4196-b51f-f6d509091346",
                "replaces_id": None,
                "pk": "2714cd07-b99f-40e3-9ae8-c97281d0d429",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "dde51fc1-af7d-4923-ad6a-06e670447a2a",
                "replaces_id": None,
                "pk": "2872d007-6146-4359-b554-6e9fe7a8eca6",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "288b739d-40a1-4454-971b-812127a5e03d",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Assign file UUIDs and checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "1c7de28f-8f18-41c7-b03a-19f900d38f34",
                "replaces_id": None,
                "pk": "28a9f8a8-0006-4828-96d5-892e6e279f72",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Transcribe SIP contents",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "297e7ebd-71bb-41e9-b1b7-945b6a9f00c5",
                "replaces_id": None,
                "pk": "2900f6d8-b64c-4f2a-8f7f-bb60a57394f6",
                "defaultnextchainlink_id": "f574b2a0-6e0b-4c74-ac5b-a73ddb9593a0",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "ec503c22-1f4d-442f-b546-f90c9a9e5c86",
                "replaces_id": None,
                "pk": "29dece8e-55a4-4f2c-b4c2-365ab6376ceb",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "abeaa79e-668b-4de0-b8cb-70f8ab8056b6",
                "replaces_id": None,
                "pk": "2a62f025-83ec-4f23-adb4-11d5da7ad8c2",
                "defaultnextchainlink_id": "11033dbd-e4d4-4dd6-8bcf-48c424e222e3",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "3ad0db9a-f57d-4664-ad34-947404dddd04",
                "replaces_id": None,
                "pk": "2adf60a0-ecd7-441a-b82f-f77c6a3964c3",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Store AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "bec683fa-f006-48a4-b298-d33b3b681cb2",
                "replaces_id": None,
                "pk": "2d32235c-02d4-4686-88a6-96f4d6c7b1c3",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "currenttask_id": "8558d885-d6c2-4d74-af46-20da45487ae7",
                "replaces_id": None,
                "pk": "2dd53959-8106-457d-a385-fee57fc93aa9",
                "defaultnextchainlink_id": "83484326-7be7-4f9f-b252-94553cd42370",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "3875546f-9137-4c8f-9fcc-ed112eaa6414",
                "replaces_id": None,
                "pk": "2e7f83f9-495a-44b3-b0cf-bff66f021a4d",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Identify DSpace files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "0c1664f2-dfcb-46d9-bd9e-5b604baef788",
                "replaces_id": None,
                "pk": "2fd123ea-196f-4c9c-95c0-117aa65ed9c6",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Characterize and extract metadata",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "00041f5a-42cd-4b77-a6d4-6ef0f376a817",
                "replaces_id": None,
                "pk": "303a65f6-a16f-4a06-807b-cb3425a30201",
                "defaultnextchainlink_id": "1b1a4565-b501-407b-b40f-2f20889423f1",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Update METS.xml document",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "currenttask_id": "275b3640-68a6-4c4e-adc1-888ea3fdfba5",
                "replaces_id": None,
                "pk": "307edcde-ad10-401c-92c4-652917c993ed",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-10T22:49:49+00:00"),
                "currenttask_id": "acd5e136-11ed-46fe-bf67-dc108f115d6b",
                "replaces_id": None,
                "pk": "31abe664-745e-4fef-a669-ff41514e0083",
                "defaultnextchainlink_id": "09b85517-e5f5-415b-a950-1a60ee285242",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "135dd73d-845a-412b-b17e-23941a3d9f78",
                "replaces_id": None,
                "pk": "31fc3f66-34e9-478f-8d1b-c29cd0012360",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "64a859be-f362-45d1-b9b4-4e15091f686f",
                "replaces_id": None,
                "pk": "3229e01f-adf3-4294-85f7-4acb01b3fbcf",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Reject transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "e20ea90b-fa16-4576-8647-199ecde0d511",
                "replaces_id": None,
                "pk": "333532b9-b7c2-4478-9415-28a3056d58df",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "530b3b90-b97a-4aaf-836f-3a889ad1d7d2",
                "replaces_id": None,
                "pk": "33d7ac55-291c-43ae-bb42-f599ef428325",
                "defaultnextchainlink_id": "576f1f43-a130-4c15-abeb-c272ec458d33",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Generate METS.xml document",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "3df5643c-2556-412f-a7ac-e2df95722dae",
                "replaces_id": None,
                "pk": "3409b898-e532-49d3-98ff-a2a1f9d988fa",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Reject SIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "be4e3ee6-9be3-465f-93f0-77a4ccdfd1db",
                "replaces_id": None,
                "pk": "3467d003-1603-49e3-b085-e58aa693afed",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "f452a117-a992-4447-9774-6a8130f05b30",
                "replaces_id": None,
                "pk": "35c8763a-0430-46be-8198-9ecb23f895c8",
                "defaultnextchainlink_id": "180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve SIP creation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-04-19T22:39:27+00:00"),
                "currenttask_id": "4554c5f9-52f9-440c-bc69-0f7be3651949",
                "replaces_id": None,
                "pk": "36609513-6502-4aca-886a-6c4ae03a9f05",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Assign file UUIDs and checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "bd9769ba-4182-4dd4-ba85-cff24ea8733e",
                "replaces_id": None,
                "pk": "370aca94-65ab-4f2a-9d7d-294a62c8b7ba",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-08T02:12:00+00:00"),
                "currenttask_id": "99712faf-6cd0-48d1-9c66-35a2033057cf",
                "replaces_id": None,
                "pk": "377f8ebb-7989-4a68-9361-658079ff8138",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "90e0993d-23d4-4d0c-8b7d-73717b58f20e",
                "replaces_id": None,
                "pk": "378ae4fc-7b62-40af-b448-a1ab47ac2c0c",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "3868c8b8-977d-4162-a319-dc487de20f11",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "62ba16c8-4a3f-4199-a48e-d557a90728e2",
                "replaces_id": None,
                "pk": "38c591d4-b7ee-4bc0-b993-c592bf15d97d",
                "defaultnextchainlink_id": "1c2550f1-3fc0-45d8-8bc4-4c06d720283b",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "73ad6c9d-8ea1-4667-ae7d-229656a49237",
                "replaces_id": None,
                "pk": "39a128e3-c35d-40b7-9363-87f75091e1ff",
                "defaultnextchainlink_id": "3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "f872b932-90dd-4501-98c4-9fc5bac9d19a",
                "replaces_id": None,
                "pk": "39e58573-2dbc-4939-bce0-96b2f55dae28",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "feac0c04-3511-4e91-9403-5c569cff7bcc",
                "replaces_id": None,
                "pk": "3c526a07-c3b8-4e53-801b-7f3d0c4857a5",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "c075014f-4051-441a-b16b-3083d5c264c5",
                "replaces_id": None,
                "pk": "3e25bda6-5314-4bb4-aa1e-90900dce887d",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "39ac9ff8-d312-4033-a2c6-44219471abda",
                "replaces_id": None,
                "pk": "3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Store AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "b57b3564-e271-4226-a5f9-2c7cf1661a83",
                "replaces_id": None,
                "pk": "3f543585-fa4f-4099-9153-dd6d53572f5c",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ea463bfd-5fa2-4936-b8c3-1ce3b74303cf",
                "replaces_id": None,
                "pk": "4103a5b0-e473-4198-8ff7-aaa6fec34749",
                "defaultnextchainlink_id": "092b47db-6f77-4072-aed3-eb248ab69e9c",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "424ee8f1-6cdd-4960-8641-ed82361d3ad7",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "fbaadb5d-63f9-440c-a607-a4ebfb973a78",
                "replaces_id": None,
                "pk": "438dc1cf-9813-44b5-a0a3-58e09ae73b8a",
                "defaultnextchainlink_id": "2e7f83f9-495a-44b3-b0cf-bff66f021a4d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "102cd6b0-5d30-4e04-9b62-4e9f12d74549",
                "replaces_id": None,
                "pk": "43c72f8b-3cea-4b4c-b99d-cfdefdfcc270",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "currenttask_id": "51e31d21-3e92-4c9f-8fec-740f559285f2",
                "replaces_id": None,
                "pk": "440ef381-8fe8-4b6e-9198-270ee5653454",
                "defaultnextchainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename with transfer UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "0bb3f551-1418-4b99-8094-05a43fcd9537",
                "replaces_id": None,
                "pk": "4417b129-fab3-4503-82dd-740f8e774bff",
                "defaultnextchainlink_id": "fdfac6e5-86c0-4c81-895c-19a9edadedef",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "3c04068f-20b8-4cbc-8166-c61faacb6628",
                "replaces_id": None,
                "pk": "4430077a-92c5-4d86-b0f8-0d31bdb731fb",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "b3875772-0f3b-4b03-b602-5304ded86397",
                "replaces_id": None,
                "pk": "45063ad6-f374-4215-a2c4-ac47be4ce2cd",
                "defaultnextchainlink_id": "61af079f-46a2-48ff-9b8a-0c78ba3a456d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "45f4a7e3-87cf-4fb4-b4f9-e36ad8c853b1",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "2e3c3f0f-069e-4ca1-b71b-93f4880a39b5",
                "replaces_id": None,
                "pk": "46dcf7b1-3750-4f49-a9be-a4bf076e304f",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "a71f40ec-77b2-4f13-91b6-da3d4a67a284",
                "replaces_id": None,
                "pk": "46e19522-9a71-48f1-9ccd-09cabfba3f38",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "c310a18a-1659-45d0-845e-06eb3321512f",
                "replaces_id": None,
                "pk": "47c83e01-7556-4c13-881f-282c6d9c7d6a",
                "defaultnextchainlink_id": "4103a5b0-e473-4198-8ff7-aaa6fec34749",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "f908bcd9-2fba-48c3-b04b-459f6ad1a4de",
                "replaces_id": None,
                "pk": "47dd6ea6-1ee7-4462-8b84-3fc4c1eeeb7f",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Store AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "134a1a94-22f0-4e67-be17-23a4c7178105",
                "replaces_id": None,
                "pk": "48703fad-dc44-4c8e-8f47-933df3ef6179",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Store AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "75e00332-24a3-4076-aed1-e3dc44379227",
                "replaces_id": None,
                "pk": "49cbcc4d-067b-4cd5-b52e-faf50857b35a",
                "defaultnextchainlink_id": "2d32235c-02d4-4686-88a6-96f4d6c7b1c3",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Assign file UUIDs and checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "4b75ca30-2eaf-431b-bffa-d737c8a0bf37",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "674e21f3-1c50-4185-8e5d-70b1ed4a7f3a",
                "replaces_id": None,
                "pk": "4edfe7e4-82ff-4c0a-ba5f-29f1ee14e17a",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Generate transfer structure report",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "ede67763-2a12-4e8f-8c36-e266d3f05c6b",
                "replaces_id": None,
                "pk": "4efe00da-6ed0-45dd-89ca-421b78c4b6be",
                "defaultnextchainlink_id": "2584b25c-8d98-44b7-beca-2b3ea2ea2505",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "549181ed-febe-487a-a036-ed6fdfa10a86",
                "replaces_id": None,
                "pk": "50b67418-cb8d-434d-acc9-4a8324e7fdd2",
                "defaultnextchainlink_id": "5d780c7d-39d0-4f4a-922b-9d1b0d217bca",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "dee46f53-8afb-4aec-820e-d495bcbeaf20",
                "replaces_id": None,
                "pk": "5158c618-6160-41d6-bbbe-ddf34b5b06bc",
                "defaultnextchainlink_id": "f09847c2-ee51-429a-9478-a860477f6b8d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Assign file UUIDs and checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "e601b1e3-a957-487f-8cbe-54160070574d",
                "replaces_id": None,
                "pk": "52269473-5325-4a11-b38a-c4aafcbd8f54",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Generate AIP METS",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "8ea17652-a136-4251-b460-d50b0c7090eb",
                "replaces_id": None,
                "pk": "53e14112-21bb-46f0-aed3-4e8c2de6678f",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Add final metadata",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "1cf09019-56a1-47eb-8fe0-9bbff158892d",
                "replaces_id": None,
                "pk": "54b73077-a062-41cc-882c-4df1eba447d9",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Generate transfer structure report",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "48416179-7ae4-47cc-a0aa-f9847da08c63",
                "replaces_id": None,
                "pk": "559d9b14-05bf-4136-918a-de74a821b759",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "07f6f419-d51f-4c69-bca6-a395adecbee0",
                "replaces_id": None,
                "pk": "55de1490-f3a0-4e1e-a25b-38b75f4f05e3",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-04-19T22:39:27+00:00"),
                "currenttask_id": "9649186d-e5bd-4765-b285-3b0d8e83b105",
                "replaces_id": None,
                "pk": "561bbb52-d95c-4004-b0d3-739c0a65f406",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "547f95f6-3fcd-45e1-98b6-a8a7d9097373",
                "replaces_id": None,
                "pk": "56da7758-913a-4cd2-a815-be140ed09357",
                "defaultnextchainlink_id": "8ce130d4-3f7e-46ec-868a-505cf9033d96",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Generate transfer structure report",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "f1ebd62a-fbf3-4790-88e8-4a3abec4ba00",
                "replaces_id": None,
                "pk": "56eebd45-5600-4768-a8c2-ec0114555a3d",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "1e02e82a-2055-4f37-af3a-7dc606f9fd97",
                "replaces_id": None,
                "pk": "576f1f43-a130-4c15-abeb-c272ec458d33",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "5b7a48e1-32ed-43f9-8ffa-e374010fcf76",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "246c34b0-b785-485f-971b-0ed9f82e1ae3",
                "replaces_id": None,
                "pk": "5c0d8661-1c49-4023-8a67-4991365d70fb",
                "defaultnextchainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "108f7f4c-72f2-4ddb-910a-24f173d64fa7",
                "replaces_id": None,
                "pk": "5c459c1a-f998-404d-a0dd-808709510b72",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "5cf308fd-a6dc-4033-bda1-61689bb55ce2",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-24T00:40:06+00:00"),
                "currenttask_id": "4745d0bb-910c-4c0d-8b81-82d7bfca7819",
                "replaces_id": None,
                "pk": "5d6a103c-9a5d-4010-83a8-6f4c61eb1478",
                "defaultnextchainlink_id": "74665638-5d8f-43f3-b7c9-98c4c8889766",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "85308c8b-b299-4453-bf40-9ac61d134015",
                "replaces_id": None,
                "pk": "5d780c7d-39d0-4f4a-922b-9d1b0d217bca",
                "defaultnextchainlink_id": "ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer checksum",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "528c8fe3-265f-45dd-b5c0-1a4ac0e15954",
                "replaces_id": None,
                "pk": "5e4bd4e8-d158-4c2a-be89-51e3e9bd4a06",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Store AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "5f213529-ced4-49b0-9e30-be4e0c9b81d5",
                "defaultnextchainlink_id": "3f543585-fa4f-4099-9153-dd6d53572f5c",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "feb27f44-3575-4d17-8e00-43aa5dc5c3dc",
                "replaces_id": None,
                "pk": "5fbc344c-19c8-48be-a753-02dac987428c",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "cd53e17c-1dd1-4e78-9086-e6e013a64536",
                "replaces_id": None,
                "pk": "60b0e812-ebbe-487e-810f-56b1b6fdd819",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "9a70cc32-2b0e-4763-a168-b81485fac366",
                "replaces_id": None,
                "pk": "61a8de9c-7b25-4f0f-b218-ad4dde261eed",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Include default Transfer processingMCP.xml",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "54a05ec3-a34f-4404-96ec-36b527445da9",
                "replaces_id": None,
                "pk": "61af079f-46a2-48ff-9b8a-0c78ba3a456d",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "32b2600c-6907-4cb2-b18a-3986f0842219",
                "replaces_id": None,
                "pk": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
                "defaultnextchainlink_id": "377f8ebb-7989-4a68-9361-658079ff8138",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "6327fdf9-9673-42a8-ace5-cccad005818b",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "ce48a9f5-4513-49e2-83db-52b01234705b",
                "replaces_id": None,
                "pk": "635ba89d-0ad6-4fc9-acc3-e6069dffdcd5",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "83755035-1dfd-4e25-9031-e1178be4bb84",
                "replaces_id": None,
                "pk": "63f35161-ba76-4a43-8cfa-c38c6a2d5b2f",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve AIC",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "81f2a21b-a7a0-44e4-a2f6-9a6cf742b052",
                "replaces_id": None,
                "pk": "6404ce13-8619-48ba-b12f-aa7a034153ac",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Upload DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7058a655-82f3-455c-9245-ad8e87e77a4f",
                "replaces_id": None,
                "pk": "651236d2-d77f-4ca7-bfe9-6332e96608ff",
                "defaultnextchainlink_id": "e3efab02-1860-42dd-a46c-25601251b930",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "65240550-d745-4afe-848f-2bf5910457c9",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Assign file UUIDs and checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "450794b5-db3e-4557-8ab8-1abd77786429",
                "replaces_id": None,
                "pk": "66c9c178-2224-41c6-9c0b-dcb60ff57b1a",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "f661aae0-05bf-4f55-a2f6-ef0f157231bd",
                "replaces_id": None,
                "pk": "67a91b4b-a5af-4b54-a836-705e6cf4eeb9",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "143b4734-9c33-4f6e-9af0-2dc09cf9017a",
                "replaces_id": None,
                "pk": "67b44f8f-bc97-4cb3-b6dd-09dba3c99d30",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "6b39088b-683e-48bd-ab89-9dab47f4e9e0",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "b3b86729-470f-4301-8861-d62574966747",
                "replaces_id": None,
                "pk": "6b931965-d5f6-4611-a536-39d5901f8f70",
                "defaultnextchainlink_id": "0a6558cf-cf5f-4646-977e-7d6b4fde47e8",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Include default Transfer processingMCP.xml",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "13aaa76e-41db-4bff-8519-1f9ba8ca794f",
                "replaces_id": None,
                "pk": "6bd4d385-c490-4c42-a195-dace8697891c",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Generate transfer structure report",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2015-05-25T16:33:13+00:00"),
                "currenttask_id": "9f7029af-739d-4ec1-840d-b92d1d30f0c7",
                "replaces_id": None,
                "pk": "6eca2676-b4ed-48d9-adb0-374e1d5c6e71",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "6ee25a55-7c08-4c9a-a114-c200a37146c4",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify SIP compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "70669a5b-01e4-4ea0-ac70-10292f87da05",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Transcribe SIP contents",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "4c64875e-9f31-4596-96d9-f99bc886bb24",
                "replaces_id": None,
                "pk": "7079be6d-3a25-41e6-a481-cee5f352fe6e",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "70f41678-baa5-46e6-a71c-4b6b4d99f4a6",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "745340f5-5741-408e-be92-34c596c00209",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "235c3727-b138-4e62-9265-c8f07761a5fa",
                "replaces_id": None,
                "pk": "74665638-5d8f-43f3-b7c9-98c4c8889766",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "55f0e6fa-834c-44f1-89f3-c912e79cea7d",
                "replaces_id": None,
                "pk": "746b1f47-2dad-427b-8915-8b0cb7acccd8",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "2bfd7cef-dcf8-4587-8043-2c69c612a6e3",
                "replaces_id": None,
                "pk": "7509e7dc-1e1b-4dce-8d21-e130515fce73",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "de195451-989e-48fe-ad0c-3ff2265b3410",
                "replaces_id": None,
                "pk": "755b4177-c587-41a7-8c52-015277568302",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process metadata directory",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-02-08T22:18:49+00:00"),
                "currenttask_id": "33c0dea0-da6c-4b8f-8038-6e95844eea95",
                "replaces_id": None,
                "pk": "75fb5d67-5efa-4232-b00b-d85236de0d3f",
                "defaultnextchainlink_id": "88807d68-062e-4d1a-a2d5-2d198c88d8ca",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Add final metadata",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "77a7fa46-92b9-418e-aa88-fbedd4114c9f",
                "defaultnextchainlink_id": "7079be6d-3a25-41e6-a481-cee5f352fe6e",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "77c722ea-5a8f-48c0-ae82-c66a3fa8ca77",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process manually normalized files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "currenttask_id": "ce57ffbc-abd9-43dc-a09b-e888397488f2",
                "replaces_id": None,
                "pk": "78b7adff-861d-4450-b6dd-3fabe96a849e",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "currenttask_id": "f8d0b7df-68e8-4214-a49d-60a91ed27029",
                "replaces_id": None,
                "pk": "7a024896-c4f7-4808-a240-44c87c762bc5",
                "defaultnextchainlink_id": "2dd53959-8106-457d-a385-fee57fc93aa9",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "5c831a10-5d75-44ca-9741-06fdfc72052a",
                "replaces_id": None,
                "pk": "7a134af0-b285-4a9f-8acf-f6947b7ed072",
                "defaultnextchainlink_id": "56da7758-913a-4cd2-a815-be140ed09357",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "c3e3f03d-c104-48c3-8c64-4290459965f4",
                "replaces_id": None,
                "pk": "7b146689-1a04-4f58-ba86-3caf2b76ddbc",
                "defaultnextchainlink_id": "f3a39155-d655-4336-8227-f8c88e4b7669",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Upload DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T14:25:06+00:00"),
                "currenttask_id": "4d56a90c-8d9f-498c-8331-cf469fcb3147",
                "replaces_id": None,
                "pk": "7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1",
                "defaultnextchainlink_id": "bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Store AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "502a8bc4-88b1-41b0-8821-f8afd984036e",
                "replaces_id": None,
                "pk": "7c44c454-e3cc-43d4-abe0-885f93d693c6",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "52d646df-fd66-4157-b8aa-32786fef9481",
                "replaces_id": None,
                "pk": "7c6a0b72-f37b-4512-87f3-267644de6f80",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename with transfer UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "6ed7ec07-5df1-470b-9a2e-a934cba8af26",
                "replaces_id": None,
                "pk": "7c95b242-1ce5-4210-b7d4-fdbb6c0aa5dd",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify SIP compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "8e06349b-d4a3-420a-9a64-69553bd9a183",
                "replaces_id": None,
                "pk": "7d0616b2-afed-41a6-819a-495032e86291",
                "defaultnextchainlink_id": "f025f58c-d48c-4ba1-8904-a56d2a67b42f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "5370a0cb-da97-4983-868a-1376d7737af5",
                "replaces_id": None,
                "pk": "7d33f228-0fa8-4f4c-a66b-24f8e264c214",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed SIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "32b2600c-6907-4cb2-b18a-3986f0842219",
                "replaces_id": None,
                "pk": "7d728c39-395f-4892-8193-92f086c0546f",
                "defaultnextchainlink_id": "b2ef06b9-bca4-49da-bc5c-866d7b3c4bb1",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "f5ca3e51-35ba-4cdd-acf5-7d4fec955e76",
                "replaces_id": None,
                "pk": "7e65c627-c11d-4aad-beed-65ceb7053fe8",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename SIP directory with SIP UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "99324102-ebe8-415d-b5d8-b299ab2f4703",
                "replaces_id": None,
                "pk": "823b0d76-9f3c-410d-83ab-f3c2cdd9ab22",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed SIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-08T02:12:00+00:00"),
                "currenttask_id": "59ebdcec-eacc-4daf-978a-1b0d8652cd0c",
                "replaces_id": None,
                "pk": "828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-23T19:41:22+00:00"),
                "currenttask_id": "26ec68d5-8d33-4fe2-bc11-f06d80fb23e0",
                "replaces_id": None,
                "pk": "83484326-7be7-4f9f-b252-94553cd42370",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "032347f1-c0fb-4c6c-96ba-886ac8ac636c",
                "replaces_id": None,
                "pk": "83d5e887-6f7c-48b0-bd81-e3f00a9da772",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "5044f7ec-96f9-4bf1-8540-671e543c2411",
                "replaces_id": None,
                "pk": "87e7659c-d5de-4541-a09c-6deec966a0c0",
                "defaultnextchainlink_id": "61af079f-46a2-48ff-9b8a-0c78ba3a456d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ef024cf9-1737-4161-b48a-13b4a8abddcd",
                "replaces_id": None,
                "pk": "88807d68-062e-4d1a-a2d5-2d198c88d8ca",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-30T19:55:47+00:00"),
                "currenttask_id": "6f5d5518-1ed4-49b8-9cd5-497d112c97e4",
                "replaces_id": None,
                "pk": "888a5bdc-9928-44f0-9fb7-91bc5f1e155b",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "3ae4931e-886e-4e0a-9a85-9b047c9983ac",
                "replaces_id": None,
                "pk": "88d2120a-4d19-4b47-922f-7438be1f52a2",
                "defaultnextchainlink_id": "89071669-3bb6-4e03-90a3-3c8b20c7f6fe",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "0ae50158-a6e2-4663-a684-61d9a8384789",
                "replaces_id": None,
                "pk": "89071669-3bb6-4e03-90a3-3c8b20c7f6fe",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-24T00:40:06+00:00"),
                "currenttask_id": "fe354b27-dbb2-4454-9c1c-340d85e67b78",
                "replaces_id": None,
                "pk": "8ba83807-2832-4e41-843c-2e55ad10ea0b",
                "defaultnextchainlink_id": "5d6a103c-9a5d-4010-83a8-6f4c61eb1478",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process metadata directory",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-02-13T22:03:39+00:00"),
                "currenttask_id": "8850aeff-8553-4ff1-ab31-99b5392a458b",
                "replaces_id": None,
                "pk": "8bc92801-4308-4e3b-885b-1a89fdcd3014",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Reformat metadata files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "f0e49772-3e2b-480d-8c06-023efc670dcd",
                "replaces_id": None,
                "pk": "8c8bac29-4102-4fd2-9d0a-a3bd2e607566",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "currenttask_id": "a8489361-b731-4d4a-861d-f4da1767665f",
                "replaces_id": None,
                "pk": "8ce130d4-3f7e-46ec-868a-505cf9033d96",
                "defaultnextchainlink_id": "ef8bd3f3-22f5-4283-bfd6-d458a2d18f22",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "51e31d21-3e92-4c9f-8fec-740f559285f2",
                "replaces_id": None,
                "pk": "8ce378a5-1418-4184-bf02-328a06e1d3be",
                "defaultnextchainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "currenttask_id": "07bf7432-fd9b-456e-9d17-5b387087723a",
                "replaces_id": None,
                "pk": "8db10a7b-924f-4561-87b4-cb6078c65aab",
                "defaultnextchainlink_id": "3868c8b8-977d-4162-a319-dc487de20f11",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "8dc0284a-45f4-486e-a78d-7af3e5b8d621",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-24T00:40:07+00:00"),
                "currenttask_id": "bacb088a-66ef-4590-b855-69f21dfdf87a",
                "replaces_id": None,
                "pk": "8de9fe10-932f-4151-88b0-b50cf271e156",
                "defaultnextchainlink_id": "9e3dd445-551d-42d1-89ba-fe6dff7c6ee6",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Identify DSpace files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "81d64862-a4f6-4e3f-b32e-47268d9eb9a3",
                "replaces_id": None,
                "pk": "8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc",
                "defaultnextchainlink_id": "eb52299b-9ae6-4a1f-831e-c7eee0de829f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "8f639582-8881-4a8b-8574-d2f86dc4db3d",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "a2e93146-a3ff-4e6c-ae3d-76ce49ca5e1b",
                "replaces_id": None,
                "pk": "9071c352-aed5-444c-ac3f-b6c52dfb65ac",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process manually normalized files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "currenttask_id": "0a521e24-b376-4a9c-9cd6-ce41e187179a",
                "replaces_id": None,
                "pk": "91ca6f1f-feb5-485d-99d2-25eed195e330",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "ee00a5c7-a69c-46cf-a5e0-a9e2f18e563e",
                "replaces_id": None,
                "pk": "91dc1ab1-487e-4121-a6c5-d8441da7a422",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Upload DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "16b8cc42-68b6-4751-b497-3e3a64101bbb",
                "replaces_id": None,
                "pk": "92879a29-45bf-4f0b-ac43-e64474f0f2f9",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "c450501a-251f-4de7-acde-91c47cf62e36",
                "replaces_id": None,
                "pk": "9520386f-bb6d-4fb9-a6b6-5845ef39375f",
                "defaultnextchainlink_id": "77c722ea-5a8f-48c0-ae82-c66a3fa8ca77",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "09f73737-f7ca-4ea2-9676-d369f390e650",
                "replaces_id": None,
                "pk": "95616c10-a79f-48ca-a352-234cc91eaf08",
                "defaultnextchainlink_id": "bd382151-afd0-41bf-bb7a-b39aef728a32",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Clean up names",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "efb7bf8e-4624-4b52-bf90-e3d389099fd9",
                "replaces_id": None,
                "pk": "970b7d17-7a6b-4d51-808b-c94b78c0d97f",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "acf7bd62-1587-4bff-b640-5b34b7196386",
                "replaces_id": None,
                "pk": "998044bb-6260-452f-a742-cfb19e80125b",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-24T00:40:07+00:00"),
                "currenttask_id": "97cc7629-c580-44db-8a41-68b6b2f23be4",
                "replaces_id": None,
                "pk": "9e3dd445-551d-42d1-89ba-fe6dff7c6ee6",
                "defaultnextchainlink_id": "e219ed78-2eda-4263-8c0f-0c7f6a86c33e",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIC",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "ea463bfd-5fa2-4936-b8c3-1ce3b74303cf",
                "replaces_id": None,
                "pk": "9e810686-d747-4da1-9908-876fb89ac78e",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process manually normalized files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "currenttask_id": "ff8f70b9-e345-4163-a784-29b432b12558",
                "replaces_id": None,
                "pk": "9e9b522a-77ab-4c17-ab08-5a4256f49d59",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process manually normalized files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "currenttask_id": "c307d6bd-cb81-46a1-89f1-bb02a43e0a3a",
                "replaces_id": None,
                "pk": "a1b65fe3-9358-479b-93b9-68f2b5e71b2b",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "8b846431-5da9-4743-906d-2cdc4e777f8f",
                "replaces_id": None,
                "pk": "a2173b55-abff-4d8f-97b9-79cc2e0a64fa",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Clean up names",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "16eaacad-e180-4be1-a13c-35ab070808a7",
                "replaces_id": None,
                "pk": "a329d39b-4711-4231-b54e-b5958934dccb",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Clean up names",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "04c7e0fb-ec4e-4637-a7b7-41601d5523bd",
                "replaces_id": None,
                "pk": "a46e95fe-4a11-4d3c-9b76-c5d8ea0b094d",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Validation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "530a3999-422f-4abb-a6be-bd29cbed04a4",
                "replaces_id": None,
                "pk": "a536828c-be65-4088-80bd-eb511a0a063d",
                "defaultnextchainlink_id": "dae3c416-a8c2-4515-9081-6dbd7b265388",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7872599e-ebfc-472b-bb11-524ff728679f",
                "replaces_id": None,
                "pk": "a6e97805-a420-41af-b708-2a56de5b47a6",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "8fa944df-1baf-4f89-8106-af013b5078f4",
                "replaces_id": None,
                "pk": "a98ba456-3dcd-4f45-804c-a40220ddc6cb",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-06T00:59:43+00:00"),
                "currenttask_id": "dde8c13d-330e-458b-9d53-0937370695fa",
                "replaces_id": None,
                "pk": "aa9ba088-0b1e-4962-a9d7-79d7a0cbea2d",
                "defaultnextchainlink_id": "45063ad6-f374-4215-a2c4-ac47be4ce2cd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "8558d885-d6c2-4d74-af46-20da45487ae7",
                "replaces_id": None,
                "pk": "aaa929e4-5c35-447e-816a-033a66b9b90b",
                "defaultnextchainlink_id": "bd792750-a55b-42e9-903a-8c898bb77df1",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve SIP creation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "c409f2b0-bcb7-49ad-a048-a217811ca9b6",
                "replaces_id": None,
                "pk": "ab69c494-23b7-4f50-acff-2e00cf7bffda",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-04-05T23:08:30+00:00"),
                "currenttask_id": "f1586bd7-f550-4588-9f45-07a212db7994",
                "replaces_id": None,
                "pk": "abd6d60c-d50f-4660-a189-ac1b34fafe85",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "a0aecc16-3f78-4579-b6d4-a10df1f89a41",
                "replaces_id": None,
                "pk": "ac85a1dc-272b-46ac-bb3e-5bf3f8e56348",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Examine contents",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "7569eff6-401f-11e3-ae52-1c6f65d9668b",
                "replaces_id": None,
                "pk": "accea2bf-ba74-4a3a-bb97-614775c74459",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "d49684b1-badd-4802-b54e-06eb6b329140",
                "replaces_id": None,
                "pk": "ad011cc2-b0eb-4f51-96bb-400149a2ea11",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-12-06T17:59:43+00:00"),
                "currenttask_id": "bf9b2fb7-43bd-4c3e-9dd0-7b6f43e6cb48",
                "replaces_id": None,
                "pk": "b04e9232-2aea-49fc-9560-27349c8eba4e",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process metadata directory",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "currenttask_id": "38b99e0c-7066-49c4-82ed-d77bd7f019a1",
                "replaces_id": None,
                "pk": "b0ffcd90-eb26-4caf-8fab-58572d205f04",
                "defaultnextchainlink_id": "e4b0c713-988a-4606-82ea-4b565936d9a7",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-24T17:04:11+00:00"),
                "currenttask_id": "ce52ace2-68fc-4bfb-8444-f32ec8c01783",
                "replaces_id": None,
                "pk": "b15c0ba6-e247-4512-8b56-860fd2b6299d",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "b20ff203-1472-40db-b879-0e59d17de867",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process metadata directory",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-02-13T22:03:39+00:00"),
                "currenttask_id": "7b07859b-015e-4a17-8bbf-0d46f910d687",
                "replaces_id": None,
                "pk": "b21018df-f67d-469a-9ceb-ac92ac68654e",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process metadata directory",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "d1f630dc-1082-4ad6-95b7-af36d2e2cf46",
                "replaces_id": None,
                "pk": "b2444a6e-c626-4487-9abc-1556dd89a8ae",
                "defaultnextchainlink_id": "04493ab2-6cad-400d-8832-06941f121a96",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract attachments",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "c74dfa47-9a6d-4a12-bffe-bf610ab75db9",
                "replaces_id": None,
                "pk": "b2552a90-e674-4a40-a482-687c046407d3",
                "defaultnextchainlink_id": "21d6d597-b876-4b3f-ab85-f97356f10507",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed SIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "7d5cb258-1ce2-4510-bd04-3517abbe8fbc",
                "replaces_id": None,
                "pk": "b2ef06b9-bca4-49da-bc5c-866d7b3c4bb1",
                "defaultnextchainlink_id": "828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Store AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "fb64af31-8f8a-4fe5-a20d-27ee26c9dda2",
                "replaces_id": None,
                "pk": "b320ce81-9982-408a-9502-097d0daa48fa",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "9413e636-1209-40b0-a735-74ec785ea14a",
                "replaces_id": None,
                "pk": "b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename SIP directory with SIP UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "3f3ab7ae-766e-4405-a05a-5ee9aea5042f",
                "replaces_id": None,
                "pk": "b3d11842-0090-420a-8919-52d7039d50e6",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "b4567e89-9fea-4256-99f5-a88987026488",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process metadata directory",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "currenttask_id": "5bd51fcb-6a68-4c5f-b99e-4fc36f51c40c",
                "replaces_id": None,
                "pk": "b6b0fe37-aa26-40bd-8be8-d3acebf3ccf8",
                "defaultnextchainlink_id": "b21018df-f67d-469a-9ceb-ac92ac68654e",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Generate METS.xml",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "23ad16a5-49fe-409d-98d9-f5a8de333f81",
                "replaces_id": None,
                "pk": "b6c9de5a-4a9f-41e1-a524-360bdca39893",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Upload DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "55123c46-78c9-4b5d-ad92-2b1f3eb658af",
                "replaces_id": None,
                "pk": "b7a83da6-ed5a-47f7-a643-1e9f9f46e364",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Store AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "f09c1aa1-8a5d-49d1-ba60-2866e026eed9",
                "replaces_id": None,
                "pk": "b7cf0d9a-504f-4f4e-9930-befa817d67ff",
                "defaultnextchainlink_id": "d5a2ef60-a757-483c-a71a-ccbffe6b80da",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "d9ce0690-a8f9-40dc-a8b5-b021f578f8ff",
                "replaces_id": None,
                "pk": "b944ec7f-7f99-491f-986d-58914c9bb4fa",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "fa3e0099-b891-43f6-a4bc-390d544fa3e9",
                "replaces_id": None,
                "pk": "b963a646-0569-43c4-89a2-e3b814c5c08e",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "f1f0409b-d4f8-419a-b625-218dc1abd335",
                "replaces_id": None,
                "pk": "bb194013-597c-4e4a-8493-b36d190f8717",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Upload DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T14:25:06+00:00"),
                "currenttask_id": "bcff2873-f006-442e-9628-5eadbb8d0db7",
                "replaces_id": None,
                "pk": "bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1",
                "defaultnextchainlink_id": "e3efab02-1860-42dd-a46c-25601251b930",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "d1004e1d-f938-4c68-ba70-0e0ae508cbbe",
                "replaces_id": None,
                "pk": "bbfbecde-370c-4e26-8087-cfa751e72e6a",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "currenttask_id": "2d9483ef-7dbb-4e7e-a9c6-76ed4de52da9",
                "replaces_id": None,
                "pk": "bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0",
                "defaultnextchainlink_id": "440ef381-8fe8-4b6e-9198-270ee5653454",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Characterize and extract metadata",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "445d6579-ee40-47d0-af6c-e2f6799f450d",
                "replaces_id": None,
                "pk": "bd382151-afd0-41bf-bb7a-b39aef728a32",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "currenttask_id": "cadd5e12-82b2-43ec-813e-85cd42b2d511",
                "replaces_id": None,
                "pk": "bd792750-a55b-42e9-903a-8c898bb77df1",
                "defaultnextchainlink_id": "307edcde-ad10-401c-92c4-652917c993ed",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "currenttask_id": "d9ebceed-2cfb-462b-b130-48fecdf55bbf",
                "replaces_id": None,
                "pk": "bda96b35-48c7-44fc-9c9e-d7c5a05016c1",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "ef0bb0cf-28d5-4687-a13d-2377341371b5",
                "replaces_id": None,
                "pk": "bdce640d-6e94-49fe-9300-3192a7e5edac",
                "defaultnextchainlink_id": "7d33f228-0fa8-4f4c-a66b-24f8e264c214",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename SIP directory with SIP UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "fa2307df-e42a-4553-aaf5-b08879b0cbf4",
                "replaces_id": None,
                "pk": "bdfecadc-8219-4109-885c-cfb9ef53ebc3",
                "defaultnextchainlink_id": "823b0d76-9f3c-410d-83ab-f3c2cdd9ab22",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "c103b2fb-9a6b-4b68-8112-b70597a6cd14",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "2d0b36bb-5c82-4ee5-b54c-f3e146ce370b",
                "replaces_id": None,
                "pk": "c2e6600d-cd26-42ed-bed5-95d41c06e37b",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Identify file format",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "7a96f085-924b-483e-bc63-440323bce587",
                "replaces_id": None,
                "pk": "c3269a0a-91db-44e8-96d0-9c748cf80177",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Clean up names",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "c379e58b-d458-46d6-a9ab-7493f685a388",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "57bd2747-181e-4f06-b969-dc012c592982",
                "replaces_id": None,
                "pk": "c5ecb5a9-d697-4188-844f-9a756d8734fa",
                "defaultnextchainlink_id": "bdce640d-6e94-49fe-9300-3192a7e5edac",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "6405c283-9eed-410d-92b1-ce7d938ef080",
                "replaces_id": None,
                "pk": "c77fee8c-7c4e-4871-a72e-94d499994869",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Clean up names",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "da756a4e-9d8b-4992-a219-2a7fd1edf2bb",
                "replaces_id": None,
                "pk": "c8f7bf7b-d903-42ec-bfdf-74d357ac4230",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "currenttask_id": "6a930177-66db-49d3-b95d-10c28ee47562",
                "replaces_id": None,
                "pk": "cb48ef2a-3394-4936-af1f-557b39620efa",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "58a83299-c854-49bb-9b16-bf97813edd8e",
                "replaces_id": None,
                "pk": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "a68d7873-86cf-42d3-a95e-68b62f92f0f9",
                "replaces_id": None,
                "pk": "cc16178b-b632-4624-9091-822dd802a2c6",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Generate AIP METS",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "c52736fa-2bc5-4142-a111-8b13751ed067",
                "replaces_id": None,
                "pk": "ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0",
                "defaultnextchainlink_id": "f1e286f9-4ec7-4e19-820c-dae7b8ea7d09",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "cddde867-4cf9-4248-ac31-f7052fae053f",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "851d679e-44db-485a-9b0e-2dfbdf80c791",
                "replaces_id": None,
                "pk": "cf71e6ff-7740-4bdb-a6a9-f392d678c6e1",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "757b5f8b-0fdf-4c5c-9cff-569d63a2d209",
                "replaces_id": None,
                "pk": "d0c463c2-da4c-4a70-accb-c4ce96ac5194",
                "defaultnextchainlink_id": "2e7f83f9-495a-44b3-b0cf-bff66f021a4d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Identify DSpace files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "e6591da1-abfa-4bf2-abeb-cc0791ba5284",
                "replaces_id": None,
                "pk": "d0dfbd93-d2d0-44db-9945-94fd8de8a1d4",
                "defaultnextchainlink_id": "8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "92a7b76c-7c5c-41b3-8657-ba4cdd9a8176",
                "replaces_id": None,
                "pk": "d1018160-aaab-4d92-adce-d518880d7c7d",
                "defaultnextchainlink_id": "f025f58c-d48c-4ba1-8904-a56d2a67b42f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Identify file format",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "currenttask_id": "38cea9c4-d75c-48f9-ba88-8052e9d3aa61",
                "replaces_id": None,
                "pk": "d1b27e9e-73c8-4954-832c-36bd1e00c802",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "currenttask_id": "6405c283-9eed-410d-92b1-ce7d938ef080",
                "replaces_id": None,
                "pk": "d2035da2-dfe1-4a56-8524-84d5732fd3a3",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Complete transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "39ac9ff8-d312-4033-a2c6-44219471abda",
                "replaces_id": None,
                "pk": "d27fd07e-d3ed-4767-96a5-44a2251c6d0a",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIC",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "f89b9e0f-8789-4292-b5d0-4a330c0205e1",
                "replaces_id": None,
                "pk": "d29105f0-161d-449d-9c34-5a5ea3263f8e",
                "defaultnextchainlink_id": "142d0a36-2b88-4b98-8a33-d809f667ecef",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename with transfer UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "d3c75c96-f8c7-4674-af46-5bcce7b05f87",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-04-05T23:08:30+00:00"),
                "currenttask_id": "d6a0dec1-63e7-4c7c-b4c0-e68f0afcedd3",
                "replaces_id": None,
                "pk": "d46f6af8-bc4e-4369-a808-c0fedb439fef",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "bafe0ba3-420a-44f2-bb15-7509ef5c498c",
                "replaces_id": None,
                "pk": "d55b42c8-c7c5-4a40-b626-d248d2bd883f",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Store AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "525db1a2-d494-4764-a900-7ff89d67c384",
                "replaces_id": None,
                "pk": "d5a2ef60-a757-483c-a71a-ccbffe6b80da",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Scan for viruses",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "d7e6404a-a186-4806-a130-7e6d27179a15",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename with transfer UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "966f5720-3081-4697-9691-c19b86ffa569",
                "replaces_id": None,
                "pk": "da2d650e-8ce3-4b9a-ac97-8ca4744b019f",
                "defaultnextchainlink_id": "4417b129-fab3-4503-82dd-740f8e774bff",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Examine contents",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "08fc82e7-bc15-4608-8171-50475e8071e2",
                "replaces_id": None,
                "pk": "dae3c416-a8c2-4515-9081-6dbd7b265388",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify SIP compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "db6d3830-9eb4-4996-8f3a-18f4f998e07f",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "24fb04f6-95c1-4244-8f3d-65061418b188",
                "replaces_id": None,
                "pk": "db9177f5-41d2-4894-be1a-a7547ed6b63a",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Complete transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "81304470-37ef-4abb-99d9-ca075a9f440e",
                "replaces_id": None,
                "pk": "db99ab43-04d7-44ab-89ec-e09d7bbdc39d",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "d7a2bfbe-3f4d-45f7-87c6-f5c3c98961cd",
                "replaces_id": None,
                "pk": "dba3028d-2029-4a87-9992-f6335d890528",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Assign file UUIDs and checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "71d4f810-8fb6-45f7-9da2-f2dc07217076",
                "replaces_id": None,
                "pk": "dc144ff4-ad74-4a6e-ac15-b0beedcaf662",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process metadata directory",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "currenttask_id": "dc2994f2-6de6-4c46-81f7-54676c5054aa",
                "replaces_id": None,
                "pk": "dc9d4991-aefa-4d7e-b7b5-84e3c4336e74",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Assign file UUIDs and checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "ddc8b2ef-a7ba-4713-9425-ed18a1fa720b",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T07:25:06+00:00"),
                "currenttask_id": "2002fd7c-e238-4cca-a393-3c1c63a04915",
                "replaces_id": None,
                "pk": "de909a42-c5b5-46e1-9985-c031b50e9d30",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "a4a4679f-72b8-48da-a202-e0a25fbc41bf",
                "replaces_id": None,
                "pk": "dec97e3c-5598-4b99-b26e-f87a435a6b7f",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Include default SIP processingMCP.xml",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "f89b9e0f-8789-4292-b5d0-4a330c0205e1",
                "replaces_id": None,
                "pk": "df02cac1-f582-4a86-b7cf-da98a58e279e",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "accc69f9-5b99-4565-92b5-114c7727d9e9",
                "replaces_id": None,
                "pk": "df1cc271-ff77-4f86-b4f3-afc01856db1f",
                "defaultnextchainlink_id": "cf71e6ff-7740-4bdb-a6a9-f392d678c6e1",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Generate METS.xml document",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "4b7e128d-193d-4b7a-8c46-b37842bac047",
                "replaces_id": None,
                "pk": "df957421-6bba-4ad7-8580-0fc04a54efd4",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "ef0bb0cf-28d5-4687-a13d-2377341371b5",
                "replaces_id": None,
                "pk": "e19f8eed-faf9-4e04-bf1f-e9418f2b2b11",
                "defaultnextchainlink_id": "22ded604-6cc0-444b-b320-f96afb15d581",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "63866950-cb04-4fe2-9b1d-9d5f1d22fc86",
                "replaces_id": None,
                "pk": "e219ed78-2eda-4263-8c0f-0c7f6a86c33e",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "cac32b11-820c-4d17-8c7f-4e71fc0be68a",
                "replaces_id": None,
                "pk": "e2c0dae9-3295-4a98-b3ff-664ab2dc0cda",
                "defaultnextchainlink_id": "7e65c627-c11d-4aad-beed-65ceb7053fe8",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-12-04T00:47:58+00:00"),
                "currenttask_id": "a73b3690-ac75-4030-bb03-0c07576b649b",
                "replaces_id": None,
                "pk": "e399bd60-202d-42df-9760-bd14497b5034",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename SIP directory with SIP UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "d61bb906-feff-4d6f-9e6c-a3f077f46b21",
                "replaces_id": None,
                "pk": "e3a6d178-fa65-4086-a4aa-6533e8f12d51",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Upload DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "e485f0f4-7d44-45c6-a0d2-bba4b2abd0d0",
                "replaces_id": None,
                "pk": "e3efab02-1860-42dd-a46c-25601251b930",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process metadata directory",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "currenttask_id": "ba0d0244-1526-4a99-ab65-43bfcd704e70",
                "replaces_id": None,
                "pk": "e4b0c713-988a-4606-82ea-4b565936d9a7",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "currenttask_id": "09fae382-37ac-45bb-9b53-d1608a44742c",
                "replaces_id": None,
                "pk": "e4e19c32-16cc-4a7f-a64d-a1f180bdb164",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "currenttask_id": "feac0c04-3511-4e91-9403-5c569cff7bcc",
                "replaces_id": None,
                "pk": "e64d26f4-3330-4d0b-bffe-81edb0dbe93d",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process manually normalized files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "currenttask_id": "ded09ddd-2deb-4d62-bfe3-84703f60c522",
                "replaces_id": None,
                "pk": "e76aec15-5dfa-4b14-9405-735863e3a6fa",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Upload DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "85ce72dd-627a-4d0d-b118-fdaedf8ed8e6",
                "replaces_id": None,
                "pk": "e85a01f1-4061-4049-8922-5694b25c23a2",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "currenttask_id": "7fd4e564-bed2-42c7-a186-7ae615381516",
                "replaces_id": None,
                "pk": "e950cd98-574b-4e57-9ef8-c2231e1ce451",
                "defaultnextchainlink_id": "5c0d8661-1c49-4023-8a67-4991365d70fb",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "dde8c13d-330e-458b-9d53-0937370695fa",
                "replaces_id": None,
                "pk": "ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c",
                "defaultnextchainlink_id": "438dc1cf-9813-44b5-a0a3-58e09ae73b8a",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Complete transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "aa2e26b3-539e-4071-b54c-bcb89650d2d2",
                "replaces_id": None,
                "pk": "eb52299b-9ae6-4a1f-831e-c7eee0de829f",
                "defaultnextchainlink_id": "db99ab43-04d7-44ab-89ec-e09d7bbdc39d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Upload DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "21292501-0c12-4376-8fb1-413286060dc2",
                "replaces_id": None,
                "pk": "ed5d8475-3793-4fb0-a8df-94bd79b26a4c",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process metadata directory",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "c1bd4921-c446-4ff9-bb34-fcd155b8132a",
                "replaces_id": None,
                "pk": "ee438694-815f-4b74-97e1-8e7dde2cc6d5",
                "defaultnextchainlink_id": "b0ffcd90-eb26-4caf-8fab-58572d205f04",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Add final metadata",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "9f0388ae-155c-4cbf-9e15-525ff03e025f",
                "replaces_id": None,
                "pk": "eeb23509-57e2-4529-8857-9d62525db048",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename with transfer UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "4b07d97a-04c1-45ce-9d9b-36bc29054223",
                "replaces_id": None,
                "pk": "ef6332ee-a890-4e1b-88de-986efc4269fb",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "2d9483ef-7dbb-4e7e-a9c6-76ed4de52da9",
                "replaces_id": None,
                "pk": "ef8bd3f3-22f5-4283-bfd6-d458a2d18f22",
                "defaultnextchainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIC",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "74146fe4-365d-4f14-9aae-21eafa7d8393",
                "replaces_id": None,
                "pk": "efd15406-fd6c-425b-8772-d460e1e79009",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Failed compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "e18e0c3a-dffb-42d2-9bfa-ea6c61328e28",
                "replaces_id": None,
                "pk": "f025f58c-d48c-4ba1-8904-a56d2a67b42f",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "f052432c-d4e7-4379-8d86-f2a08f0ae509",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Identify file format",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "currenttask_id": "97545cb5-3397-4934-9bc5-143b774e4fa7",
                "replaces_id": None,
                "pk": "f09847c2-ee51-429a-9478-a860477f6b8d",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "b5970cbb-1af7-4f8c-b41d-a0febd482da4",
                "replaces_id": None,
                "pk": "f0f64c7e-30fa-47c1-9877-43955680c0d0",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Upload DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "d7f13903-55a0-4a1c-87fa-9b75b14dccb4",
                "replaces_id": None,
                "pk": "f12ece2c-fb7e-44de-ba87-7e3c5b6feb74",
                "defaultnextchainlink_id": "e3efab02-1860-42dd-a46c-25601251b930",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Extract packages",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "86a832aa-bd37-44e2-ba02-418fb82e34f1",
                "replaces_id": None,
                "pk": "f19926dd-8fb5-4c79-8ade-c83f61f55b40",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer checksums",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "57ef1f9f-3a1a-4cdc-90fd-39b024524618",
                "replaces_id": None,
                "pk": "f1bfce12-b637-443f-85f8-b6450ca01a13",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-02-13T22:03:37+00:00"),
                "currenttask_id": "a493f430-d905-4f68-a742-f4393a43e694",
                "replaces_id": None,
                "pk": "f1e286f9-4ec7-4e19-820c-dae7b8ea7d09",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "currenttask_id": "06b45b5d-d06b-49a8-8f15-e9458fbae842",
                "replaces_id": None,
                "pk": "f2a019ea-0601-419c-a475-1b96a927a2fb",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Reject DIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ea331cfb-d4f2-40c0-98b5-34d21ee6ad3e",
                "replaces_id": None,
                "pk": "f2a1faaf-7322-4d9c-aff9-f809e7a6a6a2",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Reject AIP",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "2d8f4aa1-76ad-4c88-af81-f7f494780628",
                "replaces_id": None,
                "pk": "f2e784a0-356b-4b92-9a5a-11887aa3cf48",
                "defaultnextchainlink_id": "0d7f5dc2-b9af-43bf-b698-10fdcc5b014d",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Create SIP from Transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "e5789749-00df-4b6c-af12-47eeabc8926a",
                "replaces_id": None,
                "pk": "f378ec85-adcc-4ee6-ada2-bc90cfe20efb",
                "defaultnextchainlink_id": "39a128e3-c35d-40b7-9363-87f75091e1ff",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "41e84764-e3a0-4aac-94e9-adbe996b087f",
                "replaces_id": None,
                "pk": "f3a39155-d655-4336-8227-f8c88e4b7669",
                "defaultnextchainlink_id": "e950cd98-574b-4e57-9ef8-c2231e1ce451",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "bf0835be-4c76-4508-a5a7-cdc4c9dae217",
                "replaces_id": None,
                "pk": "f3a58cbb-20a8-4c6d-9ae4-1a5f02c1a28e",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Remove cache files",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ef0bb0cf-28d5-4687-a13d-2377341371b5",
                "replaces_id": None,
                "pk": "f3be1ee1-8881-465d-80a6-a6f093d40ec2",
                "defaultnextchainlink_id": "c379e58b-d458-46d6-a9ab-7493f685a388",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Process submission documentation",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "b24525cd-e68d-4afd-b6ec-46192bbc117b",
                "replaces_id": None,
                "pk": "f574b2a0-6e0b-4c74-ac5b-a73ddb9593a0",
                "defaultnextchainlink_id": "47dd6ea6-1ee7-4462-8b84-3fc4c1eeeb7f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Approve transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "df1c53e4-1b69-441e-bdc9-6d08c3b47c9b",
                "replaces_id": None,
                "pk": "f6bcc82a-d629-4a78-8643-bf6e3cb39fe6",
                "defaultnextchainlink_id": None,
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Normalize",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "21f8f2b6-d285-490a-9276-bfa87a0a4fb9",
                "replaces_id": None,
                "pk": "f6fdd1a7-f0c5-4631-b5d3-19421155bd7a",
                "defaultnextchainlink_id": "db9177f5-41d2-4894-be1a-a7547ed6b63a",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "TRIM transfer",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "f7488721-c936-42af-a767-2f0b39564a86",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Include default Transfer processingMCP.xml",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "df51d25b-6a63-4e7a-b164-77b929dd2f31",
                "replaces_id": None,
                "pk": "f8319d49-f1e3-45dd-a404-66165c59dec7",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
                "replaces_id": None,
                "pk": "f8be53cd-6ca2-4770-8619-8a8101a809b9",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Prepare AIC",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "f8cb20e6-27aa-44f6-b5a1-dd53b5fc71f6",
                "defaultnextchainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Verify transfer compliance",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
                "replaces_id": None,
                "pk": "f95a3ac5-47bc-4df9-a49c-d47abd1e05f3",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Quarantine",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "93e01ed2-8d69-4a56-b686-3cf507931885",
                "replaces_id": None,
                "pk": "fbc3857b-bb02-425b-89ce-2d6a39eaa542",
                "defaultnextchainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
            }
            MicroServiceChainLink.objects.create(**props)
            props = {
                "microservicegroup": "Rename with transfer UUID",
                "defaultexitmessage": "Failed",
                "reloadfilelist": True,
                "lastmodified": parse_date("2012-10-02T00:25:06+00:00"),
                "currenttask_id": "a3c27d23-dbdf-47af-bf66-4238aa1a508f",
                "replaces_id": None,
                "pk": "fdfac6e5-86c0-4c81-895c-19a9edadedef",
                "defaultnextchainlink_id": "7c95b242-1ce5-4210-b7d4-fdbb6c0aa5dd",
            }
            MicroServiceChainLink.objects.create(**props)

        with suppress_autotime(MicroServiceChainLinkExitCode, ["lastmodified"]):
            props = {
                "microservicechainlink_id": "307edcde-ad10-401c-92c4-652917c993ed",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replaces_id": None,
                "pk": None,
                "exitcode": 0,
                "nextmicroservicechainlink_id": "303a65f6-a16f-4a06-807b-cb3425a30201",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8ce130d4-3f7e-46ec-868a-505cf9033d96",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "00c7c131-5849-4bd6-a245-3edae7448bff",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "ef8bd3f3-22f5-4283-bfd6-d458a2d18f22",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "651236d2-d77f-4ca7-bfe9-6332e96608ff",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "01dd8a04-d56f-4cdb-a24e-038804208660",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e3efab02-1860-42dd-a46c-25601251b930",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "25b8ddff-4074-4803-a0dc-bbb3acd48a97",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "021d0483-272c-43a2-9854-f4998913f5d1",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "dc144ff4-ad74-4a6e-ac15-b0beedcaf662",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7c6a0b72-f37b-4512-87f3-267644de6f80",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "023547cb-a1a2-40d0-b21f-9527117593a0",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "df957421-6bba-4ad7-8580-0fc04a54efd4",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "abd6d60c-d50f-4660-a189-ac1b34fafe85",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-04-05T23:08:30+00:00"),
                "replaces_id": None,
                "pk": "029e7f42-4c35-4df0-b081-bd623fc6d6a7",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "561bbb52-d95c-4004-b0d3-739c0a65f406",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d46f6af8-bc4e-4369-a808-c0fedb439fef",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-04-05T23:08:30+00:00"),
                "replaces_id": None,
                "pk": "042bda05-ab8b-4ad2-b281-e0c2a9490f15",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f3a39155-d655-4336-8227-f8c88e4b7669",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "04412437-d888-4802-9a78-6de4c00a0dfd",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e950cd98-574b-4e57-9ef8-c2231e1ce451",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "48703fad-dc44-4c8e-8f47-933df3ef6179",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "0783a1ab-f70e-437b-8bec-cd1f2135ba2a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b7cf0d9a-504f-4f4e-9930-befa817d67ff",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "a329d39b-4711-4231-b54e-b5958934dccb",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "07aea7e1-5132-4da2-b400-21d812eeda61",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d1b27e9e-73c8-4954-832c-36bd1e00c802",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "10c40e41-fb10-48b5-9d01-336cd958afe8",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "replaces_id": None,
                "pk": "082b1079-debf-4f31-83d1-9fd4d26e8868",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "91ca6f1f-feb5-485d-99d2-25eed195e330",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f8be53cd-6ca2-4770-8619-8a8101a809b9",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "086f8a6d-ba46-4857-aaae-0fe28854231a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "5158c618-6160-41d6-bbbe-ddf34b5b06bc",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2fd123ea-196f-4c9c-95c0-117aa65ed9c6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "0a871be4-26fe-4b44-826b-65440e57595d",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d0dfbd93-d2d0-44db-9945-94fd8de8a1d4",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "20129b22-8f28-429b-a3f2-0648090fa305",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-06T18:58:24+00:00"),
                "replaces_id": None,
                "pk": "0ab37975-f67f-4a06-b973-8cb841b6015e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e64d26f4-3330-4d0b-bffe-81edb0dbe93d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "47c83e01-7556-4c13-881f-282c6d9c7d6a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "0b110f26-934c-4a2d-8857-88467983c510",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "4103a5b0-e473-4198-8ff7-aaa6fec34749",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "9e810686-d747-4da1-9908-876fb89ac78e",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "0b689082-e35b-4bc5-b2da-6773398ea6a7",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "53e14112-21bb-46f0-aed3-4e8c2de6678f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "746b1f47-2dad-427b-8915-8b0cb7acccd8",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "0bc58fa0-5d3c-4b86-9c1c-bb2a1ee18b0e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "7c44c454-e3cc-43d4-abe0-885f93d693c6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e19f8eed-faf9-4e04-bf1f-e9418f2b2b11",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "0ef15153-0d41-4b93-bdb3-4158cec405a3",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "22ded604-6cc0-444b-b320-f96afb15d581",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f2e784a0-356b-4b92-9a5a-11887aa3cf48",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "0f4bcf43-0aaf-4901-a860-bd68a5567709",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "0d7f5dc2-b9af-43bf-b698-10fdcc5b014d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "1401c4d0-fb6f-42ef-94d3-c884c25800b2",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replaces_id": None,
                "pk": "11c406a3-cc0c-4918-9aec-75cf77dbf3f4",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "43c72f8b-3cea-4b4c-b99d-cfdefdfcc270",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "333532b9-b7c2-4478-9415-28a3056d58df",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "1238736d-5b0c-4298-b8b7-d48baf69428e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f378ec85-adcc-4ee6-ada2-bc90cfe20efb",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "12fb389b-06c4-43d4-b647-9727c410088f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "39a128e3-c35d-40b7-9363-87f75091e1ff",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "52269473-5325-4a11-b38a-c4aafcbd8f54",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "1462359e-72c8-467f-b08a-02e4e3dfede1",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "28a9f8a8-0006-4828-96d5-892e6e279f72",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "78b7adff-861d-4450-b6dd-3fabe96a849e",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "replaces_id": None,
                "pk": "14680e13-e9b0-4c3a-86c0-44cb0100eb21",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "54b73077-a062-41cc-882c-4df1eba447d9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b2444a6e-c626-4487-9abc-1556dd89a8ae",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "165579c2-15c5-474b-afc2-16e1cae5d886",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "04493ab2-6cad-400d-8832-06941f121a96",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "01c651cb-c174-4ba4-b985-1d87a44d6754",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "1667d4a5-65b5-4c4b-a2bd-c273c0bf913a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d55b42c8-c7c5-4a40-b626-d248d2bd883f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "70669a5b-01e4-4ea0-ac70-10292f87da05",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "170d410a-5813-43a3-8706-a25a2f6e1d22",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "208d441b-6938-44f9-b54a-bd73f05bc764",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7d0616b2-afed-41a6-819a-495032e86291",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "18080f7f-e6aa-4448-bc6c-c928ff2629cb",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d1018160-aaab-4d92-adce-d518880d7c7d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "4edfe7e4-82ff-4c0a-ba5f-29f1ee14e17a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "18db3a8a-ee5f-47c2-b5a7-7d223c3023c0",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "2a62f025-83ec-4f23-adb4-11d5da7ad8c2",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d29105f0-161d-449d-9c34-5a5ea3263f8e",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "1977601d-0a2d-4ccc-9aa6-571d4b6b0804",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "142d0a36-2b88-4b98-8a33-d809f667ecef",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b320ce81-9982-408a-9502-097d0daa48fa",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "1c3c10d5-83cc-4b0a-9e90-a420f467432f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "5f213529-ced4-49b0-9e30-be4e0c9b81d5",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5c0d8661-1c49-4023-8a67-4991365d70fb",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "1c6d4666-822e-4d31-870b-9aa8730fb7d8",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0c96c798-9ace-4c05-b3cf-243cdad796b7",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-11-20T21:29:24+00:00"),
                "replaces_id": None,
                "pk": "1c9942e6-3b32-479e-956c-6d287d7f246f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "25b8ddff-4074-4803-a0dc-bbb3acd48a97",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "45063ad6-f374-4215-a2c4-ac47be4ce2cd",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "1cd00b46-8bb1-4179-8ace-ad09081731b4",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "87e7659c-d5de-4541-a09c-6deec966a0c0",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0e06d968-4b5b-4084-aab4-053a2a8d1679",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "1cfaebb6-10ad-458f-a14d-4f035ee3a918",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "38c591d4-b7ee-4bc0-b993-c592bf15d97d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2522d680-c7d9-4d06-8b11-a28d8bd8a71f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "replaces_id": None,
                "pk": "1f877d65-66c5-49da-bf51-2f1757b59c90",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "cc16178b-b632-4624-9091-822dd802a2c6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0e379b19-771e-4d90-a7e5-1583e4893c56",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "2017d80c-b36e-4cc5-9851-a2de64c22220",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1c2550f1-3fc0-45d8-8bc4-4c06d720283b",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "95616c10-a79f-48ca-a352-234cc91eaf08",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "21a92e57-bc78-4c62-872d-fb166294132a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "01b30826-bfc4-4e07-8ca2-4263debad642",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "39e58573-2dbc-4939-bce0-96b2f55dae28",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "22da2170-54a7-43a7-8573-5a7b998722fb",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7079be6d-3a25-41e6-a481-cee5f352fe6e",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "22ebafb1-3ec3-406a-939d-4eb9f3b8bbd1",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "2900f6d8-b64c-4f2a-8f7f-bb60a57394f6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5f213529-ced4-49b0-9e30-be4e0c9b81d5",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "2484fb84-887f-4546-ae06-5ad7c444af36",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3f543585-fa4f-4099-9153-dd6d53572f5c",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0a63befa-327d-4655-a021-341b639ee9ed",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replaces_id": None,
                "pk": "264fdc03-9102-4eb6-b671-09e48b136d27",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "0915f727-0bc3-47c8-b9b2-25dc2ecef2bb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "561bbb52-d95c-4004-b0d3-739c0a65f406",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-04-19T22:39:27+00:00"),
                "replaces_id": None,
                "pk": "27333f0b-7463-4533-8129-9f9cd88ad0c0",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d46f6af8-bc4e-4369-a808-c0fedb439fef",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "53e14112-21bb-46f0-aed3-4e8c2de6678f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "27e94795-ae8e-4e7d-942f-346024167c76",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3e25bda6-5314-4bb4-aa1e-90900dce887d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "36609513-6502-4aca-886a-6c4ae03a9f05",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-04-19T22:39:27+00:00"),
                "replaces_id": None,
                "pk": "27fb34b1-fe92-44dc-b5db-df52b60947e3",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "db6d3830-9eb4-4996-8f3a-18f4f998e07f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "002716a1-ae29-4f36-98ab-0d97192669c4",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:34+00:00"),
                "replaces_id": None,
                "pk": "2858403b-895f-4ea3-b7b7-388de75fbb39",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "291fe250-1fa9-4386-a555-375d0333c225",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "eb52299b-9ae6-4a1f-831e-c7eee0de829f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e3a6d178-fa65-4086-a4aa-6533e8f12d51",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "2a73a50f-86d8-40d0-8f49-64bac6b561ea",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "df02cac1-f582-4a86-b7cf-da98a58e279e",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "173d310c-8e40-4669-9a69-6d4c8ffd0396",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "2b1224e4-8c2a-4043-9d77-f0be8e4cde70",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "4edfe7e4-82ff-4c0a-ba5f-29f1ee14e17a",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b944ec7f-7f99-491f-986d-58914c9bb4fa",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "2b3f01ca-7101-4801-96a9-ede85dba319c",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "307edcde-ad10-401c-92c4-652917c993ed",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "01b30826-bfc4-4e07-8ca2-4263debad642",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "2c4004db-5816-4bd2-b37c-a89dee2c4fe7",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e19f8eed-faf9-4e04-bf1f-e9418f2b2b11",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "3229e01f-adf3-4294-85f7-4acb01b3fbcf",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "2d71c993-c2dc-4f9c-b8ea-6bc1a3fdbbe1",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "154dd501-a344-45a9-97e3-b30093da35f5",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b6c9de5a-4a9f-41e1-a524-360bdca39893",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "2f9305b2-30a5-4193-99c9-5e27251830b9",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "a6e97805-a420-41af-b708-2a56de5b47a6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2adf60a0-ecd7-441a-b82f-f77c6a3964c3",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "2fc642bf-1950-46de-a45c-93aa3bcd78f2",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "a6e97805-a420-41af-b708-2a56de5b47a6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "30ebe1b6-d263-4322-805f-f66ae0e8d535",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "39e58573-2dbc-4939-bce0-96b2f55dae28",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "6eca2676-b4ed-48d9-adb0-374e1d5c6e71",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2015-05-25T16:33:13+00:00"),
                "replaces_id": None,
                "pk": "310746b8-3580-40b7-a9ff-0730c8466fbb",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "56eebd45-5600-4768-a8c2-ec0114555a3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "823b0d76-9f3c-410d-83ab-f3c2cdd9ab22",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "32cae09e-0262-46b8-ba76-eb6cf6be1272",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e3a6d178-fa65-4086-a4aa-6533e8f12d51",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "214f1004-2748-4bed-a38d-48fe500c41b9",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-12T21:25:31+00:00"),
                "replaces_id": None,
                "pk": "32d6ea79-0e00-4103-8d39-ddbaaafe0c3e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "0fc3c795-dc68-4aa0-86fc-cbd6af3302fa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ee438694-815f-4b74-97e1-8e7dde2cc6d5",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "340da49e-d01f-4870-a8c4-ee8a3c827a0f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b0ffcd90-eb26-4caf-8fab-58572d205f04",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "22c0f074-07b1-445f-9e8b-bf75ac7f0b48",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "341c6bfe-7e42-40e7-a995-5af4590dea3b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d3c75c96-f8c7-4674-af46-5bcce7b05f87",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "c5ecb5a9-d697-4188-844f-9a756d8734fa",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "345fc8d9-f44d-41d7-a439-57067cc04c10",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "bdce640d-6e94-49fe-9300-3192a7e5edac",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "03ee1136-f6ad-4184-8dcb-34872f843e14",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "350f74af-d7f5-4b08-b99e-902aff95e3da",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "c379e58b-d458-46d6-a9ab-7493f685a388",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "357a0bff-fe7a-40e1-85a7-bbc17232bf2a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "a46e95fe-4a11-4d3c-9b76-c5d8ea0b094d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "cddde867-4cf9-4248-ac31-f7052fae053f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "35d72d20-e271-4874-881f-a920cfa1c5e2",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "54b73077-a062-41cc-882c-4df1eba447d9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f3be1ee1-8881-465d-80a6-a6f093d40ec2",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "36167520-cb63-4137-a4c8-a208f0d08e17",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "c379e58b-d458-46d6-a9ab-7493f685a388",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b4567e89-9fea-4256-99f5-a88987026488",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "3a3bd3d6-a9a0-4155-b361-3dceb876c99d",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "045c43ae-d6cf-44f7-97d6-c8a602748565",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bd792750-a55b-42e9-903a-8c898bb77df1",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replaces_id": None,
                "pk": "3ba57fba-c1c2-4898-a5ae-9052dc5dd018",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "307edcde-ad10-401c-92c4-652917c993ed",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5158c618-6160-41d6-bbbe-ddf34b5b06bc",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "3e7aba06-c98a-4c12-bcad-e4e849ecb14c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f09847c2-ee51-429a-9478-a860477f6b8d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d27fd07e-d3ed-4767-96a5-44a2251c6d0a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "3f0bcb8d-3c64-4b2d-ac2d-596a52735c34",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "045c43ae-d6cf-44f7-97d6-c8a602748565",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "3f70336e-c50e-44d7-875d-d099d0dae373",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "50b67418-cb8d-434d-acc9-4a8324e7fdd2",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "31abe664-745e-4fef-a669-ff41514e0083",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-10T22:49:49+00:00"),
                "replaces_id": None,
                "pk": "40733530-5ad8-40ac-b5d4-8f56af04c264",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "09b85517-e5f5-415b-a950-1a60ee285242",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b3d11842-0090-420a-8919-52d7039d50e6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "42353ec8-76cb-477f-841c-4adfc8432d78",
                "exitcode": 179,
                "nextmicroservicechainlink_id": "bdfecadc-8219-4109-885c-cfb9ef53ebc3",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b04e9232-2aea-49fc-9560-27349c8eba4e",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-06T17:43:25+00:00"),
                "replaces_id": None,
                "pk": "4322b48f-e7a9-4a9f-a8c0-bf7aac4b9289",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "a536828c-be65-4088-80bd-eb511a0a063d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "434066e6-8205-4832-a71f-cc9cd8b539d2",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "dae3c416-a8c2-4515-9081-6dbd7b265388",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ef8bd3f3-22f5-4283-bfd6-d458a2d18f22",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "460aae60-19df-4388-841b-d9d26dd5b3a0",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8ce130d4-3f7e-46ec-868a-505cf9033d96",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653d10a-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "ef8bd3f3-22f5-4283-bfd6-d458a2d18f22",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5c0d8661-1c49-4023-8a67-4991365d70fb",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653d280-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ef8bd3f3-22f5-4283-bfd6-d458a2d18f22",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653d507-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f6fdd1a7-f0c5-4631-b5d3-19421155bd7a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653d5de-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "db9177f5-41d2-4894-be1a-a7547ed6b63a",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "09b85517-e5f5-415b-a950-1a60ee285242",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653d69e-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "dba3028d-2029-4a87-9992-f6335d890528",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "440ef381-8fe8-4b6e-9198-270ee5653454",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653d8dd-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653d98a-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "440ef381-8fe8-4b6e-9198-270ee5653454",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8ce378a5-1418-4184-bf02-328a06e1d3be",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653da34-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "092b47db-6f77-4072-aed3-eb248ab69e9c",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653db8c-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653dce1-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "8ce378a5-1418-4184-bf02-328a06e1d3be",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0a6558cf-cf5f-4646-977e-7d6b4fde47e8",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653dd99-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "54b73077-a062-41cc-882c-4df1eba447d9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e950cd98-574b-4e57-9ef8-c2231e1ce451",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4653de50-4d8d-11e3-9842-94de802aa978",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "5c0d8661-1c49-4023-8a67-4991365d70fb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8ce130d4-3f7e-46ec-868a-505cf9033d96",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "466198c8-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "ef8bd3f3-22f5-4283-bfd6-d458a2d18f22",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5c0d8661-1c49-4023-8a67-4991365d70fb",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "46619bb1-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ef8bd3f3-22f5-4283-bfd6-d458a2d18f22",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "46619d14-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f6fdd1a7-f0c5-4631-b5d3-19421155bd7a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "46619e34-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "db9177f5-41d2-4894-be1a-a7547ed6b63a",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "09b85517-e5f5-415b-a950-1a60ee285242",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "46619efb-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "dba3028d-2029-4a87-9992-f6335d890528",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "440ef381-8fe8-4b6e-9198-270ee5653454",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4661a162-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4661a228-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "440ef381-8fe8-4b6e-9198-270ee5653454",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8ce378a5-1418-4184-bf02-328a06e1d3be",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4661a33f-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "092b47db-6f77-4072-aed3-eb248ab69e9c",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4661a4c2-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4661a7c3-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "8ce378a5-1418-4184-bf02-328a06e1d3be",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0a6558cf-cf5f-4646-977e-7d6b4fde47e8",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4661a88c-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "54b73077-a062-41cc-882c-4df1eba447d9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e950cd98-574b-4e57-9ef8-c2231e1ce451",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "4661c886-4d8d-11e3-9842-94de802aa978",
                "exitcode": 2,
                "nextmicroservicechainlink_id": "5c0d8661-1c49-4023-8a67-4991365d70fb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "288b739d-40a1-4454-971b-812127a5e03d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "478ab718-faa4-43c3-8b4e-31678052a46f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "154dd501-a344-45a9-97e3-b30093da35f5",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "61a8de9c-7b25-4f0f-b218-ad4dde261eed",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "48812a6e-4c7b-4fde-9ea6-50cced027b6e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3e25bda6-5314-4bb4-aa1e-90900dce887d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f8cb20e6-27aa-44f6-b5a1-dd53b5fc71f6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "4aa64bfe-3574-4bd4-8f6f-7c4cb0575f85",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "efd15406-fd6c-425b-8772-d460e1e79009",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "1c2550f1-3fc0-45d8-8bc4-4c06d720283b",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "4ad9fa2a-3c87-4cd6-8a0b-3a27ec7efbab",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "559d9b14-05bf-4136-918a-de74a821b759",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b944ec7f-7f99-491f-986d-58914c9bb4fa",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "4ba2d89a-d741-4868-98a7-6202d0c57163",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "dec97e3c-5598-4b99-b26e-f87a435a6b7f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "032cdc54-0b9b-4caf-86e8-10d63efbaec0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-06T17:43:33+00:00"),
                "replaces_id": None,
                "pk": "4bfba45a-6808-4b31-a8bf-cbf34c66111a",
                "exitcode": 179,
                "nextmicroservicechainlink_id": "b04e9232-2aea-49fc-9560-27349c8eba4e",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "4d703bf8-12ce-4fe7-9ddc-4dac274d8424",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f1e286f9-4ec7-4e19-820c-dae7b8ea7d09",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "dc9d4991-aefa-4d7e-b7b5-84e3c4336e74",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "replaces_id": None,
                "pk": "4de0e894-8eda-49eb-a915-124b4f6c3608",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b6b0fe37-aa26-40bd-8be8-d3acebf3ccf8",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "4f4b2fd0-fc20-4572-ac49-c18be1eefe15",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "dba3028d-2029-4a87-9992-f6335d890528",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "91dc1ab1-487e-4121-a6c5-d8441da7a422",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "4f85bfa3-1e4a-4698-8b02-5eb1bd434c5d",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "63f35161-ba76-4a43-8cfa-c38c6a2d5b2f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d3c75c96-f8c7-4674-af46-5bcce7b05f87",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "4ffb1b47-b240-4fcc-8012-afb2a3149750",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "da2d650e-8ce3-4b9a-ac97-8ca4744b019f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "4417b129-fab3-4503-82dd-740f8e774bff",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "5035f15f-90a9-4beb-9251-c24ec3e530d7",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "fdfac6e5-86c0-4c81-895c-19a9edadedef",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "6ee25a55-7c08-4c9a-a114-c200a37146c4",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "516512ee-0aca-4d4f-b79f-eec82ea063d7",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "61a8de9c-7b25-4f0f-b218-ad4dde261eed",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e399bd60-202d-42df-9760-bd14497b5034",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-04T00:47:58+00:00"),
                "replaces_id": None,
                "pk": "550df3a0-5cbe-4009-9be7-8d86b53c3f68",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3409b898-e532-49d3-98ff-a2a1f9d988fa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "df1cc271-ff77-4f86-b4f3-afc01856db1f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "55413eac-d358-45f1-b54e-595a6489adcf",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "cf71e6ff-7740-4bdb-a6a9-f392d678c6e1",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d0c463c2-da4c-4a70-accb-c4ce96ac5194",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "557ab052-a7a7-4eff-9869-e3f55d5d505e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "ef6332ee-a890-4e1b-88de-986efc4269fb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f6fdd1a7-f0c5-4631-b5d3-19421155bd7a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "55c70f4f-a05f-4903-9f62-fe5daa282ba7",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "db9177f5-41d2-4894-be1a-a7547ed6b63a",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "c3269a0a-91db-44e8-96d0-9c748cf80177",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "55dd25a7-944a-4a99-8b94-a508d28d0b38",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f12ece2c-fb7e-44de-ba87-7e3c5b6feb74",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "5858d1d8-9900-4e65-bf61-2a5ff648998e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e3efab02-1860-42dd-a46c-25601251b930",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f19926dd-8fb5-4c79-8ade-c83f61f55b40",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "59363759-0e3d-4635-965d-7670b489201b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1cb7e228-6e94-4c93-bf70-430af99b9264",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "dba3028d-2029-4a87-9992-f6335d890528",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "59489199-c348-4f12-82c7-f26afab99301",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "c2e6600d-cd26-42ed-bed5-95d41c06e37b",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "56da7758-913a-4cd2-a815-be140ed09357",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "5a9bdbce-2887-4817-90b6-144c16f50a26",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "8ce130d4-3f7e-46ec-868a-505cf9033d96",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bd382151-afd0-41bf-bb7a-b39aef728a32",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "5b2542c8-2088-4541-8bf9-a750eacb4ac5",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1b1a4565-b501-407b-b40f-2f20889423f1",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ac85a1dc-272b-46ac-bb3e-5bf3f8e56348",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "5bb7a0a6-44f8-4042-be96-a33200eeaa49",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "0e06d968-4b5b-4084-aab4-053a2a8d1679",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "26bf24c9-9139-4923-bf99-aa8648b1692b",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-11-06T01:07:49+00:00"),
                "replaces_id": None,
                "pk": "5c0f905e-40c8-4cdb-af87-d8635ada9f07",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f2a019ea-0601-419c-a475-1b96a927a2fb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e76aec15-5dfa-4b14-9405-735863e3a6fa",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "replaces_id": None,
                "pk": "5cd0e0ee-75a1-419f-817c-4edd6adce857",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "10c40e41-fb10-48b5-9d01-336cd958afe8",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f052432c-d4e7-4379-8d86-f2a08f0ae509",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "5d1e6692-a0fc-438d-8448-82490a874da4",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3229e01f-adf3-4294-85f7-4acb01b3fbcf",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "dc144ff4-ad74-4a6e-ac15-b0beedcaf662",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "5e481248-543b-463d-b0a4-eee87c79e71f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "370aca94-65ab-4f2a-9d7d-294a62c8b7ba",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "50b67418-cb8d-434d-acc9-4a8324e7fdd2",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "5ec10388-20a3-4e54-9e0a-45186242317b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "5d780c7d-39d0-4f4a-922b-9d1b0d217bca",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "11033dbd-e4d4-4dd6-8bcf-48c424e222e3",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "5fae3555-f2bd-4e36-aebf-32a5c11e2f1e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1ba589db-88d1-48cf-bb1a-a5f9d2b17378",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "970b7d17-7a6b-4d51-808b-c94b78c0d97f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "5ffe0c72-5a98-4fa5-8281-a266471ffb2c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "15a2df8a-7b45-4c11-b6fa-884c9b7e5c67",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "16415d2f-5642-496d-a46d-00028ef6eb0a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-04T21:29:48+00:00"),
                "replaces_id": None,
                "pk": "6027ccf7-879b-45ad-b6df-e4486d6560ff",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d0dfbd93-d2d0-44db-9945-94fd8de8a1d4",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "604d4f55-f8a5-4c57-852d-579477a22bf1",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7c95b242-1ce5-4210-b7d4-fdbb6c0aa5dd",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "62430e2d-3240-43aa-9af7-4ec9c8236576",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f8319d49-f1e3-45dd-a404-66165c59dec7",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f1bfce12-b637-443f-85f8-b6450ca01a13",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "62619dde-d34b-4648-962a-3888badd5b56",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3409b898-e532-49d3-98ff-a2a1f9d988fa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "208d441b-6938-44f9-b54a-bd73f05bc764",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "628711a4-75e2-452e-b8af-97cf30932a32",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d1018160-aaab-4d92-adce-d518880d7c7d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "1b1a4565-b501-407b-b40f-2f20889423f1",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "62af9c19-2ddb-4d5b-81b0-df1be79eb96e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "a536828c-be65-4088-80bd-eb511a0a063d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b7a83da6-ed5a-47f7-a643-1e9f9f46e364",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "637afa7b-d970-4076-aa4e-d62dfc6bb0b6",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e85a01f1-4061-4049-8922-5694b25c23a2",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7b146689-1a04-4f58-ba86-3caf2b76ddbc",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "64426665-4e8b-4814-823a-db8c9a88c8ab",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f3a39155-d655-4336-8227-f8c88e4b7669",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "aa9ba088-0b1e-4962-a9d7-79d7a0cbea2d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-11-06T01:14:17+00:00"),
                "replaces_id": None,
                "pk": "65409432-a449-4455-8eb2-5cc28af16958",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "45063ad6-f374-4215-a2c4-ac47be4ce2cd",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "15a2df8a-7b45-4c11-b6fa-884c9b7e5c67",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-02-19T00:52:53+00:00"),
                "replaces_id": None,
                "pk": "654b4527-9e55-4792-930c-94aed94b3639",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1cd3b36a-5252-4a69-9b1c-3b36829288ab",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "424ee8f1-6cdd-4960-8641-ed82361d3ad7",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "662164ca-9872-49f7-8a4b-bd306b01fca2",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "47c83e01-7556-4c13-881f-282c6d9c7d6a",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5b7a48e1-32ed-43f9-8ffa-e374010fcf76",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "666b8986-b3ae-4397-8fad-1f52c6395f62",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "0e1a8a6b-abcc-4ed6-b4fb-cbccfdc23ef5",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d1b27e9e-73c8-4954-832c-36bd1e00c802",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "replaces_id": None,
                "pk": "6740b87f-6d30-4f43-8848-1371fe9b08c5",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7e65c627-c11d-4aad-beed-65ceb7053fe8",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "674f222a-4911-4005-9c45-e3a54ac3df78",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "67a91b4b-a5af-4b54-a836-705e6cf4eeb9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ed5d8475-3793-4fb0-a8df-94bd79b26a4c",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "68d19ada-9c7a-47b3-bedc-66788d5e9e3e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b7a83da6-ed5a-47f7-a643-1e9f9f46e364",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e3efab02-1860-42dd-a46c-25601251b930",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "691782ba-080f-4e46-a945-ab3f3576b7dc",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "91ca6f1f-feb5-485d-99d2-25eed195e330",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "replaces_id": None,
                "pk": "691a64b4-7208-42c6-bc9f-db0a05961c18",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "54b73077-a062-41cc-882c-4df1eba447d9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b2ef06b9-bca4-49da-bc5c-866d7b3c4bb1",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "6a4ef1c6-d54d-46d6-af8e-8a8851fa744e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "4b75ca30-2eaf-431b-bffa-d737c8a0bf37",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "6b2786d7-60dc-4feb-94ec-b84f82a6e05d",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "66c9c178-2224-41c6-9c0b-dcb60ff57b1a",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "6b931965-d5f6-4611-a536-39d5901f8f70",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "6c381156-7012-4a3c-86f8-e7e262380011",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "0a6558cf-cf5f-4646-977e-7d6b4fde47e8",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "09b85517-e5f5-415b-a950-1a60ee285242",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-10T22:49:49+00:00"),
                "replaces_id": None,
                "pk": "6d4d9afb-7bb6-4527-9c8c-4cd9adcdedcf",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "dba3028d-2029-4a87-9992-f6335d890528",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e4e19c32-16cc-4a7f-a64d-a1f180bdb164",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "6d87f2f2-9d5a-4216-8dbf-6201a9ee8cca",
                "exitcode": 179,
                "nextmicroservicechainlink_id": "83d5e887-6f7c-48b0-bd81-e3f00a9da772",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "60b0e812-ebbe-487e-810f-56b1b6fdd819",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "6e06fd5e-3892-4e79-b64f-069876bd95a1",
                "exitcode": 100,
                "nextmicroservicechainlink_id": "31fc3f66-34e9-478f-8d1b-c29cd0012360",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "377f8ebb-7989-4a68-9361-658079ff8138",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "6e9003bf-6314-4f80-a9d3-7f64c00e7be8",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5d6a103c-9a5d-4010-83a8-6f4c61eb1478",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-24T00:40:06+00:00"),
                "replaces_id": None,
                "pk": "6f9575c3-4b84-45bf-920d-b8115e4806f4",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "74665638-5d8f-43f3-b7c9-98c4c8889766",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T07:25:07+00:00"),
                "replaces_id": None,
                "pk": "6fe4c525-f337-408a-abcc-1caf2d3ee003",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0e41c244-6c3e-46b9-a554-65e66e5c9324",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "6ff56b9a-2e0d-4117-a6ee-0ba51e6da708",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "95616c10-a79f-48ca-a352-234cc91eaf08",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0b92a510-a290-44a8-86d8-6b7139be29df",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "70d285e1-0548-4f84-bc8a-687e06a220b0",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f6fdd1a7-f0c5-4631-b5d3-19421155bd7a",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2dd53959-8106-457d-a385-fee57fc93aa9",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "replaces_id": None,
                "pk": "71a09b45-3f64-4618-af51-6a960ae16754",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "83484326-7be7-4f9f-b252-94553cd42370",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "dae3c416-a8c2-4515-9081-6dbd7b265388",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "72559113-a0a6-4ba8-8b17-c855389e5f16",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "88807d68-062e-4d1a-a2d5-2d198c88d8ca",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "72cdeeb3-4dfd-41c9-a0cb-e105ba22bf4f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7d33f228-0fa8-4f4c-a66b-24f8e264c214",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "73028cdb-b35d-4490-a89c-d0fe35c68054",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "aaa929e4-5c35-447e-816a-033a66b9b90b",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b15c0ba6-e247-4512-8b56-860fd2b6299d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-24T17:04:11+00:00"),
                "replaces_id": None,
                "pk": "730c63c4-7b81-4710-a4d0-0efe49c14708",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "303a65f6-a16f-4a06-807b-cb3425a30201",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "734283b4-527c-4d72-a8b1-f879e64df034",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1b1a4565-b501-407b-b40f-2f20889423f1",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "67b44f8f-bc97-4cb3-b6dd-09dba3c99d30",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-24T00:40:07+00:00"),
                "replaces_id": None,
                "pk": "7386614c-6b85-4fc2-9aec-1b7a8d4adb8a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "5d6a103c-9a5d-4010-83a8-6f4c61eb1478",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "635ba89d-0ad6-4fc9-acc3-e6069dffdcd5",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "767d6a50-5a17-436c-84f9-68c5991c9a57",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "a2173b55-abff-4d8f-97b9-79cc2e0a64fa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "c8f7bf7b-d903-42ec-bfdf-74d357ac4230",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "78e44cfa-d6c9-4f74-861b-4a0f9bb57dcb",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "a329d39b-4711-4231-b54e-b5958934dccb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ddc8b2ef-a7ba-4713-9425-ed18a1fa720b",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "78fc9675-6c21-4dc6-9181-9d2885726112",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "52269473-5325-4a11-b38a-c4aafcbd8f54",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "efd15406-fd6c-425b-8772-d460e1e79009",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "7941ee5a-f093-4cfb-bacc-03dfb7d51e15",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "0c2c9c9a-25b2-4a2d-a790-103da79f9604",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "78b7adff-861d-4450-b6dd-3fabe96a849e",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "replaces_id": None,
                "pk": "7963e4e9-ccca-486e-94f5-df9d141554b3",
                "exitcode": 179,
                "nextmicroservicechainlink_id": "a1b65fe3-9358-479b-93b9-68f2b5e71b2b",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "c103b2fb-9a6b-4b68-8112-b70597a6cd14",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "7a49c825-aeeb-4609-a3ba-2c2979888591",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "60b0e812-ebbe-487e-810f-56b1b6fdd819",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "63f35161-ba76-4a43-8cfa-c38c6a2d5b2f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "7aad879a-ffc4-4276-8e6e-eeb89a5bc0fa",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "7c44c454-e3cc-43d4-abe0-885f93d693c6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "04493ab2-6cad-400d-8832-06941f121a96",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "7b41df94-6544-477d-9137-a8d744cf0904",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "75fb5d67-5efa-4232-b00b-d85236de0d3f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d55b42c8-c7c5-4a40-b626-d248d2bd883f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "7c61af02-852b-4619-bcd6-962b7c2c37ae",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "0a63befa-327d-4655-a021-341b639ee9ed",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "4430077a-92c5-4d86-b0f8-0d31bdb731fb",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "7c6cef61-5d18-4069-bc48-00a636965903",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f8be53cd-6ca2-4770-8619-8a8101a809b9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "df957421-6bba-4ad7-8580-0fc04a54efd4",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "7d0a2e68-7f29-40ab-a29d-0eeadacda21b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b2552a90-e674-4a40-a482-687c046407d3",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f025f58c-d48c-4ba1-8904-a56d2a67b42f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "7d6b5e10-6cd2-4315-88d7-0afad4957d75",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "49cbcc4d-067b-4cd5-b52e-faf50857b35a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "7deb2533-ae68-4ffa-9217-85d5bb4bfd62",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b320ce81-9982-408a-9502-097d0daa48fa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "60b0e812-ebbe-487e-810f-56b1b6fdd819",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "7f2d5239-b464-4837-8e01-0fc43e31395d",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e64d26f4-3330-4d0b-bffe-81edb0dbe93d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "replaces_id": None,
                "pk": "800259c7-f6d2-4ac6-af69-07985f23efec",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d2035da2-dfe1-4a56-8524-84d5732fd3a3",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2900f6d8-b64c-4f2a-8f7f-bb60a57394f6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "804d4d23-e81b-4d81-8e67-1a3b5470c841",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f574b2a0-6e0b-4c74-ac5b-a73ddb9593a0",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "1dce8e21-7263-4cc4-aa59-968d9793b5f2",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "80547eac-c724-45e1-8804-3eabf18bea47",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "33d7ac55-291c-43ae-bb42-f599ef428325",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "6b39088b-683e-48bd-ab89-9dab47f4e9e0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "8065a544-5eb6-4868-88b5-f352b4e3f822",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "35c8763a-0430-46be-8198-9ecb23f895c8",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "21d6d597-b876-4b3f-ab85-f97356f10507",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "82c773f3-28af-4bcd-bab8-186ef528a6c9",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "c8f7bf7b-d903-42ec-bfdf-74d357ac4230",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "31fc3f66-34e9-478f-8d1b-c29cd0012360",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "8609a2ef-9da2-4803-ad4f-605bfff10795",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e4e19c32-16cc-4a7f-a64d-a1f180bdb164",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bbfbecde-370c-4e26-8087-cfa751e72e6a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "86bba355-218d-4eef-b6ef-145d17ddbbff",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "100a75f4-9d2a-41bf-8dd0-aec811ae1077",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "87dcd08a-7688-425a-ae5f-2f623feb078a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "192315ea-a1bf-44cf-8cb4-0b3edd1522a6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "4efe00da-6ed0-45dd-89ca-421b78c4b6be",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "882486b7-034e-49b8-bc65-2f6d8946bdcd",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "2584b25c-8d98-44b7-beca-2b3ea2ea2505",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "46dcf7b1-3750-4f49-a9be-a4bf076e304f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "883345d7-9bb6-455f-b546-0fbe27c08048",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "df1cc271-ff77-4f86-b4f3-afc01856db1f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "3c526a07-c3b8-4e53-801b-7f3d0c4857a5",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "88a36d00-af47-4845-8bcf-a72529ae78f8",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "c77fee8c-7c4e-4871-a72e-94d499994869",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "83d5e887-6f7c-48b0-bd81-e3f00a9da772",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "88ccca76-c4d0-4172-b722-0c0ecb3d7d46",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "29dece8e-55a4-4f2c-b4c2-365ab6376ceb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d1018160-aaab-4d92-adce-d518880d7c7d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "88e39b88-e57b-4cb5-96e4-dd48cb9e3a6f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b3d11842-0090-420a-8919-52d7039d50e6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8de9fe10-932f-4151-88b0-b50cf271e156",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-24T00:40:07+00:00"),
                "replaces_id": None,
                "pk": "8a526305-0805-4680-8dd8-3f7dd3da7854",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "9e3dd445-551d-42d1-89ba-fe6dff7c6ee6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "8b8a4bc0-277c-4d45-acc0-d02f7a34e31a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "66c9c178-2224-41c6-9c0b-dcb60ff57b1a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "8bec6c39-8b98-4e2c-9a91-f7a9c8130f2e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "2714cd07-b99f-40e3-9ae8-c97281d0d429",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "22ded604-6cc0-444b-b320-f96afb15d581",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "8c346844-b95d-4ed5-8fc3-694c34844de9",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "bd382151-afd0-41bf-bb7a-b39aef728a32",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0e1a8a6b-abcc-4ed6-b4fb-cbccfdc23ef5",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "8c9618b1-3cf2-411e-a5ef-bb4c23470c84",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "bda96b35-48c7-44fc-9c9e-d7c5a05016c1",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "eb52299b-9ae6-4a1f-831e-c7eee0de829f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "8e572576-4ad9-4a8b-8d18-80b2af8d1d4e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "db99ab43-04d7-44ab-89ec-e09d7bbdc39d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "45f4a7e3-87cf-4fb4-b4f9-e36ad8c853b1",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "8f2feee8-9c73-4ee1-bdaf-29c43bffba25",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "288b739d-40a1-4454-971b-812127a5e03d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "8f5f0648-1051-44cd-80a1-d83e21f67d42",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8f639582-8881-4a8b-8574-d2f86dc4db3d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "8f795343-1ebb-46f5-9cb4-03442c5bc14e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f378ec85-adcc-4ee6-ada2-bc90cfe20efb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2584b25c-8d98-44b7-beca-2b3ea2ea2505",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "8f95edbc-02d4-4a0e-8904-d5c027c9969b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "a329d39b-4711-4231-b54e-b5958934dccb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "3e25bda6-5314-4bb4-aa1e-90900dce887d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "8fd30c27-7125-4b9f-8e8d-d2bdd41f3525",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "002716a1-ae29-4f36-98ab-0d97192669c4",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "cc16178b-b632-4624-9091-822dd802a2c6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "9157ab64-b4d9-4e87-afc8-d2027d8ff1f4",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5cf308fd-a6dc-4033-bda1-61689bb55ce2",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "9159eb2a-e720-4bf0-bafb-ed5bd5b9db7b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "88d2120a-4d19-4b47-922f-7438be1f52a2",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8bc92801-4308-4e3b-885b-1a89fdcd3014",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-02-13T22:03:39+00:00"),
                "replaces_id": None,
                "pk": "919909a4-b66f-4bca-af3d-fc8ec6f94047",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b2444a6e-c626-4487-9abc-1556dd89a8ae",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0d7f5dc2-b9af-43bf-b698-10fdcc5b014d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-04-18T20:38:36+00:00"),
                "replaces_id": None,
                "pk": "9367abb6-a9ce-4ed6-88e0-b3370d1f0003",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "46e19522-9a71-48f1-9ccd-09cabfba3f38",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "942ba7f8-d58a-439f-97cc-10964f6c2f13",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3409b898-e532-49d3-98ff-a2a1f9d988fa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "43c72f8b-3cea-4b4c-b99d-cfdefdfcc270",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "95ba6779-2ed2-47ea-a7ad-df4a4cf3764d",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "6ee25a55-7c08-4c9a-a114-c200a37146c4",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b2552a90-e674-4a40-a482-687c046407d3",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "97dd0591-5588-4cd4-9da8-fec60f2369c0",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "21d6d597-b876-4b3f-ab85-f97356f10507",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "3467d003-1603-49e3-b085-e58aa693afed",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "98aa3486-eb3d-4273-9c42-9fc0542b3334",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2e7f83f9-495a-44b3-b0cf-bff66f021a4d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "992e8dce-80e3-4721-8f25-9e6334fae8c5",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "bbfbecde-370c-4e26-8087-cfa751e72e6a",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f1e286f9-4ec7-4e19-820c-dae7b8ea7d09",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replaces_id": None,
                "pk": "99f8045f-8da0-40f6-8fb3-b45bfc7f3bfb",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "65240550-d745-4afe-848f-2bf5910457c9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e85a01f1-4061-4049-8922-5694b25c23a2",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "9a028152-f3a2-4b98-82e1-8f77c594d1de",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e3efab02-1860-42dd-a46c-25601251b930",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bdce640d-6e94-49fe-9300-3192a7e5edac",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "9a07d5a1-1418-4007-9c7e-55462ca63751",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "7d33f228-0fa8-4f4c-a66b-24f8e264c214",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8ba83807-2832-4e41-843c-2e55ad10ea0b",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-24T00:40:07+00:00"),
                "replaces_id": None,
                "pk": "9b010021-a969-4a16-98c2-0db1ecd5d6d9",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "5d6a103c-9a5d-4010-83a8-6f4c61eb1478",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5d780c7d-39d0-4f4a-922b-9d1b0d217bca",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "9cb81a5c-a7a1-43a8-8eb6-3e999923e03c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "df02cac1-f582-4a86-b7cf-da98a58e279e",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "9cdd2a70-61a3-4590-8ccd-26dde4290be4",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f3be1ee1-8881-465d-80a6-a6f093d40ec2",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "65240550-d745-4afe-848f-2bf5910457c9",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "9d7c1a9c-85d3-407c-9be2-044885bc064a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3e25bda6-5314-4bb4-aa1e-90900dce887d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f8319d49-f1e3-45dd-a404-66165c59dec7",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "9dd9d972-d4ef-4368-8a2f-eb77ae4f4f90",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "4b75ca30-2eaf-431b-bffa-d737c8a0bf37",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T07:25:07+00:00"),
                "replaces_id": None,
                "pk": "9e7cc8ee-4732-4dfa-86c4-cdb8b9c710da",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "20515483-25ed-4133-b23e-5bb14cab8e22",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "9f6bc15e-31fc-4682-baf5-a780288eba2c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "48703fad-dc44-4c8e-8f47-933df3ef6179",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b20ff203-1472-40db-b879-0e59d17de867",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "9fc959c0-d635-44d0-8f1b-168e843b33cc",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "7b146689-1a04-4f58-ba86-3caf2b76ddbc",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "888a5bdc-9928-44f0-9fb7-91bc5f1e155b",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-12T21:25:31+00:00"),
                "replaces_id": None,
                "pk": "a085c6ce-4af0-4ac3-9755-93b4945bd71d",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "214f1004-2748-4bed-a38d-48fe500c41b9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "19c94543-14cb-4158-986b-1d2b55723cd8",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "a0bb8527-e58f-4043-a7c4-c4fc5e34d786",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3467d003-1603-49e3-b085-e58aa693afed",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b6b0fe37-aa26-40bd-8be8-d3acebf3ccf8",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "replaces_id": None,
                "pk": "a0f33c59-081b-4427-b430-43b811cf0594",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b21018df-f67d-469a-9ceb-ac92ac68654e",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5fbc344c-19c8-48be-a753-02dac987428c",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "a38d1d45-42e7-47ea-9a83-01a139f28d59",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "91dc1ab1-487e-4121-a6c5-d8441da7a422",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ef6332ee-a890-4e1b-88de-986efc4269fb",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "a5e44b09-e884-4364-8793-7d81b4a4c29b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "0c96c798-9ace-4c05-b3cf-243cdad796b7",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "fdfac6e5-86c0-4c81-895c-19a9edadedef",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "a9eb16bf-74e9-468d-b3c5-3ee9e7aa6453",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "7c95b242-1ce5-4210-b7d4-fdbb6c0aa5dd",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "cf71e6ff-7740-4bdb-a6a9-f392d678c6e1",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "aaf01618-5e54-4d28-8dcd-8904f912e552",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "2adf60a0-ecd7-441a-b82f-f77c6a3964c3",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7a024896-c4f7-4808-a240-44c87c762bc5",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "replaces_id": None,
                "pk": "ab61e4b6-1167-461f-921e-ebcb5126ff89",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "2dd53959-8106-457d-a385-fee57fc93aa9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8c8bac29-4102-4fd2-9d0a-a3bd2e607566",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "abe6c490-9749-46fc-98aa-a6814a507d72",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f1bfce12-b637-443f-85f8-b6450ca01a13",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2714cd07-b99f-40e3-9ae8-c97281d0d429",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "ad09d973-5c5d-44e9-84a2-a7dbb27dd23d",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "7c6a0b72-f37b-4512-87f3-267644de6f80",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b3d11842-0090-420a-8919-52d7039d50e6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "ae13dd4f-81d6-44d5-94c8-0c19aa6c6cf8",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e3a6d178-fa65-4086-a4aa-6533e8f12d51",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "29dece8e-55a4-4f2c-b4c2-365ab6376ceb",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "affffa5f-33b2-43cc-84e0-f7f378c9600e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "635ba89d-0ad6-4fc9-acc3-e6069dffdcd5",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "3f543585-fa4f-4099-9153-dd6d53572f5c",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "b060a877-9a59-450c-8da0-f32b97b1a516",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "20515483-25ed-4133-b23e-5bb14cab8e22",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8dc0284a-45f4-486e-a78d-7af3e5b8d621",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "b4293a9c-71c6-4dbb-a49c-1fcfc506b1ee",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "6b931965-d5f6-4611-a536-39d5901f8f70",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "440ef381-8fe8-4b6e-9198-270ee5653454",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "b5157984-6f63-4903-a582-ff1f104e6009",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "cb48ef2a-3394-4936-af1f-557b39620efa",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "replaces_id": None,
                "pk": "b61ce1c0-30f3-4871-85a2-dcf14e0f659c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "888a5bdc-9928-44f0-9fb7-91bc5f1e155b",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "b87ee978-0f02-4852-af21-4511a43010e6",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "440ef381-8fe8-4b6e-9198-270ee5653454",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0c2c9c9a-25b2-4a2d-a790-103da79f9604",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "b981edfd-d9d8-498f-a7f2-1765d6833923",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d29105f0-161d-449d-9c34-5a5ea3263f8e",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "91dc1ab1-487e-4121-a6c5-d8441da7a422",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "b992b4c5-97da-4a0b-a434-a114cfa39329",
                "exitcode": 1,
                "nextmicroservicechainlink_id": "746b1f47-2dad-427b-8915-8b0cb7acccd8",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "54b73077-a062-41cc-882c-4df1eba447d9",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "bb20acc4-ca05-4800-831d-2ef585f32e2a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "8ce378a5-1418-4184-bf02-328a06e1d3be",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "bb45ac92-22fd-44e7-9c6a-7d653edd1496",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "83257841-594d-4a0e-a4a1-1e9269c30f3d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f1e286f9-4ec7-4e19-820c-dae7b8ea7d09",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-02-13T22:03:37+00:00"),
                "replaces_id": None,
                "pk": "bbc7cbfd-c3aa-4625-8782-a461615137ed",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "378ae4fc-7b62-40af-b448-a1ab47ac2c0c",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f7488721-c936-42af-a767-2f0b39564a86",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-04T20:13:10+00:00"),
                "replaces_id": None,
                "pk": "bce1ab01-7acd-466a-8ed5-a0d2efaad960",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "2483c25a-ade8-4566-a259-c6c37350d0d6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "154dd501-a344-45a9-97e3-b30093da35f5",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "bfd11ca1-57db-4340-89bb-7e25b0386a64",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3c526a07-c3b8-4e53-801b-7f3d0c4857a5",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "142d0a36-2b88-4b98-8a33-d809f667ecef",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "bff46a44-5493-4217-b858-81e840f1ca8b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "9e810686-d747-4da1-9908-876fb89ac78e",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7c44c454-e3cc-43d4-abe0-885f93d693c6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c1dd1c2c-a18a-4716-a525-3d650cb5529a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e4e19c32-16cc-4a7f-a64d-a1f180bdb164",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "c1f6f15d-2ce9-43fd-841c-1fd916f9fd2e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "29dece8e-55a4-4f2c-b4c2-365ab6376ceb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "378ae4fc-7b62-40af-b448-a1ab47ac2c0c",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c2c7eb9e-d523-40ab-9cf2-d83f72d8977f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "ad011cc2-b0eb-4f51-96bb-400149a2ea11",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "87e7659c-d5de-4541-a09c-6deec966a0c0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c2ccb9f8-c7d3-4876-a29c-3f15c3663451",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "6bd4d385-c490-4c42-a195-dace8697891c",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "67b44f8f-bc97-4cb3-b6dd-09dba3c99d30",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-24T00:40:07+00:00"),
                "replaces_id": None,
                "pk": "c35e05aa-5bb0-454f-8ff3-66ffc625f7ef",
                "exitcode": 179,
                "nextmicroservicechainlink_id": "9e3dd445-551d-42d1-89ba-fe6dff7c6ee6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b7cf0d9a-504f-4f4e-9930-befa817d67ff",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "c3c8e23c-1c8a-4c24-b8a1-3d6e8a8c3a7b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d5a2ef60-a757-483c-a71a-ccbffe6b80da",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "087d27be-c719-47d8-9bbb-9a7d8b609c44",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "c3f1a78b-0e5e-4d3f-8d32-ba9554ebddf8",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1dce8e21-7263-4cc4-aa59-968d9793b5f2",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "3409b898-e532-49d3-98ff-a2a1f9d988fa",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c4060d14-6cfe-4e06-9c8a-17c380a9895d",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "9071c352-aed5-444c-ac3f-b6c52dfb65ac",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f2a1faaf-7322-4d9c-aff9-f809e7a6a6a2",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c4c0538a-56fd-4c8e-96dd-c58b713be284",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "c77fee8c-7c4e-4871-a72e-94d499994869",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c4c7ff3c-3eef-42e3-a68d-f11ca3e7c6dd",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f0f64c7e-30fa-47c1-9877-43955680c0d0",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bda96b35-48c7-44fc-9c9e-d7c5a05016c1",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replaces_id": None,
                "pk": "c5c68ced-17d5-4b7d-b955-a56080d5b9bb",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "26bf24c9-9139-4923-bf99-aa8648b1692b",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "77a7fa46-92b9-418e-aa88-fbedd4114c9f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c648c562-a9a2-499e-ac5b-055488d842dc",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "7079be6d-3a25-41e6-a481-cee5f352fe6e",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f574b2a0-6e0b-4c74-ac5b-a73ddb9593a0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c66b290b-3c3b-4122-86f6-d8953db77f70",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "47dd6ea6-1ee7-4462-8b84-3fc4c1eeeb7f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "9e3dd445-551d-42d1-89ba-fe6dff7c6ee6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-24T00:40:07+00:00"),
                "replaces_id": None,
                "pk": "c6e80559-2eda-484d-9f5e-bd365b11278f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e219ed78-2eda-4263-8c0f-0c7f6a86c33e",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "6327fdf9-9673-42a8-ace5-cccad005818b",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c84e7df7-2259-418d-a5f0-37108d63ac13",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "7a134af0-b285-4a9f-8acf-f6947b7ed072",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "a1b65fe3-9358-479b-93b9-68f2b5e71b2b",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "replaces_id": None,
                "pk": "c91c108d-3491-440b-97c7-b71bfcb2ebec",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "9e9b522a-77ab-4c17-ab08-5a4256f49d59",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "67a91b4b-a5af-4b54-a836-705e6cf4eeb9",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c9422b26-d2bc-4c03-a173-809d12971d27",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "4103a5b0-e473-4198-8ff7-aaa6fec34749",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "c97b8ab4-069e-4b37-8ccf-f27480ba8d6e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "092b47db-6f77-4072-aed3-eb248ab69e9c",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "a2173b55-abff-4d8f-97b9-79cc2e0a64fa",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "cb61ce7b-4ba0-483e-8dfa-5c30af4927db",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "cc349cf1-7e9d-476e-9669-d5fdacea81b4",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "438dc1cf-9813-44b5-a0a3-58e09ae73b8a",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "61c316a6-0a50-4f65-8767-1f44b1eeb6dd",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-08T02:12:00+00:00"),
                "replaces_id": None,
                "pk": "cd98e02d-19ae-408e-8199-4000d2a5dfee",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "377f8ebb-7989-4a68-9361-658079ff8138",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "35c8763a-0430-46be-8198-9ecb23f895c8",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "cdbd5aee-2ff5-463e-bdb2-b18d48d392bb",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f0f64c7e-30fa-47c1-9877-43955680c0d0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "cfd3ad31-70e2-4b7f-9643-fff6e6ab1f91",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "46e19522-9a71-48f1-9ccd-09cabfba3f38",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "77c722ea-5a8f-48c0-ae82-c66a3fa8ca77",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "d1b46b7e-57cd-4120-97d6-50f8e385f56e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "c103b2fb-9a6b-4b68-8112-b70597a6cd14",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "70f41678-baa5-46e6-a71c-4b6b4d99f4a6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "d235e950-1d4a-4180-b22c-e74b929e4c86",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "8dc0284a-45f4-486e-a78d-7af3e5b8d621",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "192315ea-a1bf-44cf-8cb4-0b3edd1522a6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "d2c5ab7b-ced1-45cd-a7da-98ab30a31259",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "2fd123ea-196f-4c9c-95c0-117aa65ed9c6",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "559d9b14-05bf-4136-918a-de74a821b759",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "d312ae33-3555-472e-803c-ef8076cb789b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "89071669-3bb6-4e03-90a3-3c8b20c7f6fe",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "d37c9a69-a757-4a7d-9f48-9299b8eb5cfa",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "092b47db-6f77-4072-aed3-eb248ab69e9c",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "d4c81458-05b5-434d-a972-46ae43417213",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "28a9f8a8-0006-4828-96d5-892e6e279f72",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "d5690bcf-1c0f-44a1-846e-e63cea2b9087",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "5e4bd4e8-d158-4c2a-be89-51e3e9bd4a06",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f2a019ea-0601-419c-a475-1b96a927a2fb",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "d6914e3c-4d4a-4b0d-9d26-eeb340ac027b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "aa9ba088-0b1e-4962-a9d7-79d7a0cbea2d",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d7e6404a-a186-4806-a130-7e6d27179a15",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "d69a5920-5c3b-46ff-bdcd-e836dfa7c954",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1c2550f1-3fc0-45d8-8bc4-4c06d720283b",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7d728c39-395f-4892-8193-92f086c0546f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-08T02:12:00+00:00"),
                "replaces_id": None,
                "pk": "d7c24320-1152-4808-96ea-81cfdd0617ed",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b2ef06b9-bca4-49da-bc5c-866d7b3c4bb1",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "1b737a9b-b4c0-4230-aa92-1e88067534b9",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-06T18:58:24+00:00"),
                "replaces_id": None,
                "pk": "d81c236d-6a0c-4bf1-a1b1-4ece6763e890",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "20129b22-8f28-429b-a3f2-0648090fa305",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "1cd3b36a-5252-4a69-9b1c-3b36829288ab",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "da1d8295-6914-4839-b1dd-6dd33ab6a41c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "67b44f8f-bc97-4cb3-b6dd-09dba3c99d30",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e2c0dae9-3295-4a98-b3ff-664ab2dc0cda",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "da54863b-44c0-4ea2-9561-34105ed5208e",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "7e65c627-c11d-4aad-beed-65ceb7053fe8",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bdfecadc-8219-4109-885c-cfb9ef53ebc3",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "dad05633-987d-4672-9b7c-1341cecbf59c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "823b0d76-9f3c-410d-83ab-f3c2cdd9ab22",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "a46e95fe-4a11-4d3c-9b76-c5d8ea0b094d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "db159412-71fa-4d94-aea6-c173e82fd7c2",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "970b7d17-7a6b-4d51-808b-c94b78c0d97f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "88d2120a-4d19-4b47-922f-7438be1f52a2",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "dc3c6084-74eb-4dc9-b3bd-6c89c8538d8a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "89071669-3bb6-4e03-90a3-3c8b20c7f6fe",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "3868c8b8-977d-4162-a319-dc487de20f11",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "replaces_id": None,
                "pk": "dc99bcd5-e3c3-4763-9b37-3bff5f92f5e9",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "f7488721-c936-42af-a767-2f0b39564a86",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "da2d650e-8ce3-4b9a-ac97-8ca4744b019f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "dcf156a2-2ee4-4673-99de-4689f281dc43",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "4417b129-fab3-4503-82dd-740f8e774bff",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "db6d3830-9eb4-4996-8f3a-18f4f998e07f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "dd9e0f88-9e96-4d8b-a9ae-e0cee1dc5365",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "70669a5b-01e4-4ea0-ac70-10292f87da05",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f95a3ac5-47bc-4df9-a49c-d47abd1e05f3",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "de6d3970-c27e-4be0-929f-07bca37db7cc",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b4567e89-9fea-4256-99f5-a88987026488",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "ad011cc2-b0eb-4f51-96bb-400149a2ea11",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "e0248782-a96c-4fa3-8a02-3157c976f4e1",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1401c4d0-fb6f-42ef-94d3-c884c25800b2",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e219ed78-2eda-4263-8c0f-0c7f6a86c33e",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "e05ae8d7-89ee-46bf-9308-f2cdaa0957f7",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "a2173b55-abff-4d8f-97b9-79cc2e0a64fa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "9e9b522a-77ab-4c17-ab08-5a4256f49d59",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "replaces_id": None,
                "pk": "e090fea3-2e44-4dd9-b17d-73c4d2088e0c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e76aec15-5dfa-4b14-9405-735863e3a6fa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "75fb5d67-5efa-4232-b00b-d85236de0d3f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-02-08T22:21:21+00:00"),
                "replaces_id": None,
                "pk": "e0935e25-62dc-43c1-b4d3-bb3c1f8f04f9",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "88807d68-062e-4d1a-a2d5-2d198c88d8ca",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "370aca94-65ab-4f2a-9d7d-294a62c8b7ba",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "e0d9e83b-89e1-4711-89e4-14dbe15bea4c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "8c8bac29-4102-4fd2-9d0a-a3bd2e607566",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "aaa929e4-5c35-447e-816a-033a66b9b90b",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "e132d3e2-6dcd-4c81-b6f3-7a0ea04193c0",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "bd792750-a55b-42e9-903a-8c898bb77df1",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2483c25a-ade8-4566-a259-c6c37350d0d6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-04T20:13:09+00:00"),
                "replaces_id": None,
                "pk": "e28ed9a4-f176-482e-a360-7893995080bc",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1b737a9b-b4c0-4230-aa92-1e88067534b9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "9071c352-aed5-444c-ac3f-b6c52dfb65ac",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "e5b32c5b-6165-4158-ac85-573f627c5a8f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "03ee1136-f6ad-4184-8dcb-34872f843e14",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "6bd4d385-c490-4c42-a195-dace8697891c",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-11-20T22:55:53+00:00"),
                "replaces_id": None,
                "pk": "e70eb6eb-0ced-481b-9872-231fd0005ad8",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "209400c1-5619-4acc-b091-b9d9c8fbb1c0",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "db99ab43-04d7-44ab-89ec-e09d7bbdc39d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replaces_id": None,
                "pk": "e7837301-3891-4d0f-8b86-6f0a95d5a30b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d27fd07e-d3ed-4767-96a5-44a2251c6d0a",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "438dc1cf-9813-44b5-a0a3-58e09ae73b8a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "e84b0a8d-7fcc-497e-969d-5046a3b24681",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "d0c463c2-da4c-4a70-accb-c4ce96ac5194",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "e8c31963-29fe-4812-846e-3d18327db4b4",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "8ce378a5-1418-4184-bf02-328a06e1d3be",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "01fd7a29-deb9-4dd1-8e28-1c48fc1ac41b",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "e9a2f2c6-fd4b-4766-8794-a96d69256e2b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "ac85a1dc-272b-46ac-bb3e-5bf3f8e56348",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2872d007-6146-4359-b554-6e9fe7a8eca6",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "e9bd8aee-74a8-4a55-bd7a-062ea4bc321b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e2c0dae9-3295-4a98-b3ff-664ab2dc0cda",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d2035da2-dfe1-4a56-8524-84d5732fd3a3",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "replaces_id": None,
                "pk": "ea5b8e14-519e-473b-818c-e62879559816",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "cb48ef2a-3394-4936-af1f-557b39620efa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "47dd6ea6-1ee7-4462-8b84-3fc4c1eeeb7f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "ea78b5c7-0bf3-46a2-a08d-faeaeeeed363",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "173d310c-8e40-4669-9a69-6d4c8ffd0396",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "38c591d4-b7ee-4bc0-b993-c592bf15d97d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "ece1558b-2b29-41aa-abe2-732510d4f47f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1c2550f1-3fc0-45d8-8bc4-4c06d720283b",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0f0c1f33-29f2-49ae-b413-3e043da5df61",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "replaces_id": None,
                "pk": "edcb6a1c-3122-4de3-80a8-b5cbae330aad",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "745340f5-5741-408e-be92-34c596c00209",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "f09847c2-ee51-429a-9478-a860477f6b8d",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "replaces_id": None,
                "pk": "ef56e6a6-5280-4227-9799-9c1d2d7c0919",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "c3269a0a-91db-44e8-96d0-9c748cf80177",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "db9177f5-41d2-4894-be1a-a7547ed6b63a",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "effb457a-885d-411e-a542-9f37e30007fc",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "cddde867-4cf9-4248-ac31-f7052fae053f",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "39a128e3-c35d-40b7-9363-87f75091e1ff",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f01f4b3e-a8a8-4ec8-b373-a1cb7d307590",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "1cb7e228-6e94-4c93-bf70-430af99b9264",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "replaces_id": None,
                "pk": "f0ba8289-b40f-4279-a968-7496f837c9f9",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "c5ecb5a9-d697-4188-844f-9a756d8734fa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "1ba589db-88d1-48cf-bb1a-a5f9d2b17378",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f11414be-45ae-4f17-bf8e-76a9dd784d39",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "087d27be-c719-47d8-9bbb-9a7d8b609c44",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b0ffcd90-eb26-4caf-8fab-58572d205f04",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replaces_id": None,
                "pk": "f1292ec3-4749-4e64-a924-c2089f97c583",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e4b0c713-988a-4606-82ea-4b565936d9a7",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "209400c1-5619-4acc-b091-b9d9c8fbb1c0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f139c451-a7d8-467d-811f-9ee556d7f1d2",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "ddc8b2ef-a7ba-4713-9425-ed18a1fa720b",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "c2e6600d-cd26-42ed-bed5-95d41c06e37b",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f2857a15-9c0a-49df-92ee-a95678940f15",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "33d7ac55-291c-43ae-bb42-f599ef428325",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f34b9825-9a86-49bd-939c-050c25e62c49",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "576f1f43-a130-4c15-abeb-c272ec458d33",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "576f1f43-a130-4c15-abeb-c272ec458d33",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f4d92639-af82-476d-84cd-508afd167fcf",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "ee438694-815f-4b74-97e1-8e7dde2cc6d5",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "745340f5-5741-408e-be92-34c596c00209",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "replaces_id": None,
                "pk": "f52ffb80-3ecd-4db0-9110-d6568cfd3e10",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "78b7adff-861d-4450-b6dd-3fabe96a849e",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0915f727-0bc3-47c8-b9b2-25dc2ecef2bb",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "replaces_id": None,
                "pk": "f5644951-ecaa-42bc-9286-ed4ee220b58f",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "5fbc344c-19c8-48be-a753-02dac987428c",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "7a134af0-b285-4a9f-8acf-f6947b7ed072",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f61a8be3-8574-49a9-9af5-cb3a01ed6ab5",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "56da7758-913a-4cd2-a815-be140ed09357",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0fc3c795-dc68-4aa0-86fc-cbd6af3302fa",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-12-04T00:47:58+00:00"),
                "replaces_id": None,
                "pk": "f6f2c768-f322-4ad5-a64a-96746dbe4afa",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "e399bd60-202d-42df-9760-bd14497b5034",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "032cdc54-0b9b-4caf-86e8-10d63efbaec0",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f77ea984-9a0e-4214-a7f4-9e33a3157837",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "01d64f58-8295-4b7b-9cab-8f1b153a504f",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f797ae30-2018-40bd-bbff-7a947058ee7b",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "01c651cb-c174-4ba4-b985-1d87a44d6754",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "bd792750-a55b-42e9-903a-8c898bb77df1",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replaces_id": None,
                "pk": "f8597642-7254-43a7-8857-8ca053d0fba5",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "1cb7e228-6e94-4c93-bf70-430af99b9264",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "74665638-5d8f-43f3-b7c9-98c4c8889766",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f98ca91f-8650-4f5c-9acb-21c0fdb5ac0a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "a2173b55-abff-4d8f-97b9-79cc2e0a64fa",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "d5a2ef60-a757-483c-a71a-ccbffe6b80da",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "f9d57a68-a7be-41ee-ad9f-b761fac65b1c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": None,
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "0a6558cf-cf5f-4646-977e-7d6b4fde47e8",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "fb0ecf23-a32e-4874-96dc-1175ee86b159",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "54b73077-a062-41cc-882c-4df1eba447d9",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "b21018df-f67d-469a-9ceb-ac92ac68654e",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-02-13T22:03:39+00:00"),
                "replaces_id": None,
                "pk": "fd465136-38f3-47b8-80dd-f02d5fa9888a",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "8bc92801-4308-4e3b-885b-1a89fdcd3014",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "2a62f025-83ec-4f23-adb4-11d5da7ad8c2",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "fe188831-76b3-4487-8712-5d727a50e8ce",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "11033dbd-e4d4-4dd6-8bcf-48c424e222e3",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e950cd98-574b-4e57-9ef8-c2231e1ce451",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "replaces_id": None,
                "pk": "fe27318c-9ee1-470f-a9ce-0f8103cc78a5",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "5c0d8661-1c49-4023-8a67-4991365d70fb",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "e4b0c713-988a-4606-82ea-4b565936d9a7",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "replaces_id": None,
                "pk": "ff97354f-9fdd-4c85-8a33-cb9e96b48229",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "dc9d4991-aefa-4d7e-b7b5-84e3c4336e74",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)
            props = {
                "microservicechainlink_id": "5e4bd4e8-d158-4c2a-be89-51e3e9bd4a06",
                "exitmessage": "Completed successfully",
                "lastmodified": parse_date("2012-10-02T00:25:07+00:00"),
                "replaces_id": None,
                "pk": "fff06898-16ff-40a5-ba41-90652f65eb9c",
                "exitcode": 0,
                "nextmicroservicechainlink_id": "b6c9de5a-4a9f-41e1-a524-360bdca39893",
            }
            MicroServiceChainLinkExitCode.objects.create(**props)

        with suppress_autotime(MicroServiceChoiceReplacementDic, ["lastmodified"]):
            props = {
                "description": "Fido version 1 PUID runs Identify using Fido",
                "lastmodified": parse_date("2013-11-15T01:18:33+00:00"),
                "replacementdic": '{"%IDCommand%":"a8e45bc1-eb35-4545-885c-dd552f1fde9a"}',
                "choiceavailableatlink_id": "f09847c2-ee51-429a-9478-a860477f6b8d",
                "replaces_id": None,
                "pk": "0db6372b-f507-4db0-9993-e745044a69f9",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "No",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replacementdic": '{"%transcribe%": "False"}',
                "choiceavailableatlink_id": "7079be6d-3a25-41e6-a481-cee5f352fe6e",
                "replaces_id": None,
                "pk": "1170e555-cd4e-4b2f-a3d6-bfb09e8fcc53",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Skip File Identification",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "replacementdic": '{"%IDCommand%":"None"}',
                "choiceavailableatlink_id": "f09847c2-ee51-429a-9478-a860477f6b8d",
                "replaces_id": None,
                "pk": "1f77af0a-2f7a-468f-af8c-653a9e61ca4f",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Siegfried version 1.0.0 PUID runs Identify using Siegfried",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replacementdic": '{"%IDCommand%":"8cc792b4-362d-4002-8981-a4e808c04b24"}',
                "choiceavailableatlink_id": "087d27be-c719-47d8-9bbb-9a7d8b609c44",
                "replaces_id": None,
                "pk": "25a91595-37f0-4373-a89a-56a757353fb8",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Use existing data",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "replacementdic": '{"%IDCommand%":"None"}',
                "choiceavailableatlink_id": "7a024896-c4f7-4808-a240-44c87c762bc5",
                "replaces_id": None,
                "pk": "3c1faec7-7e1e-4cdd-b3bd-e2f05f4baa9b",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "5 - normal compression mode",
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
                "replacementdic": '{"%AIPCompressionLevel%":"5"}',
                "choiceavailableatlink_id": "01c651cb-c174-4ba4-b985-1d87a44d6754",
                "replaces_id": None,
                "pk": "414da421-b83f-4648-895f-a34840e3c3f5",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "7 - maximum compression",
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
                "replacementdic": '{"%AIPCompressionLevel%":"7"}',
                "choiceavailableatlink_id": "01c651cb-c174-4ba4-b985-1d87a44d6754",
                "replaces_id": None,
                "pk": "4e31f579-68bd-4be1-a10e-ec5411897121",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Archivists Toolkit Config",
                "lastmodified": parse_date("2013-03-23T03:25:00+00:00"),
                "replacementdic": '{"%host%":"localhost", "%port%":"3306", "%dbname%":"atk01", "%dbuser%":"ATUser", "%dbpass%":"", "%atuser%":"atkuser", "%restrictions%":"premis", "%object_type%":"", "%ead_actuate%":"onRequest", "%ead_show%":"new", "%use_statement%":"Image-Service","%uri_prefix%":"http:www.example.com/", "%access_conditions%":"", "%use_conditions%":""}',
                "choiceavailableatlink_id": "7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1",
                "replaces_id": None,
                "pk": "5395d1ea-a892-4029-b5a8-5264a17bbade",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Fido version 1 PUID runs Identify using Fido",
                "lastmodified": parse_date("2013-11-15T01:18:33+00:00"),
                "replacementdic": '{"%IDCommand%":"a8e45bc1-eb35-4545-885c-dd552f1fde9a"}',
                "choiceavailableatlink_id": "7a024896-c4f7-4808-a240-44c87c762bc5",
                "replaces_id": None,
                "pk": "56345ae4-08d1-42df-a2f9-9ba37689d9c3",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Yes",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replacementdic": '{"%transcribe%": "True"}',
                "choiceavailableatlink_id": "7079be6d-3a25-41e6-a481-cee5f352fe6e",
                "replaces_id": None,
                "pk": "5a9985d3-ce7e-4710-85c1-f74696770fa9",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Siegfried version 1.0.0 PUID runs Identify using Siegfried",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replacementdic": '{"%IDCommand%":"8cc792b4-362d-4002-8981-a4e808c04b24"}',
                "choiceavailableatlink_id": "7a024896-c4f7-4808-a240-44c87c762bc5",
                "replaces_id": None,
                "pk": "664cbde3-e658-4288-87db-bd28266d83f5",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "9 - ultra compression",
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
                "replacementdic": '{"%AIPCompressionLevel%":"9"}',
                "choiceavailableatlink_id": "01c651cb-c174-4ba4-b985-1d87a44d6754",
                "replaces_id": None,
                "pk": "6d52fd24-8c06-4c8e-997a-e427ba0acc36",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Fido version 1 PUID runs Identify using Fido",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replacementdic": '{"%IDCommand%":"a8e45bc1-eb35-4545-885c-dd552f1fde9a"}',
                "choiceavailableatlink_id": "087d27be-c719-47d8-9bbb-9a7d8b609c44",
                "replaces_id": None,
                "pk": "6f9bfd67-f598-400a-aa2e-12b2657962fc",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "File Extension version 0.1 file extension runs Identify by File Extension",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replacementdic": '{"%IDCommand%":"41efbe1b-3fc7-4b24-9290-d0fb5d0ea9e9"}',
                "choiceavailableatlink_id": "087d27be-c719-47d8-9bbb-9a7d8b609c44",
                "replaces_id": None,
                "pk": "724b17a2-668b-4ef6-9f3b-860d8dfcbb29",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "No",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replacementdic": '{"%DeletePackage%":"False"}',
                "choiceavailableatlink_id": "f19926dd-8fb5-4c79-8ade-c83f61f55b40",
                "replaces_id": None,
                "pk": "72e8443e-a8eb-49a8-ba5f-76d52f960bde",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Skip File Identification",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replacementdic": '{"%IDCommand%":"None"}',
                "choiceavailableatlink_id": "087d27be-c719-47d8-9bbb-9a7d8b609c44",
                "replaces_id": None,
                "pk": "782bbf56-e220-48b5-9eb6-6610583f2072",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Yes",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replacementdic": '{"%DeletePackage%":"True"}',
                "choiceavailableatlink_id": "f19926dd-8fb5-4c79-8ade-c83f61f55b40",
                "replaces_id": None,
                "pk": "85b1e45d-8f98-4cae-8336-72f40e12cbef",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "3 - fast compression mode",
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
                "replacementdic": '{"%AIPCompressionLevel%":"3"}',
                "choiceavailableatlink_id": "01c651cb-c174-4ba4-b985-1d87a44d6754",
                "replaces_id": None,
                "pk": "85b2243e-ff97-4ca8-80e8-3c6b0842b360",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "File Extension version 0.1 file extension runs Identify by File Extension",
                "lastmodified": parse_date("2013-11-15T01:18:33+00:00"),
                "replacementdic": '{"%IDCommand%":"41efbe1b-3fc7-4b24-9290-d0fb5d0ea9e9"}',
                "choiceavailableatlink_id": "7a024896-c4f7-4808-a240-44c87c762bc5",
                "replaces_id": None,
                "pk": "93a4d4ee-d974-4d81-8fc7-af135f1836d3",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "7z using bzip2",
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
                "replacementdic": '{"%AIPCompressionAlgorithm%":"7z-bzip2"}',
                "choiceavailableatlink_id": "01d64f58-8295-4b7b-9cab-8f1b153a504f",
                "replaces_id": None,
                "pk": "9475447c-9889-430c-9477-6287a9574c5b",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Siegfried version 1.0.0 PUID runs Identify using Siegfried",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "replacementdic": '{"%IDCommand%":"8cc792b4-362d-4002-8981-a4e808c04b24"}',
                "choiceavailableatlink_id": "f09847c2-ee51-429a-9478-a860477f6b8d",
                "replaces_id": None,
                "pk": "bed4eeb1-d654-4d97-b98d-40eb51d3d4bb",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "7z using lzma",
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
                "replacementdic": '{"%AIPCompressionAlgorithm%":"7z-lzma"}',
                "choiceavailableatlink_id": "01d64f58-8295-4b7b-9cab-8f1b153a504f",
                "replaces_id": None,
                "pk": "c96353b9-0d55-46cf-baa0-d7c3e180dd43",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Uncompressed",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "replacementdic": '{"%AIPCompressionAlgorithm%":"None-"}',
                "choiceavailableatlink_id": "01d64f58-8295-4b7b-9cab-8f1b153a504f",
                "replaces_id": None,
                "pk": "dc04c4c0-07ea-4796-b643-66d967ed33a4",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "File Extension version 0.1 file extension runs Identify by File Extension",
                "lastmodified": parse_date("2013-11-15T01:18:33+00:00"),
                "replacementdic": '{"%IDCommand%":"41efbe1b-3fc7-4b24-9290-d0fb5d0ea9e9"}',
                "choiceavailableatlink_id": "f09847c2-ee51-429a-9478-a860477f6b8d",
                "replaces_id": None,
                "pk": "e2dc96b2-eff5-432c-9e7c-66d7f02267da",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "1 - fastest mode",
                "lastmodified": parse_date("2012-10-02T00:25:08+00:00"),
                "replacementdic": '{"%AIPCompressionLevel%":"1"}',
                "choiceavailableatlink_id": "01c651cb-c174-4ba4-b985-1d87a44d6754",
                "replaces_id": None,
                "pk": "ecfad581-b007-4612-a0e0-fcc551f4057f",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)
            props = {
                "description": "Parallel bzip2",
                "lastmodified": parse_date("2013-08-20T00:25:08+00:00"),
                "replacementdic": '{"%AIPCompressionAlgorithm%":"pbzip2-"}',
                "choiceavailableatlink_id": "01d64f58-8295-4b7b-9cab-8f1b153a504f",
                "replaces_id": None,
                "pk": "f61b00a1-ef2e-4dc4-9391-111c6f42b9a7",
            }
            MicroServiceChoiceReplacementDic.objects.create(**props)

        with suppress_autotime(StandardTaskConfig, ["lastmodified"]):
            props = {
                "execute": "identifyFileFormat_v0.0",
                "filter_subdir": "objects/attachments",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%fileFormatIdentification.log",
                "arguments": '"%IDCommand%" "%relativeLocation%" "%fileUUID%"',
                "replaces_id": None,
                "pk": "02fd0952-4c9c-4da6-9ea3-a1409c87963d",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%fileFormatIdentification.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%processingDirectory%." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "037feb3c-f4d1-44dd-842e-c681793094df",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "bagit_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": 'create "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPDirectory%" "logs/" "objects/" "METS.%SIPUUID%.xml" "thumbnails/" "metadata/" --writer filesystem --payloadmanifestalgorithm "sha512"',
                "replaces_id": None,
                "pk": "045f84de-2669-4dbc-a31b-43a4954d0481",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createMETS_v2.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--amdSec --baseDirectoryPath "%SIPDirectory%" --baseDirectoryPathString "SIPDirectory" --fileGroupIdentifier "%SIPUUID%" --fileGroupType "sip_id" --xmlFile "%SIPDirectory%METS.%SIPUUID%.xml"',
                "replaces_id": None,
                "pk": "0aec05d4-7222-4c28-89f4-043d20a812cc",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%processingDirectory%%SIPName%-%SIPUUID%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "0b1177e8-8541-4293-a238-1783c793a7b1",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "setFilePermission_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '700 -R "%relativeLocation%"',
                "replaces_id": None,
                "pk": "0b17b446-11d4-45a8-9d0c-4297b8c8887c",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "updateSizeAndChecksum_v0.0",
                "filter_subdir": "objects/manualNormalization/preservation",
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "0bdecdc8-f5ef-48dd-8a89-f937d2b3f2f9",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "sanitizeSIPName_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%SIPnameCleanup.log",
                "arguments": '"%relativeLocation%" "%SIPUUID%" "%date%" "%sharedPath%" "%unitType%"',
                "replaces_id": None,
                "pk": "0c6990d8-ce1f-4093-803b-5ca6256119ca",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%rejectedDirectory%." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "11e6fcbe-3d7b-41cc-bfac-14dee9172b51",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "getContentdmCollectionList_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%ContentdmServer%"',
                "replaces_id": None,
                "pk": "13d2adfc-8cb8-4206-bf70-04f031436ca2",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "backlogUpdatingTransferFileIndex_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-04-05T23:08:30+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPName%" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "16ce41d9-7bfa-4167-bca8-49fe358f53ba",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/selectFormatIDToolIngest/."  "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "179373e8-a6b4-4274-a245-ca3f4b105396",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "assignFileUUIDs_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--transferUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "179c8ce5-2b83-4ae2-9653-971e868fe183",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "checkForSubmissionDocumenation_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%metadata/submissionDocumentation"',
                "replaces_id": None,
                "pk": "1aaa6e10-7907-4dea-a92a-dd0931eff226",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "validateFile_v1.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "1d3ef137-b060-4b33-b13f-25aa9346877b",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/system/autoRestructureForCompliance/." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "1e5e8ee2-8b93-4e8c-bb9c-0cb40d2728dd",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createMETS_v2.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--baseDirectoryPath "%SIPDirectory%" --baseDirectoryPathString "SIPDirectory" --fileGroupIdentifier "%SIPUUID%" --fileGroupType "sip_id" --xmlFile "%SIPDirectory%METS.%SIPUUID%.xml"',
                "replaces_id": None,
                "pk": "1f3f4e3b-2f5a-47a2-8d1c-27a6f1b94b95",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "storeAIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%DIPsStore%" "%watchDirectoryPath%uploadDIP/%SIPName%-%SIPUUID%" "%SIPUUID%" "%SIPName%" "DIP"',
                "replaces_id": None,
                "pk": "1f6f0cd1-acaf-40fb-bb2a-047383b8c977",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "%DIPsStore%",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": None,
                "replaces_id": None,
                "pk": "1fa7994d-9106-4d5a-892c-539af7e4ad8d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createDirectory_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-m 770 "%SIPDirectory%DIP/" "%SIPDirectory%DIP/objects/"',
                "replaces_id": None,
                "pk": "1fb68647-9db0-49ef-b6b7-3f775646ffbe",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copy_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%METS.%SIPUUID%.xml" "%SIPDirectory%DIP/METS.%SIPUUID%.xml"',
                "replaces_id": None,
                "pk": "20915fc5-594f-46d8-aa23-bfa45b622d17",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "fileToFolder_v1.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "21f89353-30ba-4601-8690-7c235630736f",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "extractMaildirAttachments_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%SIPUUID%" "%date%"',
                "replaces_id": None,
                "pk": "24272436-39b0-44f1-a0d6-c4bdca93ce88",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "normalize_v1.0",
                "filter_subdir": "objects/",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": 'thumbnail "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "service"',
                "replaces_id": None,
                "pk": "26309e7d-6435-4700-9171-131005f29cbb",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createEvent_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--eventType "unquarantine" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --eventDateTime "%jobCreatedDate%"',
                "replaces_id": None,
                "pk": "27dfc012-7cf4-449c-b0f0-bdd252c6f6e9",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "restructureBagAIPToSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "2808a160-82df-40a8-a6ca-330151584968",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "manualNormalizationIdentifyFilesIncluded_v0.0",
                "filter_subdir": "objects/manualNormalization/",
                "lastmodified": parse_date("2013-02-19T00:52:52+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%fileUUID%"',
                "replaces_id": None,
                "pk": "2843eba9-a9cf-462a-9cfc-f24ff35a22c0",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "restructureForComplianceSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "285a7b4d-155b-4f5b-ab35-daa6414303f9",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "checkForServiceDirectory_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--SIPDirectory "%SIPDirectory%" --serviceDirectory "objects/service/" --objectsDirectory "objects/" --SIPUUID "%SIPUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "290b358c-cfff-488c-a0b7-fffce037b2c5",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createTransferMetadata_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--sipUUID "%SIPUUID%" --xmlFile "%SIPDirectory%"metadata/transfer_metadata.xml',
                "replaces_id": None,
                "pk": "290c1989-4d8a-4b6e-80bd-9ff43439aeca",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "FITS_v0.0",
                "filter_subdir": "objects/attachments",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%SIPLogsDirectory%fileMeta/%fileUUID%.xml" "%date%" "%taskUUID%" "%fileUUID%" "%fileGrpUse%"',
                "replaces_id": None,
                "pk": "2936f695-190e-49e9-b7c6-6d1610f6b6de",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "assignFileUUIDs_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%FileUUIDsError.log",
                "arguments": '--transferUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "2ad612bc-1993-407e-9d66-a8ab9c1ebbd5",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%FileUUIDs.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "elasticSearchIndex_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "2c9fd8e4-a4f9-4aa6-b443-de8a9a49e396",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copyTransfersMetadataAndLogs_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--sipDirectory "%SIPDirectory%" --sipUUID "%SIPUUID%" --sharedPath "%sharedPath%"',
                "replaces_id": None,
                "pk": "2e9fb50f-2275-4253-87e5-47d2faf1031e",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveOrMerge_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%metadata/submissionDocumentation" "%SIPDirectory%objects/submissionDocumentation"',
                "replaces_id": None,
                "pk": "2f2a9b2b-bcdb-406b-a842-898d4bed02be",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "loadLabelsFromCSV_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPDirectory%metadata/file_labels.csv"',
                "replaces_id": None,
                "pk": "2f851d03-722f-4c49-8369-64f11542af89",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "archivematicaClamscan_v0.0",
                "filter_subdir": "objects/submissionDocumentation",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%clamAVScan.txt",
                "arguments": '"%fileUUID%" "%relativeLocation%" "%date%" "%taskUUID%"',
                "replaces_id": None,
                "pk": "2fdb8408-8bbb-45d1-846b-5e28bf220d5c",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "move_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%watchDirectoryPath%uploadedDIPs/."',
                "replaces_id": None,
                "pk": "302be9f9-af3f-45da-9305-02706d81b742",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createEvent_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--eventType "quarantine" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --eventDateTime "%jobCreatedDate%"',
                "replaces_id": None,
                "pk": "30ea6854-cf7a-42d4-b1e8-3c4ca0b82b7d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "setFilePermission_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": ' -R 750 "%relativeLocation%"',
                "replaces_id": None,
                "pk": "329fd50d-42fd-44e3-940e-7dc45d1a7727",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "normalize_v1.0",
                "filter_subdir": "objects/service",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": 'access "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "service"',
                "replaces_id": None,
                "pk": "339f300d-62d1-4a46-97c2-57244f54d32e",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "assignFileUUIDs_v0.0",
                "filter_subdir": "objects/metadata",
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%FileUUIDsError.log",
                "arguments": '--sipUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%" --use "metadata" --disable-update-filegrpuse',
                "replaces_id": None,
                "pk": "34966164-9800-4ae1-91eb-0a0c608d72d5",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%FileUUIDs.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "retryNormalizeRemoveNormalized_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-24T18:18:24+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--SIPDirectory "%SIPDirectory%" --SIPUUID "%SIPUUID%" --preservation --thumbnails',
                "replaces_id": None,
                "pk": "352fc88d-4228-4bc8-9c15-508683dabc58",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "archivematicaSetTransferType_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "TRIM"',
                "replaces_id": None,
                "pk": "353f326a-c599-4e66-8e1c-6262316e3729",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/approveNormalization/preservationAndAccess/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "3565ac77-780e-43d8-87c8-8a6bf04aab40",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copy_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%sharedPath%sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml" "%SIPDirectory%processingMCP.xml" -n',
                "replaces_id": None,
                "pk": "35ef1f2d-0124-422f-a84a-5e1d756b6bf2",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "archivematicaSetTransferType_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "Standard"',
                "replaces_id": None,
                "pk": "36ad6300-5a2c-491b-867b-c202541749e8",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/SIPCreation/SIPsUnderConstruction/." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "3843f87a-12c4-4526-904a-d900572c6483",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%watchDirectoryPath%quarantined/." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "39f8d4bf-2078-4415-b600-ce2865585aca",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "examineContents_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%SIPDirectory%" "%fileUUID%"',
                "replaces_id": None,
                "pk": "3a17cc3f-eabc-4b58-90e8-1df2a96cf182",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "trimVerifyChecksums_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-12-06T14:56:58+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%date%"',
                "replaces_id": None,
                "pk": "3b889d1d-bfe1-467f-8373-2c9366127093",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "normalize_v1.0",
                "filter_subdir": "objects/",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": 'access "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "original"',
                "replaces_id": None,
                "pk": "3c256437-6435-4307-9757-fbac5c07541c",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/selectFormatIDToolTransfer/."  "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "3e8f5b9e-b3a6-4782-a944-749de6ae234d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "elasticSearchAIPIndex_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%SIPUUID%" "%SIPName%"',
                "replaces_id": None,
                "pk": "40bf5b85-7cfd-47b0-9fbc-aed6c2cde8be",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%rejectedDirectory%." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "42aed4a4-8e2b-49f3-ba03-1a45c8baf52c",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/activeTransfers/standardTransfer/." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "4306315c-1f75-4eaf-8752-f08f67f9ada4",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "failedSIPCleanup_v1.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"reject" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "44758789-e1b5-4cfe-8011-442612da2d3b",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "jsonMetadataToCSV_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPDirectory%metadata/metadata.json"',
                "replaces_id": None,
                "pk": "44d3789b-10ad-4a9c-9984-c2fe503c8720",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "updateSizeAndChecksum_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "45df6fd4-9200-4ec7-bd31-ba0338c07806",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createPointerFile_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": "%SIPUUID% %SIPName% %AIPCompressionAlgorithm% %SIPDirectory% %AIPFilename%",
                "replaces_id": None,
                "pk": "45f11547-0df9-4856-b95a-3b1ff0c658bd",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createEvent_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2013-04-19T22:39:27+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--eventType "removal from backlog" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --eventDateTime "%jobCreatedDate%"',
                "replaces_id": None,
                "pk": "463e5d1c-d680-47fa-a27a-7efd4f702355",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%processingDirectory%." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "464a0a66-571b-4e6d-ba3a-4d182551a20f",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "removeUnneededFiles_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%removeUnneededFiles.log",
                "arguments": '"%relativeLocation%" "%fileUUID%"',
                "replaces_id": None,
                "pk": "49b803e3-8342-4098-bb3f-434e1eb5cfa8",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%removeUnneededFiles.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "test_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-d "%SIPDirectory%DIP"',
                "replaces_id": None,
                "pk": "49c816cd-b443-498f-9369-9274d060ddd3",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "characterizeFile_v0.0",
                "filter_subdir": "objects/submissionDocumentation",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "4b816807-10a7-447a-b42f-f34c8b8b3b76",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createSIPsfromTRIMTransferContainers_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-12-04T21:29:48+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPObjectsDirectory%" "%SIPName%" "%SIPUUID%" "%processingDirectory%" "%sharedPath%watchedDirectories/system/autoProcessSIP/" "%sharedPath%"',
                "replaces_id": None,
                "pk": "4cfac870-24ec-4a80-8bcb-7a38fd02e048",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "compressAIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": "%AIPCompressionAlgorithm% %AIPCompressionLevel% %SIPDirectory% %SIPName% %SIPUUID%",
                "replaces_id": None,
                "pk": "4dc2b1d2-acbb-47e7-88ca-570281f3236f",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "verifyPREMISChecksums_v0.0",
                "filter_subdir": "objects/",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--fileUUID "%fileUUID%" --filePath "%relativeLocation%" --date "%date%" --eventIdentifierUUID "%taskUUID%"',
                "replaces_id": None,
                "pk": "4f400b71-37be-49d0-8da3-125abac2bfd0",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "assignFileUUIDs_v0.0",
                "filter_subdir": "objects/manualNormalization/preservation",
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--sipUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%" --use "preservation"',
                "replaces_id": None,
                "pk": "4f47371b-a69b-4a8a-87b5-01e7eb1628c3",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "move_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%rejectedDirectory%."',
                "replaces_id": None,
                "pk": "4f7e2ed6-44b9-49a7-a1b7-bbfe58eadea8",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "archivematicaClamscan_v0.0",
                "filter_subdir": "objects/",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%fileUUID%" "%relativeLocation%" "%date%" "%taskUUID%"',
                "replaces_id": None,
                "pk": "51bce222-4157-427c-aca9-a670083db223",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "FITS_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%SIPLogsDirectory%fileMeta/%fileUUID%.xml" "%date%" "%taskUUID%" "%fileUUID%" "%fileGrpUse%"',
                "replaces_id": None,
                "pk": "51eab45d-6a24-4080-a1be-1e5c9405ce25",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createDirectory_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-m 770 "%SIPDirectory%DIP/" "%SIPDirectory%DIP/objects/"',
                "replaces_id": None,
                "pk": "5341d647-dc75-4f00-8e02-cef59c9862e5",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%failed/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "5401961e-773d-41fe-8d62-8c1262f6156b",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/selectNormalizationPath/." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "55eec242-68fa-4a1b-a3cd-458c087a017b",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "assignFileUUIDs_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%FileUUIDsError.log",
                "arguments": '--transferUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "57d42245-79e2-4c2d-8ed3-b596cce416db",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%FileUUIDs.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "sanitizeObjectNames_v0.0",
                "filter_subdir": "objects/metadata",
                "lastmodified": parse_date("2013-02-13T22:03:39+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%filenameCleanup.log",
                "arguments": '"%SIPDirectory%objects/metadata/" "%SIPUUID%" "%date%" "%taskUUID%" "SIPDirectory" "sip_id" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "58b192eb-0507-4a83-ae5a-f5e260634c2a",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%filenameCleanup.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "getAipStorageLocations_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": "DS",
                "replaces_id": None,
                "pk": "5a6d1a88-1c2f-40b5-adec-ad7e533340ff",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copyRecursive_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPObjectsDirectory%metadata/OCRfiles" "%SIPDirectory%DIP"',
                "replaces_id": None,
                "pk": "5c4f877f-b352-4977-b51b-53ebc437b08c",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "renameDIPFauxToOrigUUIDs_v0.0",
                "filter_subdir": "DIP/objects",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%relativeLocation%"',
                "replaces_id": None,
                "pk": "5f5ca409-8009-4732-a47c-1a35c72abefc",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "assignFileUUIDs_v0.0",
                "filter_subdir": "objects/submissionDocumentation",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%FileUUIDsError.log",
                "arguments": '--sipUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%" --use "submissionDocumentation"',
                "replaces_id": None,
                "pk": "614b1d56-9078-4cb0-80cc-1ea87b9fbbe8",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%FileUUIDs.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "setDirectoryPermissionsForAppraisal_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "6157fe87-26ff-49da-9899-d9036b21c4b0",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "normalize_v1.0",
                "filter_subdir": "objects/service",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": 'thumbnail "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "service"',
                "replaces_id": None,
                "pk": "62f21582-3925-47f6-b17e-90f46323b0d1",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "transcribeFile_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%taskUUID%" "%fileUUID%" "%transcribe%"',
                "replaces_id": None,
                "pk": "657bdd72-8f18-4477-8018-1f6c8df7ad85",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "removeUnneededFiles_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%fileUUID%"',
                "replaces_id": None,
                "pk": "66aa823d-3b72-4d13-9ad6-c5e6580857b8",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createEvent_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2013-04-19T22:39:27+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--eventType "placement in backlog" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --eventDateTime "%jobCreatedDate%"',
                "replaces_id": None,
                "pk": "6733ebdd-5c5f-4168-81a5-fe9a2fbc10c9",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copy_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%processingMCP.xml" "%SIPDirectory%DIP/processingMCP.xml"',
                "replaces_id": None,
                "pk": "67a7341c-276e-46bf-9021-0dcd5123687f",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "manualNormalizationMoveAccessFilesToDIP_v0.0",
                "filter_subdir": "objects/manualNormalization/access",
                "lastmodified": parse_date("2013-01-03T23:01:21+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--sipUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%"',
                "replaces_id": None,
                "pk": "68b1456e-9a59-48d8-96ef-92bc20fd7cab",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copy_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-R "%SIPDirectory%thumbnails" "%SIPDirectory%DIP/."',
                "replaces_id": None,
                "pk": "6abefa8d-387d-4f23-9978-bea7e6657a57",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "archivematicaSetTransferType_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "Dspace"',
                "replaces_id": None,
                "pk": "6c261f8f-17ce-4b58-86c2-ac3bfb0d2850",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "removeHiddenFilesAndDirectories_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "6c50d546-b0a4-4900-90ac-b4bcca802368",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "archivematicaClamscan_v0.0",
                "filter_subdir": "objects/metadata",
                "lastmodified": parse_date("2013-02-13T22:03:39+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%clamAVScan.txt",
                "arguments": '"%fileUUID%" "%relativeLocation%" "%date%" "%taskUUID%"',
                "replaces_id": None,
                "pk": "7316e6ed-1c1a-4bf6-a570-aead6b544e41",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createMETS_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--sipUUID "%SIPUUID%" --basePath "%SIPDirectory%" --xmlFile "%SIPDirectory%"metadata/submissionDocumentation/METS.xml --basePathString "transferDirectory" --fileGroupIdentifier "transfer_id"',
                "replaces_id": None,
                "pk": "73b71a30-1a26-4a07-8aa8-4dfb6e66a321",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createSIPfromTransferObjects_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPObjectsDirectory%" "%SIPName%" "%SIPUUID%" "%processingDirectory%" "%sharedPath%watchedDirectories/system/autoProcessSIP/" "%sharedPath%"',
                "replaces_id": None,
                "pk": "744000f8-8688-4080-9225-5547cd3f77cc",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "normalize_v1.0",
                "filter_subdir": "objects/",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": 'preservation "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "original"',
                "replaces_id": None,
                "pk": "7478e34b-da4b-479b-ad2e-5a3d4473364f",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "trimVerifyManifest_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-12-06T14:56:58+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%date%"',
                "replaces_id": None,
                "pk": "748eef17-84d3-4b84-9439-6756f0fc697d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/createTree/." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "760a9654-de3e-4ea7-bb76-eeff06acdf95",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createMETS_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--sipUUID "%SIPUUID%" --basePath "%SIPDirectory%" --xmlFile "%SIPDirectory%"metadata/submissionDocumentation/METS.xml --basePathString "transferDirectory" --fileGroupIdentifier "transfer_id"',
                "replaces_id": None,
                "pk": "761f00af-3d9a-4cb4-b7f1-259fccedb802",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createAIC_METS_v1.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "77e6b5ec-acf7-44d0-b250-32cbe014499d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "checkTransferDirectoryForObjects_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPObjectsDirectory%"',
                "replaces_id": None,
                "pk": "77ea8809-bc90-4e9d-a144-ad6d5ec59de9",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "FITS_v0.0",
                "filter_subdir": "objects/manualNormalization/preservation",
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%SIPLogsDirectory%fileMeta/%fileUUID%.xml" "%date%" "%taskUUID%" "%fileUUID%" "%fileGrpUse%"',
                "replaces_id": None,
                "pk": "79f3c95a-c1f1-463b-ab23-972ad859e136",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "archivematicaSetTransferType_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "Maildir"',
                "replaces_id": None,
                "pk": "7b455fc5-b201-4233-ba1c-e05be059b279",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "storeAIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%AIPsStore%" "%SIPDirectory%%AIPFilename%" "%SIPUUID%" "%SIPName%" "%SIPType%"',
                "replaces_id": None,
                "pk": "7df9e91b-282f-457f-b91a-ad6135f4337d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "verifyMD5_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%date%" "%taskUUID%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "7e47b56f-f9bc-4a10-9f63-1b165354d5f4",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "remove_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-R "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "805d7c5d-5ca9-4e66-9223-767eef79e0bd",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "sanitizeObjectNames_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%filenameCleanup.log",
                "arguments": '"%SIPObjectsDirectory%" "%SIPUUID%" "%date%" "%taskUUID%" "transferDirectory" "transfer_id" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "80759ad1-c79a-4c3b-b255-735c28a50f9e",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%filenameCleanup.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "emailFailReport_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-01-08T02:11:59+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--unitType "%unitType%" --unitIdentifier "%SIPUUID%" --unitName "%SIPName%" --date "%date%" --server "localhost"',
                "replaces_id": None,
                "pk": "807603e2-9914-46e0-9be4-73d4c073d2e8",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "verifySIPCompliance_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "80c4a6ed-abe4-4e02-8de8-55a50f559dab",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "indexAIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%SIPType%"',
                "replaces_id": None,
                "pk": "81f36881-9e54-4c75-a5b2-838cfb2ca228",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "identifyFileFormat_v0.0",
                "filter_subdir": "objects/submissionDocumentation",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%IDCommand%" "%relativeLocation%" "%fileUUID%"',
                "replaces_id": None,
                "pk": "82b08f3a-ca8f-4259-bd92-2fc1ab4f9974",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "getAipStorageLocations_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": "",
                "replaces_id": None,
                "pk": "857fb861-8aa1-45c0-95f5-c5af66764142",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "restructureForCompliance_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "862c0ce2-82e3-4336-bd20-d8bcb2d0fa6c",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "identifyFileFormat_v0.0",
                "filter_subdir": "objects/metadata/",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%IDCommand%" "%relativeLocation%" "%fileUUID%"',
                "replaces_id": None,
                "pk": "866037a3-d99e-4b9c-afb5-6de527a26e35",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/storeAIP/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "867f326b-66d1-498d-87e9-b6bcacf45abd",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/approveNormalization/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "87fb2e00-03b9-4890-a4d4-0e28f27e32c2",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "manualNormalizationRemoveMNDirectories_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-01-11T00:50:39+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "8971383b-5c38-4818-975f-e539bd993eb8",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "sanitizeObjectNames_v0.0",
                "filter_subdir": "objects/attachments",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%filenameCleanup.log",
                "arguments": '"%SIPObjectsDirectory%attachments/" "%SIPUUID%" "%date%" "%taskUUID%" "transferDirectory" "transfer_id" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "89b4d447-1cfc-4bbf-beaa-fb6477b00f70",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%filenameCleanup.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "checkForAccessDirectory_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--SIPDirectory "%SIPDirectory%" --accessDirectory "objects/access/" --objectsDirectory "objects/" --DIPDirectory "DIP" --SIPUUID "%SIPUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "8c50f6ab-7fa4-449e-bea8-483999568d85",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "test_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-d "%SIPDirectory%%AIPFilename%"',
                "replaces_id": None,
                "pk": "8c96ba0c-44e5-4ff8-8c73-0c567d52e2d4",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/extractPackagesChoice/."  "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "8daffda4-397c-4f56-85db-c4376bf6891e",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "extractContents_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%transferDirectory%" "%date%" "%taskUUID%" "%DeletePackage%"',
                "replaces_id": None,
                "pk": "8fad772e-7d2e-4cdd-89e6-7976152b6696",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%extractContents.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "normalize_v1.0",
                "filter_subdir": "objects/",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": 'thumbnail "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "original"',
                "replaces_id": None,
                "pk": "8fe4a2c3-d43c-41e4-aeb9-18e8f57c9ccf",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copySubmissionDocs_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%SIPName%-%SIPUUID%"',
                "replaces_id": None,
                "pk": "919dfbcd-b328-4a7e-9340-569a9d8859df",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "hasPackages_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": "%SIPUUID%",
                "replaces_id": None,
                "pk": "93039c6d-5ef7-4a95-bf07-5f89c8886808",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%watchDirectoryPath%quarantined/." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "94d0c52f-7594-4f59-9de5-b827d8d2a7f3",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "identifyFileFormat_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%fileFormatIdentification.log",
                "arguments": '"%IDCommand%" "%relativeLocation%" "%fileUUID%" --disable-reidentify',
                "replaces_id": None,
                "pk": "9c3680a5-91cb-413f-af4e-d39c3346f8db",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%fileFormatIdentification.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createDirectory_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-m 770 "%SIPDirectory%thumbnails/"',
                "replaces_id": None,
                "pk": "9c94b1d7-0563-4be9-9d64-058d0d1a03f4",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copy_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%transferBackups/." -R --preserve',
                "replaces_id": None,
                "pk": "9e302b2b-e28d-4a61-9be7-b94e16929560",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "extractBagTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%SIPUUID%" "%processingDirectory%"  %sharedPath%',
                "replaces_id": None,
                "pk": "9e6d6445-ccc6-427a-9407-a126699f98b4",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "identifyDspaceFiles_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%SIPDirectory%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "9ea66f4e-150b-4911-b68d-29fd5d372d2c",
                "filter_file_end": "mets.xml",
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveToBacklog_v1.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-04-05T23:08:30+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "9f25a366-f7a4-4b59-b219-2d5f259a1be9",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%processingDirectory%%SIPName%-%SIPUUID%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "9f473616-9094-45b0-aa3c-41d81a204d3b",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "removeFilesWithoutPresmisMetadata_v0.0",
                "filter_subdir": "objects/",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%removedFilesWithNoPremisMetadata.log",
                "arguments": '--fileUUID "%fileUUID%" --inputFile "%relativeLocation%" --sipDirectory "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "a32fc538-efd1-4be0-95a9-5ee40cbc70fd",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%removedFilesWithNoPremisMetadata.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "generateDIPFromAIPGenerateDIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPDirectory%" "%date%"',
                "replaces_id": None,
                "pk": "a51af5c7-0ed4-41c2-9142-fc9e43e83960",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createDirectory_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-m 770 "%SIPDirectory%DIP/" "%SIPDirectory%DIP/objects/"',
                "replaces_id": None,
                "pk": "a540bd68-27fa-47c3-9fc3-bd297999478d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copy_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%sharedPath%sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml" "%SIPDirectory%processingMCP.xml" -n',
                "replaces_id": None,
                "pk": "a56a116c-167b-45c5-b634-253696270a12",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "verifyChecksumsInFileSecOfDspaceMETSFiles_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%verifyChecksumsInFileSecOfDSpaceMETSFiles.log",
                "arguments": '"%relativeLocation%" "%date%" "%taskUUID%"',
                "replaces_id": None,
                "pk": "a5bb8df6-a8f0-4279-ac6d-873ec5cf37cd",
                "filter_file_end": "mets.xml",
                "stdout_file": "%SIPLogsDirectory%verifyChecksumsInFileSecOfDSpaceMETSFiles.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "upload-archivistsToolkit_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-03-23T04:42:00+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--host="%host%" --port="%port%" --dbname="%dbname%" --dbuser="%dbuser%" --dbpass="%dbpass%" --atuser="%atuser%" --dip_location="%SIPDirectory%" --dip_name="%SIPName%" --dip_uuid="%SIPUUID%" --restrictions="%restrictions%" --object_type="%object_type%" --ead_actuate="%ead_actuate%" --ead_show="%ead_show%" --use_statement="%use_statement%" --uri_prefix="%uri_prefix%" --access_conditions="%access_conditions%" --use_conditions="%use_conditions%"',
                "replaces_id": None,
                "pk": "a650921e-b754-4e61-9713-1457cf52e77d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "postStoreAIPHook_v1.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%"',
                "replaces_id": None,
                "pk": "ab404b46-9c54-4ca5-87f1-b69a8d2299a1",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/SIPCreation/completedTransfers/." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "ac562701-7672-4e1d-a318-b986b7c9007c",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "sanitizeObjectNames_v0.0",
                "filter_subdir": "objects/submissionDocumentation",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%filenameCleanup.log",
                "arguments": '"%SIPDirectory%objects/submissionDocumentation/" "%SIPUUID%" "%date%" "%taskUUID%" "SIPDirectory" "sip_id" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "ad65bf76-3491-4c3d-afb0-acc94ff28bee",
                "filter_file_end": None,
                "stdout_file": "%SIPLogsDirectory%filenameCleanup.log",
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "manualNormalizationCreateMetadataAndRestructure_v0.0",
                "filter_subdir": "objects/manualNormalization/preservation",
                "lastmodified": parse_date("2013-01-04T23:20:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%fileUUID%" "%relativeLocation%" "%date%"',
                "replaces_id": None,
                "pk": "adde688c-eb79-4036-a3b8-49aacc6a1b36",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:34+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%watchDirectoryPath%workFlowDecisions/compressionAIPDecisions/." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "ae090b70-0234-40ea-bc11-4be27370515f",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "verifyAIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPDirectory%%AIPFilename%"',
                "replaces_id": None,
                "pk": "ae6b87d8-59c8-4ffa-b417-ce93ab472e74",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/activeTransfers/Dspace/." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "b0aa4fd2-a837-4cb8-964d-7f905326aa85",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copyTransferSubmissionDocumentation_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPDirectory%metadata/submissionDocumentation" "%sharedPath%"',
                "replaces_id": None,
                "pk": "b3c14f6c-bc91-4349-9e8f-c02f7dac27b3",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%processingDirectory%%SIPName%-%SIPUUID%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "b3fed349-54c4-4142-8d86-925b3a9f4365",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/metadataReminder/."  "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "b6b39093-297e-4180-ad61-274bc9c5b451",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "setFilePermission_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '775 "%SIPDirectory%%AIPFilename%"',
                "replaces_id": None,
                "pk": "ba937c55-6148-4f45-a9ad-9697c0cf11ed",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "failedSIPCleanup_v1.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"fail" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "bad1aea1-404c-4a0a-8f0a-83f09bf99fd5",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createMETS_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--sipUUID "%SIPUUID%" --basePath "%SIPDirectory%" --xmlFile "%SIPDirectory%"metadata/submissionDocumentation/METS.xml --basePathString "transferDirectory" --fileGroupIdentifier "transfer_id"',
                "replaces_id": None,
                "pk": "bc7d263a-3798-4e5e-8098-8e273fd5890b",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "removeAIPFilesFromIndex_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-04-22T18:37:55+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": "%SIPUUID%",
                "replaces_id": None,
                "pk": "bfaf4e65-ab7b-11e2-bace-08002742f837",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "updateSizeAndChecksum_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "c06ecc19-8f75-4ccf-a549-22fde3972f28",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "isMaildirAIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "c0ae5130-0c17-4fc1-91c7-aa36265a21d5",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "retryNormalizeRemoveNormalized_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-24T18:18:52+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--SIPDirectory "%SIPDirectory%" --SIPUUID "%SIPUUID%" --preservation --thumbnails --access',
                "replaces_id": None,
                "pk": "c15de53e-a5b2-41a1-9eee-1a7b4dd5447a",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "restructureForCompliance_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "c3625e5b-2c8d-47d9-9f66-c37111d39a07",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "verifyMD5_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%date%" "%taskUUID%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "c64b1064-c856-4758-9891-152c7eabde7f",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%failed/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "c79f55f7-637c-4d32-a6fa-1d193e87c5fc",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "updateSizeAndChecksum_v0.0",
                "filter_subdir": "objects/submissionDocumentation",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "c8f93c3d-b078-428d-bd53-1b5789cde598",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2015-05-25T16:33:13+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%processingDirectory%." "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "cb6cd728-fe54-4a50-a6cc-1c5bd9fa1198",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "loadDublinCore_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%relativeLocation%metadata/dc.json"',
                "replaces_id": None,
                "pk": "cc8a1a4f-ccc8-4639-947e-01d0a5fddbb7",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "trimCreateRightsEntries_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-12-12T21:30:55+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%date%"',
                "replaces_id": None,
                "pk": "ccbaa53f-a486-4564-9b1a-a1b7bd5b1239",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveOrMerge_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%metadata" "%SIPDirectory%objects/metadata"',
                "replaces_id": None,
                "pk": "ce13677c-8ad4-4af0-92c8-ae8763f5094d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "verifyTransferCompliance_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "cf23dd75-d273-4c4e-8394-17622adf9bd6",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createDirectory_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-m 770 "%SIPDirectory%thumbnails/"',
                "replaces_id": None,
                "pk": "d079b090-bc81-4fc6-a9c5-a267ad5f69a9",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "remove_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-R "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"',
                "replaces_id": None,
                "pk": "d12b6b59-1f1c-47c2-b1a3-2bf898740eae",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "remove_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '-R "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"',
                "replaces_id": None,
                "pk": "d17b25c7-f83c-4862-904b-8074150b1395",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "characterizeFile_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "d6307888-f5ef-4828-80d6-fb6f707ae023",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "restructureForComplianceMaildir_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "db753cdd-c556-4f4b-aa09-e55eb637244d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "archivematicaClamscan_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%clamAVScan.txt",
                "arguments": '"%fileUUID%" "%relativeLocation%" "%date%" "%taskUUID%"',
                "replaces_id": None,
                "pk": "de58249f-9594-439d-8bea-536ce59d70a3",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveSIP_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/createDip/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "df526440-c08e-49f9-9b9e-c9aa3adedc72",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "verifyMD5_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%date%" "%taskUUID%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "df65573b-70b7-4cd4-b825-d5d5d8dd016d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "characterizeFile_v0.0",
                "filter_subdir": "objects/metadata/",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "e1e813dd-87ce-4468-a6de-35b787a02c7a",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "updateSizeAndChecksum_v0.0",
                "filter_subdir": "objects/metadata",
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "e377b543-d9b8-47a9-8297-4f95ca7600b3",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "trimRestructureForCompliance_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-11-30T19:55:46+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPName%" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "e3c09c46-6d05-4369-8c12-b5af6657c8f7",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "upload-contentDM_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--uuid="%SIPName%-%SIPUUID%" --collection "%ContentdmCollection%" --server "%ContentdmServer%" --username "%ContentdmUser%" --group "%ContentdmGroup%" --outputDir "%watchDirectoryPath%uploadedDIPs"',
                "replaces_id": None,
                "pk": "e469dc77-5712-4ef1-b053-06f3cd3c34be",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-11-20T23:05:52+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/quarantineTransfer/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "e7d2a9ac-b5c5-4b5c-9e57-a3c4e98035e6",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "verifyAndRestructureTransferBag_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": True,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%SIPUUID%"',
                "replaces_id": None,
                "pk": "e884b0db-8e51-4ea6-87f9-0420ee9ddf8f",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "copy_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%sharedPath%sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml" "%SIPDirectory%processingMCP.xml" -n',
                "replaces_id": None,
                "pk": "e887c51e-afb9-48b1-b416-502a2357e621",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "%ContentdmCollection%",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": None,
                "replaces_id": None,
                "pk": "e8fb137c-d499-45a8-a4aa-a884d81b9f3d",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "manualNormalizationCheckForManualNormalizationDirectory_v0.0",
                "filter_subdir": "objects/manualNormalization/preservation",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPName%" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "e8fc5fd0-fd55-4eb6-9170-92615fc9c344",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "%AIPsStore%",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": None,
                "replaces_id": None,
                "pk": "ebab9878-f42e-4451-a24a-ec709889a858",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "updateSizeAndChecksum_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"',
                "replaces_id": None,
                "pk": "ec54a7cb-690f-4dd6-ad2b-979ae9f8d25a",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "setMaildirFileGrpUseAndFileIDs_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "ec688528-d492-4de3-a176-b777734153b1",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "saveDublinCore_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%relativeLocation%metadata/dc.json"',
                "replaces_id": None,
                "pk": "ed6daadf-a594-4327-b85c-7219c5832369",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "move_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%DIP" "%sharedPath%watchedDirectories/uploadDIP/%SIPDirectoryBasename%"',
                "replaces_id": None,
                "pk": "ed8c70b7-1456-461c-981b-6b9c84896263",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "upload-qubit_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--url="http://localhost/ica-atom/index.php" \\\r\n--email="demo@example.com" \\\r\n--password="demo" \\\r\n--uuid="%SIPUUID%" \\\r\n--rsync-target="/tmp"',
                "replaces_id": None,
                "pk": "ee80b69b-6128-4e31-9db4-ef90aa677c87",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createDirectoryTree_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPObjectsDirectory%" -o "%SIPDirectory%metadata/directory_tree.txt"',
                "replaces_id": None,
                "pk": "f1a272df-bb3f-463e-95c0-6d2062bddfb8",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "sanitizeObjectNames_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPObjectsDirectory%" "%SIPUUID%" "%date%" "%taskUUID%" "transferDirectory" "transfer_id" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "f368a36d-2b27-4f08-b662-2828a96d189a",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-11-20T23:05:52+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/quarantineTransfer/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "f46bbd28-d533-4933-9b5c-4a5d32927ff3",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "moveTransfer_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/examineContentsChoice/."  "%SIPUUID%" "%sharedPath%"',
                "replaces_id": None,
                "pk": "f62e7309-61b3-4318-a770-ab40595bc7b8",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "identifyDspaceMETSFiles_v0.0",
                "filter_subdir": "objects",
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%fileUUID%"',
                "replaces_id": None,
                "pk": "f798426b-fbe9-4fd3-9180-8df776384b14",
                "filter_file_end": "mets.xml",
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "sanitizeSIPName_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": "%SIPLogsDirectory%SIPnameCleanup.log",
                "arguments": '"%relativeLocation%" "%SIPUUID%" "%date%" "%sharedPath%" "%unitType%"',
                "replaces_id": None,
                "pk": "f8af7e00-0ae4-47ab-9d22-92395ff053fc",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "restructureDIPForContentDMUpload_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--uuid="%SIPUUID%" --dipDir "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "f9f7793c-5a70-4ffd-9727-159c1070e4f5",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "archivematicaVerifyMets_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2012-10-02T00:25:01+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPDirectory%"',
                "replaces_id": None,
                "pk": "fa903131-1d84-4d2b-b498-67a48bc44fc8",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "determineAIPVersionKeyExitCode_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '"%SIPUUID%" "%SIPDirectory%"',
                "replaces_id": None,
                "pk": "feec6329-c21a-48b6-b142-cd3c810e846f",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)
            props = {
                "execute": "createProcessedStructmap_v0.0",
                "filter_subdir": None,
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "requires_output_lock": False,
                "filter_file_start": None,
                "stderr_file": None,
                "arguments": '--sipUUID "%SIPUUID%" --basePath "%SIPDirectory%" --xmlFile "%SIPDirectory%"metadata/submissionDocumentation/METS.xml --basePathString "transferDirectory" --fileGroupIdentifier "transfer_id"',
                "replaces_id": None,
                "pk": "fefd486c-e6ce-4229-ac3d-cf53e66f46cc",
                "filter_file_end": None,
                "stdout_file": None,
            }
            StandardTaskConfig.objects.create(**props)

        with suppress_autotime(TaskConfig, ["lastmodified"]):
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Characterize and extract metadata",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "d6307888-f5ef-4828-80d6-fb6f707ae023",
                "replaces_id": None,
                "pk": "00041f5a-42cd-4b77-a6d4-6ef0f376a817",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set SIP to normalize with MediaInfo file identification.",
                "lastmodified": parse_date("2012-10-23T19:41:24+00:00"),
                "tasktypepkreference": "be6dda53-ef28-42dd-8452-e11734d57a91",
                "replaces_id": None,
                "pk": "008e5b38-b19c-48af-896f-349aaf5eba9f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set file group use and fileIDs for maildir AIP",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "ec688528-d492-4de3-a176-b777734153b1",
                "replaces_id": None,
                "pk": "032347f1-c0fb-4c6c-96ba-886ac8ac636c",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Sanitize SIP name",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "0c6990d8-ce1f-4093-803b-5ca6256119ca",
                "replaces_id": None,
                "pk": "04c7e0fb-ec4e-4637-a7b7-41601d5523bd",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "Select upload type (Project Client or direct upload)",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "06334a2c-82ed-477b-af0b-9c9f3dcade99",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set specialized processing link",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "ed98984f-69c5-45de-8a32-2c9ecf65e83f",
                "replaces_id": None,
                "pk": "06b45b5d-d06b-49a8-8f15-e9458fbae842",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set SIP to normalize with FITS-file utility file identification.",
                "lastmodified": parse_date("2012-10-23T19:41:23+00:00"),
                "tasktypepkreference": "9329d1d8-03f9-4c5e-81ec-7010552d0a3e",
                "replaces_id": None,
                "pk": "0732af8f-d60b-43e0-8f75-8e89039a05a8",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Approve TRIM transfer",
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "07bf7432-fd9b-456e-9d17-5b387087723a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9",
                "description": "Find type to process as",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "07f6f419-d51f-4c69-bca6-a395adecbee0",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to examine contents",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "f62e7309-61b3-4318-a770-ab40595bc7b8",
                "replaces_id": None,
                "pk": "08fc82e7-bc15-4608-8171-50475e8071e2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Extract contents from compressed archives",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "8fad772e-7d2e-4cdd-89e6-7976152b6696",
                "replaces_id": None,
                "pk": "09f73737-f7ca-4ea2-9676-d369f390e650",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Is maildir AIP",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "c0ae5130-0c17-4fc1-91c7-aa36265a21d5",
                "replaces_id": None,
                "pk": "09fae382-37ac-45bb-9b53-d1608a44742c",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Relate manual normalized preservation files to the original files",
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "tasktypepkreference": "adde688c-eb79-4036-a3b8-49aacc6a1b36",
                "replaces_id": None,
                "pk": "0a521e24-b376-4a9c-9cd6-ce41e187179a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move transfer back to activeTransfers directory.",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "4306315c-1f75-4eaf-8752-f08f67f9ada4",
                "replaces_id": None,
                "pk": "0ae50158-a6e2-4663-a684-61d9a8384789",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Restructure TRIM for compliance",
                "lastmodified": parse_date("2012-11-30T19:55:47+00:00"),
                "tasktypepkreference": "e3c09c46-6d05-4369-8c12-b5af6657c8f7",
                "replaces_id": None,
                "pk": "0b90715c-50bc-4cb7-a390-771a7cc8180f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set files to identify",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "65263ec0-f3ff-4fd5-9cd3-cf6f51ef92c7",
                "replaces_id": None,
                "pk": "0bb3f551-1418-4b99-8094-05a43fcd9537",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Verify checksums in fileSec of DSpace METS files",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "a5bb8df6-a8f0-4279-ac6d-873ec5cf37cd",
                "replaces_id": None,
                "pk": "0c1664f2-dfcb-46d9-bd9e-5b604baef788",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "Select file format identification command",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "0c95f944-837f-4ada-a396-2c7a818806c6",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set resume link after processing metadata directory",
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "tasktypepkreference": "6b4600f2-6df6-42cb-b611-32938b46a9cf",
                "replaces_id": None,
                "pk": "0cbfd02e-94bc-4f0d-8e56-f7af6379c3ca",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Copy OCR data to DIP directory",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "5c4f877f-b352-4977-b51b-53ebc437b08c",
                "replaces_id": None,
                "pk": "102cd6b0-5d30-4e04-9b62-4e9f12d74549",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Attempt restructure for compliance?",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "108f7f4c-72f2-4ddb-910a-24f173d64fa7",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Index AIP",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "81f36881-9e54-4c75-a5b2-838cfb2ca228",
                "replaces_id": None,
                "pk": "134a1a94-22f0-4e67-be17-23a4c7178105",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Restructure from bag AIP to SIP directory format",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "2808a160-82df-40a8-a6ca-330151584968",
                "replaces_id": None,
                "pk": "135dd73d-845a-412b-b17e-23941a3d9f78",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Rename with transfer UUID",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "0b1177e8-8541-4293-a238-1783c793a7b1",
                "replaces_id": None,
                "pk": "13aaa76e-41db-4bff-8519-1f9ba8ca794f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Workflow decision - create transfer backup",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "1423da1c-e9f8-479c-9949-4238c59899ac",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Check for Access directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "8c50f6ab-7fa4-449e-bea8-483999568d85",
                "replaces_id": None,
                "pk": "143b4734-9c33-4f6e-9af0-2dc09cf9017a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Upload DIP",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "16b8cc42-68b6-4751-b497-3e3a64101bbb",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Sanitize Transfer name",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "f8af7e00-0ae4-47ab-9d22-92395ff053fc",
                "replaces_id": None,
                "pk": "16eaacad-e180-4be1-a13c-35ab070808a7",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to compressionAIPDecisions directory",
                "lastmodified": parse_date("2013-11-07T22:51:34+00:00"),
                "tasktypepkreference": "ae090b70-0234-40ea-bc11-4be27370515f",
                "replaces_id": None,
                "pk": "18dceb0a-dfb1-4b18-81a7-c6c5c578c5f1",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Approve standard transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "1b8b596f-b6ee-440f-b59c-5e8b39a2b46d",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign checksums and file sizes to objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "ec54a7cb-690f-4dd6-ad2b-979ae9f8d25a",
                "replaces_id": None,
                "pk": "1c7de28f-8f18-41c7-b03a-19f900d38f34",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Select format identification tool",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "1cd60a70-f78e-4625-9381-3863ff819f33",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to metadata reminder",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "b6b39093-297e-4180-ad61-274bc9c5b451",
                "replaces_id": None,
                "pk": "1cf09019-56a1-47eb-8fe0-9bbff158892d",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Remove files without linking information (failed normalization artifacts etc.)",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "a32fc538-efd1-4be0-95a9-5ee40cbc70fd",
                "replaces_id": None,
                "pk": "1e02e82a-2055-4f37-af3a-7dc606f9fd97",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Approve normalization",
                "lastmodified": parse_date("2012-10-02T07:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "2002fd7c-e238-4cca-a393-3c1c63a04915",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a19bfd9f-9989-4648-9351-013a10b382ed",
                "description": "Retrieve DIP Storage Locations",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "5a6d1a88-1c2f-40b5-adec-ad7e533340ff",
                "replaces_id": None,
                "pk": "21292501-0c12-4376-8fb1-413286060dc2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Normalize for thumbnails",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "tasktypepkreference": "26309e7d-6435-4700-9171-131005f29cbb",
                "replaces_id": None,
                "pk": "21f8f2b6-d285-490a-9276-bfa87a0a4fb9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Grant normalization options for no pre-existing DIP",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "f85bbe03-8aca-4211-99b7-ddb7dfb24da1",
                "replaces_id": None,
                "pk": "235c3727-b138-4e62-9265-c8f07761a5fa",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Generate METS.xml document",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "73b71a30-1a26-4a07-8aa8-4dfb6e66a321",
                "replaces_id": None,
                "pk": "23ad16a5-49fe-409d-98d9-f5a8de333f81",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Approve zipped bagit transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "243b67e9-4d0b-4c38-8fa4-0fa3df8a5b86",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Normalize service files for access",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "tasktypepkreference": "339f300d-62d1-4a46-97c2-57244f54d32e",
                "replaces_id": None,
                "pk": "246c34b0-b785-485f-971b-0ed9f82e1ae3",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set resume link - postApproveNormalizationLink",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "95fb93a5-ef63-4ceb-8572-c0ddf88ef3ea",
                "replaces_id": None,
                "pk": "24deba11-c719-4c64-a53c-e08c85663c40",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "01b748fe-2e9d-44e4-ae5d-113f74c9a0ba",
                "description": "Select destination collection",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "e8fb137c-d499-45a8-a4aa-a884d81b9f3d",
                "replaces_id": None,
                "pk": "24f82c1a-5de7-4b2a-8ac2-68a48edf252f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Remove files without linking information (failed normalization artifacts etc.)",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "a32fc538-efd1-4be0-95a9-5ee40cbc70fd",
                "replaces_id": None,
                "pk": "24fb04f6-95c1-4244-8f3d-65061418b188",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set transfer type: TRIM",
                "lastmodified": parse_date("2012-11-30T19:55:48+00:00"),
                "tasktypepkreference": "353f326a-c599-4e66-8e1c-6262316e3729",
                "replaces_id": None,
                "pk": "256e18ca-1bcd-4b14-b3d5-4efbad5663fc",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
                "description": "Resume after normalization file identification tool selected.",
                "lastmodified": parse_date("2012-10-23T19:41:22+00:00"),
                "tasktypepkreference": "003b52a6-f80a-409c-95f9-82dd770aa132",
                "replaces_id": None,
                "pk": "26ec68d5-8d33-4fe2-bc11-f06d80fb23e0",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Add processed structMap to METS.xml document",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "tasktypepkreference": "fefd486c-e6ce-4229-ac3d-cf53e66f46cc",
                "replaces_id": None,
                "pk": "275b3640-68a6-4c4e-adc1-888ea3fdfba5",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Copy submission documentation",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "tasktypepkreference": "919dfbcd-b328-4a7e-9340-569a9d8859df",
                "replaces_id": None,
                "pk": "2894f4ea-0d11-431f-a7de-c2f765bd55a6",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Identify file format",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "82b08f3a-ca8f-4259-bd92-2fc1ab4f9974",
                "replaces_id": None,
                "pk": "28e8e81c-3380-47f6-a973-e48f94104692",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Transcribe",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "657bdd72-8f18-4477-8018-1f6c8df7ad85",
                "replaces_id": None,
                "pk": "297e7ebd-71bb-41e9-b1b7-945b6a9f00c5",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set resume link - returnFromManualNormalized",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "ba7bafe6-7241-4ffe-a0b8-97ca3c68eac1",
                "replaces_id": None,
                "pk": "29937fd7-b482-4180-8037-1b57d71e903c",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Normalize",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "2bfd7cef-dcf8-4587-8043-2c69c612a6e3",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to approve normalization directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "87fb2e00-03b9-4890-a4d4-0e28f27e32c2",
                "replaces_id": None,
                "pk": "2d0b36bb-5c82-4ee5-b54c-f3e146ce370b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Cleanup rejected SIP",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "44758789-e1b5-4cfe-8011-442612da2d3b",
                "replaces_id": None,
                "pk": "2d8f4aa1-76ad-4c88-af81-f7f494780628",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Normalize for access",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "tasktypepkreference": "3c256437-6435-4307-9757-fbac5c07541c",
                "replaces_id": None,
                "pk": "2d9483ef-7dbb-4e7e-a9c6-76ed4de52da9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set quarantine permissions on transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "0b17b446-11d4-45a8-9d0c-4297b8c8887c",
                "replaces_id": None,
                "pk": "2e3c3f0f-069e-4ca1-b71b-93f4880a39b5",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "Select compression level",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "2f6947ee-5d92-416a-bade-b1079767e641",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set resume link after handling any manual normalized files",
                "lastmodified": parse_date("2013-01-03T02:10:40+00:00"),
                "tasktypepkreference": "fc9f30bf-7f6e-4e62-9f99-689c8dc2e4ec",
                "replaces_id": None,
                "pk": "31707047-5d61-4b9f-ba58-1353d6c38e0c",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Email fail report",
                "lastmodified": parse_date("2013-01-08T02:11:59+00:00"),
                "tasktypepkreference": "807603e2-9914-46e0-9be4-73d4c073d2e8",
                "replaces_id": None,
                "pk": "32b2600c-6907-4cb2-b18a-3986f0842219",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Remove empty manual normalization directories",
                "lastmodified": parse_date("2013-01-11T00:50:39+00:00"),
                "tasktypepkreference": "8971383b-5c38-4818-975f-e539bd993eb8",
                "replaces_id": None,
                "pk": "33c0dea0-da6c-4b8f-8038-6e95844eea95",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
                "description": "Check for specialized processing",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "49d853a9-646d-4e9f-b825-d1bcc3ba77f0",
                "replaces_id": None,
                "pk": "3649f0f4-2174-44af-aef9-31ebeddeb73b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9",
                "description": "Find options to normalize as",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "38324d67-8358-4679-902d-c20dcdfd548b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "3590f73d-5eb0-44a0-91a6-5b2db6655889",
                "description": "Designate to process as a standard transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "c691548f-0131-4bd5-864c-364b1f7feb7f",
                "replaces_id": None,
                "pk": "3875546f-9137-4c8f-9fcc-ed112eaa6414",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Process JSON metadata",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "tasktypepkreference": "44d3789b-10ad-4a9c-9984-c2fe503c8720",
                "replaces_id": None,
                "pk": "38b99e0c-7066-49c4-82ed-d77bd7f019a1",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to select file ID tool",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "tasktypepkreference": "3e8f5b9e-b3a6-4782-a944-749de6ae234d",
                "replaces_id": None,
                "pk": "38cea9c4-d75c-48f9-ba88-8052e9d3aa61",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to SIP creation directory for completed transfers",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "ac562701-7672-4e1d-a318-b986b7c9007c",
                "replaces_id": None,
                "pk": "39ac9ff8-d312-4033-a2c6-44219471abda",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to quarantine",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "94d0c52f-7594-4f59-9de5-b827d8d2a7f3",
                "replaces_id": None,
                "pk": "3ad0db9a-f57d-4664-ad34-947404dddd04",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Attempt restructure for compliance",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "862c0ce2-82e3-4336-bd20-d8bcb2d0fa6c",
                "replaces_id": None,
                "pk": "3ae4931e-886e-4e0a-9a85-9b047c9983ac",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Scan for viruses",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "de58249f-9594-439d-8bea-536ce59d70a3",
                "replaces_id": None,
                "pk": "3c002fb6-a511-461e-ad16-0d2c46649374",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set unquarantined file permissions on Transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "329fd50d-42fd-44e3-940e-7dc45d1a7727",
                "replaces_id": None,
                "pk": "3c04068f-20b8-4cbc-8166-c61faacb6628",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Generate METS.xml document",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "761f00af-3d9a-4cb4-b7f1-259fccedb802",
                "replaces_id": None,
                "pk": "3df5643c-2556-412f-a7ac-e2df95722dae",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to workFlowDecisions-quarantineSIP directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "e7d2a9ac-b5c5-4b5c-9e57-a3c4e98035e6",
                "replaces_id": None,
                "pk": "3e70f50d-5056-413e-a3d1-7b4b13d2b821",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Check if SIP is from Maildir Transfer",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "c0ae5130-0c17-4fc1-91c7-aa36265a21d5",
                "replaces_id": None,
                "pk": "3f3ab7ae-766e-4405-a05a-5ee9aea5042f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create thumbnails directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "9c94b1d7-0563-4be9-9d64-058d0d1a03f4",
                "replaces_id": None,
                "pk": "41e84764-e3a0-4aac-94e9-adbe996b087f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Characterize and extract metadata for attachments",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "2936f695-190e-49e9-b7c6-6d1610f6b6de",
                "replaces_id": None,
                "pk": "445d6579-ee40-47d0-af6c-e2f6799f450d",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set resume link after processing metadata directory",
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "tasktypepkreference": "771dd17a-02d1-403b-a761-c70cc9cc1d1a",
                "replaces_id": None,
                "pk": "449530ec-cd94-4d8c-aae0-3b7cd2e2d5f9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign file UUIDs to objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "57d42245-79e2-4c2d-8ed3-b596cce416db",
                "replaces_id": None,
                "pk": "450794b5-db3e-4557-8ab8-1abd77786429",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Create removal from backlog PREMIS events",
                "lastmodified": parse_date("2013-04-19T22:39:27+00:00"),
                "tasktypepkreference": "463e5d1c-d680-47fa-a27a-7efd4f702355",
                "replaces_id": None,
                "pk": "4554c5f9-52f9-440c-bc69-0f7be3651949",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set remove preservation and access normalized files to renormalize link.",
                "lastmodified": parse_date("2012-10-24T00:40:06+00:00"),
                "tasktypepkreference": "76eaa4d2-fd4f-4741-b68c-df5b96ba81d1",
                "replaces_id": None,
                "pk": "4745d0bb-910c-4c0d-8b81-82d7bfca7819",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to approve normalization directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "3565ac77-780e-43d8-87c8-8a6bf04aab40",
                "replaces_id": None,
                "pk": "4773c7e4-df8b-4928-acdd-1e9a3235b4b1",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Remove files without linking information (failed normalization artifacts etc.)",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "a32fc538-efd1-4be0-95a9-5ee40cbc70fd",
                "replaces_id": None,
                "pk": "483d0fc9-8f89-4699-b90b-7be250bab743",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to generate transfer tree",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "760a9654-de3e-4ea7-bb76-eeff06acdf95",
                "replaces_id": None,
                "pk": "48416179-7ae4-47cc-a0aa-f9847da08c63",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set transfer type: Standard",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "36ad6300-5a2c-491b-867b-c202541749e8",
                "replaces_id": None,
                "pk": "48929c19-c0c7-41b2-8bd0-552b22e2d86f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
                "description": "Load finished with manual normalized link",
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "tasktypepkreference": "65af383e-2153-4117-a2f9-bbe83358e54b",
                "replaces_id": None,
                "pk": "4ad0eecf-aa6e-4e3c-afe4-7e230cc671b2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Rename with transfer UUID",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "0b1177e8-8541-4293-a238-1783c793a7b1",
                "replaces_id": None,
                "pk": "4b07d97a-04c1-45ce-9d9b-36bc29054223",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Generate METS.xml document",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "bc7d263a-3798-4e5e-8098-8e273fd5890b",
                "replaces_id": None,
                "pk": "4b7e128d-193d-4b7a-8c46-b37842bac047",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "Transcribe SIP contents",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "4c64875e-9f31-4596-96d9-f99bc886bb24",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Rename DIP files with original UUIDs",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "5f5ca409-8009-4732-a47c-1a35c72abefc",
                "replaces_id": None,
                "pk": "4d2ed238-1b35-43fb-9753-fcac0ede8da4",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "Choose Config for Archivists Toolkit DIP Upload",
                "lastmodified": parse_date("2013-03-26T03:25:01+00:00"),
                "tasktypepkreference": "",
                "replaces_id": None,
                "pk": "4d56a90c-8d9f-498c-8331-cf469fcb3147",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to the store AIP approval directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "867f326b-66d1-498d-87e9-b6bcacf45abd",
                "replaces_id": None,
                "pk": "502a8bc4-88b1-41b0-8821-f8afd984036e",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify mets_structmap.xml compliance",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "fa903131-1d84-4d2b-b498-67a48bc44fc8",
                "replaces_id": None,
                "pk": "5044f7ec-96f9-4bf1-8540-671e543c2411",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
                "description": "Load post approve normalization link",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "7477907c-79ec-4d48-93ae-9e0cbbfd2b65",
                "replaces_id": None,
                "pk": "5092ff10-097b-4bac-a4d8-9b4766aaf40d",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Normalize for preservation",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "tasktypepkreference": "7478e34b-da4b-479b-ad2e-5a3d4473364f",
                "replaces_id": None,
                "pk": "51e31d21-3e92-4c9f-8fec-740f559285f2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Remove the processing directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "805d7c5d-5ca9-4e66-9223-767eef79e0bd",
                "replaces_id": None,
                "pk": "525db1a2-d494-4764-a900-7ff89d67c384",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify metadata directory checksums",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "c64b1064-c856-4758-9891-152c7eabde7f",
                "replaces_id": None,
                "pk": "528c8fe3-265f-45dd-b5c0-1a4ac0e15954",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify metadata directory checksums",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "df65573b-70b7-4cd4-b825-d5d5d8dd016d",
                "replaces_id": None,
                "pk": "52d646df-fd66-4157-b8aa-32786fef9481",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Validate formats",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "1d3ef137-b060-4b33-b13f-25aa9346877b",
                "replaces_id": None,
                "pk": "530a3999-422f-4abb-a6be-bd29cbed04a4",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Characterize and extract metadata on submission documentation",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "4b816807-10a7-447a-b42f-f34c8b8b3b76",
                "replaces_id": None,
                "pk": "530b3b90-b97a-4aaf-836f-3a889ad1d7d2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Scan for viruses on extracted files",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "51bce222-4157-427c-aca9-a670083db223",
                "replaces_id": None,
                "pk": "5370a0cb-da97-4983-868a-1376d7737af5",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create thumbnails directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "9c94b1d7-0563-4be9-9d64-058d0d1a03f4",
                "replaces_id": None,
                "pk": "547f95f6-3fcd-45e1-98b6-a8a7d9097373",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Remove hidden files and directories",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "6c50d546-b0a4-4900-90ac-b4bcca802368",
                "replaces_id": None,
                "pk": "549181ed-febe-487a-a036-ed6fdfa10a86",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Failed compliance. See output in dashboard. Transfer moved back to activeTransfers.",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "b0aa4fd2-a837-4cb8-964d-7f905326aa85",
                "replaces_id": None,
                "pk": "54a05ec3-a34f-4404-96ec-36b527445da9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "01b748fe-2e9d-44e4-ae5d-113f74c9a0ba",
                "description": "Store DIP location",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "1fa7994d-9106-4d5a-892c-539af7e4ad8d",
                "replaces_id": None,
                "pk": "55123c46-78c9-4b5d-ad92-2b1f3eb658af",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Removed bagged files",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "d12b6b59-1f1c-47c2-b1a3-2bf898740eae",
                "replaces_id": None,
                "pk": "55f0e6fa-834c-44f1-89f3-c912e79cea7d",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Sanitize extracted objects' file and directory names",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "f368a36d-2b27-4f08-b662-2828a96d189a",
                "replaces_id": None,
                "pk": "57bd2747-181e-4f06-b969-dc012c592982",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify metadata directory checksums",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "7e47b56f-f9bc-4a10-9f63-1b165354d5f4",
                "replaces_id": None,
                "pk": "57ef1f9f-3a1a-4cdc-90fd-39b024524618",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Normalize",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "58a83299-c854-49bb-9b16-bf97813edd8e",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to select normalization path.",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "55eec242-68fa-4a1b-a3cd-458c087a017b",
                "replaces_id": None,
                "pk": "596a7fd5-a86b-489c-a9c0-3aa64b836cec",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to the failed directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "5401961e-773d-41fe-8d62-8c1262f6156b",
                "replaces_id": None,
                "pk": "59ebdcec-eacc-4daf-978a-1b0d8652cd0c",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Check for Service directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "290b358c-cfff-488c-a0b7-fffce037b2c5",
                "replaces_id": None,
                "pk": "5a3d244e-c7a1-4cd9-b1a8-2890bf1f254c",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Assign file UUIDs",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "4c25f856-6639-42b5-9120-3ac166dce932",
                "replaces_id": None,
                "pk": "5a9fbb03-2434-4034-b20f-bcc6f971a8e5",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign checksums and file sizes to metadata ",
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "tasktypepkreference": "e377b543-d9b8-47a9-8297-4f95ca7600b3",
                "replaces_id": None,
                "pk": "5bd51fcb-6a68-4c5f-b99e-4fc36f51c40c",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create DIP directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "5341d647-dc75-4f00-8e02-cef59c9862e5",
                "replaces_id": None,
                "pk": "5c831a10-5d75-44ca-9741-06fdfc72052a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Identify manually normalized files",
                "lastmodified": parse_date("2013-02-19T00:52:52+00:00"),
                "tasktypepkreference": "2843eba9-a9cf-462a-9cfc-f24ff35a22c0",
                "replaces_id": None,
                "pk": "602e9b26-5839-4940-b230-0264bb873fe7",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Create unquarantine PREMIS events",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "27dfc012-7cf4-449c-b0f0-bdd252c6f6e9",
                "replaces_id": None,
                "pk": "62ba16c8-4a3f-4199-a48e-d557a90728e2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Grant normalization options for pre-existing DIP",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "1871a1a5-1937-4c4d-ab05-3b0c04a0bca1",
                "replaces_id": None,
                "pk": "63866950-cb04-4fe2-9b1d-9d5f1d22fc86",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign checksums and file sizes to objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "c06ecc19-8f75-4ccf-a549-22fde3972f28",
                "replaces_id": None,
                "pk": "6405c283-9eed-410d-92b1-ce7d938ef080",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Extract zipped bag transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "9e6d6445-ccc6-427a-9407-a126699f98b4",
                "replaces_id": None,
                "pk": "64a859be-f362-45d1-b9b4-4e15091f686f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Characterize and extract metadata on metadata files",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "e1e813dd-87ce-4468-a6de-35b787a02c7a",
                "replaces_id": None,
                "pk": "6511ac58-d68e-4381-9cf3-01f2637acb4c",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign file UUIDs to submission documentation",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "614b1d56-9078-4cb0-80cc-1ea87b9fbbe8",
                "replaces_id": None,
                "pk": "674e21f3-1c50-4185-8e5d-70b1ed4a7f3a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Run FITS on manual normalized preservation files",
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "tasktypepkreference": "79f3c95a-c1f1-463b-ab23-972ad859e136",
                "replaces_id": None,
                "pk": "68920df3-66aa-44fc-b221-710dbe97680a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify TRIM manifest",
                "lastmodified": parse_date("2012-11-30T19:55:47+00:00"),
                "tasktypepkreference": "748eef17-84d3-4b84-9439-6756f0fc697d",
                "replaces_id": None,
                "pk": "6a930177-66db-49d3-b95d-10c28ee47562",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create transfer backup (sharedDirectory/transferBackups)",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "9e302b2b-e28d-4a61-9be7-b94e16929560",
                "replaces_id": None,
                "pk": "6af5d804-de90-4c5b-bdba-e15a89e1a3db",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Rename with transfer UUID",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "b3fed349-54c4-4142-8d86-925b3a9f4365",
                "replaces_id": None,
                "pk": "6ed7ec07-5df1-470b-9a2e-a934cba8af26",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify TRIM checksums",
                "lastmodified": parse_date("2012-11-30T19:55:47+00:00"),
                "tasktypepkreference": "3b889d1d-bfe1-467f-8373-2c9366127093",
                "replaces_id": None,
                "pk": "6f5d5518-1ed4-49b8-9cd5-497d112c97e4",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Upload DIP",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "ee80b69b-6128-4e31-9db4-ef90aa677c87",
                "replaces_id": None,
                "pk": "7058a655-82f3-455c-9245-ad8e87e77a4f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign file UUIDs to objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "2ad612bc-1993-407e-9d66-a8ab9c1ebbd5",
                "replaces_id": None,
                "pk": "71d4f810-8fb6-45f7-9da2-f2dc07217076",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create thumbnails directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "d079b090-bc81-4fc6-a9c5-a267ad5f69a9",
                "replaces_id": None,
                "pk": "72dce7bc-054c-4d2d-8971-a480cb894bdc",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create SIP from transfer objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "744000f8-8688-4080-9225-5547cd3f77cc",
                "replaces_id": None,
                "pk": "73ad6c9d-8ea1-4667-ae7d-229656a49237",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move submission documentation into objects directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "2f2a9b2b-bcdb-406b-a842-898d4bed02be",
                "replaces_id": None,
                "pk": "73e12d44-ec3d-41a9-b138-80ec7e31ede5",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to processing directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "464a0a66-571b-4e6d-ba3a-4d182551a20f",
                "replaces_id": None,
                "pk": "74146fe4-365d-4f14-9aae-21eafa7d8393",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create AIC METS file",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "77e6b5ec-acf7-44d0-b250-32cbe014499d",
                "replaces_id": None,
                "pk": "741a09ee-8143-4216-8919-1046571af3e9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Examine contents?",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "7569eff6-401f-11e3-ae52-1c6f65d9668b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify mets_structmap.xml compliance",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "fa903131-1d84-4d2b-b498-67a48bc44fc8",
                "replaces_id": None,
                "pk": "757b5f8b-0fdf-4c5c-9cff-569d63a2d209",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a19bfd9f-9989-4648-9351-013a10b382ed",
                "description": "Retrieve AIP Storage Locations",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "857fb861-8aa1-45c0-95f5-c5af66764142",
                "replaces_id": None,
                "pk": "75e00332-24a3-4076-aed1-e3dc44379227",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set SIP to normalize with FITS-JHOVE file identification.",
                "lastmodified": parse_date("2012-10-23T19:41:23+00:00"),
                "tasktypepkreference": "face6ee9-42d5-46ff-be1b-a645594b2da8",
                "replaces_id": None,
                "pk": "76135f22-6dba-417f-9833-89ecbe9a3d99",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Rename with transfer UUID",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "0b1177e8-8541-4293-a238-1783c793a7b1",
                "replaces_id": None,
                "pk": "76729a40-dfa1-4c1a-adbf-01fb362324f5",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "3590f73d-5eb0-44a0-91a6-5b2db6655889",
                "description": "Designate to process as a DSpace transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "f1357379-0118-4f51-aa49-37aeb702b760",
                "replaces_id": None,
                "pk": "7872599e-ebfc-472b-bb11-524ff728679f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
                "description": "Determine which files to identify",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "97ddf0be-7b07-48b1-82f6-6a3b49edde2b",
                "replaces_id": None,
                "pk": "7a96f085-924b-483e-bc63-440323bce587",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Sanitize file and directory names in metadata",
                "lastmodified": parse_date("2013-02-13T22:03:39+00:00"),
                "tasktypepkreference": "58b192eb-0507-4a83-ae5a-f5e260634c2a",
                "replaces_id": None,
                "pk": "7b07859b-015e-4a17-8bbf-0d46f910d687",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Load labels from metadata/file_labels.csv",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "2f851d03-722f-4c49-8369-64f11542af89",
                "replaces_id": None,
                "pk": "7beb3689-02a7-4f56-a6d1-9c9399f06842",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to processing directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "037feb3c-f4d1-44dd-842e-c681793094df",
                "replaces_id": None,
                "pk": "7c02a87b-7113-4851-97cd-2cf9d3fc0010",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Cleanup failed SIP",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "bad1aea1-404c-4a0a-8f0a-83f09bf99fd5",
                "replaces_id": None,
                "pk": "7d5cb258-1ce2-4510-bd04-3517abbe8fbc",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Normalize service files for thumbnails",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "tasktypepkreference": "62f21582-3925-47f6-b17e-90f46323b0d1",
                "replaces_id": None,
                "pk": "7fd4e564-bed2-42c7-a186-7ae615381516",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set transfer type: DSpace",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "6c261f8f-17ce-4b58-86c2-ac3bfb0d2850",
                "replaces_id": None,
                "pk": "80ebef4c-0dd1-45eb-b993-1db56a077db8",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create transfer metadata XML",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "290c1989-4d8a-4b6e-80bd-9ff43439aeca",
                "replaces_id": None,
                "pk": "81304470-37ef-4abb-99d9-ca075a9f440e",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Identify DSpace mets files",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "f798426b-fbe9-4fd3-9180-8df776384b14",
                "replaces_id": None,
                "pk": "81d64862-a4f6-4e3f-b32e-47268d9eb9a3",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Approve AIC",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "81f2a21b-a7a0-44e4-a2f6-9a6cf742b052",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Remove bagged files",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "d17b25c7-f83c-4862-904b-8074150b1395",
                "replaces_id": None,
                "pk": "83755035-1dfd-4e25-9031-e1178be4bb84",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "3590f73d-5eb0-44a0-91a6-5b2db6655889",
                "description": "Designate to process as a standard transfer when unquarantined",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "1c460578-e696-4378-a5d1-63ee77dd18bc",
                "replaces_id": None,
                "pk": "851d679e-44db-485a-9b0e-2dfbdf80c791",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Remove unneeded files",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "66aa823d-3b72-4d13-9ad6-c5e6580857b8",
                "replaces_id": None,
                "pk": "85308c8b-b299-4453-bf40-9ac61d134015",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Identify file format",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "tasktypepkreference": "9c3680a5-91cb-413f-af4e-d39c3346f8db",
                "replaces_id": None,
                "pk": "8558d885-d6c2-4d74-af46-20da45487ae7",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Select format identification tool",
                "lastmodified": parse_date("2012-10-24T00:45:13+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "85a2ec9b-5a80-497b-af60-04926c0bf183",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Store DIP",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "1f6f0cd1-acaf-40fb-bb2a-047383b8c977",
                "replaces_id": None,
                "pk": "85ce72dd-627a-4d0d-b118-fdaedf8ed8e6",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Examine contents",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "3a17cc3f-eabc-4b58-90e8-1df2a96cf182",
                "replaces_id": None,
                "pk": "869c4c44-6e7d-4473-934d-80c7b95a8310",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "Delete package after extraction?",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "86a832aa-bd37-44e2-ba02-418fb82e34f1",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Scan for viruses in metadata",
                "lastmodified": parse_date("2013-02-13T22:03:39+00:00"),
                "tasktypepkreference": "7316e6ed-1c1a-4bf6-a570-aead6b544e41",
                "replaces_id": None,
                "pk": "8850aeff-8553-4ff1-ab31-99b5392a458b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "Select compression algorithm",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "8a291152-729c-42f2-ab2e-c53b9f357799",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to select file ID tool",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "tasktypepkreference": "179373e8-a6b4-4274-a245-ca3f4b105396",
                "replaces_id": None,
                "pk": "8b846431-5da9-4743-906d-2cdc4e777f8f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Check transfer directory for objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "77ea8809-bc90-4e9d-a144-ad6d5ec59de9",
                "replaces_id": None,
                "pk": "8cda5b7a-fb44-4a61-a865-6ad01af5a150",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Attempt restructure for compliance",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "285a7b4d-155b-4f5b-ab35-daa6414303f9",
                "replaces_id": None,
                "pk": "8e06349b-d4a3-420a-9a64-69553bd9a183",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Generate METS.xml document",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "1f3f4e3b-2f5a-47a2-8d1c-27a6f1b94b95",
                "replaces_id": None,
                "pk": "8ea17652-a136-4251-b460-d50b0c7090eb",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Copy preconfigured choice XML to DIP directory",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "tasktypepkreference": "67a7341c-276e-46bf-9021-0dcd5123687f",
                "replaces_id": None,
                "pk": "8ed6f0e4-cd5c-4c4b-bce0-e8949ea696cd",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9",
                "description": "Find branch to continue processing",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "8fa944df-1baf-4f89-8106-af013b5078f4",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Copy thumbnails to DIP directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "6abefa8d-387d-4f23-9978-bea7e6657a57",
                "replaces_id": None,
                "pk": "90e0993d-23d4-4d0c-8b7d-73717b58f20e",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify mets_structmap.xml compliance",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "fa903131-1d84-4d2b-b498-67a48bc44fc8",
                "replaces_id": None,
                "pk": "92a7b76c-7c5c-41b3-8657-ba4cdd9a8176",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create SIPs from TRIM transfer containers",
                "lastmodified": parse_date("2012-12-04T21:29:48+00:00"),
                "tasktypepkreference": "4cfac870-24ec-4a80-8bcb-7a38fd02e048",
                "replaces_id": None,
                "pk": "9371ba25-b600-485d-b2d8-cef2f39c35ed",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9",
                "description": "Find type to remove from quarantine as",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "93e01ed2-8d69-4a56-b686-3cf507931885",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Normalize",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "9413e636-1209-40b0-a735-74ec785ea14a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "Select target CONTENTdm server",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "94942d82-8b87-4be3-a338-158f893573cd",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Generate DIP",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "a51af5c7-0ed4-41c2-9142-fc9e43e83960",
                "replaces_id": None,
                "pk": "95d2ddff-a5e5-49cd-b4da-a5dd6fd3d2eb",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Create placement in backlog PREMIS events",
                "lastmodified": parse_date("2013-04-19T22:39:27+00:00"),
                "tasktypepkreference": "6733ebdd-5c5f-4168-81a5-fe9a2fbc10c9",
                "replaces_id": None,
                "pk": "9649186d-e5bd-4765-b285-3b0d8e83b105",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set transfer type: Maildir",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "7b455fc5-b201-4233-ba1c-e05be059b279",
                "replaces_id": None,
                "pk": "966f5720-3081-4697-9691-c19b86ffa569",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "Select file format identification command",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "97545cb5-3397-4934-9bc5-143b774e4fa7",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set remove preservation normalized files to renormalize link.",
                "lastmodified": parse_date("2012-10-24T00:40:07+00:00"),
                "tasktypepkreference": "b5808a0f-e842-4820-837a-832d18398ebb",
                "replaces_id": None,
                "pk": "97cc7629-c580-44db-8a41-68b6b2f23be4",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set files to normalize",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "f226ecea-ae91-42d5-b039-39a1125b1c30",
                "replaces_id": None,
                "pk": "99324102-ebe8-415d-b5d8-b299ab2f4703",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to the failed directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "c79f55f7-637c-4d32-a6fa-1d193e87c5fc",
                "replaces_id": None,
                "pk": "99712faf-6cd0-48d1-9c66-35a2033057cf",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Scan for viruses",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "de58249f-9594-439d-8bea-536ce59d70a3",
                "replaces_id": None,
                "pk": "9a0f8eac-6a9d-4b85-8049-74954fbd6594",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Generate DIP",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "ed8c70b7-1456-461c-981b-6b9c84896263",
                "replaces_id": None,
                "pk": "9a70cc32-2b0e-4763-a168-b81485fac366",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Sanitize object's file and directory names",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "80759ad1-c79a-4c3b-b255-735c28a50f9e",
                "replaces_id": None,
                "pk": "9dd95035-e11b-4438-a6c6-a03df302933c",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Reminder: add metadata if desired",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "5c149b3b-8fb3-431c-a577-11cf349cfb38",
                "replaces_id": None,
                "pk": "9f0388ae-155c-4cbf-9e15-525ff03e025f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to processing directory",
                "lastmodified": parse_date("2015-05-25T16:33:13+00:00"),
                "tasktypepkreference": "cb6cd728-fe54-4a50-a6cc-1c5bd9fa1198",
                "replaces_id": None,
                "pk": "9f7029af-739d-4ec1-840d-b92d1d30f0c7",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set unquarantined file permissions on Transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "329fd50d-42fd-44e3-940e-7dc45d1a7727",
                "replaces_id": None,
                "pk": "a0aecc16-3f78-4579-b6d4-a10df1f89a41",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create AIP Pointer File",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "45f11547-0df9-4856-b95a-3b1ff0c658bd",
                "replaces_id": None,
                "pk": "a20c5353-9e23-4b5d-bb34-09f2efe1e54d",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "3590f73d-5eb0-44a0-91a6-5b2db6655889",
                "description": "Designate to process as a standard transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "5dffcd9c-472d-44e0-ae4d-a30705cf80cd",
                "replaces_id": None,
                "pk": "a2e93146-a3ff-4e6c-ae3d-76ce49ca5e1b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Attempt restructure for compliance",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "db753cdd-c556-4f4b-aa09-e55eb637244d",
                "replaces_id": None,
                "pk": "a3c27d23-dbdf-47af-bf66-4238aa1a508f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Check if DIP should be generated",
                "lastmodified": parse_date("2013-02-13T22:03:37+00:00"),
                "tasktypepkreference": "49c816cd-b443-498f-9369-9274d060ddd3",
                "replaces_id": None,
                "pk": "a493f430-d905-4f68-a742-f4393a43e694",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Extract packages?",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "a4a4679f-72b8-48da-a202-e0a25fbc41bf",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to extract packages",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "8daffda4-397c-4f56-85db-c4376bf6891e",
                "replaces_id": None,
                "pk": "a68d7873-86cf-42d3-a95e-68b62f92f0f9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Include default Transfer processingMCP.xml",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "a56a116c-167b-45c5-b634-253696270a12",
                "replaces_id": None,
                "pk": "a71f40ec-77b2-4f13-91b6-da3d4a67a284",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Include default Transfer processingMCP.xml",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "a56a116c-167b-45c5-b634-253696270a12",
                "replaces_id": None,
                "pk": "a73b3690-ac75-4030-bb03-0c07576b649b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Identify file format of attachments",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "02fd0952-4c9c-4da6-9ea3-a1409c87963d",
                "replaces_id": None,
                "pk": "a75ee667-3a1c-4950-9194-e07d0e6bf545",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Normalize for thumbnails",
                "lastmodified": parse_date("2013-11-15T00:31:31+00:00"),
                "tasktypepkreference": "8fe4a2c3-d43c-41e4-aeb9-18e8f57c9ccf",
                "replaces_id": None,
                "pk": "a8489361-b731-4d4a-861d-f4da1767665f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Index transfer contents",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "2c9fd8e4-a4f9-4aa6-b443-de8a9a49e396",
                "replaces_id": None,
                "pk": "aa2e26b3-539e-4071-b54c-bcb89650d2d2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign checksums and file sizes to submissionDocumentation",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "c8f93c3d-b078-428d-bd53-1b5789cde598",
                "replaces_id": None,
                "pk": "abeaa79e-668b-4de0-b8cb-70f8ab8056b6",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Create quarantine PREMIS events",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "30ea6854-cf7a-42d4-b1e8-3c4ca0b82b7d",
                "replaces_id": None,
                "pk": "accc69f9-5b99-4565-92b5-114c7727d9e9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create thumbnails directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "9c94b1d7-0563-4be9-9d64-058d0d1a03f4",
                "replaces_id": None,
                "pk": "acd5e136-11ed-46fe-bf67-dc108f115d6b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Approve maildir transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "acf7bd62-1587-4bff-b640-5b34b7196386",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Remove from quarantine",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "ad1f1ae6-658f-4281-abc2-fe2f6c5d5e8e",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set file permissions",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "6157fe87-26ff-49da-9899-d9036b21c4b0",
                "replaces_id": None,
                "pk": "ad38cdea-d1da-4d06-a7e5-6f75da85a718",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Copy transfer submission documentation",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "b3c14f6c-bc91-4349-9e8f-c02f7dac27b3",
                "replaces_id": None,
                "pk": "b24525cd-e68d-4afd-b6ec-46192bbc117b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify transfer compliance",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "cf23dd75-d273-4c4e-8394-17622adf9bd6",
                "replaces_id": None,
                "pk": "b3875772-0f3b-4b03-b602-5304ded86397",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create thumbnails directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "d079b090-bc81-4fc6-a9c5-a267ad5f69a9",
                "replaces_id": None,
                "pk": "b3b86729-470f-4301-8861-d62574966747",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify AIP",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "ae6b87d8-59c8-4ffa-b417-ce93ab472e74",
                "replaces_id": None,
                "pk": "b57b3564-e271-4226-a5f9-2c7cf1661a83",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify bag, and restructure for compliance",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "e884b0db-8e51-4ea6-87f9-0420ee9ddf8f",
                "replaces_id": None,
                "pk": "b5970cbb-1af7-4f8c-b41d-a0febd482da4",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set SIP to normalize with FITS-ffident file identification.",
                "lastmodified": parse_date("2012-10-23T19:41:23+00:00"),
                "tasktypepkreference": "6c02936d-552a-415e-b3c1-6d681b01d1c6",
                "replaces_id": None,
                "pk": "b5e6340f-07f3-4ed1-aada-7a7f049b19b9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create transfer backup (sharedDirectory/transferBackups)",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "9e302b2b-e28d-4a61-9be7-b94e16929560",
                "replaces_id": None,
                "pk": "b6167c79-1770-4519-829c-fa01718756f4",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Characterize and extract metadata on objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "51eab45d-6a24-4080-a1be-1e5c9405ce25",
                "replaces_id": None,
                "pk": "b8403044-12a3-4b63-8399-772b9adace15",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set SIP to normalize with FITS-Droid file identification.",
                "lastmodified": parse_date("2012-10-23T19:41:22+00:00"),
                "tasktypepkreference": "4093954b-5e44-4fe9-9a47-14c82158a00d",
                "replaces_id": None,
                "pk": "b8c10f19-40c9-44c8-8b9f-6fab668513f5",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move metadata to objects directory",
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "tasktypepkreference": "ce13677c-8ad4-4af0-92c8-ae8763f5094d",
                "replaces_id": None,
                "pk": "ba0d0244-1526-4a99-ab65-43bfcd704e70",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Remove preservation normalized files to renormalize.",
                "lastmodified": parse_date("2012-10-24T00:40:07+00:00"),
                "tasktypepkreference": "352fc88d-4228-4bc8-9c15-508683dabc58",
                "replaces_id": None,
                "pk": "bacb088a-66ef-4590-b855-69f21dfdf87a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Compress AIP",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "4dc2b1d2-acbb-47e7-88ca-570281f3236f",
                "replaces_id": None,
                "pk": "bafe0ba3-420a-44f2-bb15-7509ef5c498c",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Upload to Archivists Toolkit",
                "lastmodified": parse_date("2013-03-26T03:25:01+00:00"),
                "tasktypepkreference": "a650921e-b754-4e61-9713-1457cf52e77d",
                "replaces_id": None,
                "pk": "bcff2873-f006-442e-9628-5eadbb8d0db7",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign checksums and file sizes to objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "ec54a7cb-690f-4dd6-ad2b-979ae9f8d25a",
                "replaces_id": None,
                "pk": "bd9769ba-4182-4dd4-ba85-cff24ea8733e",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to the rejected directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "11e6fcbe-3d7b-41cc-bfac-14dee9172b51",
                "replaces_id": None,
                "pk": "be4e3ee6-9be3-465f-93f0-77a4ccdfd1db",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Store AIP",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "bec683fa-f006-48a4-b298-d33b3b681cb2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Remove from quarantine",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "bf0835be-4c76-4508-a5a7-cdc4c9dae217",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign checksums and file sizes to objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "45df6fd4-9200-4ec7-bd31-ba0338c07806",
                "replaces_id": None,
                "pk": "bf5a1f0c-1b3e-4196-b51f-f6d509091346",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Store the AIP",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "7df9e91b-282f-457f-b91a-ad6135f4337d",
                "replaces_id": None,
                "pk": "bf71562c-bc87-4fd0-baa6-1d85ff751ea2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
                "description": "Load options to create SIPs",
                "lastmodified": parse_date("2012-12-06T17:43:25+00:00"),
                "tasktypepkreference": "11aef684-f2c7-494e-9763-277344e139bf",
                "replaces_id": None,
                "pk": "bf9b2fb7-43bd-4c3e-9dd0-7b6f43e6cb48",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Remove indexed AIP files",
                "lastmodified": parse_date("2013-04-22T18:37:56+00:00"),
                "tasktypepkreference": "bfaf4e65-ab7b-11e2-bace-08002742f837",
                "replaces_id": None,
                "pk": "bfb30b76-ab7b-11e2-bace-08002742f837",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Prepare AIP",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "045f84de-2669-4dbc-a31b-43a4954d0481",
                "replaces_id": None,
                "pk": "c075014f-4051-441a-b16b-3083d5c264c5",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Copy transfers metadata and logs",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "2e9fb50f-2275-4253-87e5-47d2faf1031e",
                "replaces_id": None,
                "pk": "c1bd4921-c446-4ff9-bb34-fcd155b8132a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Sanitize extracted objects' file and directory names",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "89b4d447-1cfc-4bbf-beaa-fb6477b00f70",
                "replaces_id": None,
                "pk": "c2c7edcc-0e65-4df7-812f-a2ee5b5d52b6",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Move access files to DIP",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "tasktypepkreference": "68b1456e-9a59-48d8-96ef-92bc20fd7cab",
                "replaces_id": None,
                "pk": "c307d6bd-cb81-46a1-89f1-bb02a43e0a3a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create DIP directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "1fb68647-9db0-49ef-b6b7-3f775646ffbe",
                "replaces_id": None,
                "pk": "c310a18a-1659-45d0-845e-06eb3321512f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create DIP directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "a540bd68-27fa-47c3-9fc3-bd297999478d",
                "replaces_id": None,
                "pk": "c3e3f03d-c104-48c3-8c64-4290459965f4",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Approve SIP Creation",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "c409f2b0-bcb7-49ad-a048-a217811ca9b6",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Create DIP from AIP",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "c450501a-251f-4de7-acde-91c47cf62e36",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
                "description": "Load post approve normalization link",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "e076e08f-5f14-4fc3-93d0-1e80ca727f34",
                "replaces_id": None,
                "pk": "c4b2e8ce-fe02-45d4-9b0f-b163bffcc05f",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Generate METS.xml document",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "0aec05d4-7222-4c28-89f4-043d20a812cc",
                "replaces_id": None,
                "pk": "c52736fa-2bc5-4142-a111-8b13751ed067",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Upload DIP to CONTENTdm",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "e469dc77-5712-4ef1-b053-06f3cd3c34be",
                "replaces_id": None,
                "pk": "c5d7e646-01b1-4d4a-9e38-b89d97e77e33",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to workFlowDecisions-createDip directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "df526440-c08e-49f9-9b9e-c9aa3adedc72",
                "replaces_id": None,
                "pk": "c5e80ef1-aa90-45b2-beb4-c42652acf3e7",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "3590f73d-5eb0-44a0-91a6-5b2db6655889",
                "description": "Designate to process as a standard transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "5057b0ce-a7f9-48c4-a7e9-65a7d88bb4ca",
                "replaces_id": None,
                "pk": "c6f9f99a-0b60-438f-9a8d-35d4989db2bb",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Extract attachments",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "24272436-39b0-44f1-a0d6-c4bdca93ce88",
                "replaces_id": None,
                "pk": "c74dfa47-9a6d-4a12-bffe-bf610ab75db9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set SIP to normalize with FITS-FITS file identification.",
                "lastmodified": parse_date("2012-10-23T19:41:24+00:00"),
                "tasktypepkreference": "471ff5ad-1fd3-4540-9245-360cc8c9b389",
                "replaces_id": None,
                "pk": "c87ec738-b679-4d8e-8324-73038ccf0dfd",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set resume link after handling any manual normalized files",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "tasktypepkreference": "5035632e-7879-4ece-bf43-2fc253026ff5",
                "replaces_id": None,
                "pk": "caaa29bc-a2b6-487b-abff-c3031a0e147a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Create quarantine PREMIS events",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "30ea6854-cf7a-42d4-b1e8-3c4ca0b82b7d",
                "replaces_id": None,
                "pk": "cac32b11-820c-4d17-8c7f-4e71fc0be68a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Determine if transfer still contains packages",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "tasktypepkreference": "93039c6d-5ef7-4a95-bf07-5f89c8886808",
                "replaces_id": None,
                "pk": "cadd5e12-82b2-43ec-813e-85cd42b2d511",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Determine processing path for this AIP version",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "feec6329-c21a-48b6-b142-cd3c810e846f",
                "replaces_id": None,
                "pk": "cd53e17c-1dd1-4e78-9086-e6e013a64536",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set re-normalize link",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "c26b2859-7a96-462f-880a-0cd8d1b0ac32",
                "replaces_id": None,
                "pk": "ce48a9f5-4513-49e2-83db-52b01234705b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
                "description": "Determine what to remove to re-normalize.",
                "lastmodified": parse_date("2012-10-24T17:04:11+00:00"),
                "tasktypepkreference": "e56e168e-d339-45b4-bc2a-a3eb24390f0f",
                "replaces_id": None,
                "pk": "ce52ace2-68fc-4bfb-8444-f32ec8c01783",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Check for manual normalized files",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "tasktypepkreference": "e8fc5fd0-fd55-4eb6-9170-92615fc9c344",
                "replaces_id": None,
                "pk": "ce57ffbc-abd9-43dc-a09b-e888397488f2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Include default Transfer processingMCP.xml",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "a56a116c-167b-45c5-b634-253696270a12",
                "replaces_id": None,
                "pk": "cfc7f6be-3984-4727-a71a-02ce27bef791",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Failed compliance.",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "1e5e8ee2-8b93-4e8c-bb9c-0cb40d2728dd",
                "replaces_id": None,
                "pk": "d1004e1d-f938-4c68-ba70-0e0ae508cbbe",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Identify file format of metadata files",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "866037a3-d99e-4b9c-afb5-6de527a26e35",
                "replaces_id": None,
                "pk": "d1f630dc-1082-4ad6-95b7-af36d2e2cf46",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Copy METS to DIP directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "20915fc5-594f-46d8-aa23-bfa45b622d17",
                "replaces_id": None,
                "pk": "d49684b1-badd-4802-b54e-06eb6b329140",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Rename SIP directory with SIP UUID",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "9f473616-9094-45b0-aa3c-41d81a204d3b",
                "replaces_id": None,
                "pk": "d61bb906-feff-4d6f-9e6c-a3f077f46b21",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Updating transfer file index",
                "lastmodified": parse_date("2013-04-05T23:08:30+00:00"),
                "tasktypepkreference": "16ce41d9-7bfa-4167-bca8-49fe358f53ba",
                "replaces_id": None,
                "pk": "d6a0dec1-63e7-4c7c-b4c0-e68f0afcedd3",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Index AIP contents",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "40bf5b85-7cfd-47b0-9fbc-aed6c2cde8be",
                "replaces_id": None,
                "pk": "d7542890-281f-4cdb-a64c-4b6bdd88c4b8",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Remove files without linking information (failed normalization artifacts etc.)",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "a32fc538-efd1-4be0-95a9-5ee40cbc70fd",
                "replaces_id": None,
                "pk": "d7a2bfbe-3f4d-45f7-87c6-f5c3c98961cd",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Restructure DIP for CONTENTdm upload",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "f9f7793c-5a70-4ffd-9727-159c1070e4f5",
                "replaces_id": None,
                "pk": "d7f13903-55a0-4a1c-87fa-9b75b14dccb4",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Determine if transfer contains packages",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "93039c6d-5ef7-4a95-bf07-5f89c8886808",
                "replaces_id": None,
                "pk": "d9ce0690-a8f9-40dc-a8b5-b021f578f8ff",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Check if file or folder",
                "lastmodified": parse_date("2015-05-25T16:33:14+00:00"),
                "tasktypepkreference": "21f89353-30ba-4601-8690-7c235630736f",
                "replaces_id": None,
                "pk": "d9ebceed-2cfb-462b-b130-48fecdf55bbf",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Sanitize object's file and directory names",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "89b4d447-1cfc-4bbf-beaa-fb6477b00f70",
                "replaces_id": None,
                "pk": "da756a4e-9d8b-4992-a219-2a7fd1edf2bb",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign file UUIDs to metadata",
                "lastmodified": parse_date("2013-02-13T22:03:40+00:00"),
                "tasktypepkreference": "34966164-9800-4ae1-91eb-0a0c608d72d5",
                "replaces_id": None,
                "pk": "dc2994f2-6de6-4c46-81f7-54676c5054aa",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set quarantine permissions on transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "0b17b446-11d4-45a8-9d0c-4297b8c8887c",
                "replaces_id": None,
                "pk": "dde51fc1-af7d-4923-ad6a-06e670447a2a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Attempt restructure for compliance",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "c3625e5b-2c8d-47d9-9f66-c37111d39a07",
                "replaces_id": None,
                "pk": "dde8c13d-330e-458b-9d53-0937370695fa",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Workflow decision - send transfer to quarantine",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "de195451-989e-48fe-ad0c-3ff2265b3410",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign checksums to manual normalized preservation files",
                "lastmodified": parse_date("2013-01-03T02:10:38+00:00"),
                "tasktypepkreference": "0bdecdc8-f5ef-48dd-8a89-f937d2b3f2f9",
                "replaces_id": None,
                "pk": "ded09ddd-2deb-4d62-bfe3-84703f60c522",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Create unquarantine PREMIS events",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "27dfc012-7cf4-449c-b0f0-bdd252c6f6e9",
                "replaces_id": None,
                "pk": "dee46f53-8afb-4aec-820e-d495bcbeaf20",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Approve bagit transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "df1c53e4-1b69-441e-bdc9-6d08c3b47c9b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Include default Transfer processingMCP.xml",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "35ef1f2d-0124-422f-a84a-5e1d756b6bf2",
                "replaces_id": None,
                "pk": "df51d25b-6a63-4e7a-b164-77b929dd2f31",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Failed compliance. See output in dashboard. SIP moved back to SIPsUnderConstruction",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "3843f87a-12c4-4526-904a-d900572c6483",
                "replaces_id": None,
                "pk": "e18e0c3a-dffb-42d2-9bfa-ea6c61328e28",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to the rejected directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "42aed4a4-8e2b-49f3-ba03-1a45c8baf52c",
                "replaces_id": None,
                "pk": "e20ea90b-fa16-4576-8647-199ecde0d511",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Approve normalization",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "e211ae41-bf9d-4f34-8b58-9a0dcc0bebe2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set resume link after tool selected.",
                "lastmodified": parse_date("2012-10-23T19:41:25+00:00"),
                "tasktypepkreference": "1871a1a5-1937-4c4d-ab05-3b0c04a0bca1",
                "replaces_id": None,
                "pk": "e476ac7e-d3e8-43fa-bb51-5a9cf42b2713",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to the uploadedDIPs directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "302be9f9-af3f-45da-9305-02706d81b742",
                "replaces_id": None,
                "pk": "e485f0f4-7d44-45c6-a0d2-bba4b2abd0d0",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Serialize Dublin Core metadata to disk",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "ed6daadf-a594-4327-b85c-7219c5832369",
                "replaces_id": None,
                "pk": "e5789749-00df-4b6c-af12-47eeabc8926a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign file UUIDs to objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "2ad612bc-1993-407e-9d66-a8ab9c1ebbd5",
                "replaces_id": None,
                "pk": "e601b1e3-a957-487f-8cbe-54160070574d",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set resume link after tool selected.",
                "lastmodified": parse_date("2012-10-23T19:41:25+00:00"),
                "tasktypepkreference": "f85bbe03-8aca-4211-99b7-ddb7dfb24da1",
                "replaces_id": None,
                "pk": "e62e4b85-e3f1-4550-8e40-3939e6497e92",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Identify DSpace text files",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "9ea66f4e-150b-4911-b68d-29fd5d372d2c",
                "replaces_id": None,
                "pk": "e6591da1-abfa-4bf2-abeb-cc0791ba5284",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify SIP compliance",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "80c4a6ed-abe4-4e02-8de8-55a50f559dab",
                "replaces_id": None,
                "pk": "e82c3c69-3799-46fd-afc1-f479f960a362",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to workFlowDecisions-createTransferBackup directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "f46bbd28-d533-4933-9b5c-4a5d32927ff3",
                "replaces_id": None,
                "pk": "e9f57845-4609-4e0a-a573-4b488d8a4aeb",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to the rejected directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "4f7e2ed6-44b9-49a7-a1b7-bbfe58eadea8",
                "replaces_id": None,
                "pk": "ea331cfb-d4f2-40c0-98b5-34d21ee6ad3e",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create thumbnails directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "9c94b1d7-0563-4be9-9d64-058d0d1a03f4",
                "replaces_id": None,
                "pk": "ea463bfd-5fa2-4936-b8c3-1ce3b74303cf",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set TRIM options to create SIPs",
                "lastmodified": parse_date("2012-12-06T19:01:04+00:00"),
                "tasktypepkreference": "6adccf2b-1c91-448b-bf0f-56414ee237ac",
                "replaces_id": None,
                "pk": "eb14ba91-20cb-4b0e-ab5d-c30bfea4dbc8",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set resume link",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "tasktypepkreference": "d8e2c7b2-5452-4c26-b57a-04caafe9f95c",
                "replaces_id": None,
                "pk": "ec503c22-1f4d-442f-b546-f90c9a9e5c86",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Save directory tree",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "f1a272df-bb3f-463e-95c0-6d2062bddfb8",
                "replaces_id": None,
                "pk": "ede67763-2a12-4e8f-8c36-e266d3f05c6b",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Check if AIP is a file or directory",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "8c96ba0c-44e5-4ff8-8c73-0c567d52e2d4",
                "replaces_id": None,
                "pk": "ee00a5c7-a69c-46cf-a5e0-a9e2f18e563e",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Verify checksums generated on ingest",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "4f400b71-37be-49d0-8da3-125abac2bfd0",
                "replaces_id": None,
                "pk": "ef024cf9-1737-4161-b48a-13b4a8abddcd",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Remove cache files",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "49b803e3-8342-4098-bb3f-434e1eb5cfa8",
                "replaces_id": None,
                "pk": "ef0bb0cf-28d5-4687-a13d-2377341371b5",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Load Dublin Core metadata from disk",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "cc8a1a4f-ccc8-4639-947e-01d0a5fddbb7",
                "replaces_id": None,
                "pk": "efb7bf8e-4624-4b52-bf90-e3d389099fd9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Clean up after storing AIP",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "ab404b46-9c54-4ca5-87f1-b69a8d2299a1",
                "replaces_id": None,
                "pk": "f09c1aa1-8a5d-49d1-ba60-2866e026eed9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Process transfer JSON metadata",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": "44d3789b-10ad-4a9c-9984-c2fe503c8720",
                "replaces_id": None,
                "pk": "f0e49772-3e2b-480d-8c06-023efc670dcd",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move transfer to backlog",
                "lastmodified": parse_date("2013-04-05T23:08:30+00:00"),
                "tasktypepkreference": "9f25a366-f7a4-4b59-b219-2d5f259a1be9",
                "replaces_id": None,
                "pk": "f1586bd7-f550-4588-9f45-07a212db7994",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Generate transfer structure report",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "f1ebd62a-fbf3-4790-88e8-4a3abec4ba00",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Create SIP(s)",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "f1f0409b-d4f8-419a-b625-218dc1abd335",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Sanitize file and directory names in submission documentation",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "ad65bf76-3491-4c3d-afb0-acc94ff28bee",
                "replaces_id": None,
                "pk": "f23a22b8-a3b0-440b-bf4e-fb6e8e6e6b14",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Workflow decision - send transfer to quarantine",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "f3567a6d-8a45-4174-b302-a629cdbfbe92",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create thumbnails directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "9c94b1d7-0563-4be9-9d64-058d0d1a03f4",
                "replaces_id": None,
                "pk": "f452a117-a992-4447-9774-6a8130f05b30",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "3590f73d-5eb0-44a0-91a6-5b2db6655889",
                "description": "Designate to process as a DSpace transfer when unquarantined",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "5975a5df-41af-4e3e-8e4e-ec7aff3ae085",
                "replaces_id": None,
                "pk": "f5ca3e51-35ba-4cdd-acf5-7d4fec955e76",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to quarantined",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "39f8d4bf-2078-4415-b600-ce2865585aca",
                "replaces_id": None,
                "pk": "f661aae0-05bf-4f55-a2f6-ef0f157231bd",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Create rights to flag closed AIPS.",
                "lastmodified": parse_date("2012-12-12T21:37:10+00:00"),
                "tasktypepkreference": "ccbaa53f-a486-4564-9b1a-a1b7bd5b1239",
                "replaces_id": None,
                "pk": "f6fbbf4f-bf8d-49f2-a978-8d689380cafc",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Move to workFlowDecisions-quarantineSIP directory",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "f46bbd28-d533-4933-9b5c-4a5d32927ff3",
                "replaces_id": None,
                "pk": "f872b932-90dd-4501-98c4-9fc5bac9d19a",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Include default SIP processingMCP.xml",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "e887c51e-afb9-48b1-b416-502a2357e621",
                "replaces_id": None,
                "pk": "f89b9e0f-8789-4292-b5d0-4a330c0205e1",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "Select pre-normalize file format identification command",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "f8d0b7df-68e8-4214-a49d-60a91ed27029",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Check for submission documentation",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "1aaa6e10-7907-4dea-a92a-dd0931eff226",
                "replaces_id": None,
                "pk": "f908bcd9-2fba-48c3-b04b-459f6ad1a4de",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "Set files to identify",
                "lastmodified": parse_date("2013-11-07T22:51:43+00:00"),
                "tasktypepkreference": "42454e81-e776-44cc-ae9f-b40e7e5c7738",
                "replaces_id": None,
                "pk": "fa2307df-e42a-4553-aaf5-b08879b0cbf4",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "Approve DSpace transfer",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": None,
                "replaces_id": None,
                "pk": "fa3e0099-b891-43f6-a4bc-390d544fa3e9",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Sanitize file and directory names in submission documentation",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "ad65bf76-3491-4c3d-afb0-acc94ff28bee",
                "replaces_id": None,
                "pk": "fb55b404-90f5-45b6-a47c-ccfbd0de2401",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "01b748fe-2e9d-44e4-ae5d-113f74c9a0ba",
                "description": "Store AIP location",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "ebab9878-f42e-4451-a24a-ec709889a858",
                "replaces_id": None,
                "pk": "fb64af31-8f8a-4fe5-a20d-27ee26c9dda2",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Verify transfer compliance",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "cf23dd75-d273-4c4e-8394-17622adf9bd6",
                "replaces_id": None,
                "pk": "fbaadb5d-63f9-440c-a607-a4ebfb973a78",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Remove preservation and access normalized files to renormalize.",
                "lastmodified": parse_date("2012-10-24T00:40:06+00:00"),
                "tasktypepkreference": "c15de53e-a5b2-41a1-9eee-1a7b4dd5447a",
                "replaces_id": None,
                "pk": "fe354b27-dbb2-4454-9c1c-340d85e67b78",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign file UUIDs to objects",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "179c8ce5-2b83-4ae2-9653-971e868fe183",
                "replaces_id": None,
                "pk": "feac0c04-3511-4e91-9403-5c569cff7bcc",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "Set bag file permissions",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "ba937c55-6148-4f45-a9ad-9697c0cf11ed",
                "replaces_id": None,
                "pk": "feb27f44-3575-4d17-8e00-43aa5dc5c3dc",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Scan for viruses in submission documentation",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "2fdb8408-8bbb-45d1-846b-5e28bf220d5c",
                "replaces_id": None,
                "pk": "fecb3fe4-5c5c-4796-b9dc-c7d7cf33a9f3",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a19bfd9f-9989-4648-9351-013a10b382ed",
                "description": "Get list of collections on server",
                "lastmodified": parse_date("2012-10-02T00:25:11+00:00"),
                "tasktypepkreference": "13d2adfc-8cb8-4206-bf70-04f031436ca2",
                "replaces_id": None,
                "pk": "fedffebc-7292-4b94-b402-84628c4254de",
            }
            TaskConfig.objects.create(**props)
            props = {
                "tasktype_id": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "Assign UUIDs to manual normalized preservation files",
                "lastmodified": parse_date("2013-01-03T02:10:39+00:00"),
                "tasktypepkreference": "4f47371b-a69b-4a8a-87b5-01e7eb1628c3",
                "replaces_id": None,
                "pk": "ff8f70b9-e345-4163-a784-29b432b12558",
            }
            TaskConfig.objects.create(**props)

        with suppress_autotime(TaskConfigAssignMagicLink, ["lastmodified"]):
            props = {
                "pk": "1c460578-e696-4378-a5d1-63ee77dd18bc",
                "execute_id": "f3a58cbb-20a8-4c6d-9ae4-1a5f02c1a28e",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:03+00:00"),
            }
            TaskConfigAssignMagicLink.objects.create(**props)
            props = {
                "pk": "5975a5df-41af-4e3e-8e4e-ec7aff3ae085",
                "execute_id": "19adb668-b19a-4fcb-8938-f49d7485eaf3",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:03+00:00"),
            }
            TaskConfigAssignMagicLink.objects.create(**props)
            props = {
                "pk": "5dffcd9c-472d-44e0-ae4d-a30705cf80cd",
                "execute_id": "755b4177-c587-41a7-8c52-015277568302",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:03+00:00"),
            }
            TaskConfigAssignMagicLink.objects.create(**props)
            props = {
                "pk": "c691548f-0131-4bd5-864c-364b1f7feb7f",
                "execute_id": "5c459c1a-f998-404d-a0dd-808709510b72",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:03+00:00"),
            }
            TaskConfigAssignMagicLink.objects.create(**props)
            props = {
                "pk": "f1357379-0118-4f51-aa49-37aeb702b760",
                "execute_id": "05f99ffd-abf2-4f5a-9ec8-f80a59967b89",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:03+00:00"),
            }
            TaskConfigAssignMagicLink.objects.create(**props)

        with suppress_autotime(TaskConfigSetUnitVariable, ["createdtime"]):
            props = {
                "updatedtime": None,
                "microservicechainlink_id": "7509e7dc-1e1b-4dce-8d21-e130515fce73",
                "createdtime": parse_date("2012-10-23T19:41:25+00:00"),
                "variablevalue": None,
                "variable": "resumeAfterNormalizationFileIdentificationToolSelected",
                "pk": "1871a1a5-1937-4c4d-ab05-3b0c04a0bca1",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2012-10-23T19:41:23+00:00"),
                "variablevalue": "FileIDTypes.pk = '16ae42ff-1018-4815-aac8-cceacd8d88a8'",
                "variable": "normalizationFileIdentificationToolIdentifierTypes",
                "pk": "202e00f4-595e-41fb-9a96-b8ec8c76318e",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2012-10-23T19:41:22+00:00"),
                "variablevalue": "FileIDTypes.pk = 'ac5d97dc-df9e-48b2-81c5-4a8b044355fa' OR FileIDTypes.pk = 'f794555f-50ad-4fd4-9eab-67bc47c431ab'",
                "variable": "normalizationFileIdentificationToolIdentifierTypes",
                "pk": "4093954b-5e44-4fe9-9a47-14c82158a00d",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2013-11-07T22:51:43+00:00"),
                "variablevalue": "{'filterSubDir':'objects/attachments'}",
                "variable": "identifyFileFormat_v0.0",
                "pk": "42454e81-e776-44cc-ae9f-b40e7e5c7738",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2012-10-23T19:41:24+00:00"),
                "variablevalue": "FileIDTypes.pk = '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc'",
                "variable": "normalizationFileIdentificationToolIdentifierTypes",
                "pk": "42e656d6-4816-417f-b45e-92dadd0dfde5",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2012-10-23T19:41:24+00:00"),
                "variablevalue": "FileIDTypes.pk = 'c26227f7-fca8-4d98-9d8e-cfab86a2dd0a' OR FileIDTypes.pk = 'cff7437f-20c6-440a-b801-37c647da2cf1'",
                "variable": "normalizationFileIdentificationToolIdentifierTypes",
                "pk": "471ff5ad-1fd3-4540-9245-360cc8c9b389",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": "0e41c244-6c3e-46b9-a554-65e66e5c9324",
                "createdtime": parse_date("2013-11-07T22:51:43+00:00"),
                "variablevalue": None,
                "variable": "fileIDcommand-transfer",
                "pk": "65263ec0-f3ff-4fd5-9cd3-cf6f51ef92c7",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": "16415d2f-5642-496d-a46d-00028ef6eb0a",
                "createdtime": parse_date("2012-12-06T18:58:24+00:00"),
                "variablevalue": None,
                "variable": "loadOptionsToCreateSIP",
                "pk": "6adccf2b-1c91-448b-bf0f-56414ee237ac",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2012-10-23T19:41:23+00:00"),
                "variablevalue": "FileIDTypes.pk = '8e39a076-d359-4c60-b6f4-38f7ae6adcdf'",
                "variable": "normalizationFileIdentificationToolIdentifierTypes",
                "pk": "6c02936d-552a-415e-b3c1-6d681b01d1c6",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": "8ba83807-2832-4e41-843c-2e55ad10ea0b",
                "createdtime": parse_date("2012-10-24T00:40:06+00:00"),
                "variablevalue": None,
                "variable": "reNormalize",
                "pk": "76eaa4d2-fd4f-4741-b68c-df5b96ba81d1",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2012-10-23T19:41:23+00:00"),
                "variablevalue": "FileIDTypes.pk = '076cce1b-9b46-4343-a193-11c2662c9e02' OR FileIDTypes.pk = '237d393f-aba2-44ae-b61c-76232d383883'",
                "variable": "normalizationFileIdentificationToolIdentifierTypes",
                "pk": "9329d1d8-03f9-4c5e-81ec-7010552d0a3e",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": "8de9fe10-932f-4151-88b0-b50cf271e156",
                "createdtime": parse_date("2012-10-24T00:40:07+00:00"),
                "variablevalue": None,
                "variable": "reNormalize",
                "pk": "b5808a0f-e842-4820-837a-832d18398ebb",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2012-10-23T19:41:23+00:00"),
                "variablevalue": "FileIDTypes.pk = '9ffdc6e8-f25a-4e5b-aaca-02769c4e7b7f' ",
                "variable": "normalizationFileIdentificationToolIdentifierTypes",
                "pk": "be6dda53-ef28-42dd-8452-e11734d57a91",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": "b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3",
                "createdtime": parse_date("2013-11-07T22:51:35+00:00"),
                "variablevalue": None,
                "variable": "resumeAfterNormalizationFileIdentificationToolSelected",
                "pk": "d8e2c7b2-5452-4c26-b57a-04caafe9f95c",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": "2fd123ea-196f-4c9c-95c0-117aa65ed9c6",
                "createdtime": parse_date("2013-11-07T22:51:43+00:00"),
                "variablevalue": None,
                "variable": "postExtractSpecializedProcessing",
                "pk": "ed98984f-69c5-45de-8a32-2c9ecf65e83f",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2012-10-23T19:41:23+00:00"),
                "variablevalue": "FileIDTypes.pk = 'afdbee13-eec5-4182-8c6c-f5638ee290f3'",
                "variable": "normalizationFileIdentificationToolIdentifierTypes",
                "pk": "f130c16d-d419-4063-8c8b-2e4c3ad138bb",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2013-11-07T22:51:43+00:00"),
                "variablevalue": "{'filterSubDir':'objects/attachments'}",
                "variable": "normalize_v1.0",
                "pk": "f226ecea-ae91-42d5-b039-39a1125b1c30",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                "createdtime": parse_date("2012-10-23T19:41:25+00:00"),
                "variablevalue": None,
                "variable": "resumeAfterNormalizationFileIdentificationToolSelected",
                "pk": "f85bbe03-8aca-4211-99b7-ddb7dfb24da1",
            }
            TaskConfigSetUnitVariable.objects.create(**props)
            props = {
                "updatedtime": None,
                "microservicechainlink_id": None,
                "createdtime": parse_date("2012-10-23T19:41:23+00:00"),
                "variablevalue": "FileIDTypes.pk = 'b0bcccfb-04bc-4daa-a13c-77c23c2bda85' OR FileIDTypes.pk = 'dc551ed2-9d2f-4c8a-acce-760fb740af48'",
                "variable": "normalizationFileIdentificationToolIdentifierTypes",
                "pk": "face6ee9-42d5-46ff-be1b-a645594b2da8",
            }
            TaskConfigSetUnitVariable.objects.create(**props)

        with suppress_autotime(TaskConfigUnitVariableLinkPull, ["createdtime"]):
            props = {
                "updatedtime": None,
                "defaultmicroservicechainlink_id": None,
                "createdtime": parse_date("2012-10-23T19:41:22+00:00"),
                "variablevalue": None,
                "variable": "resumeAfterNormalizationFileIdentificationToolSelected",
                "pk": "003b52a6-f80a-409c-95f9-82dd770aa132",
            }
            TaskConfigUnitVariableLinkPull.objects.create(**props)
            props = {
                "updatedtime": None,
                "defaultmicroservicechainlink_id": "bb194013-597c-4e4a-8493-b36d190f8717",
                "createdtime": parse_date("2012-12-06T17:43:25+00:00"),
                "variablevalue": None,
                "variable": "loadOptionsToCreateSIP",
                "pk": "11aef684-f2c7-494e-9763-277344e139bf",
            }
            TaskConfigUnitVariableLinkPull.objects.create(**props)
            props = {
                "updatedtime": None,
                "defaultmicroservicechainlink_id": "eb52299b-9ae6-4a1f-831e-c7eee0de829f",
                "createdtime": parse_date("2013-11-07T22:51:43+00:00"),
                "variablevalue": None,
                "variable": "postExtractSpecializedProcessing",
                "pk": "49d853a9-646d-4e9f-b825-d1bcc3ba77f0",
            }
            TaskConfigUnitVariableLinkPull.objects.create(**props)
            props = {
                "updatedtime": None,
                "defaultmicroservicechainlink_id": None,
                "createdtime": parse_date("2013-01-03T02:10:38+00:00"),
                "variablevalue": None,
                "variable": "returnFromManualNormalized",
                "pk": "65af383e-2153-4117-a2f9-bbe83358e54b",
            }
            TaskConfigUnitVariableLinkPull.objects.create(**props)
            props = {
                "updatedtime": None,
                "defaultmicroservicechainlink_id": "2522d680-c7d9-4d06-8b11-a28d8bd8a71f",
                "createdtime": parse_date("2013-11-07T22:51:43+00:00"),
                "variablevalue": None,
                "variable": "fileIDcommand-transfer",
                "pk": "97ddf0be-7b07-48b1-82f6-6a3b49edde2b",
            }
            TaskConfigUnitVariableLinkPull.objects.create(**props)
            props = {
                "updatedtime": None,
                "defaultmicroservicechainlink_id": None,
                "createdtime": parse_date("2012-10-24T17:04:11+00:00"),
                "variablevalue": None,
                "variable": "reNormalize",
                "pk": "e56e168e-d339-45b4-bc2a-a3eb24390f0f",
            }
            TaskConfigUnitVariableLinkPull.objects.create(**props)

        with suppress_autotime(TaskType, ["lastmodified"]):
            props = {
                "pk": "01b748fe-2e9d-44e4-ae5d-113f74c9a0ba",
                "description": "Get user choice from microservice generated list",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:10+00:00"),
            }
            TaskType.objects.create(**props)
            props = {
                "pk": "3590f73d-5eb0-44a0-91a6-5b2db6655889",
                "description": "assign magic link",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:10+00:00"),
            }
            TaskType.objects.create(**props)
            props = {
                "pk": "36b2e239-4a57-4aa5-8ebc-7a29139baca6",
                "description": "one instance",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:10+00:00"),
            }
            TaskType.objects.create(**props)
            props = {
                "pk": "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
                "description": "get user choice to proceed with",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:10+00:00"),
            }
            TaskType.objects.create(**props)
            props = {
                "pk": "6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
                "description": "linkTaskManagerSetUnitVariable",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-22T17:05:07+00:00"),
            }
            TaskType.objects.create(**props)
            props = {
                "pk": "6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9",
                "description": "goto magic link",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:10+00:00"),
            }
            TaskType.objects.create(**props)
            props = {
                "pk": "9c84b047-9a6d-463f-9836-eafa49743b84",
                "description": "get replacement dic from user choice",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:10+00:00"),
            }
            TaskType.objects.create(**props)
            props = {
                "pk": "a19bfd9f-9989-4648-9351-013a10b382ed",
                "description": "Get microservice generated list in stdOut",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:10+00:00"),
            }
            TaskType.objects.create(**props)
            props = {
                "pk": "a6b1c323-7d36-428e-846a-e7e819423577",
                "description": "for each file",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:10+00:00"),
            }
            TaskType.objects.create(**props)
            props = {
                "pk": "c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
                "description": "linkTaskManagerUnitVariableLinkPull",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-22T17:03:13+00:00"),
            }
            TaskType.objects.create(**props)

        props = {
            "createdtime": None,
            "pk": "312fc2b3-d786-458d-a762-57add7f96c22",
            "type": "",
            "name": "Disk media formats",
        }
        Taxonomy.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "31e0bdc9-1114-4427-9f37-ca284577dcac",
            "type": "",
            "name": "Filesystem types",
        }
        Taxonomy.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "cae76c7f-4d8e-48ee-9522-4b3fbf492516",
            "type": "",
            "name": "Disk imaging software",
        }
        Taxonomy.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "cc4231ef-9886-4722-82ec-917e60d3b2c7",
            "type": "",
            "name": "Disk image format",
        }
        Taxonomy.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "f6980e68-bac2-46db-842b-da4eba4ba418",
            "type": "",
            "name": "Disk media densities",
        }
        Taxonomy.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "fbf318db-4908-4971-8273-1094d2ba29a6",
            "type": "",
            "name": "Disk imaging interfaces",
        }
        Taxonomy.objects.create(**props)

        props = {
            "createdtime": None,
            "pk": "0d6d40b5-8bf8-431d-8dd2-23d6b0b17ca0",
            "taxonomy_id": "31e0bdc9-1114-4427-9f37-ca284577dcac",
            "term": "FAT",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "35097f1b-094a-40bc-ba0c-f1260b50042a",
            "taxonomy_id": "fbf318db-4908-4971-8273-1094d2ba29a6",
            "term": "Catweasel",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "38ad5611-f05a-45d4-ac20-541c89bf0167",
            "taxonomy_id": "cae76c7f-4d8e-48ee-9522-4b3fbf492516",
            "term": "FTK imager 3.1.0.1514",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "53e7764a-f711-486d-a0aa-8ec10d1d8da5",
            "taxonomy_id": "fbf318db-4908-4971-8273-1094d2ba29a6",
            "term": "Firewire",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "6774c7ce-a760-4f29-a7a3-b948f3769f71",
            "taxonomy_id": "fbf318db-4908-4971-8273-1094d2ba29a6",
            "term": "USB",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "6836caa4-8a0f-465e-be1b-4d8c547a7bf4",
            "taxonomy_id": "cae76c7f-4d8e-48ee-9522-4b3fbf492516",
            "term": "Kryoflux",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "6e368167-ea3e-45cd-adf2-60513a7e1802",
            "taxonomy_id": "fbf318db-4908-4971-8273-1094d2ba29a6",
            "term": "IDE",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "82a367f5-8157-4ac4-a5eb-3b59aac78d16",
            "taxonomy_id": "f6980e68-bac2-46db-842b-da4eba4ba418",
            "term": "Double density",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "867ab18d-e860-445f-a254-8fcdebfe95b6",
            "taxonomy_id": "312fc2b3-d786-458d-a762-57add7f96c22",
            "term": '3.5" floppy',
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "a3a6e30d-810f-4300-8461-1b41a7b383f1",
            "taxonomy_id": "cc4231ef-9886-4722-82ec-917e60d3b2c7",
            "term": "AD1",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "c41922d6-e716-4822-a385-e2fb0009465b",
            "taxonomy_id": "312fc2b3-d786-458d-a762-57add7f96c22",
            "term": '5.25" floppy',
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "db34d5e1-0c93-4faa-bb1c-c5f5ebae6764",
            "taxonomy_id": "31e0bdc9-1114-4427-9f37-ca284577dcac",
            "term": "HFS",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "e4edb250-d70a-4f63-8234-948b05b1163e",
            "taxonomy_id": "f6980e68-bac2-46db-842b-da4eba4ba418",
            "term": "Single density",
        }
        TaxonomyTerm.objects.create(**props)
        props = {
            "createdtime": None,
            "pk": "fcefbea2-848c-4685-9032-18a87cbc7a04",
            "taxonomy_id": "cc4231ef-9886-4722-82ec-917e60d3b2c7",
            "term": "AFF3",
        }
        TaxonomyTerm.objects.create(**props)

        props = {
            "sortorder": 14,
            "fieldlabel": "Image fixity",
            "fieldname": "image_fixity",
            "fieldtype": "textarea",
            "createdtime": None,
            "pk": "0a9e346a-f08c-4e0d-9753-d9733f7205e5",
            "optiontaxonomy_id": None,
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 13,
            "fieldlabel": "Imaging software",
            "fieldname": "imaging_software",
            "fieldtype": "select",
            "createdtime": None,
            "pk": "0c1b4233-fbe7-463f-8346-be6542574b86",
            "optiontaxonomy_id": "cae76c7f-4d8e-48ee-9522-4b3fbf492516",
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 4,
            "fieldlabel": "Media format",
            "fieldname": "media_format",
            "fieldtype": "select",
            "createdtime": None,
            "pk": "13f97ff6-b312-4ab6-aea1-8438a55ae581",
            "optiontaxonomy_id": "312fc2b3-d786-458d-a762-57add7f96c22",
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 3,
            "fieldlabel": "Serial number",
            "fieldname": "serial_number",
            "fieldtype": "text",
            "createdtime": None,
            "pk": "277727e4-b621-4f68-acb4-5689f81f31cd",
            "optiontaxonomy_id": None,
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 9,
            "fieldlabel": "Examiner",
            "fieldname": "examiner",
            "fieldtype": "text",
            "createdtime": None,
            "pk": "2c1844af-1217-4fdb-afbe-a052a91b7265",
            "optiontaxonomy_id": None,
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 11,
            "fieldlabel": "Imaging success",
            "fieldname": "imaging_success",
            "fieldtype": "text",
            "createdtime": None,
            "pk": "32f0f054-96d1-42ed-add6-7aa053237b02",
            "optiontaxonomy_id": None,
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 2,
            "fieldlabel": "Media manufacture",
            "fieldname": "media_manufacture",
            "fieldtype": "text",
            "createdtime": None,
            "pk": "367ef53b-49d6-4a4e-8b2f-10267d6a7db1",
            "optiontaxonomy_id": None,
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 10,
            "fieldlabel": "Imaging date",
            "fieldname": "imaging_date",
            "fieldtype": "text",
            "createdtime": None,
            "pk": "38df3f82-5695-46d3-b4e2-df68a872778a",
            "optiontaxonomy_id": None,
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 7,
            "fieldlabel": "Imaging process notes",
            "fieldname": "imaging_process_notes",
            "fieldtype": "textarea",
            "createdtime": None,
            "pk": "7ab79b42-1c84-420e-9169-e6bdf20141df",
            "optiontaxonomy_id": None,
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 5,
            "fieldlabel": "Media density",
            "fieldname": "media_density",
            "fieldtype": "select",
            "createdtime": None,
            "pk": "a0d80573-e6ef-412e-a7a7-69bdfe3f6f8f",
            "optiontaxonomy_id": "f6980e68-bac2-46db-842b-da4eba4ba418",
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 1,
            "fieldlabel": "Label text",
            "fieldname": "label_text",
            "fieldtype": "textarea",
            "createdtime": None,
            "pk": "a9a4efa8-d8ab-4b32-8875-b10da835621c",
            "optiontaxonomy_id": None,
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 8,
            "fieldlabel": "Imaging interface",
            "fieldname": "imaging_interface",
            "fieldtype": "select",
            "createdtime": None,
            "pk": "af677693-524d-42af-be6c-d0f6a8976db1",
            "optiontaxonomy_id": "fbf318db-4908-4971-8273-1094d2ba29a6",
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 6,
            "fieldlabel": "Source filesystem",
            "fieldname": "source_filesystem",
            "fieldtype": "select",
            "createdtime": None,
            "pk": "c9344f6f-f881-4d2e-9ffa-26b7f5e42a11",
            "optiontaxonomy_id": "31e0bdc9-1114-4427-9f37-ca284577dcac",
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 12,
            "fieldlabel": "Image format",
            "fieldname": "image_format",
            "fieldtype": "select",
            "createdtime": None,
            "pk": "d3b5b380-8901-4e68-8c40-3d59578810f4",
            "optiontaxonomy_id": "cc4231ef-9886-4722-82ec-917e60d3b2c7",
        }
        TransferMetadataField.objects.create(**props)
        props = {
            "sortorder": 0,
            "fieldlabel": "Media number",
            "fieldname": "media_number",
            "fieldtype": "text",
            "createdtime": None,
            "pk": "fc69452c-ca57-448d-a46b-873afdd55e15",
            "optiontaxonomy_id": None,
        }
        TransferMetadataField.objects.create(**props)

        with suppress_autotime(WatchedDirectory, ["lastmodified"]):
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "chain_id": "bd94cc9b-7990-45a2-a255-a1b70936f9f2",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%workFlowDecisions/selectFormatIDToolTransfer/",
                "replaces_id": None,
                "pk": "11a4f280-9b43-45a0-9ebd-ec7a115ccc62",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "4171636c-e013-4ecc-ae45-60b5458c208b",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%activeTransfers/maildir",
                "replaces_id": None,
                "pk": "1caf28cd-95d5-437b-ac07-2171feb9e645",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "76e66677-40e6-41da-be15-709afb334936",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "6f0f35fb-6831-4842-9512-4a263700a29b",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%storeAIP/",
                "replaces_id": None,
                "pk": "1f49b5a3-58e9-4dfa-b3c8-45010a957146",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2012-11-30T19:55:49+00:00"),
                "chain_id": "94f764ad-805a-4d4e-8a2b-a6f2515b30c7",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%activeTransfers/TRIM/",
                "replaces_id": None,
                "pk": "20e551b3-d8b9-47c9-b9cb-2c7b701fbca7",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "ad37288a-162c-4562-8532-eb4050964c73",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%quarantined/",
                "replaces_id": None,
                "pk": "3132e312-aee3-46c1-a71d-eed431d7b563",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "907cbebd-78f5-4f79-a441-feac0ea119f7",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "28a4322d-b8a5-4bae-b2dd-71cc9ff99e73",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%uploadDIP/",
                "replaces_id": None,
                "pk": "31807189-05e5-4d5f-b31f-fa445c1b039a",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "cc38912d-6520-44e1-92ff-76bb4881a55e",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%system/autoRestructureForCompliance/",
                "replaces_id": None,
                "pk": "4e3f8390-896d-4a46-9a20-6865c45bb8da",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "76e66677-40e6-41da-be15-709afb334936",
                "lastmodified": parse_date("2013-11-07T22:51:42+00:00"),
                "chain_id": "0ea3a6f9-ff37-4f32-ac01-eec5393f008a",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%workFlowDecisions/selectFormatIDToolIngest/",
                "replaces_id": None,
                "pk": "50c378ed-6a88-4988-bf21-abe1ea3e0115",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "chain_id": "c868840c-cf0b-49db-a684-af4248702954",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%workFlowDecisions/extractPackagesChoice/",
                "replaces_id": None,
                "pk": "64198d4e-ec61-46fe-b043-228623c2b26f",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "498795c7-06f2-4f3f-95bf-57f1b35964ad",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%SIPCreation/completedTransfers/",
                "replaces_id": None,
                "pk": "6b3f9acb-6567-408e-a0cf-5e02abf535c2",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "76e66677-40e6-41da-be15-709afb334936",
                "lastmodified": parse_date("2013-11-07T22:51:35+00:00"),
                "chain_id": "9918b64c-b898-407b-bce4-a65aa3c11b89",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%system/createDIPFromAIP/",
                "replaces_id": None,
                "pk": "77ac4a58-8b4f-4519-ad0a-1a35dedb47b4",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "76e66677-40e6-41da-be15-709afb334936",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "chain_id": "86fbea68-d08c-440f-af2c-dac68556db12",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%workFlowDecisions/metadataReminder/",
                "replaces_id": None,
                "pk": "7ac9aec3-396a-485d-8695-d7015121d865",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2012-11-20T22:31:11+00:00"),
                "chain_id": "7030f152-398a-470b-b045-f5dfa9013671",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%workFlowDecisions/quarantineTransfer",
                "replaces_id": None,
                "pk": "88d93fa1-2cf2-4a47-b982-19721a697471",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "76e66677-40e6-41da-be15-709afb334936",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "fefdcee4-dd84-4b55-836f-99ef880ecdb6",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%system/autoProcessSIP",
                "replaces_id": None,
                "pk": "88f9c08e-ebc3-4334-9126-79d0489e8f39",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "b0e0bf75-6b7e-44b6-a0d0-189eea7605dd",
                "only_act_on_directories": False,
                "watched_directory_path": "%watchDirectoryPath%activeTransfers/baggitZippedDirectory",
                "replaces_id": None,
                "pk": "94df8566-7337-48f1-b3f9-abcc9e52fa4a",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "fffd5342-2337-463f-857a-b2c8c3778c6d",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%activeTransfers/standardTransfer",
                "replaces_id": None,
                "pk": "a68ef52c-0d44-4eeb-9c82-5bd9b253e7b6",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "76e66677-40e6-41da-be15-709afb334936",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "chain_id": "0766af55-a950-44d0-a79b-9f2bb65f92c8",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%system/createAIC/",
                "replaces_id": None,
                "pk": "aae2a1df-b012-492d-8d84-4fd9bcc25b71",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "816f28cd-6af1-4d26-97f3-e61645eb881b",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%activeTransfers/baggitDirectory",
                "replaces_id": None,
                "pk": "d1d46afd-8e1d-4c72-ae25-e2cea4cb8fa6",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "76e66677-40e6-41da-be15-709afb334936",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "a2e19764-b373-4093-b0dd-11d61580f180",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%SIPCreation/SIPsUnderConstruction",
                "replaces_id": None,
                "pk": "d91f3c5b-7936-4cf9-a702-117ec3e7e7d3",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "chain_id": "96b49116-b114-47e8-95d0-b3c6ae4e80f5",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%workFlowDecisions/examineContentsChoice/",
                "replaces_id": None,
                "pk": "da0ce3b8-07c4-4a89-8313-15df5884ac48",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "76e66677-40e6-41da-be15-709afb334936",
                "lastmodified": parse_date("2013-11-07T22:51:34+00:00"),
                "chain_id": "27cf6ca9-11b4-41ac-9014-f8018bcbad5e",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%workFlowDecisions/compressionAIPDecisions/",
                "replaces_id": None,
                "pk": "dfb22984-c6eb-4c5d-939c-0df43559033e",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2014-09-11T16:09:53+00:00"),
                "chain_id": "f6df8882-d076-441e-bb00-2f58d5eda098",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%workFlowDecisions/createTree/",
                "replaces_id": None,
                "pk": "e237217e-7b07-48f0-8129-36da0abfc97f",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "55fa7084-3b64-48ca-be64-08949227f85d",
                "only_act_on_directories": False,
                "watched_directory_path": "%watchDirectoryPath%activeTransfers/Dspace",
                "replaces_id": None,
                "pk": "e3b15e28-6370-42bf-a0e1-f61e4837a2a7",
            }
            WatchedDirectory.objects.create(**props)
            props = {
                "expected_type_id": "76e66677-40e6-41da-be15-709afb334936",
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
                "chain_id": "39682d0c-8d81-4fdd-8e10-85114b9eb2dd",
                "only_act_on_directories": True,
                "watched_directory_path": "%watchDirectoryPath%approveNormalization/",
                "replaces_id": None,
                "pk": "fb77de49-855d-4949-bb85-553b23cdc708",
            }
            WatchedDirectory.objects.create(**props)

        with suppress_autotime(WatchedDirectoryExpectedType, ["lastmodified"]):
            props = {
                "pk": "76e66677-40e6-41da-be15-709afb334936",
                "description": "SIP",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
            }
            WatchedDirectoryExpectedType.objects.create(**props)
            props = {
                "pk": "907cbebd-78f5-4f79-a441-feac0ea119f7",
                "description": "DIP",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
            }
            WatchedDirectoryExpectedType.objects.create(**props)
            props = {
                "pk": "f9a3a93b-f184-4048-8072-115ffac06b5d",
                "description": "Transfer",
                "replaces_id": None,
                "lastmodified": parse_date("2012-10-02T00:25:12+00:00"),
            }
            WatchedDirectoryExpectedType.objects.create(**props)


class Migration(migrations.Migration):

    dependencies = [("main", "0001_initial")]

    operations = [migrations.RunPython(load_fixtures)]

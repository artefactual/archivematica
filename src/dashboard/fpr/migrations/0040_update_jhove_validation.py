from django.db import migrations

JHOVE_TOOL_ID = "085d8690-93b7-4d31-84f7-2c5f4cbf6735"
OLD_JHOVE_CMD_ID = "4cac3267-453e-4456-9306-6d098dacb70d"
NEW_JHOVE_CMD_ID = "cb335c49-e6ce-445f-a774-494a6f2300c6"
JHOVE_VALIDATION_RULES = (
    "005d14f1-5b67-43fc-b3a5-5048ec915b0b",
    "085d5286-7616-4acd-88a4-ef65066362b9",
    "0cd29763-b64a-43cc-9a72-5f8e6317bbae",
    "10e514c0-e72a-4f70-afd0-4aed3bfa0ab9",
    "1386de15-3152-4a24-afa6-eab7a224da65",
    "18c019e8-ea26-49eb-a900-ec8388f1483d",
    "1a01813e-430f-4a91-bda2-182e4620d328",
    "26573246-96de-4682-bd17-f0bccb50abfe",
    "26f687fe-255a-469b-bca5-ac0992038789",
    "37a5d85d-58dc-4f4e-8be9-b9ecced85d0d",
    "40616003-8af5-48d8-94ca-1871ae2cfaf1",
    "407dcd55-71f5-4d83-8e21-6e3809a3fba8",
    "40966c69-42dd-49fb-8740-b22a85bc7e32",
    "42f3756b-7966-4a47-b029-59688bfc6e43",
    "4324a41f-6016-4b28-a0b0-c343dbaca42e",
    "471303d4-de26-435c-83b2-8e72beccc60d",
    "48086e84-a933-42e0-87fd-ce195137c48d",
    "4ea200fa-182c-4b17-9493-e9d3f7e467ff",
    "535152f5-88a5-439b-8619-6f42fc2e4468",
    "56c72d8a-139b-4cdf-8dd0-d65a373301d2",
    "57bbe864-2004-45a4-81be-d40aab02f170",
    "5bc4c892-fe7b-4d22-8a9a-ea8c3dd0d171",
    "6217dbf1-2b4f-49ce-ab87-d0ed1e1ef890",
    "62f0e3bd-a5bb-4fa0-b78b-dab15253b429",
    "662caf44-cd04-4990-8e28-9f8425dba782",
    "67c0b096-63f4-4e30-b26f-6ed9365ea67c",
    "6b3ba38b-e208-450d-9b48-07897b6b7c42",
    "6f4cbfc5-c560-4709-8d3e-aa5685bc4fd5",
    "713bf728-e583-4cb5-a079-f36baf1a77e7",
    "76bfa370-ac87-41e2-995b-e01bb8c977d0",
    "7af37625-f547-4d13-ab52-e5bddf249027",
    "802e24ec-5e63-4e92-a0cf-33f11b4edf06",
    "80ecc092-8f29-4810-8918-e81133092290",
    "87c23f92-ee9a-44b3-89b2-c024bbcc70a3",
    "8835348d-60f2-4dba-a834-cf26c57f821c",
    "88cb0134-7808-450f-a0f4-365a818d583a",
    "8a0a1d71-5e56-482e-81b4-b3d425106d49",
    "8e995eb3-4023-4168-b1e1-7b5f2b22237b",
    "913ff712-1856-48d7-85e9-415617fc9fdc",
    "95ef736c-e477-442e-86f4-4e9049be2b88",
    "981eae6c-4d7b-40ce-9bfd-1193c600a143",
    "986b53a8-3407-4d87-89ec-20575e61292a",
    "9d3325a1-cc0a-4fa8-9f3b-ccd5b8c884d1",
    "a01418ce-fcb9-4554-add5-72010c719865",
    "a0f916de-ed95-4f2a-9f6d-0cbfd8949cc2",
    "a7a6cc14-4d61-4030-b8dc-a1ca8ed97402",
    "aa4ad350-7e66-4637-a643-6e0bd037645d",
    "aa93748e-5899-4ecc-870e-3d47a38fda59",
    "ab286afc-f429-4e50-8a40-452c6331d630",
    "ab728cab-3072-4e20-a64b-ba2560467d93",
    "b1a60f26-8927-46c5-843b-7eddeef6213e",
    "b7dd794b-7618-4d13-a2f9-e01dae884cf6",
    "c5a30e3c-2100-4b5b-a9b5-27a236a345dd",
    "c6d7590f-83c1-4612-a300-3bff3d358199",
    "c799f39a-10fd-4125-b11c-1011ef1ca15c",
    "cddbffd4-4ada-4a6e-a713-82077a54e89e",
    "d4a1faba-a5a3-4955-a20a-6f71da1d35bc",
    "dc9dc6a9-82b6-44b7-866a-db3e6314922e",
    "dcc9bcd7-f085-4028-9599-bf4fd12816ee",
    "e0cdb544-97d3-4915-9b08-fffad57bda10",
    "e13d6459-a749-4d31-9dd0-e0a59aab36cd",
    "ecd66812-c89a-4231-802e-2e69b47bae2a",
    "ee56ca6d-f6d0-4948-9834-2c82f5d223d5",
    "eebc3670-6692-4daf-92a2-c8b76606049a",
    "f3d2b70b-0b9d-43f6-80e0-9b987b77719d",
    "f3f9652a-c903-491b-be89-5fc2469aaa1a",
    "f4074907-c111-4e6c-91ae-9c0526475a9a",
    "f51ed8e0-edb3-4ebc-84d5-11135cc1fe62",
    "f712b5a9-7dd5-4e39-b818-c7cda54b9366",
    "fcefa9af-322c-4c9b-afd2-82231dd953fc",
    "fdd758b0-99a6-4447-b082-3a1098f13bf6",
    "ff989185-1b11-4f96-8075-e605e4cf4be4",
    "ffa25cf6-c1a5-45f2-9bee-798aa04df172",
    "5df96ec2-b5a3-48b5-8599-3f292ff525c1",
    "cc464095-02b3-471b-8f1d-221aecf37741",
    "27c0dabc-fda4-4060-ab77-ce6e86f424c8",
    "886eeaba-55b3-4ed9-9441-59aa1454ecdc",
    "7497c57b-ee7a-420f-b197-e1752a0f071f",
)

NEW_JHOVE_VALIDATION_CMD = r"""
import json
import subprocess
import sys

from lxml import etree

class JhoveException(Exception):
    pass

def parse_jhove_data(target):
    args = ['jhove', '-h', 'xml', target]
    try:
        output = subprocess.check_output(args).decode("utf8")
    except subprocess.CalledProcessError:
        raise JhoveException("Jhove failed when running: " + ' '.join(args))

    return etree.fromstring(output.encode("utf8"))

def get_status(doc):
    status = doc.find('.{http://schema.openpreservation.org/ois/xml/ns/jhove}repInfo/{http://schema.openpreservation.org/ois/xml/ns/jhove}status')
    if status is None:
        raise JhoveException("Unable to find status!")

    return status.text

def get_outcome(status, format=None):
    # JHOVE returns "bytestream" for unrecognized file formats.
    # That can include unrecognized or malformed PDFs, JPEG2000s, etc.
    # Since we're whitelisting the formats we're passing in,
    # "bytestream" indicates that the format is not in fact well-formed
    # regardless of what the status reads.
    if format == "bytestream":
        return "partial pass"

    if status == "Well-Formed and valid":
        return "pass"
    elif status == "Well-Formed, but not valid":
        return "partial pass"
    else:
        return "fail"

def get_format(doc):
    format = doc.find('.{http://schema.openpreservation.org/ois/xml/ns/jhove}repInfo/{http://schema.openpreservation.org/ois/xml/ns/jhove}format')
    version = doc.find('.{http://schema.openpreservation.org/ois/xml/ns/jhove}repInfo/{http://schema.openpreservation.org/ois/xml/ns/jhove}version')

    if format is None:
        format = "Not detected"
    else:
        format = format.text

    if version is not None:
        version = version.text

    return (format, version)

def format_event_outcome_detail_note(format, version, result):
    note = 'format="{}";'.format(format)
    if version is not None:
        note = note + ' version="{}";'.format(version)
    note = note + ' result="{}"'.format(result)

    return note

def main(target):
    try:
        doc = parse_jhove_data(target)
        status = get_status(doc)
        format, version = get_format(doc)
        outcome = get_outcome(status, format)
        note = format_event_outcome_detail_note(format, version, status)

        out = {
            "eventOutcomeInformation": outcome,
            "eventOutcomeDetailNote": note
        }
        print(json.dumps(out))

        return 0
    except JhoveException as e:
        return e

if __name__ == '__main__':
    target = sys.argv[1]
    sys.exit(main(target))
"""


def data_migration_up(apps, schema_editor):
    """Update commands and rules."""
    _upgrade_fp_command(
        apps,
        NEW_JHOVE_CMD_ID,
        OLD_JHOVE_CMD_ID,
        NEW_JHOVE_VALIDATION_CMD,
        JHOVE_VALIDATION_RULES,
    )


def _upgrade_fp_command(
    apps,
    new_cmd_uuid,
    old_cmd_uuid,
    new_cmd,
    rule_uuids,
):
    FPTool = apps.get_model("fpr", "FPTool")
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    FPTool.objects.filter(uuid=JHOVE_TOOL_ID).update(version="1.26", slug="jhove-126")

    # Get the old command
    old_command = FPCommand.objects.get(uuid=old_cmd_uuid)

    # Replace the existing command with the following
    FPCommand.objects.create(
        uuid=new_cmd_uuid,
        replaces_id=old_cmd_uuid,
        tool_id=JHOVE_TOOL_ID,
        enabled=old_command.enabled,
        command=new_cmd,
        script_type="pythonScript",
        command_usage="validation",
        description="Validate using JHOVE",
    )

    # Update existing rules
    FPRule.objects.filter(uuid__in=rule_uuids).update(
        command_id=new_cmd_uuid,
    )

    # Disable the old command
    old_command.enabled = False
    old_command.save()


def data_migration_down(apps, schema_editor):
    _downgrade_fp_command(
        apps,
        OLD_JHOVE_CMD_ID,
        NEW_JHOVE_CMD_ID,
        JHOVE_VALIDATION_RULES,
    )


def _downgrade_fp_command(apps, old_cmd_uuid, new_cmd_uuid, rule_uuids):
    FPTool = apps.get_model("fpr", "FPTool")
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    # The order matters. We make sure that the rules point to the previous
    # command before the latter is deleted. Otherwise our rules would be
    # deleted by Django's on cascade mechanism
    FPRule.objects.filter(uuid__in=rule_uuids).update(
        command_id=old_cmd_uuid,
    )

    # Enable the old command. At this point we do not know if the
    # command was in fact enabled before the migration was run, so
    # this may have unexpected consequences
    old_command = FPCommand.objects.get(uuid=old_cmd_uuid)
    old_command.enabled = True
    old_command.save()

    # Delete the new command
    FPCommand.objects.filter(uuid=new_cmd_uuid).delete()
    FPTool.objects.filter(uuid=JHOVE_TOOL_ID).update(version="1.20", slug="jhove-120")


class Migration(migrations.Migration):
    dependencies = [("fpr", "0039_django32")]
    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

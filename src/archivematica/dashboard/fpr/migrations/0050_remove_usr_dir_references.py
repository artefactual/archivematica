from django.db import migrations

OLD_FIDO_CMD_UUID = "4ab42bc8-1537-4fa9-9c54-e454f2c5dcb7"

OLD_FIDO_CMD_SCRIPT = r'''
from __future__ import print_function
import os.path
import re
import subprocess
import sys

def file_tool(path):
    return subprocess.check_output(['file', path]).decode("utf8").strip()

class FidoFailed(Exception):
    def __init__(self, stdout, stderr, retcode):
        message = """
Fido exited {retcode} and no format was found.
stdout: {stdout}
---
stderr: {stderr}
""".format(stdout=stdout, stderr=stderr, retcode=retcode)
        super(FidoFailed, self).__init__(message)

def identify(file_):
    # The default buffer size fido uses, 256KB, is too small to be able to detect certain formats
    # Formats like office documents and Adobe Illustrator .ai files will be identified as other, less-specific formats
    # This larger buffer size is a bit slower and consumes more RAM, so some users may wish to customize this to reduce the buffer size
    # See: https://projects.artefactual.com/issues/5941, https://projects.artefactual.com/issues/5731
    cmd = ['fido', '-bufsize', '1048576',
           '-loadformats', '/usr/lib/archivematica/archivematicaCommon/externals/fido/archivematica_format_extensions.xml',
           os.path.abspath(file_)]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout, stderr = process.communicate()
    stdout = stdout.decode("utf8")
    stderr = stderr.decode("utf8")

    try:
        results = stdout.split('\n')[0].split(',')
    except Exception:
        raise FidoFailed(stdout, stderr, process.returncode)

    if process.returncode != 0 or results[-1] == '"fail"':
        raise FidoFailed(stdout, stderr, process.returncode)
    else:
        puid = results[2]
        if re.match('(.+)?fmt\/\d+', puid):
            return puid
        else:
            print("File identified as non-standard Fido code: {id}".format(id=puid), file=sys.stderr)
            return ""

def main(argv):
    try:
        print(identify(argv[1]))
        return 0
    except FidoFailed as e:
        file_output = file_tool(argv[1])
        # FIDO can't currently identify text files with no extension, and this
        # is a common enough usecase to special-case it
        if 'text' in file_output:
            print('x-fmt/111')
        else:
            return e
    except Exception as e:
        return e

if __name__ == '__main__':
    exit(main(sys.argv))
'''

NEW_FIDO_CMD_UUID = "25734211-bdad-45d4-9f01-fcbb77bdb58b"

NEW_FIDO_CMD_SCRIPT = r'''
import importlib.resources
import os.path
import re
import subprocess
import sys

def file_tool(path):
    return subprocess.check_output(['file', path]).decode("utf8").strip()

class FidoFailed(Exception):
    def __init__(self, stdout, stderr, retcode):
        message = """
Fido exited {retcode} and no format was found.
stdout: {stdout}
---
stderr: {stderr}
""".format(stdout=stdout, stderr=stderr, retcode=retcode)
        super(FidoFailed, self).__init__(message)

def identify(file_):
    # The default buffer size fido uses, 256KB, is too small to be able to detect certain formats
    # Formats like office documents and Adobe Illustrator .ai files will be identified as other, less-specific formats
    # This larger buffer size is a bit slower and consumes more RAM, so some users may wish to customize this to reduce the buffer size
    # See: https://projects.artefactual.com/issues/5941, https://projects.artefactual.com/issues/5731
    cmd = ['fido', '-bufsize', '1048576',
           '-loadformats', str(importlib.resources.files("archivematica.archivematicaCommon") / "externals" / "fido" / "archivematica_format_extensions.xml"),
           os.path.abspath(file_)]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout, stderr = process.communicate()
    stdout = stdout.decode("utf8")
    stderr = stderr.decode("utf8")

    try:
        results = stdout.split('\n')[0].split(',')
    except Exception:
        raise FidoFailed(stdout, stderr, process.returncode)

    if process.returncode != 0 or results[-1] == '"fail"':
        raise FidoFailed(stdout, stderr, process.returncode)
    else:
        puid = results[2]
        if re.match('(.+)?fmt\/\d+', puid):
            return puid
        else:
            print("File identified as non-standard Fido code: {id}".format(id=puid), file=sys.stderr)
            return ""

def main(argv):
    try:
        print(identify(argv[1]))
        return 0
    except FidoFailed as e:
        file_output = file_tool(argv[1])
        # FIDO can't currently identify text files with no extension, and this
        # is a common enough usecase to special-case it
        if 'text' in file_output:
            print('x-fmt/111')
        else:
            return e
    except Exception as e:
        return e

if __name__ == '__main__':
    exit(main(sys.argv))
'''

OLD_FIWALK_CMD_UUID = "928ce834-8830-44cc-a282-4ba1271f7842"

OLD_FIWALK_CMD_SCRIPT = r"fiwalk -x %relativeLocation% -c /usr/lib/archivematica/archivematicaCommon/externals/fiwalk_plugins/ficonfig.txt"

NEW_FIWALK_CMD_UUID = "fcd033ec-8e29-48e8-99b9-6dbccd8f9c6e"

NEW_FIWALK_CMD_SCRIPT = r"fiwalk -x %relativeLocation% -c %archivematicaCommonPath%/externals/fiwalk_plugins/ficonfig.txt"

FIWALK_CHARACTERIZATION_RULES = (
    "825b31d8-6ee0-46fc-bdd7-9bf32edb5755",
    "38ab3a16-e7fc-464d-8be9-1398908f78a9",
    "20cad741-3cf1-4b6a-9e71-d1e8af13ba3f",
    "ad4927da-94fa-4ac3-942e-9bafebf96a91",
    "223c794f-cfcb-458d-bc31-d90d8fe0d774",
    "5e661576-af61-44b5-834a-14ef21fb2051",
    "6f7e51b4-60b2-417f-b690-0f286a97304c",
    "c618f3d7-1fcb-476c-a076-e7413f19337b",
    "369140d2-ffdd-4050-8ff8-1947b325b4a5",
)


def update_fido_command(apps):
    IDCommand = apps.get_model("fpr", "IDCommand")

    command = IDCommand.objects.get(uuid=OLD_FIDO_CMD_UUID)

    IDCommand.objects.create(
        replaces=command,
        uuid=NEW_FIDO_CMD_UUID,
        description=command.description,
        config=command.config,
        script=NEW_FIDO_CMD_SCRIPT,
        script_type=command.script_type,
        tool=command.tool,
        enabled=command.enabled,
    )


def restore_fido_command(apps):
    IDCommand = apps.get_model("fpr", "IDCommand")

    try:
        command = IDCommand.objects.get(uuid=NEW_FIDO_CMD_UUID)
    except IDCommand.DoesNotExist:
        enabled = False
    else:
        enabled = command.enabled
        command.delete()

    IDCommand.objects.filter(uuid=OLD_FIDO_CMD_UUID).update(
        script=OLD_FIDO_CMD_SCRIPT, enabled=enabled
    )


def update_fiwalk_command(apps):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    command = FPCommand.objects.get(uuid=OLD_FIWALK_CMD_UUID)

    FPCommand.objects.create(
        replaces=command,
        uuid=NEW_FIWALK_CMD_UUID,
        tool=command.tool,
        description=command.description,
        command=NEW_FIWALK_CMD_SCRIPT,
        script_type=command.script_type,
        output_location=command.output_location,
        output_format=command.output_format,
        command_usage=command.command_usage,
        verification_command=command.verification_command,
        event_detail_command=command.event_detail_command,
        enabled=command.enabled,
    )

    FPRule.objects.filter(uuid__in=FIWALK_CHARACTERIZATION_RULES).update(
        command_id=NEW_FIWALK_CMD_UUID
    )


def restore_fiwalk_command(apps):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    try:
        command = FPCommand.objects.get(uuid=NEW_FIWALK_CMD_UUID)
    except FPCommand.DoesNotExist:
        enabled = False
    else:
        enabled = command.enabled
        command.delete()

    FPCommand.objects.filter(uuid=OLD_FIWALK_CMD_UUID).update(
        command=OLD_FIWALK_CMD_SCRIPT, enabled=enabled
    )

    FPRule.objects.filter(uuid__in=FIWALK_CHARACTERIZATION_RULES).update(
        command_id=OLD_FIWALK_CMD_UUID
    )


def data_migration_up(apps, schema_editor):
    update_fido_command(apps)
    update_fiwalk_command(apps)


def data_migration_down(apps, schema_editor):
    restore_fido_command(apps)
    restore_fiwalk_command(apps)


class Migration(migrations.Migration):
    dependencies = [("fpr", "0049_update_idtools")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

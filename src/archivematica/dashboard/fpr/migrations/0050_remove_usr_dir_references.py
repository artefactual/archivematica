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


def data_migration_up(apps, schema_editor):
    update_fido_command(apps)


def data_migration_down(apps, schema_editor):
    restore_fido_command(apps)


class Migration(migrations.Migration):
    dependencies = [("fpr", "0049_update_idtools")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

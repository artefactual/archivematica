# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations, models


# All MediaConch policy check commands in the FPR should follow the template in
# the following constant. They depend on the ammcpc module / command-line tool
# https://github.com/artefactual-labs/ammcpc being installed, which is a simple
# wrapper around the MediaConch command-line tool. Real policy check commands
# must contain values for the ``POLICY`` and ``POLICY_NAME`` constants.
POLICY_CHECK_CMD = '''
import sys
from ammcpc import MediaConchPolicyCheckerCommand

# Valuate this constant with the text (XML) of the policy.
POLICY = """
""".strip()

# Valuate this constant with the name of the policy.
POLICY_NAME = ''

if __name__ == '__main__':
    target = sys.argv[1]
    policy_checker = MediaConchPolicyCheckerCommand(
        policy=POLICY,
        policy_file_name=POLICY_NAME)
    sys.exit(policy_checker.check(target))
'''


def data_migration(apps, schema_editor):
    """FPR tool, commands, and rules for MediaConch policy checks.

    Creates the following:

    - MediaConch FPCommand for policy checks
    - MediaConch FPRule for checking .mkv preservation derivatives against a
        policy
    """

    FPTool = apps.get_model("fpr", "FPTool")
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")
    FormatVersion = apps.get_model("fpr", "FormatVersion")
    mkv_format = FormatVersion.objects.get(description="Generic MKV")

    # MediaConch Tool
    mediaconch_tool = FPTool.objects.get(description="MediaConch")

    # MediaConch Policy Check Command
    # NOTE: this command is disabled by default because it contains no policy
    # file.
    mediaconch_policy_check_command_uuid = "9ef290f7-5320-4d69-821a-3156fc184b4e"
    mediaconch_policy_check_command = FPCommand.objects.create(
        uuid=mediaconch_policy_check_command_uuid,
        tool=mediaconch_tool,
        description=(
            "Check against policy PLACEHOLDER_FOR_POLICY_FILE_NAME" " using MediaConch"
        ),
        command=POLICY_CHECK_CMD,
        script_type="pythonScript",
        command_usage="validation",
        enabled=False,
    )

    # MediaConch-against-MKV-for-policyCheckingPreservationFile Rule.
    # Create the FPR rule that causes 'Check against policy using MediaConch'
    # command to be used on 'Generic MKV' files intended for preservation in
    # the "Policy check" micro-service.
    # NOTE: this rule is disabled by default because it references a disabled
    # command that, in turn, references a non-existent MediaConch policy file.
    policy_check_preservation_rule_pk = "aaaf34ef-c00f-4bb9-85c1-01c0ad5f3a8c"
    FPRule.objects.create(
        uuid=policy_check_preservation_rule_pk,
        purpose="policy_check",
        command=mediaconch_policy_check_command,
        format=mkv_format,
        enabled=False,
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0011_mediaconch_validation")]

    FPRULE_CHOICES = [
        ("access", "Access"),
        ("characterization", "Characterization"),
        ("extract", "Extract"),
        ("preservation", "Preservation"),
        ("thumbnail", "Thumbnail"),
        ("transcription", "Transcription"),
        ("validation", "Validation"),
        ("policy_check", "Validation against a policy"),
        ("default_access", "Default access"),
        ("default_characterization", "Default characterization"),
        ("default_thumbnail", "Default thumbnail"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fprule",
            name="purpose",
            field=models.CharField(
                max_length=32, verbose_name="purpose", choices=FPRULE_CHOICES
            ),
        ),
        migrations.RunPython(data_migration),
    ]

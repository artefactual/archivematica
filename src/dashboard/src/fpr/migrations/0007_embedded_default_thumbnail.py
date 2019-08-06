# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


REPLACE_COMMAND = """
import argparse
import sys

# http://i.imgur.com/ijwSkff.jpg
DEFAULT_THUMBNAIL = \"\"\"
/9j/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB
AQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB
AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAAwADADASIAAhEBAxEB/8QAHAABAQACAgMA
AAAAAAAAAAAACAAFCQEKAwQG/8QANBAAAAUDAgIFCwUAAAAAAAAAAQMEBQYAAgcICRESExQ5eLcV
GSExV1iVmMHS1xZScYWn/8QAFgEBAQEAAAAAAAAAAAAAAAAAAAEC/8QAKBEAAgADBgUFAAAAAAAA
AAAAAAECESESMVFhkcEiQUJxoVJystHS/9oADAMBAAIRAxEAPwDelul5RzWOsiAYeh2d8yYlgjdp
mTZLBtxBOF+PVTjLXvKcmi7iufHJjLKXPye5mj7MQhQu5yxIymJVKhjKbTnl/vdQn13Pfvpa1vmN
mf30vNzvtGIj3KWDx0n9F2gML13Pfvpa1vmNmf314znLPJBJp9+tLWwNhJRhtwW6jJkNw2l2jfcF
oCYADcIAPABEA4+sQD01nq9VcUaciWEkcnTGpVBRPSCNpfSmFX2F842gNwWc4hzCACIW8RABH0UA
xdv3cZl2K2rHuPNW85dpbjLIrexrYhqAmLkscHTGsslRFi+yIZZkj48Ozu6QV6VKRvbMivKm0uBv
Sq9reDUuNFrVZivsa10WSpLlNjhDVBXjT4dJWxsjLVHFR9kua1qNyKbW5Mg6yY3AxKxKAy5PapAm
+43oLuXlPvEsDR3HbLOsLKUyksm0c5BaXVQx4zxmom+OnWTOVy2UQ6Mx56g8SGAqHDqKW2SxxQfL
LXOJ86VrugaBtURZrPeYisizHj2TWK1B8Tud9oxEe5SweOk/ou0otzvtGIj3KWDx0n9F2qCqqqoC
pC7VicpPuS5UEouwvrGkZ5PM5LQt5zByliEq6+7gAcbhAq0BuH0iAAHqAKPVI3a07SPJfc+efFjF
FZivg9z+MRVdF23RldzvtGIj3KWDx0n9F2tru4Lt+ah9ROf4VnnT9P8AEjGvb8PW4ik0fysErbiC
EjXNHmZNrwyuMXj8sFzNdTpGqRL0S1AyeRbWNIemWPnl5QQxC7zWe5H7TNH4f3OWPricarbXS3mr
O8SfgSzS12TDnVSM81nuSe0zR/8AGcr/AImq81nuSe0zR/8AGcr/AImqWn6ItYP0JLFefoOdIzaz
HjuSZND9uj94D/V8TXfWuB2styQfVk7SAH8PGVvriUaY+3ht4ahNNeoTIef8/wCQ8UyBxkGKQxdH
o9i79TuKe9O4yaNSNxdXVxkcah1zX5LuhyBMhQpkD/e9Xv7goUODEWxpEj1Ktw8LUnOtnBqSk3Wv
a+ook6pzWeKfNZH/2Q==\"\"\"

def main(target):
    with open(target, 'w+b') as f:
        f.write(DEFAULT_THUMBNAIL.decode('base64'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-location', required=True)
    args, _ = parser.parse_known_args()

    sys.exit(main(args.output_location))
"""


def data_migration(apps, schema_editor):
    """Introduce a new FPCommand "Using default thumbnail".

    The existing command expects to find the default thumbnail file in the
    Archivematica shared directory, see: https://git.io/vHD7L. This migration
    attempts to remove that level of coupling by introducing a new version of
    the command as a Python script where the contents of default.jpg are
    embedded.
    """
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    # Skip if the existing command is not replace_command_uuid.
    replace_command_uuid = "3bd47271-a3fa-4627-be97-9f7f69ddeefd"
    rule = FPRule.objects.get(enabled=True, purpose="default_thumbnail")
    if rule.command_id != replace_command_uuid:
        return

    # Static UUIDs
    uuid_new_rule = "3a19f9a3-c5d5-4934-9286-13b3ad6c24d3"
    uuid_new_command = "7c2b65c7-6cea-4f81-9f3b-53375efc5bee"

    # Create new command
    command = FPCommand.objects.create(
        uuid=uuid_new_command,
        description="Using default thumbnail",
        command=REPLACE_COMMAND,
        script_type="pythonScript",
        output_location="%outputDirectory%%postfix%.jpg",
        command_usage="normalization",
        # <FPTool: Archivematica Script version 1.0>
        tool_id="efa8474a-8526-48c3-8279-e5a76bdc0995",
        # <FormatVersion: Image (Raster): JPEG: Generic JPEG>
        output_format_id="ffb55e9a-29f1-4276-a9a5-5ef813229b79",
        # <FPCommand: Standard verification command (file exists only)>
        verification_command_id="ef3ea000-0c3c-4cae-adc2-aa2a6ccbffce",
        replaces=rule.command,
        enabled=True,
    )

    # Disable old command
    rule.command.enabled = False
    rule.command.save()

    # Create new rule
    FPRule.objects.create(
        uuid=uuid_new_rule,
        purpose="default_thumbnail",
        command=command,
        format_id="0ab4cd40-90e7-4d75-b294-498177b3897d",
        replaces=rule,
        enabled=True,
    )

    # Disable old rule
    rule.enabled = False
    rule.save()


class Migration(migrations.Migration):
    dependencies = [("fpr", "0006_i18n_models")]

    operations = [migrations.RunPython(data_migration)]

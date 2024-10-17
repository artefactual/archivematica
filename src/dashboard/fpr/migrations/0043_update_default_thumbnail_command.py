from django.db import migrations

OLD_DEFAULT_THUMBNAIL_CMD_UUID = "95149bc4-0620-4c20-964c-1d6c34b9400e"

DEFAULT_THUMBNAIL_RULES = ("3a19f9a3-c5d5-4934-9286-13b3ad6c24d3",)

NEW_DEFAULT_THUMBNAIL_CMD_UUID = "484d3a8f-9e59-4912-a5b8-f8a2deb3466a"
NEW_DEFAULT_THUMBNAIL_CMD = """
import argparse
import base64
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
    with open(target, 'wb') as f:
        f.write(base64.b64decode(DEFAULT_THUMBNAIL))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-location', required=True)
    args, _ = parser.parse_known_args()

    sys.exit(main(args.output_location))
"""


def data_migration_up(apps, schema_editor):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    # Get the old command
    old_command = FPCommand.objects.get(uuid=OLD_DEFAULT_THUMBNAIL_CMD_UUID)

    # Replace the existing command with the following
    FPCommand.objects.create(
        uuid=NEW_DEFAULT_THUMBNAIL_CMD_UUID,
        replaces_id=OLD_DEFAULT_THUMBNAIL_CMD_UUID,
        tool_id=old_command.tool_id,
        enabled=old_command.enabled,
        command=NEW_DEFAULT_THUMBNAIL_CMD,
        script_type=old_command.script_type,
        command_usage=old_command.command_usage,
        description=old_command.description,
        output_location=old_command.output_location,
        output_format_id=old_command.output_format_id,
        event_detail_command_id=old_command.event_detail_command_id,
        verification_command_id=old_command.verification_command_id,
    )

    # Update existing rules
    FPRule.objects.filter(uuid__in=DEFAULT_THUMBNAIL_RULES).update(
        command_id=NEW_DEFAULT_THUMBNAIL_CMD_UUID,
    )

    # Disable the old command
    old_command.enabled = False
    old_command.save()


def data_migration_down(apps, schema_editor):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    # The order matters. We make sure that the rules point to the previous
    # command before the latter is deleted. Otherwise our rules would be
    # deleted by Django's on cascade mechanism
    FPRule.objects.filter(uuid__in=DEFAULT_THUMBNAIL_RULES).update(
        command_id=OLD_DEFAULT_THUMBNAIL_CMD_UUID,
    )

    # Enable the old command. At this point we do not know if the
    # command was in fact enabled before the migration was run, so
    # this may have unexpected consequences
    old_command = FPCommand.objects.get(uuid=OLD_DEFAULT_THUMBNAIL_CMD_UUID)
    old_command.enabled = True
    old_command.save()

    # Delete the new command
    FPCommand.objects.filter(uuid=NEW_DEFAULT_THUMBNAIL_CMD_UUID).delete()


class Migration(migrations.Migration):
    dependencies = [("fpr", "0042_update_idtools")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

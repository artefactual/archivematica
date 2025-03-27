from django.db import migrations

# This maps the existing FPR format group descriptions with the PRONOM
# classification that should become the new format group descriptions.
FORMAT_GROUP_TO_PRONOM_CLASSIFICATION = {
    "Text (Markup)": "Text (Mark-up)",
    "Word Processing": "Word Processor",
}

NEW_FORMAT_GROUPS = ["Text (Unstructured)"]


def data_migration_up(apps, schema_editor):
    FormatGroup = apps.get_model("fpr", "FormatGroup")

    # Update existing format group descriptions.
    for old_desc, new_desc in FORMAT_GROUP_TO_PRONOM_CLASSIFICATION.items():
        format_groups = FormatGroup.objects.filter(description=old_desc)
        if format_groups.exists():
            format_groups.update(description=new_desc)

    # Add new format groups.
    FormatGroup.objects.bulk_create(
        [
            FormatGroup(description=desc)
            for desc in NEW_FORMAT_GROUPS
            if not FormatGroup.objects.filter(description=desc).exists()
        ]
    )


def data_migration_down(apps, schema_editor):
    FormatGroup = apps.get_model("fpr", "FormatGroup")

    # Revert format groups descriptions.
    for old_desc, new_desc in FORMAT_GROUP_TO_PRONOM_CLASSIFICATION.items():
        format_groups = FormatGroup.objects.filter(description=new_desc)
        if format_groups.exists():
            format_groups.update(description=old_desc)

    # Delete format groups added in this migration.
    FormatGroup.objects.filter(description__in=NEW_FORMAT_GROUPS).delete()


class Migration(migrations.Migration):
    dependencies = [("fpr", "0046_update_jhove_module_validation")]
    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

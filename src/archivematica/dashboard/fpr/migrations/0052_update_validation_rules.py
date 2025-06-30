from django.db import migrations

PRONOM_IDS = (
    "fmt/156",  # Tagged Image File Format for Internet Fax (TIFF-FX)
    "fmt/154",  # Tagged Image File Format for Electronic Photography (TIFF/EP)
    "x-fmt/388",  # Exchangeable Image File Format (Uncompressed) 2.1
    "x-fmt/387",  # Exchangeable Image File Format (Uncompressed) 2.2
    "x-fmt/399",  # Exchangeable Image File Format (Uncompressed) 2.0
    "fmt/153",  # Tagged Image File Format for Image Technology (TIFF/IT)
    "fmt/155",  # Geographic Tagged Image File Format (GeoTIFF)
)


def data_migration_up(apps, schema_editor):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FormatVersion = apps.get_model("fpr", "FormatVersion")
    FPRule = apps.get_model("fpr", "FPRule")

    command = FPCommand.objects.get(description="Validate using JHOVE TIFF-hul")

    for format_version in FormatVersion.objects.filter(pronom_id__in=PRONOM_IDS):
        FPRule.objects.get_or_create(
            purpose="validation", command=command, format=format_version
        )


def data_migration_down(apps, schema_editor):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FormatVersion = apps.get_model("fpr", "FormatVersion")
    FPRule = apps.get_model("fpr", "FPRule")

    command = FPCommand.objects.get(description="Validate using JHOVE TIFF-hul")

    for format_version in FormatVersion.objects.filter(pronom_id__in=PRONOM_IDS):
        FPRule.objects.filter(
            purpose="validation", command=command, format=format_version
        ).delete()


class Migration(migrations.Migration):
    dependencies = [("fpr", "0051_remove_maildir_commands")]
    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

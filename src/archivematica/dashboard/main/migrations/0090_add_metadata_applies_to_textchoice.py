"""Add and backfill TextChoices fields for metadata applies-to values."""

from django.db import migrations
from django.db import models

ALLOWED = {"sip", "transfer", "file"}


def _normalize_description(description):
    """Return the TextChoices value for a legacy type description."""
    if not description:
        return None
    value = description.strip().lower()
    return value if value in ALLOWED else None


def _referenced_ids(model, type_ids):
    """Return sample metadata row IDs that reference legacy type IDs."""
    return list(
        model.objects.filter(metadataappliestotype_id__in=type_ids).values_list(
            "id", flat=True
        )[:20]
    )


def validate_metadata_applies_to_types(apps, schema_editor):
    """Reject referenced legacy metadata types that cannot be mapped safely."""
    MetadataAppliesToType = apps.get_model("main", "MetadataAppliesToType")
    DublinCore = apps.get_model("main", "DublinCore")
    RightsStatement = apps.get_model("main", "RightsStatement")

    invalid_type_ids = [
        str(row.id)
        for row in MetadataAppliesToType.objects.all().only("id", "description")
        if _normalize_description(row.description) is None
    ]
    if not invalid_type_ids:
        return

    dublincore_ids = _referenced_ids(DublinCore, invalid_type_ids)
    rightsstatement_ids = _referenced_ids(RightsStatement, invalid_type_ids)
    if dublincore_ids or rightsstatement_ids:
        raise RuntimeError(
            "Unsupported MetadataAppliesToType rows are referenced by metadata: "
            "type_ids={type_ids}; dublincore_ids={dc_ids}; "
            "rightsstatement_ids={rs_ids}".format(
                type_ids=", ".join(invalid_type_ids),
                dc_ids=", ".join(str(id_) for id_ in dublincore_ids),
                rs_ids=", ".join(str(id_) for id_ in rightsstatement_ids),
            )
        )


def data_migration_up(apps, schema_editor):
    """Backfill metadata applies-to values from the legacy lookup table."""
    MetadataAppliesToType = apps.get_model("main", "MetadataAppliesToType")
    DublinCore = apps.get_model("main", "DublinCore")
    RightsStatement = apps.get_model("main", "RightsStatement")

    type_ids_by_applies_to = {}
    for row in MetadataAppliesToType.objects.all().only("id", "description"):
        applies_to = _normalize_description(row.description)
        if applies_to is not None:
            type_ids_by_applies_to.setdefault(applies_to, []).append(str(row.id))

    for applies_to in ("sip", "transfer", "file"):
        type_ids = type_ids_by_applies_to.get(applies_to, [])
        if not type_ids:
            continue
        DublinCore.objects.filter(metadataappliestotype_id__in=type_ids).update(
            metadata_applies_to=applies_to
        )
        RightsStatement.objects.filter(metadataappliestotype_id__in=type_ids).update(
            metadata_applies_to=applies_to
        )

    dublincore_ids = list(
        DublinCore.objects.filter(metadata_applies_to__isnull=True).values_list(
            "id", flat=True
        )[:20]
    )
    rightsstatement_ids = list(
        RightsStatement.objects.filter(metadata_applies_to__isnull=True).values_list(
            "id", flat=True
        )[:20]
    )
    if dublincore_ids or rightsstatement_ids:
        raise RuntimeError(
            "Unable to backfill metadata_applies_to for all metadata rows: "
            "dublincore_ids={dc_ids}; rightsstatement_ids={rs_ids}".format(
                dc_ids=", ".join(str(id_) for id_ in dublincore_ids),
                rs_ids=", ".join(str(id_) for id_ in rightsstatement_ids),
            )
        )


def data_migration_down(apps, schema_editor):
    """No-op reverse step because the forward migration only copies data."""
    return


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0089_remove_job_subjobof"),
    ]

    operations = [
        migrations.RunPython(
            validate_metadata_applies_to_types,
            reverse_code=data_migration_down,
        ),
        migrations.AddField(
            model_name="dublincore",
            name="metadata_applies_to",
            field=models.CharField(
                blank=True,
                choices=[("sip", "SIP"), ("transfer", "Transfer"), ("file", "File")],
                db_column="metadataAppliesTo",
                max_length=8,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="rightsstatement",
            name="metadata_applies_to",
            field=models.CharField(
                blank=True,
                choices=[("sip", "SIP"), ("transfer", "Transfer"), ("file", "File")],
                db_column="metadataAppliesTo",
                max_length=8,
                null=True,
            ),
        ),
        migrations.RunPython(
            data_migration_up,
            reverse_code=data_migration_down,
        ),
        migrations.AlterField(
            model_name="dublincore",
            name="metadata_applies_to",
            field=models.CharField(
                choices=[("sip", "SIP"), ("transfer", "Transfer"), ("file", "File")],
                db_column="metadataAppliesTo",
                max_length=8,
            ),
        ),
        migrations.AlterField(
            model_name="rightsstatement",
            name="metadata_applies_to",
            field=models.CharField(
                choices=[("sip", "SIP"), ("transfer", "Transfer"), ("file", "File")],
                db_column="metadataAppliesTo",
                max_length=8,
            ),
        ),
    ]

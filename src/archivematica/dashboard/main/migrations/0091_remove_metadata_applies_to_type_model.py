"""Remove legacy metadata applies-to foreign keys and lookup table."""

from django.db import migrations
from django.db import models

SIP_TYPE = "3e48343d-e2d2-4956-aaa3-b54d26eb9761"
TRANSFER_TYPE = "45696327-44c5-4e78-849b-e027a189bf4d"
FILE_TYPE = "7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17"
TYPE_BY_APPLIES_TO = {
    "sip": (SIP_TYPE, "SIP"),
    "transfer": (TRANSFER_TYPE, "Transfer"),
    "file": (FILE_TYPE, "File"),
}


def data_migration_up(apps, schema_editor):
    """No-op forward step paired with reverse FK restoration."""
    return


def data_migration_down(apps, schema_editor):
    """Restore canonical legacy rows and FK values when reversing cleanup."""
    MetadataAppliesToType = apps.get_model("main", "MetadataAppliesToType")
    DublinCore = apps.get_model("main", "DublinCore")
    RightsStatement = apps.get_model("main", "RightsStatement")

    for applies_to, (type_id, description) in TYPE_BY_APPLIES_TO.items():
        MetadataAppliesToType.objects.update_or_create(
            id=type_id,
            defaults={
                "description": description,
                "replaces": None,
            },
        )
        DublinCore.objects.filter(metadata_applies_to=applies_to).update(
            metadataappliestotype_id=type_id
        )
        RightsStatement.objects.filter(metadata_applies_to=applies_to).update(
            metadataappliestotype_id=type_id
        )


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0090_add_metadata_applies_to_textchoice"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="dublincore",
            constraint=models.CheckConstraint(
                condition=models.Q(metadata_applies_to__in=("sip", "transfer", "file")),
                name="dublincore_metadata_applies_to_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="rightsstatement",
            constraint=models.CheckConstraint(
                condition=models.Q(metadata_applies_to__in=("sip", "transfer", "file")),
                name="rightsstatement_metadata_applies_to_valid",
            ),
        ),
        migrations.AddIndex(
            model_name="dublincore",
            index=models.Index(
                fields=["metadata_applies_to", "metadataappliestoidentifier"],
                name="Dublincore_metadat_a3f17c_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="rightsstatement",
            index=models.Index(
                fields=["metadata_applies_to", "metadataappliestoidentifier"],
                name="RightsState_metadat_d1bc34_idx",
            ),
        ),
        # State-only: reverse needs nullable legacy FK columns so it can
        # recreate canonical type rows and backfill before returning to 0090.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="dublincore",
                    name="metadataappliestotype",
                    field=models.ForeignKey(
                        db_column="metadataAppliesToType",
                        null=True,
                        on_delete=models.CASCADE,
                        to="main.metadataappliestotype",
                    ),
                ),
                migrations.AlterField(
                    model_name="rightsstatement",
                    name="metadataappliestotype",
                    field=models.ForeignKey(
                        db_column="metadataAppliesToType",
                        null=True,
                        on_delete=models.CASCADE,
                        to="main.metadataappliestotype",
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            data_migration_up,
            reverse_code=data_migration_down,
        ),
        migrations.RemoveField(
            model_name="dublincore",
            name="metadataappliestotype",
        ),
        migrations.RemoveField(
            model_name="rightsstatement",
            name="metadataappliestotype",
        ),
        migrations.DeleteModel(
            name="MetadataAppliesToType",
        ),
    ]

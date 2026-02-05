from django.db import migrations
from django.db import models


def data_migration_up(apps, schema_editor):
    """Upgrade createdTime precision and backfill microseconds on MySQL."""
    if schema_editor.connection.vendor != "mysql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE Jobs MODIFY COLUMN createdTime DATETIME(6) NOT NULL;"
        )
        cursor.execute(
            """
            UPDATE Jobs
            SET createdTime = DATE_ADD(
                createdTime,
                INTERVAL LEAST(
                    999999,
                    GREATEST(0, CAST(ROUND(createdTimeDec * 1000000) AS SIGNED))
                ) MICROSECOND
            )
            WHERE createdTimeDec IS NOT NULL
              AND createdTimeDec > 0
              AND MICROSECOND(createdTime) = 0;
            """
        )


def data_migration_down(apps, schema_editor):
    """No-op reverse step to avoid lossy truncation of microsecond data."""
    return


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0087_remove_dead_rights_holder_code"),
    ]

    atomic = False

    operations = [
        migrations.RunPython(
            data_migration_up,
            reverse_code=data_migration_down,
        ),
        migrations.RemoveIndex(
            model_name="job",
            name="Jobs_unitTyp_10447a_idx",
        ),
        migrations.RemoveIndex(
            model_name="job",
            name="Jobs_SIPUUID_cf4b11_idx",
        ),
        migrations.RemoveIndex(
            model_name="job",
            name="Jobs_SIPUUID_6cf6c1_idx",
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(
                fields=("sipuuid", "createdtime", "jobuuid"),
                name="jobs_sipuuid_ctime_juidx",
            ),
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(
                fields=("sipuuid", "jobtype", "createdtime", "jobuuid"),
                name="jobs_sipuuid_jt_ctime_juidx",
            ),
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(
                fields=("unittype", "sipuuid", "createdtime", "jobuuid"),
                name="jobs_unit_sip_ctime_juidx",
            ),
        ),
        migrations.RemoveField(
            model_name="job",
            name="createdtimedec",
        ),
    ]

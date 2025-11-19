from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0084_alter_job_index_together"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="file",
            new_name="Files_sipUUID_a0d05d_idx",
            old_fields=("sip", "filegrpuse"),
        ),
        migrations.RenameIndex(
            model_name="job",
            new_name="Jobs_jobType_4a3346_idx",
            old_fields=("jobtype", "currentstep"),
        ),
        migrations.RenameIndex(
            model_name="job",
            new_name="Jobs_unitTyp_10447a_idx",
            old_fields=("unittype", "sipuuid", "createdtime", "createdtimedec"),
        ),
        migrations.RenameIndex(
            model_name="job",
            new_name="Jobs_SIPUUID_cf4b11_idx",
            old_fields=("sipuuid", "jobtype", "createdtime", "createdtimedec"),
        ),
        migrations.RenameIndex(
            model_name="job",
            new_name="Jobs_SIPUUID_6cf6c1_idx",
            old_fields=("sipuuid", "createdtime", "createdtimedec"),
        ),
        migrations.RenameIndex(
            model_name="job",
            new_name="Jobs_SIPUUID_658a37_idx",
            old_fields=(
                "sipuuid",
                "currentstep",
                "microservicegroup",
                "microservicechainlink",
            ),
        ),
    ]

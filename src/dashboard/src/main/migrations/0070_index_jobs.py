from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("main", "0069_remove_atk")]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="sipuuid",
            field=models.CharField(max_length=36, db_column="SIPUUID", db_index=True),
        ),
        migrations.AlterIndexTogether(
            name="job",
            index_together={
                ("sipuuid", "createdtime", "createdtimedec"),
                (
                    "sipuuid",
                    "currentstep",
                    "microservicegroup",
                    "microservicechainlink",
                ),
                ("sipuuid", "jobtype", "createdtime", "createdtimedec"),
                ("jobtype", "currentstep"),
            },
        ),
    ]

"""Migration to update "Resume after normalization file identification tool
selected." chain link to exit with the successful status.
"""

from django.db import migrations
from main.models import Job

# Can't use apps.get_model for this model as we need to access class attributes.


# Link: "Resume after normalization file identification tool selected."
mscl_id = "83484326-7be7-4f9f-b252-94553cd42370"


def data_migration_up(apps, schema_editor):
    mscl = apps.get_model("main", "MicroServiceChainLink")

    mscl.objects.filter(pk=mscl_id).update(
        defaultexitmessage=Job.STATUS_COMPLETED_SUCCESSFULLY
    )


def data_migration_down(apps, schema_editor):
    mscl = apps.get_model("main", "MicroServiceChainLink")

    mscl.objects.filter(pk=mscl_id).update(defaultexitmessage=Job.STATUS_FAILED)


class Migration(migrations.Migration):
    dependencies = [("main", "0057_7zip_no_compression")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

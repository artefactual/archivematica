import main.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("main", "0022_email_report_args")]

    operations = [
        migrations.AlterField(
            model_name="file",
            name="currentlocation",
            field=main.models.BlobTextField(null=True, db_column="currentLocation"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="file",
            name="originallocation",
            field=main.models.BlobTextField(db_column="originalLocation"),
            preserve_default=True,
        ),
    ]

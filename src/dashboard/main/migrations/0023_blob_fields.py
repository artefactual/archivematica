from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [("main", "0022_email_report_args")]

    operations = [
        migrations.AlterField(
            model_name="file",
            name="currentlocation",
            field=models.BinaryField(null=True, db_column="currentLocation"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="file",
            name="originallocation",
            field=models.BinaryField(db_column="originalLocation"),
            preserve_default=True,
        ),
    ]

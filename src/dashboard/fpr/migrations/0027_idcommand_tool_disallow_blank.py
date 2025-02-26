from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [("fpr", "0026_fits_nailgun_compat")]

    operations = [
        migrations.AlterField(
            model_name="idcommand",
            name="tool",
            field=models.ForeignKey(
                verbose_name="the related tool",
                to_field="uuid",
                to="fpr.IDTool",
                null=True,
                on_delete=models.CASCADE,
            ),
        )
    ]

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("fpr", "0017_ocr_unique_names")]

    operations = [
        migrations.AlterField(
            model_name="format",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                editable=False,
                populate_from="description",
                unique=True,
                verbose_name="slug",
            ),
        ),
        migrations.AlterField(
            model_name="formatgroup",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                editable=False,
                populate_from="description",
                unique=True,
                verbose_name="slug",
            ),
        ),
        migrations.AlterField(
            model_name="fptool",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                editable=False, populate_from="_slug", unique=True, verbose_name="slug"
            ),
        ),
        migrations.AlterField(
            model_name="idtool",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                editable=False,
                populate_from="_slug",
                always_update=True,
                unique=True,
                verbose_name="slug",
            ),
        ),
    ]

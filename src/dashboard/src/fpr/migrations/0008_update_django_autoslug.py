import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("fpr", "0007_embedded_default_thumbnail")]

    operations = [
        migrations.AlterField(
            model_name="format",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                populate_from="description", verbose_name="slug", editable=False
            ),
        ),
        migrations.AlterField(
            model_name="formatgroup",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                populate_from="description", verbose_name="slug", editable=False
            ),
        ),
        migrations.AlterField(
            model_name="formatversion",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                always_update=True,
                populate_from="description",
                unique_with=("format",),
                editable=False,
            ),
        ),
        migrations.AlterField(
            model_name="fptool",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                populate_from="_slug", verbose_name="slug", editable=False
            ),
        ),
        migrations.AlterField(
            model_name="idtool",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                editable=False,
                populate_from="_slug",
                always_update=True,
                verbose_name="slug",
            ),
        ),
    ]

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0085_rename_indexes"),
    ]

    operations = [
        migrations.DeleteModel(
            name="LevelOfDescription",
        ),
        migrations.RemoveField(
            model_name="siparrange",
            name="sip",
        ),
        migrations.DeleteModel(
            name="SIPArrangeAccessMapping",
        ),
        migrations.DeleteModel(
            name="SIPArrange",
        ),
    ]

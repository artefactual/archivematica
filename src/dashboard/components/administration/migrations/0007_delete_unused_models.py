from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("administration", "0006_use_statement_optional"),
        ("main", "0032_dashboardsetting_scope"),
    ]

    operations = [
        migrations.DeleteModel(name="ArchivesSpaceConfig"),
        migrations.DeleteModel(name="ArchivistsToolkitConfig"),
        migrations.DeleteModel(name="ReplacementDict"),
    ]

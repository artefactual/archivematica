from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("main", "0071_index_unitvariables_runsql")]

    operations = [
        migrations.AlterIndexTogether(
            name="file", index_together={("sip", "filegrpuse")}
        )
    ]

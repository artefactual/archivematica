from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0086_remove_appraisal"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="rightsstatement",
            name="rightsholder",
        ),
        migrations.DeleteModel(
            name="RightsStatementLinkingAgentIdentifier",
        ),
    ]

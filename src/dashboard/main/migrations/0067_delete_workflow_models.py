import uuid

import main.models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("main", "0066_archivesspace_base_url")]

    operations = [
        migrations.RemoveField(model_name="microservicechain", name="replaces"),
        migrations.RemoveField(model_name="microservicechain", name="startinglink"),
        migrations.RemoveField(
            model_name="microservicechainchoice", name="chainavailable"
        ),
        migrations.RemoveField(
            model_name="microservicechainchoice", name="choiceavailableatlink"
        ),
        migrations.RemoveField(model_name="microservicechainchoice", name="replaces"),
        migrations.RemoveField(model_name="microservicechainlink", name="currenttask"),
        migrations.RemoveField(
            model_name="microservicechainlink", name="defaultnextchainlink"
        ),
        migrations.RemoveField(model_name="microservicechainlink", name="replaces"),
        migrations.RemoveField(
            model_name="microservicechainlinkexitcode", name="microservicechainlink"
        ),
        migrations.RemoveField(
            model_name="microservicechainlinkexitcode", name="nextmicroservicechainlink"
        ),
        migrations.RemoveField(
            model_name="microservicechainlinkexitcode", name="replaces"
        ),
        migrations.RemoveField(
            model_name="microservicechoicereplacementdic", name="choiceavailableatlink"
        ),
        migrations.RemoveField(
            model_name="microservicechoicereplacementdic", name="replaces"
        ),
        migrations.RemoveField(model_name="standardtaskconfig", name="replaces"),
        migrations.RemoveField(model_name="taskconfig", name="replaces"),
        migrations.RemoveField(model_name="taskconfig", name="tasktype"),
        migrations.RemoveField(
            model_name="taskconfigsetunitvariable", name="microservicechainlink"
        ),
        migrations.RemoveField(
            model_name="taskconfigunitvariablelinkpull",
            name="defaultmicroservicechainlink",
        ),
        migrations.RemoveField(model_name="tasktype", name="replaces"),
        migrations.RemoveField(model_name="watcheddirectory", name="chain"),
        migrations.RemoveField(model_name="watcheddirectory", name="expected_type"),
        migrations.RemoveField(model_name="watcheddirectory", name="replaces"),
        migrations.RemoveField(
            model_name="watcheddirectoryexpectedtype", name="replaces"
        ),
        migrations.AlterField(
            model_name="job",
            name="microservicechainlink",
            field=main.models.UUIDField(
                max_length=36,
                null=True,
                editable=False,
                db_column="MicroServiceChainLinksPK",
                blank=True,
                default=uuid.uuid4,
            ),
        ),
        migrations.AlterField(
            model_name="unitvariable",
            name="microservicechainlink",
            field=main.models.UUIDField(
                max_length=36,
                null=True,
                editable=False,
                db_column="microServiceChainLink",
                blank=True,
                default=uuid.uuid4,
            ),
        ),
        migrations.DeleteModel(name="MicroServiceChain"),
        migrations.DeleteModel(name="MicroServiceChainChoice"),
        migrations.DeleteModel(name="MicroServiceChainLink"),
        migrations.DeleteModel(name="MicroServiceChainLinkExitCode"),
        migrations.DeleteModel(name="MicroServiceChoiceReplacementDic"),
        migrations.DeleteModel(name="StandardTaskConfig"),
        migrations.DeleteModel(name="TaskConfig"),
        migrations.DeleteModel(name="TaskConfigSetUnitVariable"),
        migrations.DeleteModel(name="TaskConfigUnitVariableLinkPull"),
        migrations.DeleteModel(name="TaskType"),
        migrations.DeleteModel(name="WatchedDirectory"),
        migrations.DeleteModel(name="WatchedDirectoryExpectedType"),
    ]

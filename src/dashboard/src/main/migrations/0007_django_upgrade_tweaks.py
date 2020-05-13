# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("main", "0006_levelofdescription")]

    operations = [
        migrations.AlterField(
            model_name="agent",
            name="identifiertype",
            field=models.TextField(
                null=True,
                verbose_name="Agent Identifier Type",
                db_column="agentIdentifierType",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="agent",
            name="identifiervalue",
            field=models.TextField(
                help_text="Used for premis:agentIdentifierValue and premis:linkingAgentIdentifierValue in the METS file.",
                null=True,
                verbose_name="Agent Identifier Value",
                db_column="agentIdentifierValue",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="agent",
            name="name",
            field=models.TextField(
                help_text="Used for premis:agentName in the METS file.",
                null=True,
                verbose_name="Agent Name",
                db_column="agentName",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="microservicechainlink",
            name="defaultnextchainlink",
            field=models.ForeignKey(
                db_column="defaultNextChainLink",
                blank=True,
                to="main.MicroServiceChainLink",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="microservicechainlink",
            name="replaces",
            field=models.ForeignKey(
                related_name="replaced_by",
                db_column="replaces",
                blank=True,
                to="main.MicroServiceChainLink",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="microservicechoicereplacementdic",
            name="lastmodified",
            field=models.DateTimeField(auto_now=True, db_column="lastModified"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementcopyright",
            name="copyrightenddateopen",
            field=models.BooleanField(
                default=False,
                help_text="Indicate end date is open",
                verbose_name="Open End Date",
                db_column="copyrightApplicableEndDateOpen",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementlicense",
            name="licenseenddateopen",
            field=models.BooleanField(
                default=False,
                help_text="Indicate end date is open",
                verbose_name="Open End Date",
                db_column="licenseApplicableEndDateOpen",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementotherrightsinformation",
            name="otherrightsenddateopen",
            field=models.BooleanField(
                default=False,
                help_text="Indicate end date is open",
                verbose_name="Open End Date",
                db_column="otherRightsApplicableEndDateOpen",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementrightsgranted",
            name="enddateopen",
            field=models.BooleanField(
                default=False,
                help_text="Indicate end date is open",
                verbose_name="Open End Date",
                db_column="endDateOpen",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementstatuteinformation",
            name="statuteenddateopen",
            field=models.BooleanField(
                default=False,
                help_text="Indicate end date is open",
                verbose_name="Open End Date",
                db_column="statuteApplicableEndDateOpen",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="dublincore",
            name="date",
            field=models.TextField(
                help_text="Use ISO 8601 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)",
                db_column="date",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="microservicechain",
            name="replaces",
            field=models.ForeignKey(
                related_name="replaced_by",
                db_column="replaces",
                blank=True,
                to="main.MicroServiceChain",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementrightsgrantednote",
            name="rightsgranted",
            field=models.ForeignKey(
                related_name="notes",
                db_column="fkRightsStatementRightsGranted",
                to="main.RightsStatementRightsGranted",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementrightsgrantedrestriction",
            name="rightsgranted",
            field=models.ForeignKey(
                related_name="restrictions",
                db_column="fkRightsStatementRightsGranted",
                to="main.RightsStatementRightsGranted",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
    ]

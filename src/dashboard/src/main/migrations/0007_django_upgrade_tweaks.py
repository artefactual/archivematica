# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_levelofdescription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agent',
            name='identifiertype',
            field=models.TextField(null=True, verbose_name=b'Agent Identifier Type', db_column=b'agentIdentifierType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='agent',
            name='identifiervalue',
            field=models.TextField(help_text=b'Used for premis:agentIdentifierValue and premis:linkingAgentIdentifierValue in the METS file.', null=True, verbose_name=b'Agent Identifier Value', db_column=b'agentIdentifierValue'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='agent',
            name='name',
            field=models.TextField(help_text=b'Used for premis:agentName in the METS file.', null=True, verbose_name=b'Agent Name', db_column=b'agentName'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='microservicechainlink',
            name='defaultnextchainlink',
            field=models.ForeignKey(db_column=b'defaultNextChainLink', blank=True, to='main.MicroServiceChainLink', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='microservicechainlink',
            name='replaces',
            field=models.ForeignKey(related_name='replaced_by', db_column=b'replaces', blank=True, to='main.MicroServiceChainLink', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='microservicechoicereplacementdic',
            name='lastmodified',
            field=models.DateTimeField(auto_now=True, db_column=b'lastModified'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementcopyright',
            name='copyrightenddateopen',
            field=models.BooleanField(default=False, help_text=b'Indicate end date is open', verbose_name=b'Open End Date', db_column=b'copyrightApplicableEndDateOpen'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementlicense',
            name='licenseenddateopen',
            field=models.BooleanField(default=False, help_text=b'Indicate end date is open', verbose_name=b'Open End Date', db_column=b'licenseApplicableEndDateOpen'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementotherrightsinformation',
            name='otherrightsenddateopen',
            field=models.BooleanField(default=False, help_text=b'Indicate end date is open', verbose_name=b'Open End Date', db_column=b'otherRightsApplicableEndDateOpen'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementrightsgranted',
            name='enddateopen',
            field=models.BooleanField(default=False, help_text=b'Indicate end date is open', verbose_name=b'Open End Date', db_column=b'endDateOpen'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementstatuteinformation',
            name='statuteenddateopen',
            field=models.BooleanField(default=False, help_text=b'Indicate end date is open', verbose_name=b'Open End Date', db_column=b'statuteApplicableEndDateOpen'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dublincore',
            name='date',
            field=models.TextField(help_text=b'Use ISO 8601 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)', db_column=b'date', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='microservicechain',
            name='replaces',
            field=models.ForeignKey(related_name='replaced_by', db_column=b'replaces', blank=True, to='main.MicroServiceChain', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementrightsgrantednote',
            name='rightsgranted',
            field=models.ForeignKey(related_name='notes', db_column=b'fkRightsStatementRightsGranted', to='main.RightsStatementRightsGranted'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementrightsgrantedrestriction',
            name='rightsgranted',
            field=models.ForeignKey(related_name='restrictions', db_column=b'fkRightsStatementRightsGranted', to='main.RightsStatementRightsGranted'),
            preserve_default=True,
        ),
    ]

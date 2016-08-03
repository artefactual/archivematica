# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import main.models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('fpr', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Access',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('sipuuid', models.CharField(max_length=36, db_column=b'SIPUUID', blank=True)),
                ('resource', models.TextField(db_column=b'resource', blank=True)),
                ('target', models.TextField(db_column=b'target', blank=True)),
                ('status', models.TextField(db_column=b'status', blank=True)),
                ('statuscode', models.PositiveSmallIntegerField(null=True, db_column=b'statusCode', blank=True)),
                ('exitcode', models.PositiveSmallIntegerField(null=True, db_column=b'exitCode', blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, db_column=b'createdTime')),
                ('updatedtime', models.DateTimeField(auto_now=True, db_column=b'updatedTime')),
            ],
            options={
                'db_table': 'Accesses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('identifiertype', models.TextField(db_column=b'agentIdentifierType')),
                ('identifiervalue', models.TextField(db_column=b'agentIdentifierValue')),
                ('name', models.TextField(db_column=b'agentName')),
                ('agenttype', models.TextField(db_column=b'agentType')),
            ],
            options={
                'db_table': 'Agents',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AtkDIPObjectResourcePairing',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('dipuuid', models.CharField(max_length=50, db_column=b'dipUUID')),
                ('fileuuid', models.CharField(max_length=50, db_column=b'fileUUID')),
                ('resourceid', models.IntegerField(db_column=b'resourceId')),
                ('resourcecomponentid', models.IntegerField(db_column=b'resourceComponentId')),
            ],
            options={
                'db_table': 'AtkDIPObjectResourcePairing',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DashboardSetting',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('name', models.CharField(max_length=255, db_column=b'name')),
                ('value', models.TextField(db_column=b'value', blank=True)),
                ('lastmodified', models.DateTimeField(auto_now=True, db_column=b'lastModified')),
            ],
            options={
                'db_table': 'DashboardSettings',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Derivation',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
            ],
            options={
                'db_table': 'Derivations',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DublinCore',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('metadataappliestoidentifier', models.CharField(max_length=36, db_column=b'metadataAppliesToidentifier')),
                ('title', models.TextField(db_column=b'title', blank=True)),
                ('is_part_of', models.TextField(help_text=b'Optional: leave blank if unsure', verbose_name=b'Part of AIC', db_column=b'isPartOf', blank=True)),
                ('creator', models.TextField(db_column=b'creator', blank=True)),
                ('subject', models.TextField(db_column=b'subject', blank=True)),
                ('description', models.TextField(db_column=b'description', blank=True)),
                ('publisher', models.TextField(db_column=b'publisher', blank=True)),
                ('contributor', models.TextField(db_column=b'contributor', blank=True)),
                ('date', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)', db_column=b'date', blank=True)),
                ('type', models.TextField(db_column=b'type', blank=True)),
                ('format', models.TextField(db_column=b'format', blank=True)),
                ('identifier', models.TextField(db_column=b'identifier', blank=True)),
                ('source', models.TextField(db_column=b'source', blank=True)),
                ('relation', models.TextField(db_column=b'relation', blank=True)),
                ('language', models.TextField(help_text=b'Use ISO 639', db_column=b'language', blank=True)),
                ('coverage', models.TextField(db_column=b'coverage', blank=True)),
                ('rights', models.TextField(db_column=b'rights', blank=True)),
            ],
            options={
                'db_table': 'Dublincore',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('event_id', django_extensions.db.fields.UUIDField(null=True, db_column=b'eventIdentifierUUID', editable=False, max_length=36, blank=True, unique=True)),
                ('event_type', models.TextField(db_column=b'eventType', blank=True)),
                ('event_datetime', models.DateTimeField(auto_now=True, db_column=b'eventDateTime')),
                ('event_detail', models.TextField(db_column=b'eventDetail', blank=True)),
                ('event_outcome', models.TextField(db_column=b'eventOutcome', blank=True)),
                ('event_outcome_detail', models.TextField(db_column=b'eventOutcomeDetailNote', blank=True)),
                ('linking_agent', models.IntegerField(null=True, db_column=b'linkingAgentIdentifier')),
            ],
            options={
                'db_table': 'Events',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'fileUUID')),
                ('originallocation', models.TextField(db_column=b'originalLocation')),
                ('currentlocation', models.TextField(db_column=b'currentLocation')),
                ('filegrpuse', models.CharField(default=b'Original', max_length=50, db_column=b'fileGrpUse')),
                ('filegrpuuid', models.CharField(max_length=36, db_column=b'fileGrpUUID', blank=True)),
                ('checksum', models.CharField(max_length=100, db_column=b'checksum', blank=True)),
                ('size', models.BigIntegerField(null=True, db_column=b'fileSize', blank=True)),
                ('label', models.TextField(blank=True)),
                ('enteredsystem', models.DateTimeField(auto_now_add=True, db_column=b'enteredSystem')),
                ('removedtime', models.DateTimeField(default=None, null=True, db_column=b'removedTime')),
            ],
            options={
                'db_table': 'Files',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileFormatVersion',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('file_uuid', models.ForeignKey(to='main.File', db_column=b'fileUUID')),
                ('format_version', models.ForeignKey(to='fpr.FormatVersion', db_column=b'fileID', to_field=b'uuid')),
            ],
            options={
                'db_table': 'FilesIdentifiedIDs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileID',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('format_name', models.TextField(db_column=b'formatName', blank=True)),
                ('format_version', models.TextField(db_column=b'formatVersion', blank=True)),
                ('format_registry_name', models.TextField(db_column=b'formatRegistryName', blank=True)),
                ('format_registry_key', models.TextField(db_column=b'formatRegistryKey', blank=True)),
                ('file', models.ForeignKey(db_column=b'fileUUID', blank=True, to='main.File', null=True)),
            ],
            options={
                'db_table': 'FilesIDs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FPCommandOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(null=True)),
                ('file', models.ForeignKey(to='main.File', db_column=b'fileUUID')),
                ('rule', models.ForeignKey(to='fpr.FPRule', db_column=b'ruleUUID', to_field=b'uuid')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('jobuuid', django_extensions.db.fields.UUIDField(primary_key=True, db_column=b'jobUUID', serialize=False, editable=False, max_length=36, blank=True)),
                ('jobtype', models.CharField(max_length=250, db_column=b'jobType', blank=True)),
                ('createdtime', models.DateTimeField(db_column=b'createdTime')),
                ('createdtimedec', models.DecimalField(default=0.0, decimal_places=10, max_digits=26, db_column=b'createdTimeDec')),
                ('directory', models.TextField(blank=True)),
                ('sipuuid', models.CharField(max_length=36, db_column=b'SIPUUID')),
                ('unittype', models.CharField(max_length=50, db_column=b'unitType', blank=True)),
                ('currentstep', models.CharField(max_length=50, db_column=b'currentStep', blank=True)),
                ('microservicegroup', models.CharField(max_length=50, db_column=b'microserviceGroup', blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('subjobof', models.CharField(max_length=36, db_column=b'subJobOf', blank=True)),
            ],
            options={
                'db_table': 'Jobs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MetadataAppliesToType',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('description', models.CharField(max_length=50, db_column=b'description')),
                ('replaces', models.CharField(max_length=36, null=True, db_column=b'replaces', blank=True)),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
            ],
            options={
                'db_table': 'MetadataAppliesToTypes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MicroServiceChain',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('description', models.TextField(db_column=b'description')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
                ('replaces', models.ForeignKey(related_name='replaced_by', db_column=b'replaces', to='main.MicroServiceChain', null=True)),
            ],
            options={
                'db_table': 'MicroServiceChains',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MicroServiceChainChoice',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
                ('chainavailable', models.ForeignKey(to='main.MicroServiceChain', db_column=b'chainAvailable')),
            ],
            options={
                'db_table': 'MicroServiceChainChoice',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MicroServiceChainLink',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('microservicegroup', models.CharField(max_length=50, db_column=b'microserviceGroup')),
                ('reloadfilelist', models.BooleanField(default=True, db_column=b'reloadFileList')),
                ('defaultexitmessage', models.CharField(default=b'Failed', max_length=36, db_column=b'defaultExitMessage')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
            ],
            options={
                'db_table': 'MicroServiceChainLinks',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MicroServiceChainLinkExitCode',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('exitcode', models.IntegerField(default=0, db_column=b'exitCode')),
                ('exitmessage', models.CharField(default=b'Completed successfully', max_length=50, db_column=b'exitMessage')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
                ('microservicechainlink', models.ForeignKey(related_name='exit_codes', db_column=b'microServiceChainLink', to='main.MicroServiceChainLink')),
                ('nextmicroservicechainlink', models.ForeignKey(related_name='parent_exit_codes+', db_column=b'nextMicroServiceChainLink', blank=True, to='main.MicroServiceChainLink', null=True)),
                ('replaces', models.ForeignKey(related_name='replaced_by', db_column=b'replaces', blank=True, to='main.MicroServiceChainLinkExitCode', null=True)),
            ],
            options={
                'db_table': 'MicroServiceChainLinksExitCodes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MicroServiceChoiceReplacementDic',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('description', models.TextField(verbose_name=b'Description', db_column=b'description')),
                ('replacementdic', models.TextField(verbose_name=b'Configuration', db_column=b'replacementDic')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
                ('choiceavailableatlink', models.ForeignKey(to='main.MicroServiceChainLink', db_column=b'choiceAvailableAtLink')),
                ('replaces', models.ForeignKey(related_name='replaced_by', db_column=b'replaces', blank=True, to='main.MicroServiceChoiceReplacementDic', null=True)),
            ],
            options={
                'db_table': 'MicroServiceChoiceReplacementDic',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('unittype', models.CharField(max_length=50, db_column=b'unitType')),
                ('unitname', models.CharField(max_length=50, db_column=b'unitName')),
                ('unitidentifier', models.CharField(max_length=36, db_column=b'unitIdentifier')),
                ('content', models.TextField(db_column=b'content')),
                ('created', models.DateTimeField(auto_now_add=True, db_column=b'created')),
            ],
            options={
                'db_table': 'Reports',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatement',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('metadataappliestoidentifier', models.CharField(max_length=50, db_column=b'metadataAppliesToidentifier')),
                ('rightsstatementidentifiertype', models.TextField(verbose_name=b'Type', db_column=b'rightsStatementIdentifierType', blank=True)),
                ('rightsstatementidentifiervalue', models.TextField(verbose_name=b'Value', db_column=b'rightsStatementIdentifierValue', blank=True)),
                ('rightsholder', models.IntegerField(default=0, verbose_name=b'Rights holder', db_column=b'fkAgent')),
                ('rightsbasis', models.TextField(verbose_name=b'Basis', db_column=b'rightsBasis')),
                ('metadataappliestotype', models.ForeignKey(to='main.MetadataAppliesToType', db_column=b'metadataAppliesToType')),
            ],
            options={
                'db_table': 'RightsStatement',
                'verbose_name': 'Rights Statement',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementCopyright',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('copyrightstatus', models.TextField(verbose_name=b'Copyright status', db_column=b'copyrightStatus', blank=True)),
                ('copyrightjurisdiction', models.TextField(verbose_name=b'Copyright jurisdiction', db_column=b'copyrightJurisdiction', blank=True)),
                ('copyrightstatusdeterminationdate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'Copyright determination date', db_column=b'copyrightStatusDeterminationDate', blank=True)),
                ('copyrightapplicablestartdate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'Copyright start date', db_column=b'copyrightApplicableStartDate', blank=True)),
                ('copyrightapplicableenddate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'Copyright end date', db_column=b'copyrightApplicableEndDate', blank=True)),
                ('copyrightenddateopen', models.BooleanField(help_text=b'Indicate end date is open', verbose_name=b'Open End Date', db_column=b'copyrightApplicableEndDateOpen')),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementCopyright',
                'verbose_name': 'Rights: Copyright',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementCopyrightDocumentationIdentifier',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('copyrightdocumentationidentifiertype', models.TextField(verbose_name=b'Copyright document identification type', db_column=b'copyrightDocumentationIdentifierType', blank=True)),
                ('copyrightdocumentationidentifiervalue', models.TextField(verbose_name=b'Copyright document identification value', db_column=b'copyrightDocumentationIdentifierValue', blank=True)),
                ('copyrightdocumentationidentifierrole', models.TextField(verbose_name=b'Copyright document identification role', db_column=b'copyrightDocumentationIdentifierRole', blank=True)),
                ('rightscopyright', models.ForeignKey(to='main.RightsStatementCopyright', db_column=b'fkRightsStatementCopyrightInformation')),
            ],
            options={
                'db_table': 'RightsStatementCopyrightDocumentationIdentifier',
                'verbose_name': 'Rights: Copyright: Docs ID',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementCopyrightNote',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('copyrightnote', models.TextField(verbose_name=b'Copyright note', db_column=b'copyrightNote', blank=True)),
                ('rightscopyright', models.ForeignKey(to='main.RightsStatementCopyright', db_column=b'fkRightsStatementCopyrightInformation')),
            ],
            options={
                'db_table': 'RightsStatementCopyrightNote',
                'verbose_name': 'Rights: Copyright: Note',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementLicense',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('licenseterms', models.TextField(verbose_name=b'License terms', db_column=b'licenseTerms', blank=True)),
                ('licenseapplicablestartdate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'License start date', db_column=b'licenseApplicableStartDate', blank=True)),
                ('licenseapplicableenddate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'License end date', db_column=b'licenseApplicableEndDate', blank=True)),
                ('licenseenddateopen', models.BooleanField(help_text=b'Indicate end date is open', verbose_name=b'Open End Date', db_column=b'licenseApplicableEndDateOpen')),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementLicense',
                'verbose_name': 'Rights: License',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementLicenseDocumentationIdentifier',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('licensedocumentationidentifiertype', models.TextField(verbose_name=b'License documentation identification type', db_column=b'licenseDocumentationIdentifierType', blank=True)),
                ('licensedocumentationidentifiervalue', models.TextField(verbose_name=b'License documentation identification value', db_column=b'licenseDocumentationIdentifierValue', blank=True)),
                ('licensedocumentationidentifierrole', models.TextField(verbose_name=b'License document identification role', db_column=b'licenseDocumentationIdentifierRole', blank=True)),
                ('rightsstatementlicense', models.ForeignKey(to='main.RightsStatementLicense', db_column=b'fkRightsStatementLicense')),
            ],
            options={
                'db_table': 'RightsStatementLicenseDocumentationIdentifier',
                'verbose_name': 'Rights: License: Docs ID',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementLicenseNote',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('licensenote', models.TextField(verbose_name=b'License note', db_column=b'licenseNote', blank=True)),
                ('rightsstatementlicense', models.ForeignKey(to='main.RightsStatementLicense', db_column=b'fkRightsStatementLicense')),
            ],
            options={
                'db_table': 'RightsStatementLicenseNote',
                'verbose_name': 'Rights: License: Note',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementLinkingAgentIdentifier',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('linkingagentidentifiertype', models.TextField(verbose_name=b'Linking Agent', db_column=b'linkingAgentIdentifierType', blank=True)),
                ('linkingagentidentifiervalue', models.TextField(verbose_name=b'Linking Agent Value', db_column=b'linkingAgentIdentifierValue', blank=True)),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementLinkingAgentIdentifier',
                'verbose_name': 'Rights: Agent',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementOtherRightsDocumentationIdentifier',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('otherrightsdocumentationidentifiertype', models.TextField(verbose_name=b'Other rights document identification type', db_column=b'otherRightsDocumentationIdentifierType', blank=True)),
                ('otherrightsdocumentationidentifiervalue', models.TextField(verbose_name=b'Other right document identification value', db_column=b'otherRightsDocumentationIdentifierValue', blank=True)),
                ('otherrightsdocumentationidentifierrole', models.TextField(verbose_name=b'Other rights document identification role', db_column=b'otherRightsDocumentationIdentifierRole', blank=True)),
            ],
            options={
                'db_table': 'RightsStatementOtherRightsDocumentationIdentifier',
                'verbose_name': 'Rights: Other: Docs ID',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementOtherRightsInformation',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('otherrightsbasis', models.TextField(verbose_name=b'Other rights basis', db_column=b'otherRightsBasis', blank=True)),
                ('otherrightsapplicablestartdate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'Other rights start date', db_column=b'otherRightsApplicableStartDate', blank=True)),
                ('otherrightsapplicableenddate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'Other rights end date', db_column=b'otherRightsApplicableEndDate', blank=True)),
                ('otherrightsenddateopen', models.BooleanField(help_text=b'Indicate end date is open', verbose_name=b'Open End Date', db_column=b'otherRightsApplicableEndDateOpen')),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementOtherRightsInformation',
                'verbose_name': 'Rights: Other',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementOtherRightsInformationNote',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('otherrightsnote', models.TextField(verbose_name=b'Other rights note', db_column=b'otherRightsNote', blank=True)),
                ('rightsstatementotherrights', models.ForeignKey(to='main.RightsStatementOtherRightsInformation', db_column=b'fkRightsStatementOtherRightsInformation')),
            ],
            options={
                'db_table': 'RightsStatementOtherRightsNote',
                'verbose_name': 'Rights: Other: Note',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementRightsGranted',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('act', models.TextField(db_column=b'act', blank=True)),
                ('startdate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'Start', db_column=b'startDate', blank=True)),
                ('enddate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'End', db_column=b'endDate', blank=True)),
                ('enddateopen', models.BooleanField(help_text=b'Indicate end date is open', verbose_name=b'Open End Date', db_column=b'endDateOpen')),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementRightsGranted',
                'verbose_name': 'Rights: Granted',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementRightsGrantedNote',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('rightsgrantednote', models.TextField(verbose_name=b'Rights note', db_column=b'rightsGrantedNote', blank=True)),
                ('rightsgranted', models.ForeignKey(to='main.RightsStatementRightsGranted', db_column=b'fkRightsStatementRightsGranted')),
            ],
            options={
                'db_table': 'RightsStatementRightsGrantedNote',
                'verbose_name': 'Rights: Granted: Note',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementRightsGrantedRestriction',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('restriction', models.TextField(db_column=b'restriction', blank=True)),
                ('rightsgranted', models.ForeignKey(to='main.RightsStatementRightsGranted', db_column=b'fkRightsStatementRightsGranted')),
            ],
            options={
                'db_table': 'RightsStatementRightsGrantedRestriction',
                'verbose_name': 'Rights: Granted: Restriction',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementStatuteDocumentationIdentifier',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('statutedocumentationidentifiertype', models.TextField(verbose_name=b'Statute document identification type', db_column=b'statuteDocumentationIdentifierType', blank=True)),
                ('statutedocumentationidentifiervalue', models.TextField(verbose_name=b'Statute document identification value', db_column=b'statuteDocumentationIdentifierValue', blank=True)),
                ('statutedocumentationidentifierrole', models.TextField(verbose_name=b'Statute document identification role', db_column=b'statuteDocumentationIdentifierRole', blank=True)),
            ],
            options={
                'db_table': 'RightsStatementStatuteDocumentationIdentifier',
                'verbose_name': 'Rights: Statute: Docs ID',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementStatuteInformation',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('statutejurisdiction', models.TextField(verbose_name=b'Statute jurisdiction', db_column=b'statuteJurisdiction', blank=True)),
                ('statutecitation', models.TextField(verbose_name=b'Statute citation', db_column=b'statuteCitation', blank=True)),
                ('statutedeterminationdate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'Statute determination date', db_column=b'statuteInformationDeterminationDate', blank=True)),
                ('statuteapplicablestartdate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'Statute start date', db_column=b'statuteApplicableStartDate', blank=True)),
                ('statuteapplicableenddate', models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', verbose_name=b'Statute end date', db_column=b'statuteApplicableEndDate', blank=True)),
                ('statuteenddateopen', models.BooleanField(help_text=b'Indicate end date is open', verbose_name=b'Open End Date', db_column=b'statuteApplicableEndDateOpen')),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementStatuteInformation',
                'verbose_name': 'Rights: Statute',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RightsStatementStatuteInformationNote',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('statutenote', models.TextField(verbose_name=b'Statute note', db_column=b'statuteNote', blank=True)),
                ('rightsstatementstatute', models.ForeignKey(to='main.RightsStatementStatuteInformation', db_column=b'fkRightsStatementStatuteInformation')),
            ],
            options={
                'db_table': 'RightsStatementStatuteInformationNote',
                'verbose_name': 'Rights: Statute: Note',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SIP',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'sipUUID')),
                ('createdtime', models.DateTimeField(db_column=b'createdTime')),
                ('currentpath', models.TextField(null=True, db_column=b'currentPath', blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('aip_filename', models.TextField(null=True, db_column=b'aipFilename', blank=True)),
                ('sip_type', models.CharField(default=b'SIP', max_length=8, db_column=b'sipType', choices=[(b'SIP', b'SIP'), (b'AIC', b'AIC')])),
                ('magiclinkexitmessage', models.CharField(max_length=50, null=True, db_column=b'magicLinkExitMessage', blank=True)),
                ('magiclink', models.ForeignKey(db_column=b'magicLink', blank=True, to='main.MicroServiceChainLink', null=True)),
            ],
            options={
                'db_table': 'SIPs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SIPArrange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_path', models.CharField(default=None, max_length=255, unique=True, null=True, blank=True)),
                ('arrange_path', models.CharField(max_length=255)),
                ('file_uuid', django_extensions.db.fields.UUIDField(default=None, max_length=36, null=True, editable=False, blank=True)),
                ('transfer_uuid', django_extensions.db.fields.UUIDField(default=None, max_length=36, null=True, editable=False, blank=True)),
                ('sip_created', models.BooleanField(default=False)),
                ('aip_created', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Arranged SIPs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StandardTaskConfig',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('execute', models.CharField(max_length=250, null=True, db_column=b'execute')),
                ('arguments', models.TextField(null=True, db_column=b'arguments')),
                ('filter_subdir', models.CharField(max_length=50, null=True, db_column=b'filterSubDir', blank=True)),
                ('filter_file_start', models.CharField(max_length=50, null=True, db_column=b'filterFileStart', blank=True)),
                ('filter_file_end', models.CharField(max_length=50, null=True, db_column=b'filterFileEnd', blank=True)),
                ('requires_output_lock', models.BooleanField(default=False, db_column=b'requiresOutputLock')),
                ('stdout_file', models.CharField(max_length=250, null=True, db_column=b'standardOutputFile', blank=True)),
                ('stderr_file', models.CharField(max_length=250, null=True, db_column=b'standardErrorFile', blank=True)),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
                ('replaces', models.ForeignKey(related_name='replaced_by', db_column=b'replaces', blank=True, to='main.StandardTaskConfig', null=True)),
            ],
            options={
                'db_table': 'StandardTasksConfigs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('taskuuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'taskUUID')),
                ('createdtime', models.DateTimeField(db_column=b'createdTime')),
                ('fileuuid', models.CharField(max_length=36, null=True, db_column=b'fileUUID', blank=True)),
                ('filename', models.TextField(db_column=b'fileName', blank=True)),
                ('execution', models.CharField(max_length=250, db_column=b'exec', blank=True)),
                ('arguments', models.CharField(max_length=1000, blank=True)),
                ('starttime', models.DateTimeField(default=None, null=True, db_column=b'startTime')),
                ('endtime', models.DateTimeField(default=None, null=True, db_column=b'endTime')),
                ('client', models.CharField(max_length=50, blank=True)),
                ('stdout', models.TextField(db_column=b'stdOut', blank=True)),
                ('stderror', models.TextField(db_column=b'stdError', blank=True)),
                ('exitcode', models.BigIntegerField(null=True, db_column=b'exitCode', blank=True)),
                ('job', models.ForeignKey(to='main.Job', db_column=b'jobuuid')),
            ],
            options={
                'db_table': 'Tasks',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskConfig',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('tasktypepkreference', models.CharField(default=None, max_length=36, null=True, db_column=b'taskTypePKReference', blank=True)),
                ('description', models.TextField(db_column=b'description')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
                ('replaces', models.ForeignKey(related_name='replaced_by', db_column=b'replaces', blank=True, to='main.TaskConfig', null=True)),
            ],
            options={
                'db_table': 'TasksConfigs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskConfigAssignMagicLink',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
                ('execute', models.ForeignKey(db_column=b'execute', blank=True, to='main.MicroServiceChainLink', null=True)),
                ('replaces', models.ForeignKey(related_name='replaced_by', db_column=b'replaces', blank=True, to='main.TaskConfigAssignMagicLink', null=True)),
            ],
            options={
                'db_table': 'TasksConfigsAssignMagicLink',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskConfigSetUnitVariable',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('variable', models.TextField(blank=True)),
                ('variablevalue', models.TextField(null=True, db_column=b'variableValue', blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, db_column=b'createdTime')),
                ('updatedtime', models.DateTimeField(auto_now=True, null=True, db_column=b'updatedTime')),
                ('microservicechainlink', models.ForeignKey(db_column=b'microServiceChainLink', to='main.MicroServiceChainLink', null=True)),
            ],
            options={
                'db_table': 'TasksConfigsSetUnitVariable',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskConfigUnitVariableLinkPull',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('variable', models.TextField(blank=True)),
                ('variablevalue', models.TextField(null=True, db_column=b'variableValue', blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, db_column=b'createdTime')),
                ('updatedtime', models.DateTimeField(auto_now=True, null=True, db_column=b'updatedTime')),
                ('defaultmicroservicechainlink', models.ForeignKey(db_column=b'defaultMicroServiceChainLink', to='main.MicroServiceChainLink', null=True)),
            ],
            options={
                'db_table': 'TasksConfigsUnitVariableLinkPull',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskType',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('description', models.TextField(blank=True)),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
                ('replaces', models.ForeignKey(related_name='replaced_by', db_column=b'replaces', blank=True, to='main.TaskType', null=True)),
            ],
            options={
                'db_table': 'TaskTypes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Taxonomy',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, null=True, db_column=b'createdTime')),
                ('name', models.CharField(max_length=255, db_column=b'name', blank=True)),
                ('type', models.CharField(default=b'open', max_length=50)),
            ],
            options={
                'db_table': 'Taxonomies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaxonomyTerm',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, null=True, db_column=b'createdTime')),
                ('term', models.CharField(max_length=255, db_column=b'term')),
                ('taxonomy', models.ForeignKey(to='main.Taxonomy', db_column=b'taxonomyUUID')),
            ],
            options={
                'db_table': 'TaxonomyTerms',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'transferUUID')),
                ('currentlocation', models.TextField(db_column=b'currentLocation')),
                ('type', models.CharField(max_length=50, db_column=b'type')),
                ('accessionid', models.TextField(db_column=b'accessionID')),
                ('sourceofacquisition', models.TextField(db_column=b'sourceOfAcquisition', blank=True)),
                ('typeoftransfer', models.TextField(db_column=b'typeOfTransfer', blank=True)),
                ('description', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('magiclinkexitmessage', models.CharField(max_length=50, null=True, db_column=b'magicLinkExitMessage', blank=True)),
                ('magiclink', models.ForeignKey(db_column=b'magicLink', blank=True, to='main.MicroServiceChainLink', null=True)),
            ],
            options={
                'db_table': 'Transfers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TransferMetadataField',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, null=True, db_column=b'createdTime')),
                ('fieldlabel', models.CharField(max_length=50, db_column=b'fieldLabel', blank=True)),
                ('fieldname', models.CharField(max_length=50, db_column=b'fieldName')),
                ('fieldtype', models.CharField(max_length=50, db_column=b'fieldType')),
                ('sortorder', models.IntegerField(default=0, db_column=b'sortOrder')),
                ('optiontaxonomy', models.ForeignKey(db_column=b'optionTaxonomyUUID', to='main.Taxonomy', null=True)),
            ],
            options={
                'db_table': 'TransferMetadataFields',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TransferMetadataFieldValue',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, db_column=b'createdTime')),
                ('fieldvalue', models.TextField(db_column=b'fieldValue', blank=True)),
                ('field', models.ForeignKey(to='main.TransferMetadataField', db_column=b'fieldUUID')),
            ],
            options={
                'db_table': 'TransferMetadataFieldValues',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TransferMetadataSet',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, db_column=b'createdTime')),
                ('createdbyuserid', models.IntegerField(db_column=b'createdByUserID')),
            ],
            options={
                'db_table': 'TransferMetadataSets',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnitVariable',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('unittype', models.CharField(max_length=50, null=True, db_column=b'unitType', blank=True)),
                ('unituuid', models.CharField(help_text=b'Semantically a foreign key to SIP or Transfer', max_length=36, null=True, db_column=b'unitUUID')),
                ('variable', models.TextField(null=True, db_column=b'variable')),
                ('variablevalue', models.TextField(null=True, db_column=b'variableValue')),
                ('createdtime', models.DateTimeField(auto_now_add=True, db_column=b'createdTime')),
                ('updatedtime', models.DateTimeField(auto_now=True, db_column=b'updatedTime')),
                ('microservicechainlink', models.ForeignKey(db_column=b'microServiceChainLink', blank=True, to='main.MicroServiceChainLink', help_text=b'UUID of the MicroServiceChainLink if used in task type linkTaskManagerUnitVariableLinkPull', null=True)),
            ],
            options={
                'db_table': 'UnitVariables',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WatchedDirectory',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('watched_directory_path', models.TextField(null=True, db_column=b'watchedDirectoryPath', blank=True)),
                ('only_act_on_directories', models.BooleanField(default=True, db_column=b'onlyActOnDirectories')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
                ('chain', models.ForeignKey(db_column=b'chain', to='main.MicroServiceChain', null=True)),
            ],
            options={
                'db_table': 'WatchedDirectories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WatchedDirectoryExpectedType',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('description', models.TextField(null=True)),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
                ('replaces', models.ForeignKey(db_column=b'replaces', to='main.WatchedDirectoryExpectedType', null=True)),
            ],
            options={
                'db_table': 'WatchedDirectoriesExpectedTypes',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='watcheddirectory',
            name='expected_type',
            field=models.ForeignKey(db_column=b'expectedType', to='main.WatchedDirectoryExpectedType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='watcheddirectory',
            name='replaces',
            field=models.ForeignKey(db_column=b'replaces', to='main.WatchedDirectory', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='transfermetadatafieldvalue',
            name='set',
            field=models.ForeignKey(to='main.TransferMetadataSet', db_column=b'setUUID'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='transfer',
            name='transfermetadatasetrow',
            field=models.ForeignKey(db_column=b'transferMetadataSetRowUUID', blank=True, to='main.TransferMetadataSet', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taskconfig',
            name='tasktype',
            field=models.ForeignKey(to='main.TaskType', db_column=b'taskType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rightsstatementstatutedocumentationidentifier',
            name='rightsstatementstatute',
            field=models.ForeignKey(to='main.RightsStatementStatuteInformation', db_column=b'fkRightsStatementStatuteInformation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rightsstatementotherrightsdocumentationidentifier',
            name='rightsstatementotherrights',
            field=models.ForeignKey(to='main.RightsStatementOtherRightsInformation', db_column=b'fkRightsStatementOtherRightsInformation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microservicechainlink',
            name='currenttask',
            field=models.ForeignKey(to='main.TaskConfig', db_column=b'currentTask'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microservicechainlink',
            name='defaultnextchainlink',
            field=models.ForeignKey(to='main.MicroServiceChainLink', null=True, db_column=b'defaultNextChainLink'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microservicechainlink',
            name='replaces',
            field=models.ForeignKey(related_name='replaced_by', db_column=b'replaces', to='main.MicroServiceChainLink', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microservicechainchoice',
            name='choiceavailableatlink',
            field=models.ForeignKey(to='main.MicroServiceChainLink', db_column=b'choiceAvailableAtLink'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microservicechainchoice',
            name='replaces',
            field=models.ForeignKey(related_name='replaced_by', db_column=b'replaces', blank=True, to='main.MicroServiceChainChoice', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microservicechain',
            name='startinglink',
            field=models.ForeignKey(to='main.MicroServiceChainLink', db_column=b'startingLink'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='microservicechainlink',
            field=models.ForeignKey(db_column=b'MicroServiceChainLinksPK', blank=True, to='main.MicroServiceChainLink', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='sip',
            field=models.ForeignKey(db_column=b'sipUUID', blank=True, to='main.SIP', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='transfer',
            field=models.ForeignKey(db_column=b'transferUUID', blank=True, to='main.Transfer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='file_uuid',
            field=models.ForeignKey(db_column=b'fileUUID', blank=True, to='main.File', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dublincore',
            name='metadataappliestotype',
            field=models.ForeignKey(to='main.MetadataAppliesToType', db_column=b'metadataAppliesToType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='derivation',
            name='derived_file',
            field=models.ForeignKey(related_name='original_file_set', db_column=b'derivedFileUUID', to='main.File'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='derivation',
            name='event',
            field=models.ForeignKey(db_column=b'relatedEventUUID', to_field=b'event_id', blank=True, to='main.Event', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='derivation',
            name='source_file',
            field=models.ForeignKey(related_name='derived_file_set', db_column=b'sourceFileUUID', to='main.File'),
            preserve_default=True,
        ),
    ]

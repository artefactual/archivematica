# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'uuid')),
                ('agentIdentifierType', models.CharField(max_length=100)),
                ('agentIdentifierValue', models.CharField(max_length=100)),
                ('agentName', models.CharField(max_length=100)),
                ('agentType', models.CharField(max_length=100)),
                ('clientIP', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'Agent',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Command',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'pk')),
                ('commandUsage', models.CharField(max_length=15)),
                ('commandType', models.CharField(max_length=36)),
                ('verificationCommand', models.CharField(max_length=36, null=True)),
                ('eventDetailCommand', models.CharField(max_length=36, null=True)),
                ('supportedBy', models.CharField(max_length=36, null=True, db_column=b'supportedBy')),
                ('command', models.TextField(db_column=b'command')),
                ('outputLocation', models.TextField(null=True, db_column=b'outputLocation')),
                ('description', models.TextField(db_column=b'description')),
                ('outputFileFormat', models.TextField(null=True, db_column=b'outputFileFormat')),
                ('replaces', models.CharField(max_length=36, null=True, db_column=b'replaces')),
                ('lastmodified', models.DateTimeField(null=True, db_column=b'lastModified')),
                ('enabled', models.IntegerField(default=1, null=True, db_column=b'enabled')),
            ],
            options={
                'db_table': 'Command',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommandClassification',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'pk')),
                ('classification', models.TextField(null=True, db_column=b'classification')),
                ('replaces', models.CharField(max_length=36, null=True, db_column=b'replaces')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified')),
                ('enabled', models.IntegerField(default=1, null=True, db_column=b'enabled')),
            ],
            options={
                'db_table': 'CommandClassification',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommandRelationship',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'pk')),
                ('commandClassification', models.CharField(max_length=36)),
                ('command', models.CharField(max_length=36, null=True)),
                ('fileID', models.CharField(max_length=36, null=True)),
                ('replaces', models.CharField(max_length=36, null=True)),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified')),
                ('enabled', models.IntegerField(default=1, null=True, db_column=b'enabled')),
            ],
            options={
                'db_table': 'CommandRelationship',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommandsSupportedBy',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'pk')),
                ('description', models.TextField(null=True, db_column=b'description')),
                ('replaces', models.CharField(max_length=36, null=True, db_column=b'replaces')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified')),
                ('enabled', models.IntegerField(default=1, null=True, db_column=b'enabled')),
            ],
            options={
                'db_table': 'CommandsSupportedBy',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommandType',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'pk')),
                ('replaces', models.CharField(max_length=36, null=True, db_column=b'replaces')),
                ('type', models.TextField(db_column=b'type')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified')),
                ('enabled', models.IntegerField(default=1, null=True, db_column=b'enabled')),
            ],
            options={
                'db_table': 'CommandType',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileID',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'pk')),
                ('description', models.TextField(db_column=b'description')),
                ('validpreservationformat', models.IntegerField(default=0, null=True, db_column=b'validPreservationFormat')),
                ('validaccessformat', models.IntegerField(default=0, null=True, db_column=b'validAccessFormat')),
                ('fileidtype', models.CharField(max_length=36, null=True, db_column=b'fileidtype_id')),
                ('replaces', models.CharField(max_length=36, null=True, db_column=b'replaces')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified')),
                ('enabled', models.IntegerField(default=1, null=True, db_column=b'enabled')),
            ],
            options={
                'db_table': 'FileID',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileIDsBySingleID',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'pk')),
                ('fileID', models.CharField(max_length=36, null=True)),
                ('id', models.TextField(db_column=b'id')),
                ('tool', models.TextField(db_column=b'tool')),
                ('toolVersion', models.TextField(null=True, db_column=b'toolVersion')),
                ('replaces', models.CharField(max_length=36, null=True, db_column=b'replaces')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified')),
                ('enabled', models.IntegerField(default=1, null=True, db_column=b'enabled')),
            ],
            options={
                'db_table': 'FileIDsBySingleID',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileIDType',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'pk')),
                ('description', models.TextField(null=True, db_column=b'description')),
                ('replaces', models.CharField(max_length=36, null=True, db_column=b'replaces')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified')),
                ('enabled', models.IntegerField(default=1, null=True, db_column=b'enabled')),
            ],
            options={
                'db_table': 'FileIDType',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Format',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.UUIDField(help_text=b'Unique identifier', unique=True, max_length=36, editable=False, blank=True)),
                ('description', models.CharField(help_text=b'Common name of format', max_length=128)),
                ('slug', autoslug.fields.AutoSlugField(editable=False)),
            ],
            options={
                'ordering': ['group', 'description'],
                'verbose_name': 'Format',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FormatGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.UUIDField(help_text=b'Unique identifier', unique=True, max_length=36, editable=False, blank=True)),
                ('description', models.CharField(max_length=128, verbose_name=b'Format Group')),
                ('slug', autoslug.fields.AutoSlugField(editable=False)),
            ],
            options={
                'ordering': ['description'],
                'verbose_name': 'Format Group',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FormatVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=True)),
                ('lastmodified', models.DateTimeField(auto_now_add=True)),
                ('uuid', django_extensions.db.fields.UUIDField(help_text=b'Unique identifier', unique=True, max_length=36, editable=False, blank=True)),
                ('version', models.CharField(max_length=10, null=True, blank=True)),
                ('pronom_id', models.CharField(max_length=32, null=True, blank=True)),
                ('description', models.CharField(help_text=b'Formal name to go in the METS file.', max_length=128, null=True, blank=True)),
                ('access_format', models.BooleanField(default=False)),
                ('preservation_format', models.BooleanField(default=False)),
                ('slug', autoslug.fields.AutoSlugField(editable=False)),
                ('format', models.ForeignKey(related_name='version_set', to_field=b'uuid', to='fpr.Format', null=True)),
                ('replaces', models.ForeignKey(to_field=b'uuid', blank=True, to='fpr.FormatVersion', null=True)),
            ],
            options={
                'ordering': ['format', 'description'],
                'verbose_name': 'Format Version',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FPCommand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=True)),
                ('lastmodified', models.DateTimeField(auto_now_add=True)),
                ('uuid', django_extensions.db.fields.UUIDField(help_text=b'Unique identifier', unique=True, max_length=36, editable=False, blank=True)),
                ('description', models.CharField(max_length=256)),
                ('command', models.TextField()),
                ('script_type', models.CharField(max_length=16, choices=[(b'bashScript', b'Bash Script'), (b'pythonScript', b'Python Script'), (b'command', b'Command Line'), (b'as_is', b'No shebang (#!/path/to/interpreter) needed')])),
                ('output_location', models.TextField(null=True, blank=True)),
                ('command_usage', models.CharField(max_length=16, choices=[(b'characterization', b'Characterization'), (b'event_detail', b'Event Detail'), (b'extraction', b'Extraction'), (b'normalization', b'Normalization'), (b'transcription', b'Transcription'), (b'validation', b'Validation'), (b'verification', b'Verification')])),
                ('event_detail_command', models.ForeignKey(related_name='+', to_field=b'uuid', blank=True, to='fpr.FPCommand', null=True)),
                ('output_format', models.ForeignKey(to_field=b'uuid', blank=True, to='fpr.FormatVersion', null=True)),
                ('replaces', models.ForeignKey(to_field=b'uuid', blank=True, to='fpr.FPCommand', null=True)),
            ],
            options={
                'ordering': ['description'],
                'verbose_name': 'Format Policy Command',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FPRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=True)),
                ('lastmodified', models.DateTimeField(auto_now_add=True)),
                ('uuid', django_extensions.db.fields.UUIDField(help_text=b'Unique identifier', unique=True, max_length=36, editable=False, blank=True)),
                ('purpose', models.CharField(max_length=32, choices=[(b'access', b'Access'), (b'characterization', b'Characterization'), (b'extract', b'Extract'), (b'preservation', b'Preservation'), (b'thumbnail', b'Thumbnail'), (b'transcription', b'Transcription'), (b'validation', b'Validation'), (b'default_access', b'Default Access'), (b'default_characterization', b'Default Characterization'), (b'default_thumbnail', b'Default Thumbnail')])),
                ('count_attempts', models.IntegerField(default=0)),
                ('count_okay', models.IntegerField(default=0)),
                ('count_not_okay', models.IntegerField(default=0)),
                ('command', models.ForeignKey(to='fpr.FPCommand', to_field=b'uuid')),
                ('format', models.ForeignKey(to='fpr.FormatVersion', to_field=b'uuid')),
                ('replaces', models.ForeignKey(to_field=b'uuid', blank=True, to='fpr.FPRule', null=True)),
            ],
            options={
                'verbose_name': 'Format Policy Rule',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FPTool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.UUIDField(help_text=b'Unique identifier', unique=True, max_length=36, editable=False, blank=True)),
                ('description', models.CharField(help_text=b'Name of tool', max_length=256)),
                ('version', models.CharField(max_length=64)),
                ('enabled', models.BooleanField(default=True)),
                ('slug', autoslug.fields.AutoSlugField(editable=False)),
            ],
            options={
                'verbose_name': 'Normalization Tool',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IDCommand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=True)),
                ('lastmodified', models.DateTimeField(auto_now_add=True)),
                ('uuid', django_extensions.db.fields.UUIDField(help_text=b'Unique identifier', unique=True, max_length=36, editable=False, blank=True)),
                ('description', models.CharField(help_text=b'Name to identify script', max_length=256, verbose_name=b'Identifier')),
                ('config', models.CharField(max_length=4, choices=[(b'PUID', b'PUID'), (b'MIME', b'mime-type'), (b'ext', b'file extension')])),
                ('script', models.TextField(help_text=b'Script to be executed.')),
                ('script_type', models.CharField(max_length=16, choices=[(b'bashScript', b'Bash Script'), (b'pythonScript', b'Python Script'), (b'command', b'Command Line'), (b'as_is', b'No shebang (#!/path/to/interpreter) needed')])),
                ('replaces', models.ForeignKey(to_field=b'uuid', blank=True, to='fpr.IDCommand', null=True)),
            ],
            options={
                'ordering': ['description'],
                'verbose_name': 'Format Identification Command',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IDRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=True)),
                ('lastmodified', models.DateTimeField(auto_now_add=True)),
                ('uuid', django_extensions.db.fields.UUIDField(help_text=b'Unique identifier', unique=True, max_length=36, editable=False, blank=True)),
                ('command_output', models.TextField()),
                ('command', models.ForeignKey(to='fpr.IDCommand', to_field=b'uuid')),
                ('format', models.ForeignKey(to='fpr.FormatVersion', to_field=b'uuid')),
                ('replaces', models.ForeignKey(to_field=b'uuid', blank=True, to='fpr.IDRule', null=True)),
            ],
            options={
                'verbose_name': 'Format Identification Rule',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IDTool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.UUIDField(help_text=b'Unique identifier', unique=True, max_length=36, editable=False, blank=True)),
                ('description', models.CharField(help_text=b'Name of tool', max_length=256)),
                ('version', models.CharField(max_length=64)),
                ('enabled', models.BooleanField(default=True)),
                ('slug', autoslug.fields.AutoSlugField(editable=False)),
            ],
            options={
                'verbose_name': 'Format Identification Tool',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='idcommand',
            name='tool',
            field=models.ForeignKey(to_field=b'uuid', blank=True, to='fpr.IDTool', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fpcommand',
            name='tool',
            field=models.ForeignKey(to='fpr.FPTool', to_field=b'uuid', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fpcommand',
            name='verification_command',
            field=models.ForeignKey(related_name='+', to_field=b'uuid', blank=True, to='fpr.FPCommand', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='format',
            name='group',
            field=models.ForeignKey(to='fpr.FormatGroup', to_field=b'uuid', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fileid',
            name='format',
            field=models.ForeignKey(to='fpr.FormatVersion', to_field=b'uuid', null=True),
            preserve_default=True,
        ),
    ]

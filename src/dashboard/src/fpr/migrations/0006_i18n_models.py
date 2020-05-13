# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models
import autoslug.fields


class Migration(migrations.Migration):

    dependencies = [("fpr", "0005_update_tool_versions")]

    operations = [
        migrations.AlterModelOptions(
            name="formatgroup",
            options={"ordering": ["description"], "verbose_name": "Format group"},
        ),
        migrations.AlterModelOptions(
            name="formatversion",
            options={
                "ordering": ["format", "description"],
                "verbose_name": "Format version",
            },
        ),
        migrations.AlterModelOptions(
            name="fpcommand",
            options={
                "ordering": ["description"],
                "verbose_name": "Format policy command",
            },
        ),
        migrations.AlterModelOptions(
            name="fprule", options={"verbose_name": "Format policy rule"}
        ),
        migrations.AlterModelOptions(
            name="fptool", options={"verbose_name": "Normalization tool"}
        ),
        migrations.AlterModelOptions(
            name="idcommand",
            options={
                "ordering": ["description"],
                "verbose_name": "Format identification command",
            },
        ),
        migrations.AlterModelOptions(
            name="idrule", options={"verbose_name": "Format identification rule"}
        ),
        migrations.AlterModelOptions(
            name="idtool", options={"verbose_name": "Format identification tool"}
        ),
        migrations.AlterField(
            model_name="agent",
            name="agentIdentifierType",
            field=models.CharField(
                max_length=100, verbose_name="agent identifier type"
            ),
        ),
        migrations.AlterField(
            model_name="agent",
            name="agentIdentifierValue",
            field=models.CharField(
                max_length=100, verbose_name="agent identifier value"
            ),
        ),
        migrations.AlterField(
            model_name="agent",
            name="agentName",
            field=models.CharField(max_length=100, verbose_name="agent name"),
        ),
        migrations.AlterField(
            model_name="agent",
            name="agentType",
            field=models.CharField(max_length=100, verbose_name="agent type"),
        ),
        migrations.AlterField(
            model_name="agent",
            name="clientIP",
            field=models.CharField(max_length=100, verbose_name="client IP address"),
        ),
        migrations.AlterField(
            model_name="command",
            name="command",
            field=models.TextField(verbose_name="command", db_column="command"),
        ),
        migrations.AlterField(
            model_name="command",
            name="commandType",
            field=models.CharField(max_length=36, verbose_name="command type"),
        ),
        migrations.AlterField(
            model_name="command",
            name="commandUsage",
            field=models.CharField(max_length=15, verbose_name="command usage"),
        ),
        migrations.AlterField(
            model_name="command",
            name="description",
            field=models.TextField(verbose_name="description", db_column="description"),
        ),
        migrations.AlterField(
            model_name="command",
            name="enabled",
            field=models.IntegerField(
                default=1, null=True, verbose_name="enabled", db_column="enabled"
            ),
        ),
        migrations.AlterField(
            model_name="command",
            name="eventDetailCommand",
            field=models.CharField(
                max_length=36, null=True, verbose_name="event detail command"
            ),
        ),
        migrations.AlterField(
            model_name="command",
            name="lastmodified",
            field=models.DateTimeField(
                null=True, verbose_name="last modified", db_column="lastModified"
            ),
        ),
        migrations.AlterField(
            model_name="command",
            name="outputFileFormat",
            field=models.TextField(
                null=True,
                verbose_name="output file format",
                db_column="outputFileFormat",
            ),
        ),
        migrations.AlterField(
            model_name="command",
            name="outputLocation",
            field=models.TextField(
                null=True, verbose_name="output location", db_column="outputLocation"
            ),
        ),
        migrations.AlterField(
            model_name="command",
            name="replaces",
            field=models.CharField(
                max_length=36, null=True, verbose_name="replaces", db_column="replaces"
            ),
        ),
        migrations.AlterField(
            model_name="command",
            name="supportedBy",
            field=models.CharField(
                max_length=36,
                null=True,
                verbose_name="supported by",
                db_column="supportedBy",
            ),
        ),
        migrations.AlterField(
            model_name="command",
            name="verificationCommand",
            field=models.CharField(
                max_length=36, null=True, verbose_name="verification command"
            ),
        ),
        migrations.AlterField(
            model_name="commandclassification",
            name="classification",
            field=models.TextField(
                null=True, verbose_name="classification", db_column="classification"
            ),
        ),
        migrations.AlterField(
            model_name="commandclassification",
            name="enabled",
            field=models.IntegerField(
                default=1, null=True, verbose_name="enabled", db_column="enabled"
            ),
        ),
        migrations.AlterField(
            model_name="commandclassification",
            name="lastmodified",
            field=models.DateTimeField(
                verbose_name="last modified", db_column="lastModified"
            ),
        ),
        migrations.AlterField(
            model_name="commandclassification",
            name="replaces",
            field=models.CharField(
                max_length=36, null=True, verbose_name="replaces", db_column="replaces"
            ),
        ),
        migrations.AlterField(
            model_name="commandrelationship",
            name="command",
            field=models.CharField(max_length=36, null=True, verbose_name="command"),
        ),
        migrations.AlterField(
            model_name="commandrelationship",
            name="commandClassification",
            field=models.CharField(max_length=36, verbose_name="command clasification"),
        ),
        migrations.AlterField(
            model_name="commandrelationship",
            name="enabled",
            field=models.IntegerField(
                default=1, null=True, verbose_name="enabled", db_column="enabled"
            ),
        ),
        migrations.AlterField(
            model_name="commandrelationship",
            name="fileID",
            field=models.CharField(max_length=36, null=True, verbose_name="file ID"),
        ),
        migrations.AlterField(
            model_name="commandrelationship",
            name="lastmodified",
            field=models.DateTimeField(
                verbose_name="last modified", db_column="lastModified"
            ),
        ),
        migrations.AlterField(
            model_name="commandrelationship",
            name="replaces",
            field=models.CharField(max_length=36, null=True, verbose_name="replaces"),
        ),
        migrations.AlterField(
            model_name="commandssupportedby",
            name="description",
            field=models.TextField(
                null=True, verbose_name="description", db_column="description"
            ),
        ),
        migrations.AlterField(
            model_name="commandssupportedby",
            name="enabled",
            field=models.IntegerField(
                default=1, null=True, verbose_name="enabled", db_column="enabled"
            ),
        ),
        migrations.AlterField(
            model_name="commandssupportedby",
            name="lastmodified",
            field=models.DateTimeField(
                verbose_name="last modified", db_column="lastModified"
            ),
        ),
        migrations.AlterField(
            model_name="commandssupportedby",
            name="replaces",
            field=models.CharField(
                max_length=36, null=True, verbose_name="replaces", db_column="replaces"
            ),
        ),
        migrations.AlterField(
            model_name="commandtype",
            name="enabled",
            field=models.IntegerField(
                default=1, null=True, verbose_name="enabled", db_column="enabled"
            ),
        ),
        migrations.AlterField(
            model_name="commandtype",
            name="lastmodified",
            field=models.DateTimeField(
                verbose_name="last modified", db_column="lastModified"
            ),
        ),
        migrations.AlterField(
            model_name="commandtype",
            name="replaces",
            field=models.CharField(
                max_length=36, null=True, verbose_name="replaces", db_column="replaces"
            ),
        ),
        migrations.AlterField(
            model_name="commandtype",
            name="type",
            field=models.TextField(verbose_name="type", db_column="type"),
        ),
        migrations.AlterField(
            model_name="fileid",
            name="description",
            field=models.TextField(verbose_name="description", db_column="description"),
        ),
        migrations.AlterField(
            model_name="fileid",
            name="enabled",
            field=models.IntegerField(
                default=1, null=True, verbose_name="enabled", db_column="enabled"
            ),
        ),
        migrations.AlterField(
            model_name="fileid",
            name="fileidtype",
            field=models.CharField(
                max_length=36,
                null=True,
                verbose_name="file ID type",
                db_column="fileidtype_id",
            ),
        ),
        migrations.AlterField(
            model_name="fileid",
            name="format",
            field=models.ForeignKey(
                verbose_name="the related format",
                to_field="uuid",
                to="fpr.FormatVersion",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="fileid",
            name="lastmodified",
            field=models.DateTimeField(
                verbose_name="last modified", db_column="lastModified"
            ),
        ),
        migrations.AlterField(
            model_name="fileid",
            name="replaces",
            field=models.CharField(
                max_length=36, null=True, verbose_name="replaces", db_column="replaces"
            ),
        ),
        migrations.AlterField(
            model_name="fileid",
            name="validaccessformat",
            field=models.IntegerField(
                default=0,
                null=True,
                verbose_name="valid access format",
                db_column="validAccessFormat",
            ),
        ),
        migrations.AlterField(
            model_name="fileid",
            name="validpreservationformat",
            field=models.IntegerField(
                default=0,
                null=True,
                verbose_name="valid preservation format",
                db_column="validPreservationFormat",
            ),
        ),
        migrations.AlterField(
            model_name="fileidsbysingleid",
            name="enabled",
            field=models.IntegerField(
                default=1, null=True, verbose_name="enabled", db_column="enabled"
            ),
        ),
        migrations.AlterField(
            model_name="fileidsbysingleid",
            name="fileID",
            field=models.CharField(max_length=36, null=True, verbose_name="file ID"),
        ),
        migrations.AlterField(
            model_name="fileidsbysingleid",
            name="lastmodified",
            field=models.DateTimeField(
                verbose_name="last modified", db_column="lastModified"
            ),
        ),
        migrations.AlterField(
            model_name="fileidsbysingleid",
            name="replaces",
            field=models.CharField(
                max_length=36, null=True, verbose_name="replaces", db_column="replaces"
            ),
        ),
        migrations.AlterField(
            model_name="fileidsbysingleid",
            name="tool",
            field=models.TextField(verbose_name="tool", db_column="tool"),
        ),
        migrations.AlterField(
            model_name="fileidsbysingleid",
            name="toolVersion",
            field=models.TextField(
                null=True, verbose_name="tool version", db_column="toolVersion"
            ),
        ),
        migrations.AlterField(
            model_name="fileidtype",
            name="description",
            field=models.TextField(
                null=True, verbose_name="description", db_column="description"
            ),
        ),
        migrations.AlterField(
            model_name="fileidtype",
            name="enabled",
            field=models.IntegerField(
                default=1, null=True, verbose_name="enabled", db_column="enabled"
            ),
        ),
        migrations.AlterField(
            model_name="fileidtype",
            name="lastmodified",
            field=models.DateTimeField(
                verbose_name="last modified", db_column="lastModified"
            ),
        ),
        migrations.AlterField(
            model_name="fileidtype",
            name="replaces",
            field=models.CharField(
                max_length=36, null=True, verbose_name="replaces", db_column="replaces"
            ),
        ),
        migrations.AlterField(
            model_name="format",
            name="description",
            field=models.CharField(
                help_text="Common name of format",
                max_length=128,
                verbose_name="description",
            ),
        ),
        migrations.AlterField(
            model_name="format",
            name="group",
            field=models.ForeignKey(
                verbose_name="the related group",
                to_field="uuid",
                to="fpr.FormatGroup",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="format",
            name="slug",
            field=autoslug.fields.AutoSlugField(verbose_name="slug", editable=False),
        ),
        migrations.AlterField(
            model_name="formatgroup",
            name="description",
            field=models.CharField(max_length=128, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="formatgroup",
            name="slug",
            field=autoslug.fields.AutoSlugField(verbose_name="slug", editable=False),
        ),
        migrations.AlterField(
            model_name="formatversion",
            name="access_format",
            field=models.BooleanField(default=False, verbose_name="access format"),
        ),
        migrations.AlterField(
            model_name="formatversion",
            name="description",
            field=models.CharField(
                help_text="Formal name to go in the METS file.",
                max_length=128,
                null=True,
                verbose_name="description",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="formatversion",
            name="enabled",
            field=models.BooleanField(default=True, verbose_name="enabled"),
        ),
        migrations.AlterField(
            model_name="formatversion",
            name="format",
            field=models.ForeignKey(
                related_name="version_set",
                verbose_name="the related format",
                to_field="uuid",
                to="fpr.Format",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="formatversion",
            name="lastmodified",
            field=models.DateTimeField(auto_now_add=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="formatversion",
            name="preservation_format",
            field=models.BooleanField(
                default=False, verbose_name="preservation format"
            ),
        ),
        migrations.AlterField(
            model_name="formatversion",
            name="pronom_id",
            field=models.CharField(
                max_length=32, null=True, verbose_name="pronom id", blank=True
            ),
        ),
        migrations.AlterField(
            model_name="formatversion",
            name="replaces",
            field=models.ForeignKey(
                verbose_name="the related model",
                to_field="uuid",
                blank=True,
                to="fpr.FormatVersion",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="formatversion",
            name="version",
            field=models.CharField(
                max_length=10, null=True, verbose_name="version", blank=True
            ),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="command",
            field=models.TextField(verbose_name="command"),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="command_usage",
            field=models.CharField(
                max_length=16,
                verbose_name="command usage",
                choices=[
                    ("characterization", "Characterization"),
                    ("event_detail", "Event Detail"),
                    ("extraction", "Extraction"),
                    ("normalization", "Normalization"),
                    ("transcription", "Transcription"),
                    ("validation", "Validation"),
                    ("verification", "Verification"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="description",
            field=models.CharField(max_length=256, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="enabled",
            field=models.BooleanField(default=True, verbose_name="enabled"),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="event_detail_command",
            field=models.ForeignKey(
                related_name="+",
                verbose_name="the related event detail command",
                to_field="uuid",
                blank=True,
                to="fpr.FPCommand",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="lastmodified",
            field=models.DateTimeField(auto_now_add=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="output_format",
            field=models.ForeignKey(
                verbose_name="the related output format",
                to_field="uuid",
                blank=True,
                to="fpr.FormatVersion",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="output_location",
            field=models.TextField(
                null=True, verbose_name="output location", blank=True
            ),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="replaces",
            field=models.ForeignKey(
                verbose_name="the related model",
                to_field="uuid",
                blank=True,
                to="fpr.FPCommand",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="script_type",
            field=models.CharField(
                max_length=16,
                verbose_name="script type",
                choices=[
                    ("bashScript", "Bash script"),
                    ("pythonScript", "Python script"),
                    ("command", "Command line"),
                    ("as_is", "No shebang needed"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="tool",
            field=models.ForeignKey(
                verbose_name="the related tool",
                to_field="uuid",
                to="fpr.FPTool",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="fpcommand",
            name="verification_command",
            field=models.ForeignKey(
                related_name="+",
                verbose_name="the related verification command",
                to_field="uuid",
                blank=True,
                to="fpr.FPCommand",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="fprule",
            name="command",
            field=models.ForeignKey(
                to="fpr.FPCommand",
                to_field="uuid",
                verbose_name="the related command",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="fprule",
            name="count_attempts",
            field=models.IntegerField(default=0, verbose_name="count attempts"),
        ),
        migrations.AlterField(
            model_name="fprule",
            name="count_not_okay",
            field=models.IntegerField(default=0, verbose_name="count not okay"),
        ),
        migrations.AlterField(
            model_name="fprule",
            name="count_okay",
            field=models.IntegerField(default=0, verbose_name="count okay"),
        ),
        migrations.AlterField(
            model_name="fprule",
            name="enabled",
            field=models.BooleanField(default=True, verbose_name="enabled"),
        ),
        migrations.AlterField(
            model_name="fprule",
            name="format",
            field=models.ForeignKey(
                to="fpr.FormatVersion",
                to_field="uuid",
                verbose_name="the related format",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="fprule",
            name="lastmodified",
            field=models.DateTimeField(auto_now_add=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="fprule",
            name="purpose",
            field=models.CharField(
                max_length=32,
                verbose_name="purpose",
                choices=[
                    ("access", "Access"),
                    ("characterization", "Characterization"),
                    ("extract", "Extract"),
                    ("preservation", "Preservation"),
                    ("thumbnail", "Thumbnail"),
                    ("transcription", "Transcription"),
                    ("validation", "Validation"),
                    ("default_access", "Default access"),
                    ("default_characterization", "Default characterization"),
                    ("default_thumbnail", "Default thumbnail"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="fprule",
            name="replaces",
            field=models.ForeignKey(
                verbose_name="the related model",
                to_field="uuid",
                blank=True,
                to="fpr.FPRule",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="fptool",
            name="description",
            field=models.CharField(
                help_text="Name of tool", max_length=256, verbose_name="description"
            ),
        ),
        migrations.AlterField(
            model_name="fptool",
            name="enabled",
            field=models.BooleanField(default=True, verbose_name="enabled"),
        ),
        migrations.AlterField(
            model_name="fptool",
            name="slug",
            field=autoslug.fields.AutoSlugField(verbose_name="slug", editable=False),
        ),
        migrations.AlterField(
            model_name="fptool",
            name="version",
            field=models.CharField(max_length=64, verbose_name="version"),
        ),
        migrations.AlterField(
            model_name="idcommand",
            name="config",
            field=models.CharField(
                max_length=4,
                verbose_name="configuration",
                choices=[
                    ("PUID", "PUID"),
                    ("MIME", "MIME type"),
                    ("ext", "File extension"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="idcommand",
            name="description",
            field=models.CharField(
                help_text="Name to identify script",
                max_length=256,
                verbose_name="description",
            ),
        ),
        migrations.AlterField(
            model_name="idcommand",
            name="enabled",
            field=models.BooleanField(default=True, verbose_name="enabled"),
        ),
        migrations.AlterField(
            model_name="idcommand",
            name="lastmodified",
            field=models.DateTimeField(auto_now_add=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="idcommand",
            name="replaces",
            field=models.ForeignKey(
                verbose_name="the related model",
                to_field="uuid",
                blank=True,
                to="fpr.IDCommand",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="idcommand",
            name="script",
            field=models.TextField(
                help_text="Script to be executed.", verbose_name="script"
            ),
        ),
        migrations.AlterField(
            model_name="idcommand",
            name="script_type",
            field=models.CharField(
                max_length=16,
                verbose_name="script type",
                choices=[
                    ("bashScript", "Bash script"),
                    ("pythonScript", "Python script"),
                    ("command", "Command line"),
                    ("as_is", "No shebang needed"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="idcommand",
            name="tool",
            field=models.ForeignKey(
                verbose_name="the related tool",
                to_field="uuid",
                blank=True,
                to="fpr.IDTool",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="idrule",
            name="command",
            field=models.ForeignKey(
                to="fpr.IDCommand",
                to_field="uuid",
                verbose_name="the related command",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="idrule",
            name="command_output",
            field=models.TextField(verbose_name="command output"),
        ),
        migrations.AlterField(
            model_name="idrule",
            name="enabled",
            field=models.BooleanField(default=True, verbose_name="enabled"),
        ),
        migrations.AlterField(
            model_name="idrule",
            name="format",
            field=models.ForeignKey(
                to="fpr.FormatVersion",
                to_field="uuid",
                verbose_name="the related format",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="idrule",
            name="lastmodified",
            field=models.DateTimeField(auto_now_add=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="idrule",
            name="replaces",
            field=models.ForeignKey(
                verbose_name="the related model",
                to_field="uuid",
                blank=True,
                to="fpr.IDRule",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="idtool",
            name="description",
            field=models.CharField(
                help_text="Name of tool", max_length=256, verbose_name="description"
            ),
        ),
        migrations.AlterField(
            model_name="idtool",
            name="enabled",
            field=models.BooleanField(default=True, verbose_name="enabled"),
        ),
        migrations.AlterField(
            model_name="idtool",
            name="slug",
            field=autoslug.fields.AutoSlugField(verbose_name="slug", editable=False),
        ),
        migrations.AlterField(
            model_name="idtool",
            name="version",
            field=models.CharField(max_length=64, verbose_name="version"),
        ),
    ]

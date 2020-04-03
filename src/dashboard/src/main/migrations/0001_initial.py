# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations
import main.models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [("fpr", "__first__")]

    operations = [
        migrations.CreateModel(
            name="Access",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "sipuuid",
                    models.CharField(max_length=36, db_column="SIPUUID", blank=True),
                ),
                ("resource", models.TextField(db_column="resource", blank=True)),
                ("target", models.TextField(db_column="target", blank=True)),
                ("status", models.TextField(db_column="status", blank=True)),
                (
                    "statuscode",
                    models.PositiveSmallIntegerField(
                        null=True, db_column="statusCode", blank=True
                    ),
                ),
                (
                    "exitcode",
                    models.PositiveSmallIntegerField(
                        null=True, db_column="exitCode", blank=True
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(auto_now_add=True, db_column="createdTime"),
                ),
                (
                    "updatedtime",
                    models.DateTimeField(auto_now=True, db_column="updatedTime"),
                ),
            ],
            options={"db_table": "Accesses"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Agent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                ("identifiertype", models.TextField(db_column="agentIdentifierType")),
                ("identifiervalue", models.TextField(db_column="agentIdentifierValue")),
                ("name", models.TextField(db_column="agentName")),
                ("agenttype", models.TextField(db_column="agentType")),
            ],
            options={"db_table": "Agents"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="AtkDIPObjectResourcePairing",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                ("dipuuid", models.CharField(max_length=50, db_column="dipUUID")),
                ("fileuuid", models.CharField(max_length=50, db_column="fileUUID")),
                ("resourceid", models.IntegerField(db_column="resourceId")),
                (
                    "resourcecomponentid",
                    models.IntegerField(db_column="resourceComponentId"),
                ),
            ],
            options={"db_table": "AtkDIPObjectResourcePairing"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="DashboardSetting",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                ("name", models.CharField(max_length=255, db_column="name")),
                ("value", models.TextField(db_column="value", blank=True)),
                (
                    "lastmodified",
                    models.DateTimeField(auto_now=True, db_column="lastModified"),
                ),
            ],
            options={"db_table": "DashboardSettings"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Derivation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                )
            ],
            options={"db_table": "Derivations"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="DublinCore",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "metadataappliestoidentifier",
                    models.CharField(
                        max_length=36, db_column="metadataAppliesToidentifier"
                    ),
                ),
                ("title", models.TextField(db_column="title", blank=True)),
                (
                    "is_part_of",
                    models.TextField(
                        help_text="Optional: leave blank if unsure",
                        verbose_name="Part of AIC",
                        db_column="isPartOf",
                        blank=True,
                    ),
                ),
                ("creator", models.TextField(db_column="creator", blank=True)),
                ("subject", models.TextField(db_column="subject", blank=True)),
                ("description", models.TextField(db_column="description", blank=True)),
                ("publisher", models.TextField(db_column="publisher", blank=True)),
                ("contributor", models.TextField(db_column="contributor", blank=True)),
                (
                    "date",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)",
                        db_column="date",
                        blank=True,
                    ),
                ),
                ("type", models.TextField(db_column="type", blank=True)),
                ("format", models.TextField(db_column="format", blank=True)),
                ("identifier", models.TextField(db_column="identifier", blank=True)),
                ("source", models.TextField(db_column="source", blank=True)),
                ("relation", models.TextField(db_column="relation", blank=True)),
                (
                    "language",
                    models.TextField(
                        help_text="Use ISO 639", db_column="language", blank=True
                    ),
                ),
                ("coverage", models.TextField(db_column="coverage", blank=True)),
                ("rights", models.TextField(db_column="rights", blank=True)),
            ],
            options={"db_table": "Dublincore"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "event_id",
                    django_extensions.db.fields.UUIDField(
                        null=True,
                        db_column="eventIdentifierUUID",
                        editable=False,
                        max_length=36,
                        blank=True,
                        unique=True,
                    ),
                ),
                ("event_type", models.TextField(db_column="eventType", blank=True)),
                (
                    "event_datetime",
                    models.DateTimeField(auto_now=True, db_column="eventDateTime"),
                ),
                ("event_detail", models.TextField(db_column="eventDetail", blank=True)),
                (
                    "event_outcome",
                    models.TextField(db_column="eventOutcome", blank=True),
                ),
                (
                    "event_outcome_detail",
                    models.TextField(db_column="eventOutcomeDetailNote", blank=True),
                ),
                (
                    "linking_agent",
                    models.IntegerField(null=True, db_column="linkingAgentIdentifier"),
                ),
            ],
            options={"db_table": "Events"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="File",
            fields=[
                (
                    "uuid",
                    models.CharField(
                        max_length=36,
                        serialize=False,
                        primary_key=True,
                        db_column="fileUUID",
                    ),
                ),
                ("originallocation", models.TextField(db_column="originalLocation")),
                ("currentlocation", models.TextField(db_column="currentLocation")),
                (
                    "filegrpuse",
                    models.CharField(
                        default="Original", max_length=50, db_column="fileGrpUse"
                    ),
                ),
                (
                    "filegrpuuid",
                    models.CharField(
                        max_length=36, db_column="fileGrpUUID", blank=True
                    ),
                ),
                (
                    "checksum",
                    models.CharField(max_length=100, db_column="checksum", blank=True),
                ),
                (
                    "size",
                    models.BigIntegerField(null=True, db_column="fileSize", blank=True),
                ),
                ("label", models.TextField(blank=True)),
                (
                    "enteredsystem",
                    models.DateTimeField(auto_now_add=True, db_column="enteredSystem"),
                ),
                (
                    "removedtime",
                    models.DateTimeField(
                        default=None, null=True, db_column="removedTime"
                    ),
                ),
            ],
            options={"db_table": "Files"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="FileFormatVersion",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "file_uuid",
                    models.ForeignKey(
                        to="main.File", db_column="fileUUID", on_delete=models.CASCADE
                    ),
                ),
                (
                    "format_version",
                    models.ForeignKey(
                        to="fpr.FormatVersion",
                        db_column="fileID",
                        to_field="uuid",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "FilesIdentifiedIDs"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="FileID",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                ("format_name", models.TextField(db_column="formatName", blank=True)),
                (
                    "format_version",
                    models.TextField(db_column="formatVersion", blank=True),
                ),
                (
                    "format_registry_name",
                    models.TextField(db_column="formatRegistryName", blank=True),
                ),
                (
                    "format_registry_key",
                    models.TextField(db_column="formatRegistryKey", blank=True),
                ),
                (
                    "file",
                    models.ForeignKey(
                        db_column="fileUUID",
                        blank=True,
                        to="main.File",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "FilesIDs"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="FPCommandOutput",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("content", models.TextField(null=True)),
                (
                    "file",
                    models.ForeignKey(
                        to="main.File", db_column="fileUUID", on_delete=models.CASCADE
                    ),
                ),
                (
                    "rule",
                    models.ForeignKey(
                        to="fpr.FPRule",
                        db_column="ruleUUID",
                        to_field="uuid",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Job",
            fields=[
                (
                    "jobuuid",
                    django_extensions.db.fields.UUIDField(
                        primary_key=True,
                        db_column="jobUUID",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "jobtype",
                    models.CharField(max_length=250, db_column="jobType", blank=True),
                ),
                ("createdtime", models.DateTimeField(db_column="createdTime")),
                (
                    "createdtimedec",
                    models.DecimalField(
                        default=0.0,
                        decimal_places=10,
                        max_digits=26,
                        db_column="createdTimeDec",
                    ),
                ),
                ("directory", models.TextField(blank=True)),
                ("sipuuid", models.CharField(max_length=36, db_column="SIPUUID")),
                (
                    "unittype",
                    models.CharField(max_length=50, db_column="unitType", blank=True),
                ),
                (
                    "currentstep",
                    models.CharField(
                        max_length=50, db_column="currentStep", blank=True
                    ),
                ),
                (
                    "microservicegroup",
                    models.CharField(
                        max_length=50, db_column="microserviceGroup", blank=True
                    ),
                ),
                ("hidden", models.BooleanField(default=False)),
                (
                    "subjobof",
                    models.CharField(max_length=36, db_column="subJobOf", blank=True),
                ),
            ],
            options={"db_table": "Jobs"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MetadataAppliesToType",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "description",
                    models.CharField(max_length=50, db_column="description"),
                ),
                (
                    "replaces",
                    models.CharField(
                        max_length=36, null=True, db_column="replaces", blank=True
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
            ],
            options={"db_table": "MetadataAppliesToTypes"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MicroServiceChain",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                ("description", models.TextField(db_column="description")),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        related_name="replaced_by",
                        db_column="replaces",
                        to="main.MicroServiceChain",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "MicroServiceChains"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MicroServiceChainChoice",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
                (
                    "chainavailable",
                    models.ForeignKey(
                        to="main.MicroServiceChain",
                        db_column="chainAvailable",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "MicroServiceChainChoice"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MicroServiceChainLink",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "microservicegroup",
                    models.CharField(max_length=50, db_column="microserviceGroup"),
                ),
                (
                    "reloadfilelist",
                    models.BooleanField(default=True, db_column="reloadFileList"),
                ),
                (
                    "defaultexitmessage",
                    models.CharField(
                        default="Failed", max_length=36, db_column="defaultExitMessage"
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
            ],
            options={"db_table": "MicroServiceChainLinks"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MicroServiceChainLinkExitCode",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                ("exitcode", models.IntegerField(default=0, db_column="exitCode")),
                (
                    "exitmessage",
                    models.CharField(
                        default="Completed successfully",
                        max_length=50,
                        db_column="exitMessage",
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
                (
                    "microservicechainlink",
                    models.ForeignKey(
                        related_name="exit_codes",
                        db_column="microServiceChainLink",
                        to="main.MicroServiceChainLink",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "nextmicroservicechainlink",
                    models.ForeignKey(
                        related_name="parent_exit_codes+",
                        db_column="nextMicroServiceChainLink",
                        blank=True,
                        to="main.MicroServiceChainLink",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        related_name="replaced_by",
                        db_column="replaces",
                        blank=True,
                        to="main.MicroServiceChainLinkExitCode",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "MicroServiceChainLinksExitCodes"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MicroServiceChoiceReplacementDic",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        verbose_name="Description", db_column="description"
                    ),
                ),
                (
                    "replacementdic",
                    models.TextField(
                        verbose_name="Configuration", db_column="replacementDic"
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
                (
                    "choiceavailableatlink",
                    models.ForeignKey(
                        to="main.MicroServiceChainLink",
                        db_column="choiceAvailableAtLink",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        related_name="replaced_by",
                        db_column="replaces",
                        blank=True,
                        to="main.MicroServiceChoiceReplacementDic",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "MicroServiceChoiceReplacementDic"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Report",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                ("unittype", models.CharField(max_length=50, db_column="unitType")),
                ("unitname", models.CharField(max_length=50, db_column="unitName")),
                (
                    "unitidentifier",
                    models.CharField(max_length=36, db_column="unitIdentifier"),
                ),
                ("content", models.TextField(db_column="content")),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, db_column="created"),
                ),
            ],
            options={"db_table": "Reports"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatement",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "metadataappliestoidentifier",
                    models.CharField(
                        max_length=50, db_column="metadataAppliesToidentifier"
                    ),
                ),
                (
                    "rightsstatementidentifiertype",
                    models.TextField(
                        verbose_name="Type",
                        db_column="rightsStatementIdentifierType",
                        blank=True,
                    ),
                ),
                (
                    "rightsstatementidentifiervalue",
                    models.TextField(
                        verbose_name="Value",
                        db_column="rightsStatementIdentifierValue",
                        blank=True,
                    ),
                ),
                (
                    "rightsholder",
                    models.IntegerField(
                        default=0, verbose_name="Rights holder", db_column="fkAgent"
                    ),
                ),
                (
                    "rightsbasis",
                    models.TextField(verbose_name="Basis", db_column="rightsBasis"),
                ),
                (
                    "metadataappliestotype",
                    models.ForeignKey(
                        to="main.MetadataAppliesToType",
                        db_column="metadataAppliesToType",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "RightsStatement", "verbose_name": "Rights Statement"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementCopyright",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "copyrightstatus",
                    models.TextField(
                        verbose_name="Copyright status",
                        db_column="copyrightStatus",
                        blank=True,
                    ),
                ),
                (
                    "copyrightjurisdiction",
                    models.TextField(
                        verbose_name="Copyright jurisdiction",
                        db_column="copyrightJurisdiction",
                        blank=True,
                    ),
                ),
                (
                    "copyrightstatusdeterminationdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="Copyright determination date",
                        db_column="copyrightStatusDeterminationDate",
                        blank=True,
                    ),
                ),
                (
                    "copyrightapplicablestartdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="Copyright start date",
                        db_column="copyrightApplicableStartDate",
                        blank=True,
                    ),
                ),
                (
                    "copyrightapplicableenddate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="Copyright end date",
                        db_column="copyrightApplicableEndDate",
                        blank=True,
                    ),
                ),
                (
                    "copyrightenddateopen",
                    models.BooleanField(
                        help_text="Indicate end date is open",
                        verbose_name="Open End Date",
                        db_column="copyrightApplicableEndDateOpen",
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementCopyright",
                "verbose_name": "Rights: Copyright",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementCopyrightDocumentationIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "copyrightdocumentationidentifiertype",
                    models.TextField(
                        verbose_name="Copyright document identification type",
                        db_column="copyrightDocumentationIdentifierType",
                        blank=True,
                    ),
                ),
                (
                    "copyrightdocumentationidentifiervalue",
                    models.TextField(
                        verbose_name="Copyright document identification value",
                        db_column="copyrightDocumentationIdentifierValue",
                        blank=True,
                    ),
                ),
                (
                    "copyrightdocumentationidentifierrole",
                    models.TextField(
                        verbose_name="Copyright document identification role",
                        db_column="copyrightDocumentationIdentifierRole",
                        blank=True,
                    ),
                ),
                (
                    "rightscopyright",
                    models.ForeignKey(
                        to="main.RightsStatementCopyright",
                        db_column="fkRightsStatementCopyrightInformation",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementCopyrightDocumentationIdentifier",
                "verbose_name": "Rights: Copyright: Docs ID",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementCopyrightNote",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "copyrightnote",
                    models.TextField(
                        verbose_name="Copyright note",
                        db_column="copyrightNote",
                        blank=True,
                    ),
                ),
                (
                    "rightscopyright",
                    models.ForeignKey(
                        to="main.RightsStatementCopyright",
                        db_column="fkRightsStatementCopyrightInformation",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementCopyrightNote",
                "verbose_name": "Rights: Copyright: Note",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementLicense",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "licenseterms",
                    models.TextField(
                        verbose_name="License terms",
                        db_column="licenseTerms",
                        blank=True,
                    ),
                ),
                (
                    "licenseapplicablestartdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="License start date",
                        db_column="licenseApplicableStartDate",
                        blank=True,
                    ),
                ),
                (
                    "licenseapplicableenddate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="License end date",
                        db_column="licenseApplicableEndDate",
                        blank=True,
                    ),
                ),
                (
                    "licenseenddateopen",
                    models.BooleanField(
                        help_text="Indicate end date is open",
                        verbose_name="Open End Date",
                        db_column="licenseApplicableEndDateOpen",
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementLicense",
                "verbose_name": "Rights: License",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementLicenseDocumentationIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "licensedocumentationidentifiertype",
                    models.TextField(
                        verbose_name="License documentation identification type",
                        db_column="licenseDocumentationIdentifierType",
                        blank=True,
                    ),
                ),
                (
                    "licensedocumentationidentifiervalue",
                    models.TextField(
                        verbose_name="License documentation identification value",
                        db_column="licenseDocumentationIdentifierValue",
                        blank=True,
                    ),
                ),
                (
                    "licensedocumentationidentifierrole",
                    models.TextField(
                        verbose_name="License document identification role",
                        db_column="licenseDocumentationIdentifierRole",
                        blank=True,
                    ),
                ),
                (
                    "rightsstatementlicense",
                    models.ForeignKey(
                        to="main.RightsStatementLicense",
                        db_column="fkRightsStatementLicense",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementLicenseDocumentationIdentifier",
                "verbose_name": "Rights: License: Docs ID",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementLicenseNote",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "licensenote",
                    models.TextField(
                        verbose_name="License note", db_column="licenseNote", blank=True
                    ),
                ),
                (
                    "rightsstatementlicense",
                    models.ForeignKey(
                        to="main.RightsStatementLicense",
                        db_column="fkRightsStatementLicense",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementLicenseNote",
                "verbose_name": "Rights: License: Note",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementLinkingAgentIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "linkingagentidentifiertype",
                    models.TextField(
                        verbose_name="Linking Agent",
                        db_column="linkingAgentIdentifierType",
                        blank=True,
                    ),
                ),
                (
                    "linkingagentidentifiervalue",
                    models.TextField(
                        verbose_name="Linking Agent Value",
                        db_column="linkingAgentIdentifierValue",
                        blank=True,
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementLinkingAgentIdentifier",
                "verbose_name": "Rights: Agent",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementOtherRightsDocumentationIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "otherrightsdocumentationidentifiertype",
                    models.TextField(
                        verbose_name="Other rights document identification type",
                        db_column="otherRightsDocumentationIdentifierType",
                        blank=True,
                    ),
                ),
                (
                    "otherrightsdocumentationidentifiervalue",
                    models.TextField(
                        verbose_name="Other right document identification value",
                        db_column="otherRightsDocumentationIdentifierValue",
                        blank=True,
                    ),
                ),
                (
                    "otherrightsdocumentationidentifierrole",
                    models.TextField(
                        verbose_name="Other rights document identification role",
                        db_column="otherRightsDocumentationIdentifierRole",
                        blank=True,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementOtherRightsDocumentationIdentifier",
                "verbose_name": "Rights: Other: Docs ID",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementOtherRightsInformation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "otherrightsbasis",
                    models.TextField(
                        verbose_name="Other rights basis",
                        db_column="otherRightsBasis",
                        blank=True,
                    ),
                ),
                (
                    "otherrightsapplicablestartdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="Other rights start date",
                        db_column="otherRightsApplicableStartDate",
                        blank=True,
                    ),
                ),
                (
                    "otherrightsapplicableenddate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="Other rights end date",
                        db_column="otherRightsApplicableEndDate",
                        blank=True,
                    ),
                ),
                (
                    "otherrightsenddateopen",
                    models.BooleanField(
                        help_text="Indicate end date is open",
                        verbose_name="Open End Date",
                        db_column="otherRightsApplicableEndDateOpen",
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementOtherRightsInformation",
                "verbose_name": "Rights: Other",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementOtherRightsInformationNote",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "otherrightsnote",
                    models.TextField(
                        verbose_name="Other rights note",
                        db_column="otherRightsNote",
                        blank=True,
                    ),
                ),
                (
                    "rightsstatementotherrights",
                    models.ForeignKey(
                        to="main.RightsStatementOtherRightsInformation",
                        db_column="fkRightsStatementOtherRightsInformation",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementOtherRightsNote",
                "verbose_name": "Rights: Other: Note",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementRightsGranted",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                ("act", models.TextField(db_column="act", blank=True)),
                (
                    "startdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="Start",
                        db_column="startDate",
                        blank=True,
                    ),
                ),
                (
                    "enddate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="End",
                        db_column="endDate",
                        blank=True,
                    ),
                ),
                (
                    "enddateopen",
                    models.BooleanField(
                        help_text="Indicate end date is open",
                        verbose_name="Open End Date",
                        db_column="endDateOpen",
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementRightsGranted",
                "verbose_name": "Rights: Granted",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementRightsGrantedNote",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "rightsgrantednote",
                    models.TextField(
                        verbose_name="Rights note",
                        db_column="rightsGrantedNote",
                        blank=True,
                    ),
                ),
                (
                    "rightsgranted",
                    models.ForeignKey(
                        to="main.RightsStatementRightsGranted",
                        db_column="fkRightsStatementRightsGranted",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementRightsGrantedNote",
                "verbose_name": "Rights: Granted: Note",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementRightsGrantedRestriction",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                ("restriction", models.TextField(db_column="restriction", blank=True)),
                (
                    "rightsgranted",
                    models.ForeignKey(
                        to="main.RightsStatementRightsGranted",
                        db_column="fkRightsStatementRightsGranted",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementRightsGrantedRestriction",
                "verbose_name": "Rights: Granted: Restriction",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementStatuteDocumentationIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "statutedocumentationidentifiertype",
                    models.TextField(
                        verbose_name="Statute document identification type",
                        db_column="statuteDocumentationIdentifierType",
                        blank=True,
                    ),
                ),
                (
                    "statutedocumentationidentifiervalue",
                    models.TextField(
                        verbose_name="Statute document identification value",
                        db_column="statuteDocumentationIdentifierValue",
                        blank=True,
                    ),
                ),
                (
                    "statutedocumentationidentifierrole",
                    models.TextField(
                        verbose_name="Statute document identification role",
                        db_column="statuteDocumentationIdentifierRole",
                        blank=True,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementStatuteDocumentationIdentifier",
                "verbose_name": "Rights: Statute: Docs ID",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementStatuteInformation",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "statutejurisdiction",
                    models.TextField(
                        verbose_name="Statute jurisdiction",
                        db_column="statuteJurisdiction",
                        blank=True,
                    ),
                ),
                (
                    "statutecitation",
                    models.TextField(
                        verbose_name="Statute citation",
                        db_column="statuteCitation",
                        blank=True,
                    ),
                ),
                (
                    "statutedeterminationdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="Statute determination date",
                        db_column="statuteInformationDeterminationDate",
                        blank=True,
                    ),
                ),
                (
                    "statuteapplicablestartdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="Statute start date",
                        db_column="statuteApplicableStartDate",
                        blank=True,
                    ),
                ),
                (
                    "statuteapplicableenddate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        verbose_name="Statute end date",
                        db_column="statuteApplicableEndDate",
                        blank=True,
                    ),
                ),
                (
                    "statuteenddateopen",
                    models.BooleanField(
                        help_text="Indicate end date is open",
                        verbose_name="Open End Date",
                        db_column="statuteApplicableEndDateOpen",
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementStatuteInformation",
                "verbose_name": "Rights: Statute",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RightsStatementStatuteInformationNote",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "statutenote",
                    models.TextField(
                        verbose_name="Statute note", db_column="statuteNote", blank=True
                    ),
                ),
                (
                    "rightsstatementstatute",
                    models.ForeignKey(
                        to="main.RightsStatementStatuteInformation",
                        db_column="fkRightsStatementStatuteInformation",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementStatuteInformationNote",
                "verbose_name": "Rights: Statute: Note",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="SIP",
            fields=[
                (
                    "uuid",
                    models.CharField(
                        max_length=36,
                        serialize=False,
                        primary_key=True,
                        db_column="sipUUID",
                    ),
                ),
                ("createdtime", models.DateTimeField(db_column="createdTime")),
                (
                    "currentpath",
                    models.TextField(null=True, db_column="currentPath", blank=True),
                ),
                ("hidden", models.BooleanField(default=False)),
                (
                    "aip_filename",
                    models.TextField(null=True, db_column="aipFilename", blank=True),
                ),
                (
                    "sip_type",
                    models.CharField(
                        default="SIP",
                        max_length=8,
                        db_column="sipType",
                        choices=[("SIP", "SIP"), ("AIC", "AIC")],
                    ),
                ),
                (
                    "magiclinkexitmessage",
                    models.CharField(
                        max_length=50,
                        null=True,
                        db_column="magicLinkExitMessage",
                        blank=True,
                    ),
                ),
                (
                    "magiclink",
                    models.ForeignKey(
                        db_column="magicLink",
                        blank=True,
                        to="main.MicroServiceChainLink",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "SIPs"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="SIPArrange",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "original_path",
                    models.CharField(
                        default=None, max_length=255, unique=True, null=True, blank=True
                    ),
                ),
                ("arrange_path", models.CharField(max_length=255)),
                (
                    "file_uuid",
                    django_extensions.db.fields.UUIDField(
                        default=None,
                        max_length=36,
                        null=True,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "transfer_uuid",
                    django_extensions.db.fields.UUIDField(
                        default=None,
                        max_length=36,
                        null=True,
                        editable=False,
                        blank=True,
                    ),
                ),
                ("sip_created", models.BooleanField(default=False)),
                ("aip_created", models.BooleanField(default=False)),
            ],
            options={"verbose_name": "Arranged SIPs"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="StandardTaskConfig",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "execute",
                    models.CharField(max_length=250, null=True, db_column="execute"),
                ),
                ("arguments", models.TextField(null=True, db_column="arguments")),
                (
                    "filter_subdir",
                    models.CharField(
                        max_length=50, null=True, db_column="filterSubDir", blank=True
                    ),
                ),
                (
                    "filter_file_start",
                    models.CharField(
                        max_length=50,
                        null=True,
                        db_column="filterFileStart",
                        blank=True,
                    ),
                ),
                (
                    "filter_file_end",
                    models.CharField(
                        max_length=50, null=True, db_column="filterFileEnd", blank=True
                    ),
                ),
                (
                    "requires_output_lock",
                    models.BooleanField(default=False, db_column="requiresOutputLock"),
                ),
                (
                    "stdout_file",
                    models.CharField(
                        max_length=250,
                        null=True,
                        db_column="standardOutputFile",
                        blank=True,
                    ),
                ),
                (
                    "stderr_file",
                    models.CharField(
                        max_length=250,
                        null=True,
                        db_column="standardErrorFile",
                        blank=True,
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        related_name="replaced_by",
                        db_column="replaces",
                        blank=True,
                        to="main.StandardTaskConfig",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "StandardTasksConfigs"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "taskuuid",
                    models.CharField(
                        max_length=36,
                        serialize=False,
                        primary_key=True,
                        db_column="taskUUID",
                    ),
                ),
                ("createdtime", models.DateTimeField(db_column="createdTime")),
                (
                    "fileuuid",
                    models.CharField(
                        max_length=36, null=True, db_column="fileUUID", blank=True
                    ),
                ),
                ("filename", models.TextField(db_column="fileName", blank=True)),
                (
                    "execution",
                    models.CharField(max_length=250, db_column="exec", blank=True),
                ),
                ("arguments", models.CharField(max_length=1000, blank=True)),
                (
                    "starttime",
                    models.DateTimeField(
                        default=None, null=True, db_column="startTime"
                    ),
                ),
                (
                    "endtime",
                    models.DateTimeField(default=None, null=True, db_column="endTime"),
                ),
                ("client", models.CharField(max_length=50, blank=True)),
                ("stdout", models.TextField(db_column="stdOut", blank=True)),
                ("stderror", models.TextField(db_column="stdError", blank=True)),
                (
                    "exitcode",
                    models.BigIntegerField(null=True, db_column="exitCode", blank=True),
                ),
                (
                    "job",
                    models.ForeignKey(
                        to="main.Job", db_column="jobuuid", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={"db_table": "Tasks"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TaskConfig",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "tasktypepkreference",
                    models.CharField(
                        default=None,
                        max_length=36,
                        null=True,
                        db_column="taskTypePKReference",
                        blank=True,
                    ),
                ),
                ("description", models.TextField(db_column="description")),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        related_name="replaced_by",
                        db_column="replaces",
                        blank=True,
                        to="main.TaskConfig",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TasksConfigs"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TaskConfigAssignMagicLink",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
                (
                    "execute",
                    models.ForeignKey(
                        db_column="execute",
                        blank=True,
                        to="main.MicroServiceChainLink",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        related_name="replaced_by",
                        db_column="replaces",
                        blank=True,
                        to="main.TaskConfigAssignMagicLink",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TasksConfigsAssignMagicLink"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TaskConfigSetUnitVariable",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                ("variable", models.TextField(blank=True)),
                (
                    "variablevalue",
                    models.TextField(null=True, db_column="variableValue", blank=True),
                ),
                (
                    "createdtime",
                    models.DateTimeField(auto_now_add=True, db_column="createdTime"),
                ),
                (
                    "updatedtime",
                    models.DateTimeField(
                        auto_now=True, null=True, db_column="updatedTime"
                    ),
                ),
                (
                    "microservicechainlink",
                    models.ForeignKey(
                        db_column="microServiceChainLink",
                        to="main.MicroServiceChainLink",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TasksConfigsSetUnitVariable"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TaskConfigUnitVariableLinkPull",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                ("variable", models.TextField(blank=True)),
                (
                    "variablevalue",
                    models.TextField(null=True, db_column="variableValue", blank=True),
                ),
                (
                    "createdtime",
                    models.DateTimeField(auto_now_add=True, db_column="createdTime"),
                ),
                (
                    "updatedtime",
                    models.DateTimeField(
                        auto_now=True, null=True, db_column="updatedTime"
                    ),
                ),
                (
                    "defaultmicroservicechainlink",
                    models.ForeignKey(
                        db_column="defaultMicroServiceChainLink",
                        to="main.MicroServiceChainLink",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TasksConfigsUnitVariableLinkPull"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TaskType",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        related_name="replaced_by",
                        db_column="replaces",
                        blank=True,
                        to="main.TaskType",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TaskTypes"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Taxonomy",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(
                        auto_now_add=True, null=True, db_column="createdTime"
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, db_column="name", blank=True),
                ),
                ("type", models.CharField(default="open", max_length=50)),
            ],
            options={"db_table": "Taxonomies"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TaxonomyTerm",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(
                        auto_now_add=True, null=True, db_column="createdTime"
                    ),
                ),
                ("term", models.CharField(max_length=255, db_column="term")),
                (
                    "taxonomy",
                    models.ForeignKey(
                        to="main.Taxonomy",
                        db_column="taxonomyUUID",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TaxonomyTerms"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Transfer",
            fields=[
                (
                    "uuid",
                    models.CharField(
                        max_length=36,
                        serialize=False,
                        primary_key=True,
                        db_column="transferUUID",
                    ),
                ),
                ("currentlocation", models.TextField(db_column="currentLocation")),
                ("type", models.CharField(max_length=50, db_column="type")),
                ("accessionid", models.TextField(db_column="accessionID")),
                (
                    "sourceofacquisition",
                    models.TextField(db_column="sourceOfAcquisition", blank=True),
                ),
                (
                    "typeoftransfer",
                    models.TextField(db_column="typeOfTransfer", blank=True),
                ),
                ("description", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "magiclinkexitmessage",
                    models.CharField(
                        max_length=50,
                        null=True,
                        db_column="magicLinkExitMessage",
                        blank=True,
                    ),
                ),
                (
                    "magiclink",
                    models.ForeignKey(
                        db_column="magicLink",
                        blank=True,
                        to="main.MicroServiceChainLink",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "Transfers"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TransferMetadataField",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(
                        auto_now_add=True, null=True, db_column="createdTime"
                    ),
                ),
                (
                    "fieldlabel",
                    models.CharField(max_length=50, db_column="fieldLabel", blank=True),
                ),
                ("fieldname", models.CharField(max_length=50, db_column="fieldName")),
                ("fieldtype", models.CharField(max_length=50, db_column="fieldType")),
                ("sortorder", models.IntegerField(default=0, db_column="sortOrder")),
                (
                    "optiontaxonomy",
                    models.ForeignKey(
                        db_column="optionTaxonomyUUID",
                        to="main.Taxonomy",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TransferMetadataFields"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TransferMetadataFieldValue",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(auto_now_add=True, db_column="createdTime"),
                ),
                ("fieldvalue", models.TextField(db_column="fieldValue", blank=True)),
                (
                    "field",
                    models.ForeignKey(
                        to="main.TransferMetadataField",
                        db_column="fieldUUID",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TransferMetadataFieldValues"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TransferMetadataSet",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(auto_now_add=True, db_column="createdTime"),
                ),
                ("createdbyuserid", models.IntegerField(db_column="createdByUserID")),
            ],
            options={"db_table": "TransferMetadataSets"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="UnitVariable",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "unittype",
                    models.CharField(
                        max_length=50, null=True, db_column="unitType", blank=True
                    ),
                ),
                (
                    "unituuid",
                    models.CharField(
                        help_text="Semantically a foreign key to SIP or Transfer",
                        max_length=36,
                        null=True,
                        db_column="unitUUID",
                    ),
                ),
                ("variable", models.TextField(null=True, db_column="variable")),
                (
                    "variablevalue",
                    models.TextField(null=True, db_column="variableValue"),
                ),
                (
                    "createdtime",
                    models.DateTimeField(auto_now_add=True, db_column="createdTime"),
                ),
                (
                    "updatedtime",
                    models.DateTimeField(auto_now=True, db_column="updatedTime"),
                ),
                (
                    "microservicechainlink",
                    models.ForeignKey(
                        db_column="microServiceChainLink",
                        blank=True,
                        to="main.MicroServiceChainLink",
                        help_text="UUID of the MicroServiceChainLink if used in task type linkTaskManagerUnitVariableLinkPull",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "UnitVariables"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="WatchedDirectory",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                (
                    "watched_directory_path",
                    models.TextField(
                        null=True, db_column="watchedDirectoryPath", blank=True
                    ),
                ),
                (
                    "only_act_on_directories",
                    models.BooleanField(default=True, db_column="onlyActOnDirectories"),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
                (
                    "chain",
                    models.ForeignKey(
                        db_column="chain",
                        to="main.MicroServiceChain",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "WatchedDirectories"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="WatchedDirectoryExpectedType",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                ("description", models.TextField(null=True)),
                (
                    "lastmodified",
                    models.DateTimeField(db_column="lastModified", auto_now=True),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        db_column="replaces",
                        to="main.WatchedDirectoryExpectedType",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "WatchedDirectoriesExpectedTypes"},
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="watcheddirectory",
            name="expected_type",
            field=models.ForeignKey(
                db_column="expectedType",
                to="main.WatchedDirectoryExpectedType",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="watcheddirectory",
            name="replaces",
            field=models.ForeignKey(
                db_column="replaces",
                to="main.WatchedDirectory",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="transfermetadatafieldvalue",
            name="set",
            field=models.ForeignKey(
                to="main.TransferMetadataSet",
                db_column="setUUID",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="transfer",
            name="transfermetadatasetrow",
            field=models.ForeignKey(
                db_column="transferMetadataSetRowUUID",
                blank=True,
                to="main.TransferMetadataSet",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="taskconfig",
            name="tasktype",
            field=models.ForeignKey(
                to="main.TaskType", db_column="taskType", on_delete=models.CASCADE
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="rightsstatementstatutedocumentationidentifier",
            name="rightsstatementstatute",
            field=models.ForeignKey(
                to="main.RightsStatementStatuteInformation",
                db_column="fkRightsStatementStatuteInformation",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="rightsstatementotherrightsdocumentationidentifier",
            name="rightsstatementotherrights",
            field=models.ForeignKey(
                to="main.RightsStatementOtherRightsInformation",
                db_column="fkRightsStatementOtherRightsInformation",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="microservicechainlink",
            name="currenttask",
            field=models.ForeignKey(
                to="main.TaskConfig", db_column="currentTask", on_delete=models.CASCADE
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="microservicechainlink",
            name="defaultnextchainlink",
            field=models.ForeignKey(
                to="main.MicroServiceChainLink",
                null=True,
                db_column="defaultNextChainLink",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="microservicechainlink",
            name="replaces",
            field=models.ForeignKey(
                related_name="replaced_by",
                db_column="replaces",
                to="main.MicroServiceChainLink",
                null=True,
                blank=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="microservicechainchoice",
            name="choiceavailableatlink",
            field=models.ForeignKey(
                to="main.MicroServiceChainLink",
                db_column="choiceAvailableAtLink",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="microservicechainchoice",
            name="replaces",
            field=models.ForeignKey(
                related_name="replaced_by",
                db_column="replaces",
                blank=True,
                to="main.MicroServiceChainChoice",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="microservicechain",
            name="startinglink",
            field=models.ForeignKey(
                to="main.MicroServiceChainLink",
                db_column="startingLink",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="job",
            name="microservicechainlink",
            field=models.ForeignKey(
                db_column="MicroServiceChainLinksPK",
                blank=True,
                to="main.MicroServiceChainLink",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="file",
            name="sip",
            field=models.ForeignKey(
                db_column="sipUUID",
                blank=True,
                to="main.SIP",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="file",
            name="transfer",
            field=models.ForeignKey(
                db_column="transferUUID",
                blank=True,
                to="main.Transfer",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="event",
            name="file_uuid",
            field=models.ForeignKey(
                db_column="fileUUID",
                blank=True,
                to="main.File",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="dublincore",
            name="metadataappliestotype",
            field=models.ForeignKey(
                to="main.MetadataAppliesToType",
                db_column="metadataAppliesToType",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="derivation",
            name="derived_file",
            field=models.ForeignKey(
                related_name="original_file_set",
                db_column="derivedFileUUID",
                to="main.File",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="derivation",
            name="event",
            field=models.ForeignKey(
                db_column="relatedEventUUID",
                to_field="event_id",
                blank=True,
                to="main.Event",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="derivation",
            name="source_file",
            field=models.ForeignKey(
                related_name="derived_file_set",
                db_column="sourceFileUUID",
                to="main.File",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
    ]

from typing import Any
from typing import Dict

from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'FPRule'
        db.create_table(
            "fpr_fprule",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "replaces",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.FPRule"], to_field="uuid", null=True, blank=True
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.BooleanField")(default=True),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        auto_now_add=True, blank=True
                    ),
                ),
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        unique=True, max_length=36, blank=True
                    ),
                ),
                (
                    "purpose",
                    self.gf("django.db.models.fields.CharField")(max_length=32),
                ),
                (
                    "command",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.FPCommand"], to_field="uuid"
                    ),
                ),
                (
                    "format",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.FormatVersion"], to_field="uuid"
                    ),
                ),
                (
                    "count_attempts",
                    self.gf("django.db.models.fields.IntegerField")(default=0),
                ),
                (
                    "count_okay",
                    self.gf("django.db.models.fields.IntegerField")(default=0),
                ),
                (
                    "count_not_okay",
                    self.gf("django.db.models.fields.IntegerField")(default=0),
                ),
            ),
        )
        db.send_create_signal("fpr", ["FPRule"])

        # Adding model 'FPTool'
        db.create_table(
            "fpr_fptool",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        unique=True, max_length=36, blank=True
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.CharField")(max_length=256),
                ),
                (
                    "version",
                    self.gf("django.db.models.fields.CharField")(max_length=64),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.BooleanField")(default=True),
                ),
                (
                    "slug",
                    self.gf("autoslug.fields.AutoSlugField")(
                        unique_with=(), max_length=50, populate_from="_slug"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["FPTool"])

        # Adding model 'FormatVersion'
        db.create_table(
            "fpr_formatversion",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "replaces",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.FormatVersion"],
                        to_field="uuid",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.BooleanField")(default=True),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        auto_now_add=True, blank=True
                    ),
                ),
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        unique=True, max_length=36, blank=True
                    ),
                ),
                (
                    "format",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        related_name="version_set",
                        to_field="uuid",
                        null=True,
                        to=orm["fpr.Format"],
                    ),
                ),
                (
                    "version",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=10, null=True, blank=True
                    ),
                ),
                (
                    "pronom_id",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=32, null=True, blank=True
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=128, null=True, blank=True
                    ),
                ),
                (
                    "access_format",
                    self.gf("django.db.models.fields.BooleanField")(default=False),
                ),
                (
                    "preservation_format",
                    self.gf("django.db.models.fields.BooleanField")(default=False),
                ),
                (
                    "slug",
                    self.gf("autoslug.fields.AutoSlugField")(
                        unique_with=("format",),
                        max_length=50,
                        populate_from="description",
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["FormatVersion"])

        # Adding model 'IDRule'
        db.create_table(
            "fpr_idrule",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "replaces",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.IDRule"], to_field="uuid", null=True, blank=True
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.BooleanField")(default=True),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        auto_now_add=True, blank=True
                    ),
                ),
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        unique=True, max_length=36, blank=True
                    ),
                ),
                (
                    "command",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.IDCommand"], to_field="uuid"
                    ),
                ),
                (
                    "format",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.FormatVersion"], to_field="uuid"
                    ),
                ),
                ("command_output", self.gf("django.db.models.fields.TextField")()),
            ),
        )
        db.send_create_signal("fpr", ["IDRule"])

        # Adding model 'IDTool'
        db.create_table(
            "fpr_idtool",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        unique=True, max_length=36, blank=True
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.CharField")(max_length=256),
                ),
                (
                    "version",
                    self.gf("django.db.models.fields.CharField")(max_length=64),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.BooleanField")(default=True),
                ),
                (
                    "slug",
                    self.gf("autoslug.fields.AutoSlugField")(
                        unique_with=(), max_length=50, populate_from="_slug"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["IDTool"])

        # Adding model 'IDCommand'
        db.create_table(
            "fpr_idcommand",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "replaces",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.IDCommand"], to_field="uuid", null=True, blank=True
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.BooleanField")(default=True),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        auto_now_add=True, blank=True
                    ),
                ),
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        unique=True, max_length=36, blank=True
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.CharField")(max_length=256),
                ),
                ("config", self.gf("django.db.models.fields.CharField")(max_length=4)),
                ("script", self.gf("django.db.models.fields.TextField")()),
                (
                    "script_type",
                    self.gf("django.db.models.fields.CharField")(max_length=16),
                ),
                (
                    "tool",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.IDTool"], to_field="uuid", null=True, blank=True
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["IDCommand"])

        # Adding model 'FormatGroup'
        db.create_table(
            "fpr_formatgroup",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        unique=True, max_length=36, blank=True
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.CharField")(max_length=128),
                ),
                (
                    "slug",
                    self.gf("autoslug.fields.AutoSlugField")(
                        unique_with=(), max_length=50, populate_from="description"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["FormatGroup"])

        # Adding model 'Format'
        db.create_table(
            "fpr_format",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        unique=True, max_length=36, blank=True
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.CharField")(max_length=128),
                ),
                (
                    "group",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.FormatGroup"], to_field="uuid", null=True
                    ),
                ),
                (
                    "slug",
                    self.gf("autoslug.fields.AutoSlugField")(
                        unique_with=(), max_length=50, populate_from="description"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["Format"])

        # Adding model 'FPCommand'
        db.create_table(
            "fpr_fpcommand",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "replaces",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.FPCommand"], to_field="uuid", null=True, blank=True
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.BooleanField")(default=True),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        auto_now_add=True, blank=True
                    ),
                ),
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        unique=True, max_length=36, blank=True
                    ),
                ),
                (
                    "tool",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.FPTool"], to_field="uuid", null=True
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.CharField")(max_length=256),
                ),
                ("command", self.gf("django.db.models.fields.TextField")()),
                (
                    "script_type",
                    self.gf("django.db.models.fields.CharField")(max_length=16),
                ),
                (
                    "output_location",
                    self.gf("django.db.models.fields.TextField")(null=True, blank=True),
                ),
                (
                    "output_format",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["fpr.FormatVersion"],
                        to_field="uuid",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "command_usage",
                    self.gf("django.db.models.fields.CharField")(max_length=16),
                ),
                (
                    "verification_command",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        blank=True,
                        related_name="+",
                        to_field="uuid",
                        null=True,
                        to=orm["fpr.FPCommand"],
                    ),
                ),
                (
                    "event_detail_command",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        blank=True,
                        related_name="+",
                        to_field="uuid",
                        null=True,
                        to=orm["fpr.FPCommand"],
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["FPCommand"])

        # Adding field 'FileID.format'
        db.add_column(
            "FileID",
            "format",
            self.gf("django.db.models.fields.related.ForeignKey")(
                to=orm["fpr.FormatVersion"], to_field="uuid", null=True
            ),
            keep_default=False,
        )

        # Changing field 'FileIDsBySingleID.replaces'
        db.alter_column(
            "FileIDsBySingleID",
            "replaces",
            self.gf("django.db.models.fields.CharField")(
                max_length=36, null=True, db_column="replaces"
            ),
        )

        # Changing field 'CommandClassification.replaces'
        db.alter_column(
            "CommandClassification",
            "replaces",
            self.gf("django.db.models.fields.CharField")(
                max_length=36, null=True, db_column="replaces"
            ),
        )

        # Changing field 'FileIDType.replaces'
        db.alter_column(
            "FileIDType",
            "replaces",
            self.gf("django.db.models.fields.CharField")(
                max_length=36, null=True, db_column="replaces"
            ),
        )

        # Changing field 'CommandType.replaces'
        db.alter_column(
            "CommandType",
            "replaces",
            self.gf("django.db.models.fields.CharField")(
                max_length=36, null=True, db_column="replaces"
            ),
        )

    def backwards(self, orm):
        # Deleting model 'FPRule'
        db.delete_table("fpr_fprule")

        # Deleting model 'FPTool'
        db.delete_table("fpr_fptool")

        # Deleting model 'FormatVersion'
        db.delete_table("fpr_formatversion")

        # Deleting model 'IDRule'
        db.delete_table("fpr_idrule")

        # Deleting model 'IDTool'
        db.delete_table("fpr_idtool")

        # Deleting model 'IDCommand'
        db.delete_table("fpr_idcommand")

        # Deleting model 'FormatGroup'
        db.delete_table("fpr_formatgroup")

        # Deleting model 'Format'
        db.delete_table("fpr_format")

        # Deleting model 'FPCommand'
        db.delete_table("fpr_fpcommand")

        # Deleting field 'FileID.format'
        db.delete_column("FileID", "format_id")

        # Changing field 'FileIDsBySingleID.replaces'
        db.alter_column(
            "FileIDsBySingleID",
            "replaces",
            self.gf("django.db.models.fields.CharField")(
                max_length=50, null=True, db_column="replaces"
            ),
        )

        # Changing field 'CommandClassification.replaces'
        db.alter_column(
            "CommandClassification",
            "replaces",
            self.gf("django.db.models.fields.CharField")(
                max_length=50, null=True, db_column="replaces"
            ),
        )

        # Changing field 'FileIDType.replaces'
        db.alter_column(
            "FileIDType",
            "replaces",
            self.gf("django.db.models.fields.CharField")(
                max_length=50, null=True, db_column="replaces"
            ),
        )

        # Changing field 'CommandType.replaces'
        db.alter_column(
            "CommandType",
            "replaces",
            self.gf("django.db.models.fields.CharField")(
                max_length=50, null=True, db_column="replaces"
            ),
        )

    models: Dict[str, Any] = {
        "fpr.agent": {
            "Meta": {"object_name": "Agent", "db_table": "u'Agent'"},
            "agentIdentifierType": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "agentIdentifierValue": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "agentName": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "agentType": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "clientIP": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "primary_key": "True", "db_column": "'uuid'"},
            ),
        },
        "fpr.command": {
            "Meta": {"object_name": "Command", "db_table": "u'Command'"},
            "command": (
                "django.db.models.fields.TextField",
                [],
                {"db_column": "'command'"},
            ),
            "commandType": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36"},
            ),
            "commandUsage": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "15"},
            ),
            "description": (
                "django.db.models.fields.TextField",
                [],
                {"db_column": "'description'"},
            ),
            "enabled": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "1", "null": "True", "db_column": "'enabled'"},
            ),
            "eventDetailCommand": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True"},
            ),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"null": "True", "db_column": "'lastModified'"},
            ),
            "outputFileFormat": (
                "django.db.models.fields.TextField",
                [],
                {"null": "True", "db_column": "'outputFileFormat'"},
            ),
            "outputLocation": (
                "django.db.models.fields.TextField",
                [],
                {"null": "True", "db_column": "'outputLocation'"},
            ),
            "replaces": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True", "db_column": "'replaces'"},
            ),
            "supportedBy": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True", "db_column": "'supportedBy'"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "primary_key": "True", "db_column": "'pk'"},
            ),
            "verificationCommand": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True"},
            ),
        },
        "fpr.commandclassification": {
            "Meta": {
                "object_name": "CommandClassification",
                "db_table": "u'CommandClassification'",
            },
            "classification": (
                "django.db.models.fields.TextField",
                [],
                {"null": "True", "db_column": "'classification'"},
            ),
            "enabled": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "1", "null": "True", "db_column": "'enabled'"},
            ),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"db_column": "'lastModified'"},
            ),
            "replaces": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True", "db_column": "'replaces'"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "primary_key": "True", "db_column": "'pk'"},
            ),
        },
        "fpr.commandrelationship": {
            "Meta": {
                "object_name": "CommandRelationship",
                "db_table": "u'CommandRelationship'",
            },
            "command": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True"},
            ),
            "commandClassification": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36"},
            ),
            "enabled": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "1", "null": "True", "db_column": "'enabled'"},
            ),
            "fileID": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True"},
            ),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"db_column": "'lastModified'"},
            ),
            "replaces": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "primary_key": "True", "db_column": "'pk'"},
            ),
        },
        "fpr.commandssupportedby": {
            "Meta": {
                "object_name": "CommandsSupportedBy",
                "db_table": "u'CommandsSupportedBy'",
            },
            "description": (
                "django.db.models.fields.TextField",
                [],
                {"null": "True", "db_column": "'description'"},
            ),
            "enabled": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "1", "null": "True", "db_column": "'enabled'"},
            ),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"db_column": "'lastModified'"},
            ),
            "replaces": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True", "db_column": "'replaces'"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "primary_key": "True", "db_column": "'pk'"},
            ),
        },
        "fpr.commandtype": {
            "Meta": {"object_name": "CommandType", "db_table": "u'CommandType'"},
            "enabled": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "1", "null": "True", "db_column": "'enabled'"},
            ),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"db_column": "'lastModified'"},
            ),
            "replaces": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True", "db_column": "'replaces'"},
            ),
            "type": ("django.db.models.fields.TextField", [], {"db_column": "'type'"}),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "primary_key": "True", "db_column": "'pk'"},
            ),
        },
        "fpr.fileid": {
            "Meta": {"object_name": "FileID", "db_table": "u'FileID'"},
            "description": (
                "django.db.models.fields.TextField",
                [],
                {"db_column": "'description'"},
            ),
            "enabled": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "1", "null": "True", "db_column": "'enabled'"},
            ),
            "fileidtype": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True", "db_column": "'fileidtype_id'"},
            ),
            "format": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "to": "orm['fpr.FormatVersion']",
                    "to_field": "'uuid'",
                    "null": "True",
                },
            ),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"db_column": "'lastModified'"},
            ),
            "replaces": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True", "db_column": "'replaces'"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "primary_key": "True", "db_column": "'pk'"},
            ),
            "validaccessformat": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0", "null": "True", "db_column": "'validAccessFormat'"},
            ),
            "validpreservationformat": (
                "django.db.models.fields.IntegerField",
                [],
                {
                    "default": "0",
                    "null": "True",
                    "db_column": "'validPreservationFormat'",
                },
            ),
        },
        "fpr.fileidsbysingleid": {
            "Meta": {
                "object_name": "FileIDsBySingleID",
                "db_table": "u'FileIDsBySingleID'",
            },
            "enabled": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "1", "null": "True", "db_column": "'enabled'"},
            ),
            "fileID": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True"},
            ),
            "id": ("django.db.models.fields.TextField", [], {"db_column": "'id'"}),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"db_column": "'lastModified'"},
            ),
            "replaces": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True", "db_column": "'replaces'"},
            ),
            "tool": ("django.db.models.fields.TextField", [], {"db_column": "'tool'"}),
            "toolVersion": (
                "django.db.models.fields.TextField",
                [],
                {"null": "True", "db_column": "'toolVersion'"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "primary_key": "True", "db_column": "'pk'"},
            ),
        },
        "fpr.fileidtype": {
            "Meta": {"object_name": "FileIDType", "db_table": "u'FileIDType'"},
            "description": (
                "django.db.models.fields.TextField",
                [],
                {"null": "True", "db_column": "'description'"},
            ),
            "enabled": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "1", "null": "True", "db_column": "'enabled'"},
            ),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"db_column": "'lastModified'"},
            ),
            "replaces": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "null": "True", "db_column": "'replaces'"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "primary_key": "True", "db_column": "'pk'"},
            ),
        },
        "fpr.format": {
            "Meta": {"ordering": "['group', 'description']", "object_name": "Format"},
            "description": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "128"},
            ),
            "group": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['fpr.FormatGroup']", "to_field": "'uuid'", "null": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "slug": (
                "autoslug.fields.AutoSlugField",
                [],
                {
                    "unique_with": "()",
                    "max_length": "50",
                    "populate_from": "'description'",
                },
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "36", "blank": "True"},
            ),
        },
        "fpr.formatgroup": {
            "Meta": {"ordering": "['description']", "object_name": "FormatGroup"},
            "description": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "128"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "slug": (
                "autoslug.fields.AutoSlugField",
                [],
                {
                    "unique_with": "()",
                    "max_length": "50",
                    "populate_from": "'description'",
                },
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "36", "blank": "True"},
            ),
        },
        "fpr.formatversion": {
            "Meta": {
                "ordering": "['format', 'description']",
                "object_name": "FormatVersion",
            },
            "access_format": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "description": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "128", "null": "True", "blank": "True"},
            ),
            "enabled": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "format": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "related_name": "'version_set'",
                    "to_field": "'uuid'",
                    "null": "True",
                    "to": "orm['fpr.Format']",
                },
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now_add": "True", "blank": "True"},
            ),
            "preservation_format": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "pronom_id": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "32", "null": "True", "blank": "True"},
            ),
            "replaces": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "to": "orm['fpr.FormatVersion']",
                    "to_field": "'uuid'",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "slug": (
                "autoslug.fields.AutoSlugField",
                [],
                {
                    "unique_with": "('format',)",
                    "max_length": "50",
                    "populate_from": "'description'",
                },
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "36", "blank": "True"},
            ),
            "version": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "10", "null": "True", "blank": "True"},
            ),
        },
        "fpr.fpcommand": {
            "Meta": {"ordering": "['description']", "object_name": "FPCommand"},
            "command": ("django.db.models.fields.TextField", [], {}),
            "command_usage": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "16"},
            ),
            "description": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "256"},
            ),
            "enabled": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "event_detail_command": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "blank": "True",
                    "related_name": "'+'",
                    "to_field": "'uuid'",
                    "null": "True",
                    "to": "orm['fpr.FPCommand']",
                },
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now_add": "True", "blank": "True"},
            ),
            "output_format": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "to": "orm['fpr.FormatVersion']",
                    "to_field": "'uuid'",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "output_location": (
                "django.db.models.fields.TextField",
                [],
                {"null": "True", "blank": "True"},
            ),
            "replaces": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "to": "orm['fpr.FPCommand']",
                    "to_field": "'uuid'",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "script_type": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "16"},
            ),
            "tool": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['fpr.FPTool']", "to_field": "'uuid'", "null": "True"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "36", "blank": "True"},
            ),
            "verification_command": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "blank": "True",
                    "related_name": "'+'",
                    "to_field": "'uuid'",
                    "null": "True",
                    "to": "orm['fpr.FPCommand']",
                },
            ),
        },
        "fpr.fprule": {
            "Meta": {"object_name": "FPRule"},
            "command": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['fpr.FPCommand']", "to_field": "'uuid'"},
            ),
            "count_attempts": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "count_not_okay": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "count_okay": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "enabled": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "format": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['fpr.FormatVersion']", "to_field": "'uuid'"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now_add": "True", "blank": "True"},
            ),
            "purpose": ("django.db.models.fields.CharField", [], {"max_length": "32"}),
            "replaces": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "to": "orm['fpr.FPRule']",
                    "to_field": "'uuid'",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "36", "blank": "True"},
            ),
        },
        "fpr.fptool": {
            "Meta": {"object_name": "FPTool"},
            "description": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "256"},
            ),
            "enabled": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "slug": (
                "autoslug.fields.AutoSlugField",
                [],
                {"unique_with": "()", "max_length": "50", "populate_from": "'_slug'"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "36", "blank": "True"},
            ),
            "version": ("django.db.models.fields.CharField", [], {"max_length": "64"}),
        },
        "fpr.idcommand": {
            "Meta": {"ordering": "['description']", "object_name": "IDCommand"},
            "config": ("django.db.models.fields.CharField", [], {"max_length": "4"}),
            "description": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "256"},
            ),
            "enabled": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now_add": "True", "blank": "True"},
            ),
            "replaces": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "to": "orm['fpr.IDCommand']",
                    "to_field": "'uuid'",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "script": ("django.db.models.fields.TextField", [], {}),
            "script_type": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "16"},
            ),
            "tool": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "to": "orm['fpr.IDTool']",
                    "to_field": "'uuid'",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "36", "blank": "True"},
            ),
        },
        "fpr.idrule": {
            "Meta": {"object_name": "IDRule"},
            "command": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['fpr.IDCommand']", "to_field": "'uuid'"},
            ),
            "command_output": ("django.db.models.fields.TextField", [], {}),
            "enabled": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "format": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['fpr.FormatVersion']", "to_field": "'uuid'"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "lastmodified": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now_add": "True", "blank": "True"},
            ),
            "replaces": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "to": "orm['fpr.IDRule']",
                    "to_field": "'uuid'",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "36", "blank": "True"},
            ),
        },
        "fpr.idtool": {
            "Meta": {"object_name": "IDTool"},
            "description": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "256"},
            ),
            "enabled": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "slug": (
                "autoslug.fields.AutoSlugField",
                [],
                {"unique_with": "()", "max_length": "50", "populate_from": "'_slug'"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "36", "blank": "True"},
            ),
            "version": ("django.db.models.fields.CharField", [], {"max_length": "64"}),
        },
    }

    complete_apps = ["fpr"]

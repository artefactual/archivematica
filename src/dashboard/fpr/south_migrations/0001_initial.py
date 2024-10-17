from typing import Any
from typing import Dict

from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'Agent'
        db.create_table(
            "Agent",
            (
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, primary_key=True, db_column="uuid"
                    ),
                ),
                (
                    "agentIdentifierType",
                    self.gf("django.db.models.fields.CharField")(max_length=100),
                ),
                (
                    "agentIdentifierValue",
                    self.gf("django.db.models.fields.CharField")(max_length=100),
                ),
                (
                    "agentName",
                    self.gf("django.db.models.fields.CharField")(max_length=100),
                ),
                (
                    "agentType",
                    self.gf("django.db.models.fields.CharField")(max_length=100),
                ),
                (
                    "clientIP",
                    self.gf("django.db.models.fields.CharField")(max_length=100),
                ),
            ),
        )
        db.send_create_signal("fpr", ["Agent"])

        # Adding model 'CommandType'
        db.create_table(
            "CommandType",
            (
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, primary_key=True, db_column="pk"
                    ),
                ),
                (
                    "replaces",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=50, null=True, db_column="replaces"
                    ),
                ),
                (
                    "type",
                    self.gf("django.db.models.fields.TextField")(db_column="type"),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        db_column="lastModified"
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.IntegerField")(
                        default=1, null=True, db_column="enabled"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["CommandType"])

        # Adding model 'Command'
        db.create_table(
            "Command",
            (
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, primary_key=True, db_column="pk"
                    ),
                ),
                (
                    "commandUsage",
                    self.gf("django.db.models.fields.CharField")(max_length=15),
                ),
                (
                    "commandType",
                    self.gf("django.db.models.fields.CharField")(max_length=36),
                ),
                (
                    "verificationCommand",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True
                    ),
                ),
                (
                    "eventDetailCommand",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True
                    ),
                ),
                (
                    "supportedBy",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True, db_column="supportedBy"
                    ),
                ),
                (
                    "command",
                    self.gf("django.db.models.fields.TextField")(db_column="command"),
                ),
                (
                    "outputLocation",
                    self.gf("django.db.models.fields.TextField")(
                        null=True, db_column="outputLocation"
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.TextField")(
                        db_column="description"
                    ),
                ),
                (
                    "outputFileFormat",
                    self.gf("django.db.models.fields.TextField")(
                        null=True, db_column="outputFileFormat"
                    ),
                ),
                (
                    "replaces",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True, db_column="replaces"
                    ),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        null=True, db_column="lastModified"
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.IntegerField")(
                        default=1, null=True, db_column="enabled"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["Command"])

        # Adding model 'CommandsSupportedBy'
        db.create_table(
            "CommandsSupportedBy",
            (
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, primary_key=True, db_column="pk"
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.TextField")(
                        null=True, db_column="description"
                    ),
                ),
                (
                    "replaces",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True, db_column="replaces"
                    ),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        db_column="lastModified"
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.IntegerField")(
                        default=1, null=True, db_column="enabled"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["CommandsSupportedBy"])

        # Adding model 'FileIDType'
        db.create_table(
            "FileIDType",
            (
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, primary_key=True, db_column="pk"
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.TextField")(
                        null=True, db_column="description"
                    ),
                ),
                (
                    "replaces",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=50, null=True, db_column="replaces"
                    ),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        db_column="lastModified"
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.IntegerField")(
                        default=1, null=True, db_column="enabled"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["FileIDType"])

        # Adding model 'FileID'
        db.create_table(
            "FileID",
            (
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, primary_key=True, db_column="pk"
                    ),
                ),
                (
                    "description",
                    self.gf("django.db.models.fields.TextField")(
                        db_column="description"
                    ),
                ),
                (
                    "validpreservationformat",
                    self.gf("django.db.models.fields.IntegerField")(
                        default=0, null=True, db_column="validPreservationFormat"
                    ),
                ),
                (
                    "validaccessformat",
                    self.gf("django.db.models.fields.IntegerField")(
                        default=0, null=True, db_column="validAccessFormat"
                    ),
                ),
                (
                    "fileidtype",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True, db_column="fileidtype_id"
                    ),
                ),
                (
                    "replaces",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True, db_column="replaces"
                    ),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        db_column="lastModified"
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.IntegerField")(
                        default=1, null=True, db_column="enabled"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["FileID"])

        # Adding model 'CommandClassification'
        db.create_table(
            "CommandClassification",
            (
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, primary_key=True, db_column="pk"
                    ),
                ),
                (
                    "classification",
                    self.gf("django.db.models.fields.TextField")(
                        null=True, db_column="classification"
                    ),
                ),
                (
                    "replaces",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=50, null=True, db_column="replaces"
                    ),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        db_column="lastModified"
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.IntegerField")(
                        default=1, null=True, db_column="enabled"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["CommandClassification"])

        # Adding model 'CommandRelationship'
        db.create_table(
            "CommandRelationship",
            (
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, primary_key=True, db_column="pk"
                    ),
                ),
                (
                    "commandClassification",
                    self.gf("django.db.models.fields.CharField")(max_length=36),
                ),
                (
                    "command",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True
                    ),
                ),
                (
                    "fileID",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True
                    ),
                ),
                (
                    "replaces",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True
                    ),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        db_column="lastModified"
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.IntegerField")(
                        default=1, null=True, db_column="enabled"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["CommandRelationship"])

        # Adding model 'FileIDsBySingleID'
        db.create_table(
            "FileIDsBySingleID",
            (
                (
                    "uuid",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, primary_key=True, db_column="pk"
                    ),
                ),
                (
                    "fileID",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=36, null=True
                    ),
                ),
                ("id", self.gf("django.db.models.fields.TextField")(db_column="id")),
                (
                    "tool",
                    self.gf("django.db.models.fields.TextField")(db_column="tool"),
                ),
                (
                    "toolVersion",
                    self.gf("django.db.models.fields.TextField")(
                        null=True, db_column="toolVersion"
                    ),
                ),
                (
                    "replaces",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=50, null=True, db_column="replaces"
                    ),
                ),
                (
                    "lastmodified",
                    self.gf("django.db.models.fields.DateTimeField")(
                        db_column="lastModified"
                    ),
                ),
                (
                    "enabled",
                    self.gf("django.db.models.fields.IntegerField")(
                        default=1, null=True, db_column="enabled"
                    ),
                ),
            ),
        )
        db.send_create_signal("fpr", ["FileIDsBySingleID"])

    def backwards(self, orm):
        # Deleting model 'Agent'
        db.delete_table("Agent")

        # Deleting model 'CommandType'
        db.delete_table("CommandType")

        # Deleting model 'Command'
        db.delete_table("Command")

        # Deleting model 'CommandsSupportedBy'
        db.delete_table("CommandsSupportedBy")

        # Deleting model 'FileIDType'
        db.delete_table("FileIDType")

        # Deleting model 'FileID'
        db.delete_table("FileID")

        # Deleting model 'CommandClassification'
        db.delete_table("CommandClassification")

        # Deleting model 'CommandRelationship'
        db.delete_table("CommandRelationship")

        # Deleting model 'FileIDsBySingleID'
        db.delete_table("FileIDsBySingleID")

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
                {"max_length": "50", "null": "True", "db_column": "'replaces'"},
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
                {"max_length": "50", "null": "True", "db_column": "'replaces'"},
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
                {"max_length": "50", "null": "True", "db_column": "'replaces'"},
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
                {"max_length": "50", "null": "True", "db_column": "'replaces'"},
            ),
            "uuid": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "36", "primary_key": "True", "db_column": "'pk'"},
            ),
        },
    }

    complete_apps = ["fpr"]

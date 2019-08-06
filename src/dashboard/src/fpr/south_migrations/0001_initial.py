# -*- coding: utf-8 -*-
from __future__ import absolute_import

from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'Agent'
        db.create_table(
            u"Agent",
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
        db.send_create_signal(u"fpr", ["Agent"])

        # Adding model 'CommandType'
        db.create_table(
            u"CommandType",
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
        db.send_create_signal(u"fpr", ["CommandType"])

        # Adding model 'Command'
        db.create_table(
            u"Command",
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
        db.send_create_signal(u"fpr", ["Command"])

        # Adding model 'CommandsSupportedBy'
        db.create_table(
            u"CommandsSupportedBy",
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
        db.send_create_signal(u"fpr", ["CommandsSupportedBy"])

        # Adding model 'FileIDType'
        db.create_table(
            u"FileIDType",
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
        db.send_create_signal(u"fpr", ["FileIDType"])

        # Adding model 'FileID'
        db.create_table(
            u"FileID",
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
        db.send_create_signal(u"fpr", ["FileID"])

        # Adding model 'CommandClassification'
        db.create_table(
            u"CommandClassification",
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
        db.send_create_signal(u"fpr", ["CommandClassification"])

        # Adding model 'CommandRelationship'
        db.create_table(
            u"CommandRelationship",
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
        db.send_create_signal(u"fpr", ["CommandRelationship"])

        # Adding model 'FileIDsBySingleID'
        db.create_table(
            u"FileIDsBySingleID",
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
        db.send_create_signal(u"fpr", ["FileIDsBySingleID"])

    def backwards(self, orm):
        # Deleting model 'Agent'
        db.delete_table(u"Agent")

        # Deleting model 'CommandType'
        db.delete_table(u"CommandType")

        # Deleting model 'Command'
        db.delete_table(u"Command")

        # Deleting model 'CommandsSupportedBy'
        db.delete_table(u"CommandsSupportedBy")

        # Deleting model 'FileIDType'
        db.delete_table(u"FileIDType")

        # Deleting model 'FileID'
        db.delete_table(u"FileID")

        # Deleting model 'CommandClassification'
        db.delete_table(u"CommandClassification")

        # Deleting model 'CommandRelationship'
        db.delete_table(u"CommandRelationship")

        # Deleting model 'FileIDsBySingleID'
        db.delete_table(u"FileIDsBySingleID")

    models = {
        u"fpr.agent": {
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
        u"fpr.command": {
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
        u"fpr.commandclassification": {
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
        u"fpr.commandrelationship": {
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
        u"fpr.commandssupportedby": {
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
        u"fpr.commandtype": {
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
        u"fpr.fileid": {
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
        u"fpr.fileidsbysingleid": {
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
        u"fpr.fileidtype": {
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

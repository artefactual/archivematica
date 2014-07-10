#!/usr/bin/python2 -OO

import os
import sys

from getFromRestAPI import each_record, FPRConnectionError

from annoying.functions import get_object_or_None

# Set up Django settings
sys.path.append('/usr/share/archivematica/dashboard')
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'
import django.db
from django.conf import settings as django_settings

from fpr import models
import main.models


class FPRClient(object):
    """FPR Client provides methods to download data from FPR Server"""

    def __init__(self, fprserver='https://fpr.archivematica.org/fpr/api/v2/'):
        self.fprserver = fprserver
        self.maxLastUpdate = None
        self.maxLastUpdateUUID = None
        self.count_rules_updated = 0
        self.retry = {}

    def getMaxLastUpdate(self):
        (last_updated, _) = main.models.UnitVariable.objects.get_or_create(
                unittype='FPR', unituuid='Client', variable='maxLastUpdate',
                defaults={'variablevalue': "2000-01-01T00:00:00"})
        self.maxLastUpdate = last_updated.variablevalue
        self.maxLastUpdateUUID = last_updated.id

    def setMaxLastUpdate(self):
        main.models.UnitVariable.objects.filter(id=self.maxLastUpdateUUID).update(variablevalue=self.maxLastUpdate)

    def addResource(self, fields, model):
        """ Add an object with data `fields` to the model `model`.  Adds to
        retry dictionary if it fails to be inserted because of an integrity
        error so it can be retried. """
        # Update lastmodified if exists
        if 'lastmodified' in fields and fields['lastmodified'] > self.maxLastUpdate:
            self.maxLastUpdate = fields['lastmodified']

        # If an fields with this UUID exists, update enabled
        obj = get_object_or_None(model, uuid=fields['uuid'])
        if obj:
            print 'Object already in DB:', get_object_or_None(model, uuid=fields['uuid'])
            if not hasattr(model, 'replaces') and hasattr(model, 'enabled'):
                obj.enabled = fields['enabled']
                obj.save()
            return
        # Otherwise, new fields, need to add to database

        # TastyPie doesn't like fields named format, so they're all fmt
        if 'fmt' in fields:
            fields['format'] = fields.pop('fmt')

        # Only keep fields that are in the model
        valid_fields = {k: v for k, v in fields.iteritems()
                        if k in model._meta.get_all_field_names()}

        # Convert foreign keys from URIs to just UUIDs
        for field, value in valid_fields.iteritems():
            if isinstance(value, basestring) and value.startswith('/fpr/api/'):
                # Parse out UUID.  value.split gives
                # ['', 'fpr', 'api', '<version>', '<resource>', '<uuid>', '']
                uuid = value.split('/')[-2]
                del valid_fields[field]
                valid_fields[field + u"_id"] = uuid
        # Insert FormatGroup for Formats if not exist
        if model == models.Format:
            if not get_object_or_None(
                    models.FormatGroup,
                    uuid=fields['group']['uuid']):
                models.FormatGroup.objects.create(**fields['group'])
            valid_fields['group_id'] = fields['group']['uuid']
            del valid_fields['group']

        # Create
        try:
            obj = model.objects.create(**valid_fields)
        except django.db.utils.IntegrityError:
            self.retry[model].append(valid_fields)
            print 'Integrity error failed; will retry later'
            return
        self.count_rules_updated += 1

        # Update enabled on self and replaces
        if hasattr(model, 'replaces'):
            if obj.replaces is None:
                # First rule in a chain is always enabled
                obj.enabled = True
            elif obj.replaces.enabled:
                # If replacing an active rule, disable it and set self active
                obj.replaces.enabled = False
                obj.replaces.save()
                obj.enabled = True
            else:  # obj.replaces is disabled
                obj.enabled = False
            obj.save()

            # Check for a manual replacement
            # Look for another rule that has the same replaces value
            # Insert obj as that rule's parent
            if obj.replaces is not None:
                existing_rules = model.objects.filter(replaces=obj.replaces).exclude(uuid=valid_fields['uuid'])
                if len(existing_rules) >= 1:
                    existing_rules[0].replaces = obj
                    existing_rules[0].save()

        print 'Added:', obj

    def autoUpdateFPR(self):
        self.getMaxLastUpdate()
        maxLastUpdateAtStart = self.maxLastUpdate
        print 'maxLastUpdateAtStart', maxLastUpdateAtStart
        resources = [
            (models.Format, 'format'),
            (models.FormatVersion, 'format-version'),
            (models.IDTool, 'id-tool'),
            (models.IDCommand, 'id-command'),
            (models.IDRule, 'id-rule'),
            (models.FPTool, 'fp-tool'),
            (models.FPCommand, 'fp-command'),
            (models.FPRule, 'fp-rule'),
        ]

        for table, resource in resources:
            print 'resource:', resource
            try:
                table._meta.get_field_by_name('lastmodified')
            except django.db.models.fields.FieldDoesNotExist:
                start_at = None
            else:
                start_at = maxLastUpdateAtStart

            kwargs = {
                "url": self.fprserver,
                "verify": django_settings.FPR_VERIFY_CERT
            }
            if start_at:
                kwargs["start_at"] = start_at

            self.retry[table] = []
            for entry in each_record(resource, **kwargs):
                self.addResource(entry, table)
            print 'Retrying entries that fail because of foreign keys'
            for entry in self.retry[table]:
                print "Retrying:", entry
                # Create
                obj = table.objects.create(**entry)
                self.count_rules_updated += 1
                # Update enabled on self and replaces
                if hasattr(table, 'replaces') and obj.replaces:
                    if obj.replaces.enabled:
                        obj.replaces.enabled = False
                        obj.replaces.save()
                    else:  # obj.replaces is disabled
                        obj.enabled = False
                        obj.save()
                print 'Added:', obj

        print 'maxLastUpdate at end', self.maxLastUpdate
        if self.maxLastUpdate != maxLastUpdateAtStart:
            self.setMaxLastUpdate()

    def getUpdates(self):
        status = 'failed'
        exception = None
        try:
            self.autoUpdateFPR()
        except django.db.utils.IntegrityError as e:
            response = "Error updating FPR"
            exception = e
        except FPRConnectionError as e:
            response = "Error connecting to FPR"
            exception = e
        except Exception as e:
            response = 'Error updating FPR'
            exception = e
            raise
        else:
            status = 'success'
            if self.count_rules_updated == 0:
                response = "No updates at this time"
            elif self.count_rules_updated > 0:
                response = "Successfully updated FPR: {} changes".format(self.count_rules_updated)
        return (status, response, exception)


if __name__ == '__main__':
    ret = FPRClient().getUpdates()
    print ret

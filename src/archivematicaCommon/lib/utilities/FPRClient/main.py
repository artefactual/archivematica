#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage FPRClient
# @author Joseph Perry <joseph@artefactual.com>
import os
import sys
import uuid

import getFromRestAPI

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface

# Set up Django settings
path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'
import django.db

from annoying.functions import get_object_or_None

from fpr import models

databaseInterface.printSQL = False

class FPRClient(object):
    """FPR Client provides methods to download data from FPR Server"""

    def __init__(self, fprserver='https://fpr.archivematica.org/fpr/api/v2/'):
        self.fprserver = fprserver
        self.maxLastUpdate = None
        self.maxLastUpdateUUID = None
        self.count_rules_updated = 0
        self.retry = {}

    def getMaxLastUpdate(self):
        sql = """SELECT pk, variableValue FROM UnitVariables WHERE unitType = 'FPR' AND unitUUID = 'Client' AND variable = 'maxLastUpdate' """
        rows = databaseInterface.queryAllSQL(sql)
        if rows:
            self.maxLastUpdateUUID, self.maxLastUpdate = rows[0]
        else:
            self.maxLastUpdate = "2000-01-01T00:00:00"
            self.maxLastUpdateUUID = str(uuid.uuid4())
    
    def setMaxLastUpdate(self):
        sql = """INSERT INTO UnitVariables(pk, variableValue, variable, unitType, unitUUID) VALUES ('{pk}', '{variableValue}', 'maxLastUpdate', 'FPR', 'Client') ON DUPLICATE KEY UPDATE variableValue='{variableValue}';""".format(
                pk=self.maxLastUpdateUUID,
                variableValue=self.maxLastUpdate
            )
        databaseInterface.runSQL(sql)

    def addResource(self, fields, table):
        """ Add an object with data `fields` to the model `table`.  Adds to
        retry dictionary if it fails to be inserted because of an integrity
        error so it can be retried. """
        # Update lastmodified if exists
        if 'lastmodified' in fields and fields['lastmodified'] > self.maxLastUpdate:
            self.maxLastUpdate = fields['lastmodified']

        # If an fields with this UUID exists, update enabled
        obj = get_object_or_None(table, uuid=fields['uuid'])
        if obj:
            print 'Object already in DB:', get_object_or_None(table, uuid=fields['uuid'])
            if not hasattr(table, 'replaces') and hasattr(table, 'enabled'):
                obj.enabled = fields['enabled']
                obj.save()
            return
        # Otherwise, new fields, need to add to table
        # print 'fields', fields
        # TastyPie doesn't like fields named format, so they're all fmt
        if 'fmt' in fields:
            fields['format'] = fields.pop('fmt')

        # Only keep fields that are in the model
        valid_fields = dict(
            [ (k, v) for k, v in fields.iteritems()
                if k in table._meta.get_all_field_names()
            ])

        # Convert foreign keys from URIs to just UUIDs
        for field, value in valid_fields.iteritems():
            if isinstance(value, basestring) and value.startswith('/fpr/api/'):
                # Parse out UUID.  value.split gives
                # ['', 'fpr', 'api', '<version>', '<resource>', '<uuid>', '']
                uuid = value.split('/')[-2]
                del valid_fields[field]
                valid_fields[field+u"_id"] = uuid
        # Insert FormatGroup for Formats if not exist
        if table == models.Format:
            if not get_object_or_None(
                    models.FormatGroup,
                    uuid=fields['group']['uuid']):
                models.FormatGroup.objects.create(**fields['group'])
            valid_fields['group_id'] = fields['group']['uuid']
            del valid_fields['group']

        # Create
        try:
            obj = table.objects.create(**valid_fields)
        except django.db.utils.IntegrityError:
            self.retry[table].append(valid_fields)
            print 'Integrity error failed; will retry later'
            return
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

    
    def autoUpdateFPR(self):
        self.getMaxLastUpdate()
        maxLastUpdateAtStart = self.maxLastUpdate
        print 'maxLastUpdateAtStart', maxLastUpdateAtStart
        databaseInterface.runSQL("SET foreign_key_checks = 0;")
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

        for r in resources:
            table, resource = r
            print 'resource:', resource
            params = {
                "format": "json",
                "limit": "0"
            }
            try:
                table._meta.get_field_by_name('lastmodified')
            except django.db.models.fields.FieldDoesNotExist:
                pass
            else:
                params["order_by"] = "lastmodified",
                params['lastmodified__gte'] = maxLastUpdateAtStart
            # TODO handle pagination of results for FPRServer
            #  Should handle pagination here, rather than creating big array
            #  of entries - possibly use generator function?
            entries = getFromRestAPI.getFromRestAPI(self.fprserver, resource, params, verbose=False, auth=None)

            self.retry[table] = []
            for entry in entries:
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

        databaseInterface.runSQL("SET foreign_key_checks = 1;")
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
        except getFromRestAPI.FPRConnectionError as e:
            response = "Error connecting to FPR"
            exception = e
        except Exception as e:
            response = 'Error updating FPR'
            exception = e
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

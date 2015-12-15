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
# @subpackage archivematicaClientScript
# @author Mike Cantelon <mike@artefactual.com>

import argparse

import csv
import ConfigParser
import json
import os
import shutil
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface

clientConfigFilePath = '/etc/archivematica/MCPClient/clientConfig.conf'
config = ConfigParser.SafeConfigParser()
config.read(clientConfigFilePath)

SHARED_DIR = config.get('MCPClient', 'sharedDirectoryMounted')

def copyToNetX(sip_uuid):
    get_transfer_uuid(sip_uuid)

    print "Trying to get DIP path for SIP UUID " + sip_uuid

    dip_path = get_dip_path(sip_uuid)
    print 'DIP path is: ' + dip_path

    dip_uuid = dip_path[-36:]
    print 'DIP UUID is: ' + dip_uuid

    transfer_uuid = get_transfer_uuid(sip_uuid)
    object_id = get_accession_number(transfer_uuid)
    if object_id is None:
        print 'No object ID found.'
        exit(1)

    component_id = get_component_id(transfer_uuid)
    if component_id is None:
        print 'No component ID found.'
        component_id = ''

    netx_path_csv = get_netx_path('csv')
    print 'NetX CSV path is: ' + netx_path_csv

    netx_path_objects = get_netx_path('objects')
    print 'NetX object path is: ' + netx_path_objects

    # cycle through objects, copying to destination path and and writing CSV
    # file of files/attributes
    csv_filepath = os.path.join(netx_path_csv, 'metadata.csv')
    needs_header = False if os.path.isfile(csv_filepath) else True

    with open(csv_filepath, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)

        if needs_header:
            # write header CSV row
            writer.writerow(['filename', 'ObjectID', 'Component Number', 'dip_uuid'])

        objects_path = os.path.join(dip_path, 'objects')

        for object in os.listdir(objects_path):
            # copy file to NetX directory
            shutil.copyfile(
                os.path.join(objects_path, object),
                os.path.join(netx_path_objects, object)
            )

            # write CSV row
            writer.writerow([object, object_id, component_id, sip_uuid])

def get_dip_path(sip_uuid):
    sql = """SELECT directory FROM Jobs WHERE jobType='Upload DIP' AND SIPUUID='%s'""" % (sip_uuid)
    rows = databaseInterface.queryAllSQL(sql)

    if len(rows) < 1:
        print >>sys.stderr, "Job directory not found in database."
        exit(1)
    else:
        directory = rows[0][0]
        return directory.rstrip('/').replace('%sharedPath%', SHARED_DIR)

def get_netx_path(path_type):
    sql = """SELECT value FROM DashboardSettings WHERE name='netx_dest_path_%s'""" % (path_type)
    rows = databaseInterface.queryAllSQL(sql)

    if len(rows) != 1:
        print >>sys.stderr, "NetX %s path setting not found in database." % (path_type)
        exit(1)
    else:
        return rows[0][0]

def get_transfer_uuid(sip_uuid):
    sql = """SELECT transferUUID FROM Files WHERE sipUUID =  '%s' AND transferUUID IS NOT NULL LIMIT 1""" % (sip_uuid)
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    sqlLock.release()
    if row is None:
        return None
    return row[0]

def get_accession_number(transfer_uuid):
    sql = """SELECT accessionID FROM Transfers WHERE transferUUID =  '%s'""" % (transfer_uuid)
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    sqlLock.release()
    if row is None:
        return None
    return row[0]

def get_component_id(transfer_uuid):
    # Attempt to get component ID from database
    sql = """SELECT identifier FROM Dublincore WHERE metadataAppliesToidentifier = '%s'""" % (transfer_uuid)
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    sqlLock.release()
    if row is None or row[0] == '':
        # Get transfer location
        sql = """SELECT currentLocation FROM Transfers WHERE transferUUID = '%s'""" % (transfer_uuid)
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        sqlLock.release()
        if row is None:
            return None

        # Attempt to get component ID from JSON file
        transfer_path = row[0].rstrip('/').replace('%sharedPath%', SHARED_DIR)
        json_file_path = os.path.join(transfer_path, 'metadata/netx.json')

        try:
            netx_config = json.load(open(json_file_path))

            print 'Component ID found in nets.json file.'
            return netx_config[0]['component.identifier'] 
        except:
            return None
    else:
        print 'Component ID found in Dublincore data.'
        return row[0]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='restructure')
    parser.add_argument('--uuid', action="store", dest='uuid', metavar='UUID', required=True, help='SIP-UUID')

    args = parser.parse_args()

    copyToNetX(args.uuid)

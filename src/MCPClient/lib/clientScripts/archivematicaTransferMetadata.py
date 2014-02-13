#!/usr/bin/python2

from __future__ import print_function
from argparse import ArgumentParser
from lxml import etree
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface

def fetch_set_uuid(sip_uuid):
    sql = """SELECT pk FROM TransferMetadataSets
    INNER JOIN Transfers ON transferMetadataSetRowUUID = pk
    WHERE transferUUID = '{}'
    """.format(sip_uuid)
    print(sql, file=sys.stderr)
    cursor, sql_lock = databaseInterface.querySQL(sql)
    results = cursor.fetchone()
    sql_lock.release()

    # Will be empty if no metadata was saved
    if not results:
        return
    else:
        set_uuid, = results

    return set_uuid

def fetch_fields_and_values(sip_uuid):
    set_uuid = fetch_set_uuid(sip_uuid)
    if set_uuid is None:
        return []

    sql = """SELECT fieldName, fieldValue FROM TransferMetadataFieldValues FV
    INNER JOIN TransferMetadataFields F ON FV.fieldUUID = F.pk
    WHERE FV.setUUID = '{}' AND fieldValue <> ''
    """.format(set_uuid)
    print(sql, file=sys.stderr)
    cursor, sql_lock = databaseInterface.querySQL(sql)

    results = cursor.fetchall()
    sql_lock.release()

    return results

def build_element(label, value, root):
    print(label, value, file=sys.stderr)
    element = etree.SubElement(root, label)
    element.text = value
    return element

if __name__ == '__main__':
    parser = ArgumentParser(description='Create a generic XML document from transfer metadata')
    parser.add_argument('-S', '--sipUUID', action='store', dest='sip_uuid')
    parser.add_argument('-x', '--xmlFile', action='store', dest='xml_file')
    opts = parser.parse_args()

    root = etree.Element('transfer_metadata')

    values = fetch_fields_and_values(opts.sip_uuid)
    elements = [build_element(label, value, root) for (label, value) in values]

    # If there is no transfer metadata, skip writing the XML
    if not elements:
        sys.exit()

    tree = etree.ElementTree(root)
    tree.write(opts.xml_file, pretty_print=True, xml_declaration=True)

    print(etree.tostring(tree))

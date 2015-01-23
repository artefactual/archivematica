#!/usr/bin/python2

from __future__ import print_function
from argparse import ArgumentParser
from lxml import etree
import sys

# dashboard
from main.models import Transfer


def fetch_set(sip_uuid):
    transfer = Transfer.objects.get(uuid=sip_uuid)
    return transfer.transfermetadatasetrow

def fetch_fields_and_values(sip_uuid):
    metadata_set = fetch_set(sip_uuid)
    if metadata_set is None:
        return []

    results = metadata_set.transfermetadatafieldvalue_set.exclude(fieldvalue='').values_list('field__fieldname', 'fieldvalue')

    return results

def build_element(label, value, root):
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

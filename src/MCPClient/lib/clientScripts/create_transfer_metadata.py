#!/usr/bin/env python
from argparse import ArgumentParser

import django
from lxml import etree

django.setup()
# dashboard
from main.models import Transfer

from client import metrics


def fetch_set(sip_uuid):
    transfer = Transfer.objects.get(uuid=sip_uuid)
    return transfer.transfermetadatasetrow


def fetch_fields_and_values(sip_uuid):
    metadata_set = fetch_set(sip_uuid)
    if metadata_set is None:
        return []

    results = metadata_set.transfermetadatafieldvalue_set.exclude(
        fieldvalue=""
    ).values_list("field__fieldname", "fieldvalue")

    return results


def build_element(label, value, root):
    element = etree.SubElement(root, label)
    element.text = value
    return element


def call(jobs):
    parser = ArgumentParser(
        description="Create a generic XML document from transfer metadata"
    )
    parser.add_argument("-S", "--sipUUID", action="store", dest="sip_uuid")
    parser.add_argument("-x", "--xmlFile", action="store", dest="xml_file")

    for job in jobs:
        with job.JobContext():
            opts = parser.parse_args(job.args[1:])

            root = etree.Element("transfer_metadata")

            values = fetch_fields_and_values(opts.sip_uuid)
            elements = [build_element(label, value, root) for (label, value) in values]

            # If there is no transfer metadata, skip writing the XML
            if elements:
                tree = etree.ElementTree(root)
                tree.write(
                    opts.xml_file,
                    pretty_print=True,
                    xml_declaration=True,
                    encoding="utf-8",
                )

                job.pyprint(etree.tostring(tree, encoding="utf8"))

            # This is an odd point to mark the transfer as "completed", but it's the
            # last step in the "Complete Transfer" microservice group before the folder
            # move, so it seems like the best option we have for now.
            metrics.transfer_completed(opts.sip_uuid)

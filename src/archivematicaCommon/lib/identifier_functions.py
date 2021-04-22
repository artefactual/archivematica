# -*- coding: utf-8 -*-
"""
Functions to fetch identifiers for indexing in ElasticSearch.

See also src/MCPClient/lib/clientScripts/index_aip.py where these are used.
"""
from __future__ import absolute_import

from lxml import etree


def extract_identifiers_from_mods(mods_path):
    """
    Parse MODS identifiers from a MODS file.

    :return: List of identifiers, possibly empty.
    """
    doc = etree.parse(mods_path)
    elements = doc.findall("//{http://www.loc.gov/mods/v3}identifier")
    return [e.text for e in elements if e.text is not None]


def extract_identifier_from_islandora(islandora_path):
    """
    Parse an Islandora identifier from a METS file.

    This typically occurs when using the FEDORA deposit storage service space.

    :return: List of identifiers, possibly empty.
    """
    tree = etree.parse(islandora_path)
    root = tree.getroot()
    objid = root.attrib.get("OBJID")
    return [objid] if objid else []

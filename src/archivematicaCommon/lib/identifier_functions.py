# -*- coding: UTF-8 -*-
"""
Functions to fetch identifiers for indexing in ElasticSearch.

See also src/MCPClient/lib/clientScripts/indexAIP.py where these are used.
"""

from lxml import etree

def extract_identifiers_from_mods(mods_path):
    """
    Parse MODS identifiers from a MODS file.

    :return: List of identifiers, possibly empty.
    """
    doc = etree.parse(mods_path)
    elements = doc.findall('//{http://www.loc.gov/mods/v3}identifier')
    return [e.text for e in elements if e.text is not None]

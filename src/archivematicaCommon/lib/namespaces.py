# -*- coding: utf-8 -*-
from __future__ import absolute_import

from xml.etree import ElementPath

dcNS = "http://purl.org/dc/elements/1.1/"
dctermsNS = "http://purl.org/dc/terms/"
dspaceNS = "http://www.dspace.org/xmlns/dspace/dim"
fitsNS = "http://hul.harvard.edu/ois/xml/ns/fits/fits_output"
metsNS = "http://www.loc.gov/METS/"
premisNS = "http://www.loc.gov/premis/v3"
premisNS_V2 = "info:lc/xmlns/premis-v2"
xlinkNS = "http://www.w3.org/1999/xlink"
xsiNS = "http://www.w3.org/2001/XMLSchema-instance"

dcBNS = "{" + dcNS + "}"
dctermsBNS = "{" + dctermsNS + "}"
dspaceBNS = "{" + dspaceNS + "}"
fitsBNS = "{" + fitsNS + "}"
metsBNS = "{" + metsNS + "}"
premisBNS = "{" + premisNS + "}"
premisBNS_V2 = "{" + premisNS_V2 + "}"
xlinkBNS = "{" + xlinkNS + "}"
xsiBNS = "{" + xsiNS + "}"

NSMAP = {
    "dc": dcNS,
    "dcterms": dctermsNS,
    "dim": dspaceNS,
    "fits": fitsNS,
    "mets": metsNS,
    "premis": premisNS,
    "xlink": xlinkNS,
    "xsi": xsiNS,
}


def nsmap_for_premis2():
    """Return a copy of ``NSMAP`` with ``premis`` using PREMIS 2.

    ``NSMAP`` uses PREMIS 3. This function can be used when look ups are
    targeting PREMIS 2 instead, e.g. reingest.
    """
    nsmap = NSMAP.copy()
    nsmap["premis"] = premisNS_V2
    return nsmap


# The functions below require a cache clear, because the namespace maps
# are being altered when falling back to PREMIS 2
# (Ref. https://stackoverflow.com/a/24872696/1572895)


def xml_find_premis(elem, path):
    """``find`` with PREMIS 2 fallback."""
    matches = elem.find(path, namespaces=NSMAP)
    if matches is None:
        ElementPath._cache.clear()
        matches = elem.find(path, namespaces=nsmap_for_premis2())
    return matches


def xml_findall_premis(elem, path):
    """``findall`` with PREMIS 2 fallback."""
    matches = elem.findall(path, namespaces=NSMAP)
    if matches == []:
        ElementPath._cache.clear()
        matches = elem.findall(path, namespaces=nsmap_for_premis2())
    return matches


def xml_findtext_premis(elem, path, default=""):
    """``findtext`` with PREMIS 2 fallback."""
    match = elem.findtext(path, namespaces=NSMAP)
    if match is None:
        ElementPath._cache.clear()
        match = elem.findtext(path, namespaces=nsmap_for_premis2())
    return match or default


def xml_xpath_premis(elem, path):
    """``xpath`` with PREMIS 2 fallback."""
    matches = elem.xpath(path, namespaces=NSMAP)
    if not matches:
        ElementPath._cache.clear()
        matches = elem.xpath(path, namespaces=nsmap_for_premis2())
    return matches

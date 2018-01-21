#!/usr/bin/env python2

dcNS = "http://purl.org/dc/elements/1.1/"
dctermsNS = "http://purl.org/dc/terms/"
dspaceNS = "http://www.dspace.org/xmlns/dspace/dim"
fitsNS = "http://hul.harvard.edu/ois/xml/ns/fits/fits_output"
metsNS = "http://www.loc.gov/METS/"
premisNS = "info:lc/xmlns/premis-v2"
premisV3NS = "http://www.loc.gov/premis/v3"
xlinkNS = "http://www.w3.org/1999/xlink"
xsiNS = "http://www.w3.org/2001/XMLSchema-instance"

dcBNS = "{" + dcNS + "}"
dctermsBNS = "{" + dctermsNS + "}"
dspaceBNS = "{" + dspaceNS + "}"
fitsBNS = "{" + fitsNS + "}"
metsBNS = "{" + metsNS + "}"
premisBNS = "{" + premisNS + "}"
premisV3BNS = "{" + premisV3NS + "}"
xlinkBNS = "{" + xlinkNS + "}"
xsiBNS = "{" + xsiNS + "}"

NSMAP = {
    'dc': dcNS,
    'dcterms': dctermsNS,
    'dim': dspaceNS,
    'fits': fitsNS,
    'mets': metsNS,
    'premis': premisNS,
    'premisv3': premisV3NS,
    'xlink': xlinkNS,
    'xsi': xsiNS,
}

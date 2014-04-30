#!/usr/bin/python -OO

dcNS="http://purl.org/dc/elements/1.1/"
dctermsNS = "http://purl.org/dc/terms/"
fitsNS = "http://hul.harvard.edu/ois/xml/ns/fits/fits_output"
metsNS = "http://www.loc.gov/METS/"
premisNS = "info:lc/xmlns/premis-v2"
xlinkNS = "http://www.w3.org/1999/xlink"
xsiNS = "http://www.w3.org/2001/XMLSchema-instance"

dcBNS = "{" + dcNS + "}"
dctermsBNS = "{" + dctermsNS + "}"
fitsBNS = "{" + fitsNS + "}"
metsBNS = "{" + metsNS + "}"
premisBNS = "{" + premisNS + "}"
xlinkBNS = "{" + xlinkNS + "}"
xsiBNS = "{" + xsiNS + "}"

NSMAP = {
    'dc': dcNS,
    'dcterms': dctermsNS,
    'fits': fitsNS,
    'mets': metsNS,
    'premis': premisNS,
    'xlink': xlinkNS,
    'xsi': xsiNS,
}

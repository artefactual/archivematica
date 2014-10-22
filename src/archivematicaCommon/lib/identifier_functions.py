from lxml import etree

def extract_identifiers_from_mods(mods_path):
    doc = etree.parse(mods_path)
    elements = doc.findall('//{http://www.loc.gov/mods/v3}identifier')
    return [e.text for e in elements]

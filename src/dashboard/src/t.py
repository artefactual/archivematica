from lxml import etree

file = open(file_path, 'r')
xml = file.read()

tree = etree.fromstring(xml)
root = tree.getroot()
#choices = root.find('preconfiguredChoices')


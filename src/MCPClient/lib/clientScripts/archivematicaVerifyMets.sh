#!/bin/bash

set -e
sipPath="$1"
metsFile="${sipPath}metadata/mets_structmap.xml"
schema="/usr/lib/archivematica/archivematicaCommon/externals/mets/mets.xsd"

#not used... doesn't put file in correct location either
if [ ! -f "${schema}" ]; then
	echo TODO
    echo getting mets.xsd
    wget http://www.loc.gov/standards/mets/mets.xsd /usr/lib/archivematica/archivematicaCommon/externals/mets/mets.xsd
fi

if [ -f "${metsFile}" ]; then
    xmllint --noout --schema "$schema" "${sipPath}metadata/mets_structmap.xml"
else
	echo No metadata/mets_structmap.xml file to verify.
fi

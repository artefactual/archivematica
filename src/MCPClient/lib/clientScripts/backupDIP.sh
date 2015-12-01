#!/bin/bash

DIP="$1"
DIPsStore="${2}`basename $1`/"
uploadedObjects="DIPUploadedFiles.txt"

cd "$DIP"
ls objects > "$uploadedObjects"

mkdir "${DIPsStore}"
chmod 750 "${DIPsStore}"
mv "objectsBackup" "${DIPsStore}."
chmod -R 750 "$uploadedObjects"
mv "$uploadedObjects" "${DIPsStore}."
chmod 770 "${DIPsStore}${uploadedObjects}"
cp "METS.xml" "${DIPsStore}."
chmod 750 "${DIPsStore}METS.xml"

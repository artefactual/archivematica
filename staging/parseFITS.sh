#!/bin/bash
tmpDir="`pwd`"
cd "`dirname $0`"

#in file utility output: <format>
./parseFITS.fileUtility.py

#in ffident output: <mimetype>
./parseFITS.ffident.py

#in DROID output: <IdentificationFile>
./parseFITS.DROID.py

#in JHOVE output: <format>
./parseFITS.Jhove.py

#in FITS output: <identify format>

cd "$tmpDir"

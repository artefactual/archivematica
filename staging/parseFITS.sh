#!/bin/bash
tmpDir="`pwd`"
cd "`dirname $0`"

#in file utility output: <format>
./parseFITS.fileUtility.py
./parseFITS.fileUtility.MimeType.py

#in ffident output: <mimetype>
./parseFITS.ffident.py

#in DROID output: <IdentificationFile>
./parseFITS.DROID.py
./parseFITS.DROID.MimeType.py

#in JHOVE output: <format>
./parseFITS.Jhove.py
./parseFITS.Jhove.MimeType.py

#in FITS output: <identify format>
./parseFITS.FITS.MimeType.py
./parseFITS.FITS.format.py

cd "$tmpDir"

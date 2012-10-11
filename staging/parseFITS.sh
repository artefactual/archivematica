#!/bin/bash
tmpDir="`pwd`"
cd "`dirname $0`"
#in file utility output: <format>
./parseFITS.fileUtility.py
#in ffident output: <mimetype>
#in DROID output: <IdentificationFile>
#in JHOVE output: <format>
#in FITS output: <identify format>
cd "$tmpDir"

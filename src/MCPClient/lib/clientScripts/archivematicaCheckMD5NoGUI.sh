#!/bin/bash

#create temp report files
UUID=`uuid`
failTmp=/tmp/fail-$UUID
passTmp=/tmp/pass-$UUID
reportTmp=/tmp/report-$UUID

checkFolder="$1"
md5Digest="$2"
integrityReport="$3"
checksumTool="$4"

tmpDir=`pwd`
cd "$checkFolder"
#check for passing checksums
"${checksumTool}" -r -m "$md5Digest" . > $passTmp
#check for failing checksums
"${checksumTool}" -r -x "$md5Digest" . > $failTmp
cd $tmpDir      



#Count number of Passed/Failed
numberPass=`wc -l $passTmp| cut -d" " -f1`
numberFail=`wc -l $failTmp| cut -d" " -f1`

#Create report
echo "PASSED" >> $reportTmp
cat $passTmp >> $reportTmp
echo " " >> $reportTmp
echo $numberPass "items passed integrity checking" >> $reportTmp
echo " " >> $reportTmp
echo " " >> $reportTmp
echo "FAILED" >> $reportTmp
cat $failTmp >> $reportTmp
echo " " >> $reportTmp
echo $numberFail "items failed integrity checking" >> $reportTmp

#copy pasta
cp $reportTmp "$integrityReport"
cat $failTmp 1>&2

#cleanup
rm $failTmp $passTmp $reportTmp

exit $numberFail

#!/bin/bash
#
# Arguments:
# $1 - %SIPDirectory%
# $2 - %SIPName%-%SIPUUID%

# Copy submission documentation from the AIP back into the SIP
subdir="$1/submissionDocumentation"
mkdir -p $subdir
cp -R "$1/$2/data/objects/submissionDocumentation" $subdir || true

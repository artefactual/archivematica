#!/usr/bin/env python2

from __future__ import print_function
import sys
import os

SIPUUID = sys.argv[1]
SIPName = sys.argv[2]
SIPDirectory = sys.argv[3]

manualNormalizationPath = os.path.join(SIPDirectory, "objects", "manualNormalization")
print('Manual normalization path:', manualNormalizationPath)
if os.path.isdir(manualNormalizationPath):
    mn_access_path = os.path.join(manualNormalizationPath, "access")
    mn_preserve_path = os.path.join(manualNormalizationPath, "preservation")
    # Return to indicate manually normalized files exist
    if os.path.isdir(mn_access_path) and os.listdir(mn_access_path):
        print('Manually normalized files found')
        sys.exit(179)

    if os.path.isdir(mn_preserve_path) and os.listdir(mn_preserve_path):
        print('Manually normalized files found')
        sys.exit(179)
exit(0)

#!/usr/bin/env python2

import sys

# fileOperations requires Django to be set up
import django
django.setup()
# archivematicaCommon
from fileOperations import updateFileGrpUse

from custom_handlers import get_script_logger
logger = get_script_logger("archivematica.mcp.client.manualNormalizationIdentifyFilesIncluded")

fileUUID = sys.argv[1]
updateFileGrpUse(fileUUID, "manualNormalization")

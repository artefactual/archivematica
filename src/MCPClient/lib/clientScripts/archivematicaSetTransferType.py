#!/usr/bin/env python2

import sys

import django
django.setup()
# dashboard
from main.models import Transfer

# archivematicaCommon
from custom_handlers import get_script_logger

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.setTransferType")
    transferUUID = sys.argv[1]
    transferType = sys.argv[2]

    Transfer.objects.filter(uuid=transferUUID).update(type=transferType)

#!/usr/bin/env python2
from __future__ import print_function
import sys
from custom_handlers import get_script_logger

from validateDerivative import DerivativeValidator

if __name__ == '__main__':
    logger = get_script_logger(
        "archivematica.mcp.client.validatePreservationDerivative")
    file_path = sys.argv[1]
    file_uuid = sys.argv[2]
    sip_uuid = sys.argv[3]
    shared_path = sys.argv[4]
    validator = DerivativeValidator(file_path, file_uuid, sip_uuid, shared_path)
    sys.exit(validator.validate())

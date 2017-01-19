#!/usr/bin/env python2
from __future__ import print_function
import sys
from custom_handlers import get_script_logger

import django
django.setup()
from main.models import Derivation, File

from validateDerivative import DerivativeValidator


class AccessDerivativeValidator(DerivativeValidator):

    purpose = 'validateAccessDerivative'
    not_derivative_msg = 'is not an access derivative'

    def is_derivative(self):
        """Returns ``True`` if the file with UUID ``self.file_uuid`` encodes an
        access derivative.
        """
        file_model = File.objects.get(uuid=self.file_uuid)
        if file_model.filegrpuse == 'access':
            try:
                Derivation.objects.get(derived_file__uuid=self.file_uuid,
                                       event__isnull=True)
                return True
            except Derivation.DoesNotExist:
                return False
        else:
            return False


if __name__ == '__main__':
    logger = get_script_logger(
        "archivematica.mcp.client.validateAccessDerivative")
    file_path = sys.argv[1]
    file_uuid = sys.argv[2]
    sip_uuid = sys.argv[3]
    shared_path = sys.argv[4]
    validator = AccessDerivativeValidator(file_path, file_uuid, sip_uuid, shared_path)
    sys.exit(validator.validate())

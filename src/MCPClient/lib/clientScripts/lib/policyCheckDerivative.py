from __future__ import print_function
import sys
from custom_handlers import get_script_logger
from main.models import Derivation
from policyCheck import PolicyChecker


class DerivativePolicyChecker(PolicyChecker):

    purpose = 'checkingDerivativePolicy'

    def is_derivative(self, for_access=False):
        if self.is_manually_normalized_access_derivative:
            return True
        # Access derivatives have Derivation rows with NULL event types (cf.
        # normalize.py client script).
        event_type = 'normalization'
        if for_access:
            event_type = None
        try:
            Derivation.objects.get(derived_file__uuid=self.file_uuid,
                                   event__event_type=event_type)
            return True
        except Derivation.DoesNotExist:
            return False

    def we_check_this_type_of_file(self):
        if not self.is_derivative():
            print('File {uuid} is not a derivative; not performing a policy'
                  ' check.'.format(uuid=self.file_uuid))
            return False
        return True

#!/usr/bin/env python2
from __future__ import print_function
import sys
from custom_handlers import get_script_logger

from policyCheckDerivative import DerivativePolicyChecker


class AccessDerivativePolicyChecker(DerivativePolicyChecker):

    purpose = 'checkingAccessDerivativePolicy'

    def we_check_this_type_of_file(self):
        if self.is_derivative(for_access=True) and self.is_for_access():
            return True
        print('File {uuid} is not an access derivative; not performing'
                ' a policy check.'.format(uuid=self.file_uuid))
        if not self.is_derivative(for_access=True):
            print('File {uuid} is not a derivative.'.format(
                uuid=self.file_uuid))
        if not self.is_for_access():
            print('File {uuid} is not for access.'.format(
                uuid=self.file_uuid))
        return False

if __name__ == '__main__':
    logger = get_script_logger(
        "archivematica.mcp.client.policyCheck")
    file_path = sys.argv[1]
    file_uuid = sys.argv[2]
    sip_uuid = sys.argv[3]
    shared_path = sys.argv[4]
    policy_checker = AccessDerivativePolicyChecker(
        file_path, file_uuid, sip_uuid, shared_path)
    sys.exit(policy_checker.check())

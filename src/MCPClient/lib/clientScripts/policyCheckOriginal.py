#!/usr/bin/env python2
from __future__ import print_function
import os
import sys

from custom_handlers import get_script_logger
from main.models import Transfer
from policyCheck import PolicyChecker


class OriginalPolicyChecker(PolicyChecker):

    purpose = 'checkingOriginalPolicy'

    def we_check_this_type_of_file(self):
        # During transfer we check all files. Is this correct or are there
        # classes of file that we do not want to perform policy checks on?
        return True

    @property
    def sip_logs_dir(self):
        """Return the absolute path the logs/ directory of the Transfer that the
        target file is a part of. NOTE: here we are overriding a method in the
        super-class that expects the logs/ directory to be in the SIP; however,
        in this case, there is no SIP and we're looking for the logs/ directory
        of the transfer.
        """
        if self._sip_logs_dir:
            return self._sip_logs_dir
        try:
            transfer_model = Transfer.objects.get(uuid=self.sip_uuid)
        except (Transfer.DoesNotExist, Transfer.MultipleObjectsReturned):
            print('Warning: unable to retrieve Transfer model corresponding to'
                  ' Transfer UUID {}'.format(self.sip_uuid), file=sys.stderr)
            return None
        else:
            transfer_path = transfer_model.currentlocation.replace(
                '%sharedPath%', self.shared_path, 1)
            logs_dir = os.path.join(transfer_path, 'logs')
            if os.path.isdir(logs_dir):
                self._sip_logs_dir = logs_dir
                return logs_dir
            print('Warning: unable to find a logs/ directory in the Transfer'
                  ' with UUID {}'.format(self.sip_uuid), file=sys.stderr)
            return None


if __name__ == '__main__':
    logger = get_script_logger(
        "archivematica.mcp.client.policyCheckOriginal")
    file_path = sys.argv[1]
    file_uuid = sys.argv[2]
    sip_uuid = sys.argv[3]
    shared_path = sys.argv[4]
    policy_checker = OriginalPolicyChecker(file_path, file_uuid, sip_uuid,
                                           shared_path)
    sys.exit(policy_checker.check())

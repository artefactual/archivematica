#!/usr/bin/env python

import sys

# dashboard
from fpr.models import FPRule
from main.models import FileFormatVersion, Transfer


def is_extractable(f):
    try:
        format = f.fileformatversion_set.get().format_version
    except FileFormatVersion.DoesNotExist:
        return False

    extract_rules = FPRule.active.filter(purpose="extract", format=format)
    if extract_rules:
        return True
    else:
        return False


def main(sip_uuid):
    transfer = Transfer.objects.get(uuid=sip_uuid)
    for f in transfer.file_set.iterator():
        if is_extractable(f):
            return 0

    return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))

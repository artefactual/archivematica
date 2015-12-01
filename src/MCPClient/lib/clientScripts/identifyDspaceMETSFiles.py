#!/usr/bin/env python2

import sys

import django
django.setup()
# dashboard
from main.models import File


if __name__ == '__main__':
    metsFileUUID =  sys.argv[1]

    File.objects.filter(uuid=metsFileUUID).update(filegrpuse='DSPACEMETS')

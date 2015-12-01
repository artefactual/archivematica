#!/usr/bin/env python2

import os
import sys

import django
os.environ["DJANGO_SETTINGS_MODULE"] = "settings.local"
sys.path.append("/usr/share/archivematica/dashboard")
django.setup()
from main.models import WatchedDirectory


def removeEverythingInDirectory(directory):
    if directory[-1] != "/":
        directory = "%s/" % (directory)
    execute = "sudo rm -rf \"%s\"*" % (directory)
    print "executing: ", execute
    os.system(execute)

def cleanWatchedDirectories():
    for path, in WatchedDirectory.objects.values_list('watched_directory_path'):
        try:
            directory = path.replace("%watchDirectoryPath%", "/var/archivematica/sharedDirectory/watchedDirectories/", 1)
            removeEverythingInDirectory(directory)
        except Exception as inst:
            print "debug except 2"
            print type(inst)     # the exception instance
            print inst.args      # arguments stored in .args

if __name__ == '__main__':
    import getpass
    user = getpass.getuser()
    print "user: ", user
    if user != "root":
        print "Please run as root (with sudo)"
        exit (1)
    cleanWatchedDirectories()
    alsoRemove = [
        "/var/archivematica/sharedDirectory/failed/",
        "/var/archivematica/sharedDirectory/currentlyProcessing/",
        "/var/archivematica/sharedDirectory/rejected/",
        "/var/archivematica/sharedDirectory/completed/transfers/",
    ]
    for directory in alsoRemove:
        removeEverythingInDirectory(directory)

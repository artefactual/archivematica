#!/usr/bin/env python2

import collections
import lxml.etree as etree
import os
import re
import sys

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import DashboardSetting


REQUIRED_DIRECTORIES = [
    "logs",
    "logs/fileMeta",
    "metadata",
    "metadata/submissionDocumentation",
    "objects",
]

OPTIONAL_FILES = [
    "processingMCP.xml",
]

MANUAL_NORMALIZATION_DIRECTORIES = [
    "objects/manualNormalization/access",
    "objects/manualNormalization/preservation",
]

def get_setting(setting, default=''):
    try:
        return DashboardSetting.objects.get(name=setting).value
    except DashboardSetting.DoesNotExist:
        return default


class OrderedListsDict(collections.OrderedDict):
    """
    OrderedDict where all keys are lists, and elements are appended automatically.
    """

    def __setitem__(self, key, value):
        # When inserting, insert into a list of items with the same key
        try:
            self[key]
        except KeyError:
            super(OrderedListsDict, self).__setitem__(key, [])
        self[key].append(value)


def unicodeToStr(string):
    if isinstance(string, unicode):
        string = string.encode("utf-8")
    return string

def strToUnicode(string):
    if isinstance(string, str):
        string = string.decode("utf-8")
    return string


def getTagged(root, tag):
    ret = []
    for element in root:
        #print element.tag
        #print tag
        #print element.tag == tag
        if element.tag == tag:
            ret.append(element)
            #return ret #only return the first encounter
    return ret


def appendEventToFile(SIPLogsDirectory, fileUUID, eventXML):
    xmlFile = SIPLogsDirectory + "fileMeta/" + fileUUID + ".xml"
    appendEventToFile2(xmlFile, eventXML)

def appendEventToFile2(xmlFile, eventXML):
    tree = etree.parse( xmlFile )
    root = tree.getroot()

    events = getTagged(root, "events")[0]
    events.append(eventXML)

    tree = etree.ElementTree(root)
    tree.write(xmlFile)

def archivematicaRenameFile(SIPLogsDirectory, fileUUID, newName, eventXML):
    xmlFile = SIPLogsDirectory + "fileMeta/" + fileUUID + ".xml"
    newName = newName.decode('utf-8')
    tree = etree.parse( xmlFile )
    root = tree.getroot()
    xmlFileName = getTagged(root, "currentFileName")[0]
    xmlFileName.text = newName

    events = getTagged(root, "events")[0]
    events.append(eventXML)

    #print etree.tostring(root, pretty_print=True)

    tree = etree.ElementTree(root)
    tree.write(xmlFile)


def fileNoLongerExists(root, objectsDir):
    """Returns 0 if not deleted, 1 if deleted, -1 if deleted, but already an event to indicated it has been removed"""
    events = getTagged(root, "events")[0]

    for event in getTagged(events, "event"):
        #print >>sys.stderr , "event"
        etype = getTagged(event, "eventType")
        if len(etype) and etype[0].text == "fileRemoved":
            #print >>sys.stderr , "file already removed"
            return -1

    currentName = getTagged(root, "currentFileName")[0].text

    currentName2 = currentName.replace("objects", objectsDir, 1)
    if os.path.isfile(currentName2.encode('utf8')):
        return 0
    else:
        print currentName
        return 1

def escapeForCommand(string):
    ret = string
    if isinstance(ret, basestring):
        ret = ret.replace("\\", "\\\\")
        ret = ret.replace("\"", "\\\"")
        ret = ret.replace("`", "\`")
        #ret = ret.replace("'", "\\'")
        #ret = ret.replace("$", "\\$")
    return ret

# This replaces non-unicode characters with a replacement character,
# and is primarily used for arbitrary strings (e.g. filenames, paths)
# that might not be valid unicode to begin with.
def escape(string):
    if isinstance(string, basestring):
        string = string.decode('utf-8', errors='replace')
    return string


# Normalize non-DC CONTENTdm metadata element names to match those used
# in transfer's metadata.csv files.
def normalizeNonDcElementName(string):
     # Convert non-alphanumerics to _, remove extra _ from ends of string.
     normalizedString = re.sub(r"\W+", '_', string)
     normalizedString = normalizedString.strip('_')
     # Lower case string.
     normalizedString = normalizedString.lower()
     return normalizedString

def find_metadata_files(sip_path, filename):
    """
    Check the SIP and transfer metadata directories for filename.

    Helper function to collect all of a particular metadata file (e.g. metadata.csv) in a SIP.

    SIP-level files will be at the end of the list, if they exist.

    :param sip_path: Path of the SIP to check
    :param filename: Name of the metadata file to search for
    :return: List of full paths to instances of filename
    """
    paths = []
    # Check transfers
    transfers_md_path = os.path.join(sip_path, 'objects', 'metadata', 'transfers')
    try:
        transfers = os.listdir(transfers_md_path)
    except OSError:
        transfers = []
    for transfer in transfers:
        path = os.path.join(transfers_md_path, transfer, filename)
        if os.path.isfile(path):
            paths.append(path)
    # Check SIP metadata dir
    path = os.path.join(sip_path, 'objects', 'metadata', filename)
    if os.path.isfile(path):
        paths.append(path)
    return paths

def create_directories(directories, basepath='', printing=False):
    for directory in directories:
        dir_path = os.path.join(basepath, directory)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
            if printing:
                print 'Creating directory', dir_path

def create_structured_directory(basepath, manual_normalization=False, printing=False):
    create_directories(REQUIRED_DIRECTORIES, basepath=basepath, printing=printing)
    if manual_normalization:
        create_directories(MANUAL_NORMALIZATION_DIRECTORIES, basepath=basepath, printing=printing)

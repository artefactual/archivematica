#!/usr/bin/env python2

import sys

from linkTaskManager import LinkTaskManager

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import TaskConfigAssignMagicLink

global choicesAvailableForUnits
choicesAvailableForUnits = {}

class linkTaskManagerAssignMagicLink(LinkTaskManager):
    """Assign a link to the unit to process when loaded.
        Deprecated! Replaced with Set/Load Unit Variable"""
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerAssignMagicLink, self).__init__(jobChainLink, pk, unit)

        ###GET THE MAGIC NUMBER FROM THE TASK stuff
        link = 0
        try:
            link = TaskConfigAssignMagicLink.objects.get(id=pk).execute
        except TaskConfigAssignMagicLink.DoesNotExist:
            pass

        ###Update the unit
        #set the magic number
        self.unit.setMagicLink(link, exitStatus="")
        self.jobChainLink.linkProcessingComplete(0)

#!/usr/bin/env python2

import sys

from linkTaskManager import LinkTaskManager
global choicesAvailableForUnits
choicesAvailableForUnits = {}

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import TaskConfigSetUnitVariable

class linkTaskManagerSetUnitVariable(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerSetUnitVariable, self).__init__(jobChainLink, pk, unit)
        ###GET THE MAGIC NUMBER FROM THE TASK stuff
        var = TaskConfigSetUnitVariable.objects.get(id=pk)

        ###Update the unit
        #set the magic number
        self.unit.setVariable(var.variable, var.variablevalue, var.microservicechainlink_id)
        self.jobChainLink.linkProcessingComplete(0)

#!/usr/bin/env python2

import sys

from linkTaskManager import LinkTaskManager
global choicesAvailableForUnits
choicesAvailableForUnits = {}

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import TaskConfigUnitVariableLinkPull

class linkTaskManagerUnitVariableLinkPull(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerUnitVariableLinkPull, self).__init__(jobChainLink, pk, unit)
        var = TaskConfigUnitVariableLinkPull.objects.get(id=pk)
        link = self.unit.getmicroServiceChainLink(var.variable, var.variablevalue, var.defaultmicroservicechainlink_id)
        
        ###Update the unit
        if link != None:
            self.jobChainLink.setExitMessage("Completed successfully")
            self.jobChainLink.jobChain.nextChainLink(link, passVar=self.jobChainLink.passVar)

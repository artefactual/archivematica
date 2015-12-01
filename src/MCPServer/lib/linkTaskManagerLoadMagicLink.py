#!/usr/bin/env python2

from linkTaskManager import LinkTaskManager
global choicesAvailableForUnits
choicesAvailableForUnits = {}

class linkTaskManagerLoadMagicLink(LinkTaskManager):
    """Load a link from the unit to process.
        Deprecated! Replaced with Set/Load Unit Variable"""
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerLoadMagicLink, self).__init__(jobChainLink, pk, unit)
        ###Update the unit
        magicLink = self.unit.getMagicLink()
        if magicLink != None:
            link, exitStatus = magicLink
            self.jobChainLink.setExitMessage("Completed successfully")
            self.jobChainLink.jobChain.nextChainLink(link, passVar=self.jobChainLink.passVar)

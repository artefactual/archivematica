#!/usr/bin/env python2

import sys
import uuid

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from dicts import ReplacementDict


class LinkTaskManager(object):
    """ Common manager for MicroServiceChainLinks of different task types. """
    def __init__(self, jobChainLink, pk, unit):
        """ Initalize common variables. """
        self.jobChainLink = jobChainLink
        self.pk = pk
        self.unit = unit
        self.UUID = str(uuid.uuid4())

    def update_passvar_replacement_dict(self, replace_dict):
        """ Update the ReplacementDict in the passVar, creating one if needed. """
        if self.jobChainLink.passVar is not None:
            if isinstance(self.jobChainLink.passVar, list):
                # Search the list for a ReplacementDict, and update it if it
                # exists, otherwise append to list
                for passVar in self.jobChainLink.passVar:
                    if isinstance(passVar, ReplacementDict):
                        passVar.update(replace_dict)
                        break
                else:
                    self.jobChainLink.passVar.append(replace_dict)
            elif isinstance(self.jobChainLink.passVar, ReplacementDict):
                # passVar is a ReplacementDict that needs to be updated
                self.jobChainLink.passVar.update(replace_dict)
            else:
                # Create list with existing passVar and replace_dict
                self.jobChainLink.passVar = [replace_dict, self.jobChainLink.passVar]
        else:
            # PassVar is empty, create new list
            self.jobChainLink.passVar = [replace_dict]

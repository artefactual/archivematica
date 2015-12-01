#!/usr/bin/env python2

# Stdlib, alphabetical by import source
import logging
import os
import sys
import threading

# This project,  alphabetical by import source
from linkTaskManager import LinkTaskManager
from taskStandard import taskStandard
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivematicaFunctions
import databaseFunctions
from dicts import ChoicesDict, ReplacementDict
sys.path.append("/usr/share/archivematica/dashboard")
from main.models import StandardTaskConfig

LOGGER = logging.getLogger('archivematica.mcp.server')

class linkTaskManagerGetMicroserviceGeneratedListInStdOut(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerGetMicroserviceGeneratedListInStdOut, self).__init__(jobChainLink, pk, unit)
        self.tasks = []
        stc = StandardTaskConfig.objects.get(id=str(pk))
        filterSubDir = stc.filter_subdir
        self.requiresOutputLock = stc.requires_output_lock
        standardOutputFile = stc.stdout_file
        standardErrorFile = stc.stderr_file
        execute = stc.execute
        self.execute = execute
        arguments = stc.arguments

        if filterSubDir:
            directory = os.path.join(unit.currentPath, filterSubDir)
        else:
            directory = unit.currentPath

        # Apply passvar replacement values
        if self.jobChainLink.passVar is not None:
            if isinstance(self.jobChainLink.passVar, list):
                for passVar in self.jobChainLink.passVar:
                    if isinstance(passVar, ReplacementDict):
                        arguments, standardOutputFile, standardErrorFile = passVar.replace(arguments, standardOutputFile, standardErrorFile)
            elif isinstance(self.jobChainLink.passVar, ReplacementDict):
                arguments, standardOutputFile, standardErrorFile = self.jobChainLink.passVar.replace(arguments, standardOutputFile, standardErrorFile)

        # Apply unit (SIP/Transfer) replacement values
        commandReplacementDic = unit.getReplacementDic(directory)
        # Escape all values for shell
        for key, value in commandReplacementDic.items():
                commandReplacementDic[key] = archivematicaFunctions.escapeForCommand(value)
        arguments, standardOutputFile, standardErrorFile = commandReplacementDic.replace(arguments, standardOutputFile, standardErrorFile)

        self.task = taskStandard(self, execute, arguments, standardOutputFile, standardErrorFile, UUID=self.UUID)
        databaseFunctions.logTaskCreatedSQL(self, commandReplacementDic, self.UUID, arguments)
        t = threading.Thread(target=self.task.performTask)
        t.daemon = True
        t.start()

    def taskCompletedCallBackFunction(self, task):
        databaseFunctions.logTaskCompletedSQL(task)
        try:
            choices = ChoicesDict.fromstring(task.results["stdOut"])
        except Exception:
            LOGGER.exception('Unable to create dic from output %s', task.results['stdOut'])
            choices = ChoicesDict({})
        if self.jobChainLink.passVar is not None:
            if isinstance(self.jobChainLink.passVar, list):
                for index, value in enumerate(self.jobChainLink.passVar):
                    if isinstance(value, ChoicesDict):
                        self.jobChainLink.passVar[index] = choices
                        break
                else:
                    self.jobChainLink.passVar.append(choices)
            else:
                self.jobChainLink.passVar = [choices, self.jobChainLink.passVar]
        else:
            self.jobChainLink.passVar = [choices]

        self.jobChainLink.linkProcessingComplete(task.results["exitCode"], self.jobChainLink.passVar)

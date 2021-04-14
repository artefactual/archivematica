# -*- coding: utf-8 -*-

"""Shared directory setup.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import os

from django.conf import settings

from processing import BUILTIN_CONFIGS, install_builtin_config


logger = logging.getLogger("archivematica.mcp.server.shareddirs")


def create():
    dirs = (
        "arrange",
        "completed",
        "completed/transfers",
        "currentlyProcessing",
        "DIPbackups",
        "failed",
        "rejected",
        "sharedMicroServiceTasksConfigs",
        "sharedMicroServiceTasksConfigs/createXmlEventsAssist",
        "sharedMicroServiceTasksConfigs/generateAIP",
        "sharedMicroServiceTasksConfigs/generateAIP/bagit",
        "sharedMicroServiceTasksConfigs/processingMCPConfigs",
        "sharedMicroServiceTasksConfigs/transcoder",
        "sharedMicroServiceTasksConfigs/transcoder/defaultIcons",
        "SIPbackups",
        "tmp",
        "watchedDirectories",
        "watchedDirectories/activeTransfers",
        "watchedDirectories/activeTransfers/baggitDirectory",
        "watchedDirectories/activeTransfers/baggitZippedDirectory",
        "watchedDirectories/activeTransfers/dataverseTransfer",
        "watchedDirectories/activeTransfers/Dspace",
        "watchedDirectories/activeTransfers/maildir",
        "watchedDirectories/activeTransfers/standardTransfer",
        "watchedDirectories/activeTransfers/TRIM",
        "watchedDirectories/activeTransfers/zippedDirectory",
        "watchedDirectories/approveNormalization",
        "watchedDirectories/SIPCreation",
        "watchedDirectories/SIPCreation/completedTransfers",
        "watchedDirectories/SIPCreation/SIPsUnderConstruction",
        "watchedDirectories/storeAIP",
        "watchedDirectories/system",
        "watchedDirectories/system/autoProcessSIP",
        "watchedDirectories/system/autoRestructureForCompliance",
        "watchedDirectories/system/createAIC",
        "watchedDirectories/system/reingestAIP",
        "watchedDirectories/uploadDIP",
        "watchedDirectories/uploadedDIPs",
        "watchedDirectories/workFlowDecisions",
        "watchedDirectories/workFlowDecisions/compressionAIPDecisions",
        "watchedDirectories/workFlowDecisions/createTree",
        "watchedDirectories/workFlowDecisions/examineContentsChoice",
        "watchedDirectories/workFlowDecisions/extractPackagesChoice",
        "watchedDirectories/workFlowDecisions/metadataReminder",
        "watchedDirectories/workFlowDecisions/selectFormatIDToolIngest",
        "watchedDirectories/workFlowDecisions/selectFormatIDToolTransfer",
        "www",
        "www/AIPsStore",
        "www/AIPsStore/transferBacklog",
        "www/AIPsStore/transferBacklog/arrange",
        "www/AIPsStore/transferBacklog/originals",
        "www/DIPsStore",
    )
    for dirname in dirs:
        dirname = os.path.join(settings.SHARED_DIRECTORY, dirname)
        if os.path.isdir(dirname):
            continue
        logger.info("Creating directory: %s", dirname)
        os.makedirs(dirname, mode=0o770)

    # Populate processing configurations
    for config in BUILTIN_CONFIGS:
        install_builtin_config(config)

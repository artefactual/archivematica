"""
A job corresponds to a microservice, a link in the workflow, and the `Jobs`
table in the database.

Initialization of `Job` objects is typically done via a `JobChain`,
corresponding to a chain in the workflow. The `JobChain` object handles
determining the next job to be run, and passing data between jobs.

The `Job` class is a base class for other job types. There are various
concrete types of jobs, handled by subclasses:
    * `ClientScriptJob`, handling Jobs to be execute on MCPClient
    * `DecisionJob`, handling workflow decision points
    * `LocalJob`, handling work done directly on MCPServer
"""

from archivematica.MCPServer.server.jobs.base import Job
from archivematica.MCPServer.server.jobs.chain import JobChain
from archivematica.MCPServer.server.jobs.client import ClientScriptJob
from archivematica.MCPServer.server.jobs.client import DirectoryClientScriptJob
from archivematica.MCPServer.server.jobs.client import FilesClientScriptJob
from archivematica.MCPServer.server.jobs.client import OutputClientScriptJob
from archivematica.MCPServer.server.jobs.decisions import DecisionJob
from archivematica.MCPServer.server.jobs.decisions import NextChainDecisionJob
from archivematica.MCPServer.server.jobs.decisions import OutputDecisionJob
from archivematica.MCPServer.server.jobs.decisions import UpdateContextDecisionJob
from archivematica.MCPServer.server.jobs.local import GetUnitVarLinkJob
from archivematica.MCPServer.server.jobs.local import LocalJob
from archivematica.MCPServer.server.jobs.local import SetUnitVarLinkJob

__all__ = (
    "ClientScriptJob",
    "DecisionJob",
    "DirectoryClientScriptJob",
    "FilesClientScriptJob",
    "GetUnitVarLinkJob",
    "Job",
    "JobChain",
    "LocalJob",
    "NextChainDecisionJob",
    "OutputClientScriptJob",
    "OutputDecisionJob",
    "SetUnitVarLinkJob",
    "UpdateContextDecisionJob",
)

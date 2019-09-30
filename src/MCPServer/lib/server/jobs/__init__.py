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
from __future__ import absolute_import, division, print_function, unicode_literals


from server.jobs.base import Job
from server.jobs.chain import JobChain
from server.jobs.client import (
    ClientScriptJob,
    DirectoryClientScriptJob,
    FilesClientScriptJob,
    OutputClientScriptJob,
)
from server.jobs.decisions import (
    DecisionJob,
    NextChainDecisionJob,
    OutputDecisionJob,
    UpdateContextDecisionJob,
)
from server.jobs.local import GetUnitVarLinkJob, LocalJob, SetUnitVarLinkJob

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

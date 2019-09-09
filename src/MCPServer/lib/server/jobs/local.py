# -*- coding: utf-8 -*-

"""
Jobs executed locally in MCP server.
"""
from __future__ import absolute_import, unicode_literals

from main import models

from server.db import auto_close_old_connections
from server.jobs.base import Job


class LocalJob(Job):
    """Base class for jobs that are executed directly."""


class GetUnitVarLinkJob(LocalJob):
    """Gets the next link in the chain from a UnitVariable.
    """

    # TODO: replace this concept, if possible

    @auto_close_old_connections
    def run(self, *args, **kwargs):
        super(GetUnitVarLinkJob, self).run(*args, **kwargs)

        try:
            unitvar = models.UnitVariable.objects.get(
                unittype=self.package.UNIT_VARIABLE_TYPE,
                unituuid=self.package.uuid,
                variable=self.link.config["variable"],
            )
        except models.UnitVariable.DoesNotExist:
            link_id = self.link.config["chain_id"]
        else:
            link_id = unitvar.microservicechainlink

        try:
            link = self.link.workflow.get_link(link_id)
        except KeyError:
            raise ValueError(
                "Failed to find workflow link {} (set in unit variable)".format(link_id)
            )

        self.job_chain.next_link = link

        return self


class SetUnitVarLinkJob(LocalJob):
    """Sets the unit variable configured in the workflow.
    """

    # TODO: why? replace this concept, if possible

    @auto_close_old_connections
    def run(self, *args, **kwargs):
        super(SetUnitVarLinkJob, self).run(*args, **kwargs)

        self.package.set_variable(
            self.link.config["variable"],
            self.link.config["variable_value"],
            self.link.config["chain_id"],
        )

        return self

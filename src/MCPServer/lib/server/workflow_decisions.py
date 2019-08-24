# -*- coding: utf-8 -*-
"""
Workflow decision points.

TODO: merge with DecisionJob, or isolate better.
"""
from __future__ import unicode_literals

import logging

from django.conf import six

from server.db import auto_close_old_connections
from server.queues import package_queue
from server.translation import TranslationLabel
from server.workflow_abilities import choice_is_available

from main import models


logger = logging.getLogger("archivematica.mcp.server")


class WorkflowDecision(object):
    """Base class for workflow decisions.
    """

    def __init__(self, job):
        self.job = job
        self.choices = self.get_choices()  # {value: description}

    @property
    def link(self):
        return self.job.link

    @property
    def package(self):
        return self.job.package

    @property
    def workflow(self):
        return self.job.job_chain.workflow

    def get_choices(self):
        raise NotImplementedError

    def decide(self, choice, user_id=None):
        raise NotImplementedError


class NextChainDecision(WorkflowDecision):
    """Decision dictating the next processing chain.
    """

    def get_choices(self):
        choices = {}
        for chain_id in self.link.config["chain_choices"]:
            try:
                chain = self.workflow.get_chain(chain_id)
            except KeyError:
                continue
            if choice_is_available(self.link, chain):
                choices[chain_id] = chain["description"]

        return choices

    @auto_close_old_connections
    def decide(self, choice, user_id=None):
        # TODO: fix circular imports :(
        from server.jobs import JobChain

        # TODO: the default automated processing config uses a choice that isn't
        # listed in the workflow (d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e, for link
        # 755b4177-c587-41a7-8c52-015277568302). Fix that.
        # if choice not in self.choices:
        #     raise ValueError("{} is not one of the available choices".format(choice))

        chain = self.workflow.get_chain(choice)
        logger.info("Using user selected chain %s for link %s", chain.id, self.link.id)

        if user_id is not None:
            agent_id = models.UserProfile.objects.get(user_id=user_id).agent_id
            self.package.set_variable("activeAgent", agent_id, None)

        self.job.mark_complete()
        self.job.continue_processing()

        # TODO: Return a job chain and schedule it via the queue
        job_chain = JobChain(self.package, chain, self.workflow)
        package_queue.schedule_job_chain(job_chain)


class OutputDecision(WorkflowDecision):
    """Decision based on the output of the previous job.
    """

    def get_choices(self):
        choices = {}

        if self.job.job_chain.generated_choices:
            for _, value in self.job.job_chain.generated_choices.items():
                choices[value["uri"]] = TranslationLabel(value["description"])

        return choices

    @auto_close_old_connections
    def decide(self, choice, user_id=None):
        # TODO: DRY with sibling classes
        if choice not in self.choices:
            raise ValueError("{} is not one of the available choices".format(choice))

        if user_id is not None:
            agent_id = models.UserProfile.objects.get(user_id=user_id).agent_id
            self.package.set_variable("activeAgent", agent_id, None)

        # Pass the choice to the next job. This case is only used to select
        # an AIP store URI, and the value of execute (script_name here) is a
        # replacement string (e.g. %AIPsStore%)
        self.job.job_chain.context[self.link.config["execute"]] = choice

        self.job.continue_processing()

        return None


class UpdateContextDecision(WorkflowDecision):
    """Update job chain context based on a user choice

    Pulls from DashboardSettings model, or xml.
    """

    def get_choices(self):
        choices = {}
        # TODO: this is kind of an odd side effect here; refactor
        self.choice_items = []

        for index, item in enumerate(self.link.config["replacements"]):
            # item description is already translated in workflow
            choices[six.text_type(index)] = item["description"]
            self.choice_items.append(self._format_items(item["items"]))

        return choices

    def _format_items(self, items):
        """Wrap replacement items with the ``%`` wildcard character."""
        return {"%{}%".format(key): value for key, value in six.iteritems(items)}

    @auto_close_old_connections
    def decide(self, choice, user_id=None):
        # TODO: DRY with sibling classes
        if choice not in self.choices:
            raise ValueError("{} is not one of the available choices".format(choice))

        choice_index = int(choice)
        items = self.choice_items[choice_index]

        if user_id is not None:
            agent_id = models.UserProfile.objects.get(user_id=user_id).agent_id
            self.package.set_variable("activeAgent", agent_id, None)

        self.job.job_chain.context.update(items)
        self.job.continue_processing()

        return None

# -*- coding: utf-8 -*-
"""
Jobs relating to user decisions.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from collections import OrderedDict

import abc
import logging
import threading

from django.utils import six

from server.db import auto_close_old_connections
from server.jobs.base import Job
from server.processing_config import load_preconfigured_choice, load_processing_xml
from server.translation import TranslationLabel
from server.workflow_abilities import choice_is_available

from main import models


logger = logging.getLogger("archivematica.mcp.server.jobs.decisions")


@six.add_metaclass(abc.ABCMeta)
class DecisionJob(Job):
    """A Job that handles a workflow decision point.

    The `run` method checks if a choice has been preconfigured. If so,
    it executes as a normal job. If not, the `awaiting_decision`
    attribute is set, and the job returns itself to the package queue,
    which will mark the job as awaiting a decision.
    """

    def __init__(self, *args, **kwargs):
        super(DecisionJob, self).__init__(*args, **kwargs)

        self._awaiting_decision_event = threading.Event()

    @property
    def awaiting_decision(self):
        return self._awaiting_decision_event.is_set()

    @property
    def workflow(self):
        return self.link.workflow

    def run(self, *args, **kwargs):
        super(DecisionJob, self).run(*args, **kwargs)

        logger.info("Running %s (package %s)", self.description, self.package.uuid)
        # Reload the package, in case the path has changed
        self.package.reload()
        self.save_to_db()

        preconfigured_choice = self.get_preconfigured_choice()
        if preconfigured_choice:
            return self.decide(preconfigured_choice)
        else:
            self.mark_awaiting_decision()
            # Special case for DecisionJob; we're not ready to move to the next
            # job until a decision has been made. The queue has handling for
            # this to prevent going into a loop.
            return self

    def get_preconfigured_choice(self):
        """Check the processing XML file for a pre-selected choice.

        Returns a value for choices if found, None otherwise.
        """
        return load_preconfigured_choice(self.package.current_path, self.link.id)

    def mark_awaiting_decision(self):
        super(DecisionJob, self).mark_awaiting_decision()

        self._awaiting_decision_event.set()

    # TODO: this (global?) active agent setting isn't really the concern of
    # the job; move it elsewhere.
    @auto_close_old_connections()
    def set_active_agent(self, user_id):
        if user_id is None:
            return
        agent_id = models.UserProfile.objects.get(user_id=user_id).agent_id
        self.package.set_variable("activeAgent", agent_id, None)

    @abc.abstractmethod
    def get_choices(self):
        """Returns a dict of value: description choices."""

    @abc.abstractmethod
    def decide(self, choice):
        """Make a choice, resulting in this job being completed and the
        next one started.
        """


class NextChainDecisionJob(DecisionJob):
    """
    A type of workflow decision that determines the next chain to be executed,
    by UUID.
    """

    def get_choices(self):
        choices = OrderedDict()
        for chain_id in self.link.config["chain_choices"]:
            try:
                chain = self.workflow.get_chain(chain_id)
            except KeyError:
                continue
            if choice_is_available(self.link, chain):
                choices[chain_id] = chain["description"]

        return choices

    @auto_close_old_connections()
    def decide(self, choice):
        # TODO: fix circular imports :(
        from server.jobs import JobChain

        if choice not in self.get_choices():
            raise ValueError("{} is not one of the available choices".format(choice))

        chain = self.workflow.get_chain(choice)
        logger.info("Using user selected chain %s for link %s", chain.id, self.link.id)

        self.mark_complete()

        job_chain = JobChain(self.package, chain, self.workflow)
        return next(job_chain, None)


class OutputDecisionJob(DecisionJob):
    """A job that handles a workflow decision point, with choices based on script output."""

    def get_preconfigured_choice(self):
        desired_choice = load_preconfigured_choice(
            self.package.current_path, self.link.id
        )
        if desired_choice and self.job_chain.generated_choices:
            for key, data in self.job_chain.generated_choices.items():
                if data["uri"] == desired_choice:
                    return data["uri"]

        return None

    def get_choices(self):
        choices = OrderedDict()

        if self.job_chain.generated_choices:
            for _, value in self.job_chain.generated_choices.items():
                choices[value["uri"]] = TranslationLabel(value["description"])

        return choices

    @auto_close_old_connections()
    def decide(self, choice):
        if choice not in self.get_choices():
            raise ValueError("{} is not one of the available choices".format(choice))

        # Pass the choice to the next job. This case is only used to select
        # an AIP store URI, and the value of execute (script_name here) is a
        # replacement string (e.g. %AIPsStore%)
        self.job_chain.context[self.link.config["execute"]] = choice
        self.mark_complete()

        return next(self.job_chain, None)


class UpdateContextDecisionJob(DecisionJob):
    """A job that updates the job chain context based on a user choice."""

    # TODO: This type of job is mostly copied from the previous
    # linkTaskManagerReplacementDicFromChoice, and it seems to have multiple
    # ways of executing. It could use some cleanup.

    # Maps decision point UUIDs and decision UUIDs to their "canonical"
    # equivalents. This is useful for when there are multiple decision points which
    # are effectively identical and a preconfigured decision for one should hold for
    # all of the others as well. For example, there are 5 "Assign UUIDs to
    # directories?" decision points and making a processing config decision for the
    # designated canonical one, in this case
    # 'bd899573-694e-4d33-8c9b-df0af802437d', should result in that decision taking
    # effect for all of the others as well. This allows that.
    # TODO: this should be defined in the workflow, not hardcoded here
    CHOICE_MAPPING = {
        # Decision point "Assign UUIDs to directories?"
        "8882bad4-561c-4126-89c9-f7f0c083d5d7": "bd899573-694e-4d33-8c9b-df0af802437d",
        "e10a31c3-56df-4986-af7e-2794ddfe8686": "bd899573-694e-4d33-8c9b-df0af802437d",
        "d6f6f5db-4cc2-4652-9283-9ec6a6d181e5": "bd899573-694e-4d33-8c9b-df0af802437d",
        "1563f22f-f5f7-4dfe-a926-6ab50d408832": "bd899573-694e-4d33-8c9b-df0af802437d",
        # Decision "Yes" (for "Assign UUIDs to directories?")
        "7e4cf404-e62d-4dc2-8d81-6141e390f66f": "2dc3f487-e4b0-4e07-a4b3-6216ed24ca14",
        "2732a043-b197-4cbc-81ab-4e2bee9b74d3": "2dc3f487-e4b0-4e07-a4b3-6216ed24ca14",
        "aa793efa-1b62-498c-8f92-cab187a99a2a": "2dc3f487-e4b0-4e07-a4b3-6216ed24ca14",
        "efd98ddb-80a6-4206-80bf-81bf00f84416": "2dc3f487-e4b0-4e07-a4b3-6216ed24ca14",
        # Decision "No" (for "Assign UUIDs to directories?")
        "0053c670-3e61-4a3e-a188-3a2dd1eda426": "891f60d0-1ba8-48d3-b39e-dd0934635d29",
        "8e93e523-86bb-47e1-a03a-4b33e13f8c5e": "891f60d0-1ba8-48d3-b39e-dd0934635d29",
        "6dfbeff8-c6b1-435b-833a-ed764229d413": "891f60d0-1ba8-48d3-b39e-dd0934635d29",
        "dc0ee6b6-ed5f-42a3-bc8f-c9c7ead03ed1": "891f60d0-1ba8-48d3-b39e-dd0934635d29",
    }

    @auto_close_old_connections()
    def run(self, *args, **kwargs):
        # Intentionally don't call super() here
        logger.info("Running %s (package %s)", self.description, self.package.uuid)
        # Reload the package, in case the path has changed
        self.package.reload()
        self.save_to_db()

        # TODO: split this out? Workflow items with no replacements configured
        # seems like a different case.
        dashboard_settings = self._get_dashboard_setting_choice()
        if dashboard_settings and not self.link.config["replacements"]:
            self.job_chain.context.update(dashboard_settings)
            self.mark_complete()
            return next(self.job_chain, None)

        preconfigured_context = self.load_preconfigured_context()
        if preconfigured_context:
            logger.debug(
                "Job %s got preconfigured context %s", self.uuid, preconfigured_context
            )
            self.job_chain.context.update(preconfigured_context)
            self.mark_complete()
            return next(self.job_chain, None)
        else:
            self.mark_awaiting_decision()
            return self

    @auto_close_old_connections()
    def _get_dashboard_setting_choice(self):
        """Load settings associated to this task into dictionary.

        The model used (``DashboardSetting``) is a shared model.
        """
        try:
            link = self.workflow.get_link(self.link["fallback_link_id"])
        except KeyError:
            return None

        execute = link.config["execute"]
        if not execute:
            return None

        return self._format_items(models.DashboardSetting.objects.get_dict(execute))

    def _format_items(self, items):
        """Wrap replacement items with the ``%`` wildcard character."""
        return {"%{}%".format(key): value for key, value in six.iteritems(items)}

    def load_preconfigured_context(self):
        normalized_choice_id = self.CHOICE_MAPPING.get(self.link.id, self.link.id)

        processing_xml = load_processing_xml(self.package.current_path)
        if processing_xml is not None:
            for preconfiguredChoice in processing_xml.findall(".//preconfiguredChoice"):
                if preconfiguredChoice.find("appliesTo").text == normalized_choice_id:
                    desired_choice = preconfiguredChoice.find("goToChain").text
                    desired_choice = self.CHOICE_MAPPING.get(
                        desired_choice, desired_choice
                    )

                    try:
                        link = self.workflow.get_link(normalized_choice_id)
                    except KeyError:
                        return None

                    for replacement in link.config["replacements"]:
                        if replacement["id"] == desired_choice:
                            # In our JSON-encoded document, the items in
                            # the replacements are not wrapped, do it here.
                            # Needed by ReplacementDict.
                            return self._format_items(replacement["items"])

        return None

    def get_choices(self):
        choices = OrderedDict()
        # TODO: this is kind of an odd side effect here; refactor
        self.choice_items = []

        for index, item in enumerate(self.link.config["replacements"]):
            # item description is already translated in workflow
            choices[six.text_type(index)] = item["description"]
            self.choice_items.append(self._format_items(item["items"]))

        return choices

    @auto_close_old_connections()
    def decide(self, choice, user_id=None):
        # TODO: DRY with sibling classes
        if choice not in self.get_choices():
            raise ValueError("{} is not one of the available choices".format(choice))

        choice_index = int(choice)
        items = self.choice_items[choice_index]

        self.job_chain.context.update(items)
        self.mark_complete()

        return next(self.job_chain, None)

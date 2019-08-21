# -*- coding: utf-8 -*-
"""
Jobs handling user decisions.
"""
from __future__ import unicode_literals

import logging
import os

from lxml import etree
from django.conf import settings
from django.utils import six

from server.db import auto_close_old_connections
from server.jobs.base import Job
from server.queues import decision_queue
from server.workflow_decisions import (
    NextChainDecision,
    OutputDecision,
    UpdateContextDecision,
)

from main import models


logger = logging.getLogger("archivematica.mcp.server.jobs.decisions")


class DecisionJob(Job):
    """Job that handles a workflow decision point.
    """

    @property
    def decision_class(self):
        raise NotImplementedError

    @property
    def workflow(self):
        return self.link.workflow

    @property
    def processing_file_path(self):
        return os.path.join(self.package.current_path, settings.PROCESSING_XML_FILE)

    def run(self, *args, **kwargs):
        super(DecisionJob, self).run(*args, **kwargs)

        decision = self.decision_class(self)

        preconfigured_choice = self.load_preconfigured_choice()
        if preconfigured_choice:
            decision.decide(preconfigured_choice)
        else:
            self.mark_awaiting_decision()
            decision_queue.put(self, decision)

        return self

    def load_preconfigured_choice(self):
        """Check the processing XML file for a pre-selected choice.

        Returns a value for choices if found, None otherwise.
        """
        raise NotImplementedError

    def load_processing_xml(self):
        if not os.path.isfile(self.processing_file_path):
            return None

        try:
            tree = etree.parse(self.processing_file_path)
        except etree.LxmlError:
            logger.warning(
                "Error parsing xml at %s for pre-configured choice",
                self.processing_file_path,
                exc_info=True,
            )
            return None

        return tree.getroot()


class NextChainDecisionJob(DecisionJob):
    """Job that decides on the next chain to be executed."""

    @property
    def decision_class(self):
        return NextChainDecision

    def load_preconfigured_choice(self):
        choice = None

        processing_xml = self.load_processing_xml()
        if processing_xml is not None:
            for preconfigured_choice in processing_xml.findall(
                ".//preconfiguredChoice"
            ):
                if preconfigured_choice.find("appliesTo").text == self.link.id:
                    choice = preconfigured_choice.find("goToChain").text

        return choice


class OutputDecisionJob(DecisionJob):
    """A job that handles a workflow decision point, with choices based on script output.
    """

    @property
    def decision_class(self):
        return OutputDecision

    def load_preconfigured_choice(self):
        processing_xml = self.load_processing_xml()
        if processing_xml is not None:
            for choice in processing_xml.findall(".//preconfiguredChoice"):
                # Find the choice whose text matches this link's description
                if choice.find("appliesTo").text == self.link.id:
                    # Search self.choices for desired choice, return index of
                    # matching choice
                    desired_choice = choice.find("goToChain").text

                    if self.job_chain.generated_choices:
                        for key, data in self.job_chain.generated_choices.items():
                            if data["uri"] == desired_choice:
                                return data["uri"]

        return None


class UpdateContextDecisionJob(DecisionJob):
    """A job that updates the job chain context based on a user choice.
    """

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

    @property
    def decision_class(self):
        return UpdateContextDecision

    def run(self, *args, **kwargs):
        # Skip the parent class here, and run Job's run method
        # TODO: clean this up
        super(DecisionJob, self).run(*args, **kwargs)

        # TODO: split this out? Workflow items with no replacements configured
        # seems like a different case.
        dashboard_settings = self._get_dashboard_setting_choice()
        if dashboard_settings and not self.config["replacements"]:
            self.job_chain.update(dashboard_settings)
            self.mark_complete()
            return self

        preconfigured_context = self.load_preconfigured_context()
        if preconfigured_context:
            self.job_chain.context.update(preconfigured_context)
            self.mark_complete()
        else:
            decision = self.decision_class(self)
            decision_queue.put(self, decision)
            self.mark_awaiting_decision()

        return self

    @auto_close_old_connections
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

        processing_xml = self.load_processing_xml()
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

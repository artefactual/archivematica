from __future__ import unicode_literals

import ast
import logging
import os
import threading
import uuid

import lxml.etree as etree
from django.conf import settings
from django.utils import six

from main import models

from db import auto_close_old_connections
from job import JobChain
from scheduler import package_scheduler
from translation import TranslationLabel
from workflow_abilities import choice_is_available


logger = logging.getLogger("archivematica.mcp.server")
# Global shared state. TODO: cleanup
choices_available = {}
choices_available_lock = threading.Lock()


def _escape_for_command_line(value):
    # escape slashes, quotes, backticks
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    value = value.replace("`", "\`")

    return value


class BaseLinkExecutor(object):
    """
    Base class for link executors, which handle the execution of workflow links.
    """

    def __init__(self, job, unit):
        self.job = job
        self.unit = unit
        self.uuid = uuid.uuid4()

    @property
    def job_chain(self):
        return self.job.job_chain

    @property
    def link(self):
        return self.job.link

    @property
    def config(self):
        return self.link.config

    @property
    def workflow(self):
        return self.job.job_chain.workflow


class ClientScriptLinkExecutor(BaseLinkExecutor):
    """Base class for link executors that run client scripts.
    """

    capture_task_output = False

    def __init__(self, *args, **kwargs):
        super(ClientScriptLinkExecutor, self).__init__(*args, **kwargs)

        # Cache unit (SIP/Transfer) replacement values
        self.command_replacements = self.unit.get_replacement_mapping(
            filter_subdir_path=self.config.get("filter_subdir")
        )
        if self.job_chain.context is not None:
            self.command_replacements.update(self.job_chain.context)

    @property
    def script_name(self):
        return self.config.get("execute")

    @property
    def arguments(self):
        return self.config.get("arguments")

    @property
    def stdout_file(self):
        return self.config.get("stdout_file")

    @property
    def stderr_file(self):
        return self.config.get("stderr_file")

    def replace_values(self, command, replacements):
        if command is None:
            return None

        for key, replacement in six.iteritems(replacements):
            escaped_replacement = _escape_for_command_line(replacement)
            command = command.replace(key, escaped_replacement)

        return command

    def execute(self):
        arguments = self.replace_values(self.arguments, self.command_replacements)
        stdout_file = self.replace_values(self.stdout_file, self.command_replacements)
        stderr_file = self.replace_values(self.stderr_file, self.command_replacements)

        self.job.add_task(
            arguments,
            stdout_file,
            stderr_file,
            self.command_replacements,
            wants_output=self.capture_task_output,
        )


class DirectoryLinkExecutor(ClientScriptLinkExecutor):
    """
    Handles links that pass a directory (e.g. "objects/") to mcp client for execution.
    """


class FileLinkExecutor(ClientScriptLinkExecutor):
    """
    Handles links that pass individual files to mcp client for execution.
    """

    @auto_close_old_connections
    def execute(self):
        # TODO simplify / break up this method
        filter_file_end = self.config.get("filter_file_end", "")
        filter_file_start = self.config.get("filter_file_start", "")
        filter_subdir = self.config.get("filter_subdir", "")

        # Check if filterSubDir has been overridden for this Transfer/SIP
        # TODO: just pass the correct subdir via config
        try:
            var = models.UnitVariable.objects.get(
                unittype=self.unit.UNIT_VARIABLE_TYPE,
                unituuid=self.unit.uuid,
                variable=self.script_name,
            )
        except (
            models.UnitVariable.DoesNotExist,
            models.UnitVariable.MultipleObjectsReturned,
        ):
            var = None

        if var:
            try:
                script_override = ast.literal_eval(var.variablevalue)
            except (SyntaxError, ValueError):
                pass
            else:
                filter_subdir = script_override.get("filterSubDir")

        for file_replacements in self.unit.files(
            filter_filename_start=filter_file_start,
            filter_filename_end=filter_file_end,
            filter_subdir=filter_subdir,
        ):
            # File replacement values take priority
            command_replacements = self.command_replacements.copy()
            command_replacements.update(file_replacements)

            arguments = self.replace_values(self.arguments, command_replacements)
            stdout_file = self.replace_values(self.stdout_file, command_replacements)
            stderr_file = self.replace_values(self.stderr_file, command_replacements)

            self.job.add_task(arguments, stdout_file, stderr_file, command_replacements)


class GetJobOutputLinkExecutor(ClientScriptLinkExecutor):
    """Gets output from mcp client, and passes the result to the next job.
    """

    capture_task_output = True

    def execute(self):
        super(GetJobOutputLinkExecutor, self).execute()

        self.job.add_callback(self.handle_job_complete)

    def handle_job_complete(self, job):
        try:
            # Load the "first" item from a dict
            stdout = six.next(six.itervalues(job.tasks)).stdout
        except KeyError:
            stdout = None

        logger.debug("stdout emitted by client: %s", stdout)

        try:
            choices = ast.literal_eval(stdout)
        except (ValueError, SyntaxError):
            logger.exception("Unable to parse output %s", stdout)
            choices = {}

        # Store on chain for next job
        self.job_chain.generated_choices = choices


class ChoiceLinkExecutor(BaseLinkExecutor):
    """Used to get a user selection, from a list of chains, to process"""

    def __init__(self, *args, **kwargs):
        super(ChoiceLinkExecutor, self).__init__(*args, **kwargs)

        self.choices = []
        self._populate_choices()

    @property
    def processing_file_path(self):
        return os.path.join(self.unit.current_path, settings.PROCESSING_XML_FILE)

    def execute(self):
        chain_id = self.load_choice_from_xml()
        if chain_id is not None:
            self.job.mark_complete()
            chain = self.workflow.get_chain(chain_id)
            job_chain = JobChain(self.unit, chain, self.workflow)
            package_scheduler.schedule_job_chain(job_chain)
        else:
            with choices_available_lock:
                choices_available[str(self.job.uuid)] = self
            self.job.mark_awaiting_decision()

    def _populate_choices(self):
        for chain_id in self.link.config["chain_choices"]:
            try:
                chain = self.workflow.get_chain(chain_id)
            except KeyError:
                continue
            if choice_is_available(self.link, chain, settings):
                self.choices.append((chain_id, chain["description"], None))

    def load_choice_from_xml(self):
        choice = None

        if os.path.isfile(self.processing_file_path):
            tree = etree.parse(self.processing_file_path)
            root = tree.getroot()
            for preconfigured_choice in root.findall(".//preconfiguredChoice"):
                if preconfigured_choice.find("appliesTo").text == self.link.id:
                    choice = preconfigured_choice.find("goToChain").text

        return choice

    def xmlify(self):
        """Returns an etree XML representation of the choices available."""
        ret = etree.Element("choicesAvailableForUnit")
        etree.SubElement(ret, "UUID").text = str(self.job.uuid)
        ret.append(self.unit.xmlify())
        choices = etree.SubElement(ret, "choices")
        for id_, description, __ in self.choices:
            choice = etree.SubElement(choices, "choice")
            etree.SubElement(choice, "chainAvailable").text = six.text_type(id_)
            etree.SubElement(choice, "description").text = six.text_type(description)

        return ret

    @auto_close_old_connections
    def proceed_with_choice(self, choice, user_id=None):
        """
        `choice` is a chain UUID here"""
        if user_id is not None:
            agent_id = models.UserProfile.objects.get(user_id=user_id).agent_id
            self.unit.set_variable("activeAgent", agent_id, None)

        if choice not in [option[0] for option in self.choices]:
            raise ValueError("{} is not one of the available choices".format(choice))

        with choices_available_lock:
            try:
                del choices_available[str(self.job.uuid)]
            except KeyError:
                pass
        self.job.mark_complete()

        logger.info("Using user selected chain %s for link %s", choice, self.link.id)
        chain = self.workflow.get_chain(choice)

        job_chain = JobChain(self.unit, chain, self.workflow)
        package_scheduler.schedule_job_chain(job_chain)


class ChoiceFromOutputLinkExecutor(ChoiceLinkExecutor):
    def execute(self):
        index = self.load_choice_from_xml()
        if index is not None:
            self.job.mark_complete()
            self.proceed_with_choice(index, user_id=None)
        else:
            with choices_available_lock:
                choices_available[str(self.job.uuid)] = self
            self.job.mark_awaiting_decision()

    def load_choice_from_xml(self):
        """ Check the processing XML file for a pre-selected choice.

        Returns an index for self.choices if found, None otherwise. """
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

        root = tree.getroot()

        for choice in root.findall(".//preconfiguredChoice"):
            # Find the choice whose text matches this link's description
            if choice.find("appliesTo").text == self.link.id:
                # Search self.choices for desired choice, return index of
                # matching choice
                desired_choice = choice.find("goToChain").text
                for choice in self.choices:
                    index, description, replace_dict = choice
                    if desired_choice == description or desired_choice in replace_dict:
                        return index

        return None

    def _populate_choices(self):
        if self.job_chain.generated_choices is None:
            return

        for index, (_, value) in enumerate(self.job_chain.generated_choices.items()):
            description = TranslationLabel(value["description"])
            self.choices.append((index, description, value["uri"]))

    @auto_close_old_connections
    def proceed_with_choice(self, choice, user_id=None):
        # TODO: DRY this method w/ parent
        if user_id is not None:
            agent_id = models.UserProfile.objects.get(user_id=user_id).agent_id
            self.unit.set_variable("activeAgent", agent_id, None)

        choice = int(choice)
        try:
            context_value = self.choices[choice][2]
        except (KeyError, IndexError):
            raise ValueError("{} is not one of the available choices".format(choice))

        with choices_available_lock:
            try:
                del choices_available[str(self.job.uuid)]
            except KeyError:
                pass
        self.job.mark_complete()

        # Pass the choice to the next job. This case is only used to select
        # an AIP store URI, and the value of execute (script_name here) is a
        # replacement string (e.g. %AIPsStore%)
        self.job_chain.context[self.config["execute"]] = context_value

        self.job.exit_code = 0


class ChoiceFromDashboardSettingLinkExecutor(ChoiceLinkExecutor):

    # Maps decision point UUIDs and decision UUIDs to their "canonical"
    # equivalents. This is useful for when there are multiple decision points which
    # are effectively identical and a preconfigured decision for one should hold for
    # all of the others as well. For example, there are 5 "Assign UUIDs to
    # directories?" decision points and making a processing config decision for the
    # designated canonical one, in this case
    # 'bd899573-694e-4d33-8c9b-df0af802437d', should result in that decision taking
    # effect for all of the others as well. This allows that.
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

    def execute(self):
        # There are MicroServiceChoiceReplacementDic links with no
        # replacements (``self.choices`` has zero elements at this point). This
        # is true for the following chain links:
        #
        #   - ``Choose config for AtoM DIP upload``
        #   - ``Choose Config for ArchivesSpace DIP Upload``
        #
        # The only purpose of these links is to  load settings from the
        # Dashboard configuration store (``DashboardSetting``), e.g.
        # connection details or credentials that are needed to perform the
        # upload of the DIP to the remote system.
        #
        # Once the settings are loaded, we proceed with the next chain link
        # automatically instead of prompting the user with a single choice
        # which was considered inconvenient and confusing. In the future, it
        # should be possible to prompt the user only if we want to have the
        # user decide between multiple configurations, e.g. more than one
        # AtoM instance is available and the user wants to decide which one is
        # going to be used.
        dashboard_settings = self._get_dashboard_setting_choice()
        if dashboard_settings and not self.choices:
            logger.debug("Found Dashboard settings for this task, proceed.")
            for key, value in dashboard_settings.items():
                key = "%%{}%%".format(key)
                self.job_chain.context[key] = value

            self.job.exit_code = 0
            return

        replacements = self.load_choice_from_xml()
        if replacements is not None:
            self.job.mark_complete()
            self.job_chain.context.update(replacements)
            self.job.exit_code = 0
        else:
            with choices_available_lock:
                choices_available[str(self.job.uuid)] = self
            self.job.mark_awaiting_decision()

    def _populate_choices(self):
        for index, item in enumerate(self.config["replacements"]):
            self.choices.append(
                (index, item["description"], self._format_items(item["items"]))
            )

    @auto_close_old_connections
    def _get_dashboard_setting_choice(self):
        """Load settings associated to this task into a ``ReplacementDict``.

        The model used (``DashboardSetting``) is a shared model.
        """
        try:
            link = self.workflow.get_link(self.link["fallback_link_id"])
        except KeyError:
            return None

        execute = link.config["execute"]
        if not execute:
            return None

        return models.DashboardSetting.objects.get_dict(execute)

    def _format_items(self, items):
        """Wrap replacement items with the ``%`` wildcard character."""
        return {"%{}%".format(key): value for key, value in items.items()}

    def load_choice_from_xml(self):
        # TODO: cleanup this method
        ret = None
        xmlFilePath = os.path.join(self.unit.current_path, settings.PROCESSING_XML_FILE)

        if os.path.isfile(xmlFilePath):
            # For a list of items with pks:
            # SELECT TasksConfigs.description, choiceAvailableAtLink, ' ' AS 'SPACE', MicroServiceChains.description, chainAvailable FROM MicroServiceChainChoice Join MicroServiceChains on MicroServiceChainChoice.chainAvailable = MicroServiceChains.pk Join MicroServiceChainLinks on MicroServiceChainLinks.pk = MicroServiceChainChoice.choiceAvailableAtLink Join TasksConfigs on TasksConfigs.pk = MicroServiceChainLinks.currentTask ORDER BY choiceAvailableAtLink desc;
            this_choice_point = self.CHOICE_MAPPING.get(self.link.id, self.link.id)
            tree = etree.parse(xmlFilePath)
            root = tree.getroot()
            for preconfiguredChoice in root.findall(".//preconfiguredChoice"):
                if preconfiguredChoice.find("appliesTo").text == this_choice_point:
                    desiredChoice = preconfiguredChoice.find("goToChain").text
                    desiredChoice = self.CHOICE_MAPPING.get(
                        desiredChoice, desiredChoice
                    )

                    try:
                        link = self.workflow.get_link(this_choice_point)
                    except KeyError:
                        return
                    for replacement in link.config["replacements"]:
                        if replacement["id"] == desiredChoice:
                            # In our JSON-encoded document, the items in
                            # the replacements are not wrapped, do it here.
                            # Needed by ReplacementDict.
                            ret = self._format_items(replacement["items"])
                            break
                    else:
                        return

        return ret

    @auto_close_old_connections
    def proceed_with_choice(self, choice, user_id=None):
        # TODO: DRY this method w/ parent
        if user_id is not None:
            agent_id = models.UserProfile.objects.get(user_id=user_id).agent_id
            self.unit.set_variable("activeAgent", agent_id, None)

        choice = int(choice)

        try:
            _, _, items = self.choices[choice]
        except IndexError:
            raise ValueError("{} is not one of the available choices".format(choice))

        with choices_available_lock:
            try:
                del choices_available[str(self.job.uuid)]
            except KeyError:
                pass
        self.job.mark_complete()

        self.job_chain.context.update(items)
        self.job.exit_code = 0


class GetUnitVarLinkExecutor(BaseLinkExecutor):
    """Gets the next link from a unit variable, and proceed to that link."""

    @auto_close_old_connections
    def execute(self):
        try:
            unitvar = models.UnitVariable.objects.get(
                unittype=self.unit.UNIT_VARIABLE_TYPE,
                unituuid=self.unit.uuid,
                variable=self.link.config["variable"],
            )
        except models.UnitVariable.DoesNotExist:
            link_id = self.link.config["chain_id"]
        else:
            link_id = unitvar.microservicechainlink

        try:
            link = self.workflow.get_link(link_id)
        except KeyError:
            raise ValueError(
                "Failed to find workflow link {} (set in unit variable)".format(link_id)
            )

        self.job.exit_code = 0
        self.job_chain.next_link = link


class SetUnitVarLinkExecutor(BaseLinkExecutor):
    """Sets a unit variable, and proceed to the next link."""

    def execute(self):
        var_name = self.config.get("variable")
        var_value = self.config.get("variable_value")
        chain_id = self.config.get("chain_id")

        self.unit.set_variable(var_name, var_value, chain_id)
        self.job.exit_code = 0

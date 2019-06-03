#!/usr/bin/env python2
"""Runs zero or more FPR validation commands against the provided file and
returns an exit code. May also print to stdout, generate an Event model in the
db, and/or write command-specific stdout to disk.

If a format has no defined validation commands, no command is run.

`concurrent_instances` is intentionally unused in order to mitigate a problem
where MediaConch (one of the default validation tools) may block forever if
there are more than one instance running in the same machine. See
https://github.com/archivematica/Issues/issues/44 for more details.

Arguments:
    [FILE_PATH] [FILE_UUID] [SIP_UUID] [SHARED_PATH] [FILE_TYPE]

"""

import ast
import os
from pprint import pformat
import sys

import django
from django.db import transaction

django.setup()
from fpr.models import FPRule, FormatVersion
from main.models import Derivation, File, SIP

from custom_handlers import get_script_logger
import databaseFunctions
from executeOrRunSubProcess import executeOrRun
from dicts import replace_string_values

from django.conf import settings as mcpclient_settings
from lib import setup_dicts


SUCCESS_CODE = 0
FAIL_CODE = 1
NOT_DERIVATIVE_CODE = 0
NO_RULES_CODE = 0
DERIVATIVE_TYPES = ("preservation", "access")


def main(job, file_path, file_uuid, sip_uuid, shared_path, file_type):
    setup_dicts(mcpclient_settings)

    validator = Validator(job, file_path, file_uuid, sip_uuid, shared_path, file_type)
    return validator.validate()


logger = get_script_logger("archivematica.mcp.client.validateFile")


class Validator(object):
    """A validator validates a file, during transfer or ingest, using FPR
    config.

    If the file is an access derivative or a preservation derivative, the
    ``file_type`` will be 'access' or 'preservation', respectively. This will
    trigger specialized behaviour. The default (an original) behaviour
    corresponds to a ``file_type`` of 'original'.

    Usage: initialize on a file and then call the ``validate`` method to
    determine whether a given file conforms to a given specification.
    """

    def __init__(self, job, file_path, file_uuid, sip_uuid, shared_path, file_type):
        self.job = job
        self.file_path = file_path
        self.file_uuid = file_uuid
        self.sip_uuid = sip_uuid
        self.shared_path = shared_path
        self.file_type = file_type
        self.purpose = "validation"
        self._sip_logs_dir = None
        self._sip_pres_val_dir = None

    def validate(self):
        """Validate the file identified by ``self.file_uuid``, using all rules
        that apply. Return an error code (1 or 0), which the script as a whole
        also returns. Side effects include printing to stdout/stderr (which
        gets displayed in the dashboard), creating Event models in the db, and
        saving log/stdout files within the unit's (Transfer/SIP) directory
        structure.
        """
        if self.file_type in DERIVATIVE_TYPES and not self._file_is_derivative():
            self.job.print_output(
                "File {uuid} {not_derivative_msg}; not validating.".format(
                    uuid=self.file_uuid, not_derivative_msg=self._not_derivative_msg()
                )
            )
            return NOT_DERIVATIVE_CODE
        rules = self._get_rules()
        if not rules:
            return NO_RULES_CODE
        rule_outputs = []
        for rule in rules:
            rule_outputs.append(self._execute_rule_command(rule))
        if "failed" in rule_outputs:
            return FAIL_CODE
        return SUCCESS_CODE

    def _get_rules(self):
        """Return all FPR rules that apply to files of this type."""
        try:
            fmt = FormatVersion.active.get(fileformatversion__file_uuid=self.file_uuid)
        except FormatVersion.DoesNotExist:
            rules = fmt = None
        if fmt:
            rules = FPRule.active.filter(format=fmt.uuid, purpose=self.purpose)
        # Check default rules.
        if not rules:
            rules = FPRule.active.filter(purpose="default_{}".format(self.purpose))
        return rules

    def _execute_rule_command(self, rule):
        """Run the command against the file and return either 'passed' or
        'failed'. If the command errors or determines that the file is invalid,
        return 'failed'. Non-errors will result in the creation of an Event
        model in the db. Preservation derivative validation will result in the
        stdout from the command being saved to disk within the unit (i.e., SIP).
        """
        result = "passed"
        if rule.command.script_type in ("bashScript", "command"):
            command_to_execute = replace_string_values(
                rule.command.command,
                file_=self.file_uuid,
                sip=self.sip_uuid,
                type_="file",
            )
            args = []
        else:
            command_to_execute = rule.command.command
            args = [self.file_path]
        self.job.print_output("Running", rule.command.description)
        exitstatus, stdout, stderr = executeOrRun(
            type=rule.command.script_type,
            text=command_to_execute,
            printing=False,
            arguments=args,
        )
        if exitstatus != 0:
            self.job.print_error(
                "Command {description} failed with exit status {status};"
                " stderr:".format(
                    description=rule.command.description, status=exitstatus
                )
            )
            return "failed"
        # Parse output and generate an Event
        # TODO: Evaluating a python string from a user-definable script seems
        # insecure practice; should be JSON.
        output = ast.literal_eval(stdout)
        event_detail = (
            'program="{tool.description}";'
            ' version="{tool.version}"'.format(tool=rule.command.tool)
        )
        # If the FPR command has not errored but the actual validation
        # determined that the file is not valid, then we want to both create a
        # validation event in the db and set ``failed`` to ``True`` because we
        # want the micro-service in the dashboard GUI to indicate "Failed".
        # NOTE: this requires that the stdout of all validation FPR commands be
        # a dict (preferably a JSON object) with an ``eventOutcomeInformation``
        # boolean attribute.
        if output.get("eventOutcomeInformation") == "pass":
            self.job.print_output(
                'Command "{}" was successful'.format(rule.command.description)
            )
        elif output.get("eventOutcomeInformation") == "partial pass":
            self.job.print_output(
                'Command "{}" was partially successful'.format(rule.command.description)
            )
        else:
            self.job.pyprint(
                "Command {cmd_description} indicated failure with this"
                " output:\n\n{output}".format(
                    cmd_description=rule.command.description, output=pformat(stdout)
                ),
                file=sys.stderr,
            )
            result = "failed"
        if self.file_type == "preservation":
            self._save_stdout_to_logs_dir(output)
        self.job.print_output(
            "Creating {purpose} event for {file_path} ({file_uuid})".format(
                purpose=self.purpose, file_path=self.file_path, file_uuid=self.file_uuid
            )
        )
        databaseFunctions.insertIntoEvents(
            fileUUID=self.file_uuid,
            eventType="validation",  # From PREMIS controlled vocab.
            eventDetail=event_detail,
            eventOutcome=output.get("eventOutcomeInformation"),
            eventOutcomeDetailNote=output.get("eventOutcomeDetailNote"),
        )
        return result

    def _save_stdout_to_logs_dir(self, output):
        """Save the validation command's output from validating the file to a
        file at logs/implementationChecks/<input_filename>.xml in the SIP.
        ``output`` is expected to be a dict with a ``stdout`` key.
        """
        stdout = output.get("stdout")
        if stdout and self.sip_pres_val_dir:
            filename = os.path.basename(self.file_path)
            stdout_path = os.path.join(self.sip_pres_val_dir, "{}.xml".format(filename))
            with open(stdout_path, "w") as f:
                f.write(stdout)

    def _file_is_derivative(self):
        """Return ``True`` if the file we are validating is a derivative, i.e.,
        a modified version created for preservation or access.
        """
        if self.file_type == "preservation":
            return self._file_is_preservation_derivative()
        return self._file_is_access_derivative()

    def _file_is_preservation_derivative(self):
        """Returns ``True`` if the file with UUID ``self.file_uuid`` is a
        preservation derivative.
        """
        try:
            Derivation.objects.get(
                derived_file__uuid=self.file_uuid, event__event_type="normalization"
            )
            return True
        except Derivation.DoesNotExist:
            return False

    def _file_is_access_derivative(self):
        """Returns ``True`` if the file with UUID ``self.file_uuid`` is an
        access derivative.
        """
        try:
            file_model = File.objects.get(uuid=self.file_uuid)
            if file_model.filegrpuse == "access":
                try:
                    Derivation.objects.get(
                        derived_file__uuid=self.file_uuid, event__isnull=True
                    )
                    return True
                except Derivation.DoesNotExist:
                    return False
            else:
                return False
        except File.DoesNotExist:
            return False

    def _not_derivative_msg(self):
        """Return the message to print if the file is not a derivative."""
        if self.file_type == "preservation":
            return "is not a preservation derivative"
        return "is not an access derivative"

    @property
    def sip_logs_dir(self):
        """Return the absolute path the logs/ directory of the SIP that the
        target file is a part of.
        """
        if self._sip_logs_dir:
            return self._sip_logs_dir
        try:
            sip_model = SIP.objects.get(uuid=self.sip_uuid)
        except (SIP.DoesNotExist, SIP.MultipleObjectsReturned):
            self.job.print_error(
                "Warning: unable to retrieve SIP model corresponding to SIP"
                " UUID {}".format(self.sip_uuid)
            )
            return None
        else:
            sip_path = sip_model.currentpath.replace(
                "%sharedPath%", self.shared_path, 1
            )
            logs_dir = os.path.join(sip_path, "logs")
            if os.path.isdir(logs_dir):
                self._sip_logs_dir = logs_dir
                return logs_dir
            self.job.print_error(
                "Warning: unable to find a logs/ directory in the SIP"
                " with UUID {}".format(self.sip_uuid)
            )
            return None

    @property
    def sip_pres_val_dir(self):
        """Return the full path to the directory within the SIP where stdout
        from perservation derivative validation output should be written to
        disk.
        TODO: the leaf dir of the path return is 'implementationChecks' because
        this functionality was implemented with MediaConch implementation
        checks in mind. However, if saving command stdout to the logs/ dir of a
        SIP is needed for validation based on other tools, this directory name
        may need to be changed in a context-sensitive way.
        """
        if self._sip_pres_val_dir:
            return self._sip_pres_val_dir
        if self.sip_logs_dir:
            _sip_pres_val_dir = os.path.join(self.sip_logs_dir, "implementationChecks")
            if os.path.isdir(_sip_pres_val_dir):
                self._sip_pres_val_dir = _sip_pres_val_dir
            else:
                try:
                    os.makedirs(_sip_pres_val_dir)
                except OSError:
                    pass
                else:
                    self._sip_pres_val_dir = _sip_pres_val_dir
        return self._sip_pres_val_dir


def _get_shared_path(argv):
    try:
        return argv[4]
    except IndexError:
        return None


def _get_file_type(argv):
    try:
        return argv[5]
    except IndexError:
        return "original"


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                file_path = job.args[1]
                file_uuid = job.args[2]
                sip_uuid = job.args[3]
                shared_path = _get_shared_path(job.args)
                file_type = _get_file_type(job.args)
                job.set_status(
                    main(job, file_path, file_uuid, sip_uuid, shared_path, file_type)
                )

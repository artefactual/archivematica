#!/usr/bin/env python
"""Runs zero or more FPR policy check against the provided file and returns an
exit code. May also print to stdout, generate an Event models in the db,
and/or write command-specific stdout to disk.

If a format has no defined policy check commands, no command is run.

Arguments::

    [FILE_PATH] [FILE_UUID] [SIP_UUID] [SHARED_PATH] [FILE_TYPE]

"""

import json
import os

import django
from custom_handlers import get_script_logger

django.setup()
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import databaseFunctions
from client.job import Job
from dicts import replace_string_values
from django.conf import settings as mcpclient_settings
from django.core.exceptions import ValidationError
from django.db import transaction
from executeOrRunSubProcess import executeOrRun
from fpr.models import FormatVersion
from fpr.models import FPRule
from lib import setup_dicts
from main.models import SIP
from main.models import Derivation
from main.models import File
from main.models import Transfer

# Note that linkTaskManagerFiles.py will take the highest exit code it has seen
# from all tasks and will use that as the exit code of the job as a whole.
SUCCESS_CODE = 0
NOT_APPLICABLE_CODE = 0
FAIL_CODE = 1


def main(
    job: Job,
    file_path: str,
    file_uuid: str,
    sip_uuid: str,
    shared_path: str,
    file_type: str,
) -> int:
    """Entry point for policy checker."""
    setup_dicts(mcpclient_settings)

    policy_checker = PolicyChecker(
        job, file_path, file_uuid, sip_uuid, shared_path, file_type
    )
    return policy_checker.check()


logger = get_script_logger("archivematica.mcp.client.policyCheck")


class PolicyChecker:
    """Checks a file against one or more policies.
    Checks whether a given file conforms to all of the MediaConch policies
    that the system is configured to run against that type of file, given the
    file's format and its purpose, i.e., whether it is intended for access or
    preservation. Usage involves initializing on a file and then calling the
    ``check`` method.
    """

    def __init__(
        self,
        job: Job,
        file_path: str,
        file_uuid: Optional[str],
        sip_uuid: str,
        shared_path: str,
        file_type: str,
    ) -> None:
        """Initiate a new policy check."""
        self.job = job
        self.file_path = file_path
        self.file_uuid = file_uuid
        self.sip_uuid = sip_uuid
        self.shared_path = shared_path
        self.file_type = file_type
        self.policies_dir = self._get_policies_dir()
        self.is_manually_normalized_access_derivative = (
            self._get_is_manually_normalized_access_derivative()
        )
        self._sip_logs_dir: Optional[str] = None
        self._sip_subm_doc_dir: Optional[str] = None
        self._sip_policy_checks_dir: Optional[str] = None

    def check(self) -> int:
        """Check the file identified by ``self.file_uuid`` against any
        policy-check FPR commands that are applicable. If any fail, return a
        non-zero exit code; otherwise return ``0``.
        """
        if not self.is_manually_normalized_access_derivative:
            try:
                self.file_model = File.objects.get(uuid=self.file_uuid)
            except (File.DoesNotExist, ValidationError):
                self.job.pyprint(
                    "Not performing a policy check because there is no file"
                    f" with UUID {self.file_uuid}."
                )
                return NOT_APPLICABLE_CODE
        if not self._we_check_this_type_of_file():
            return NOT_APPLICABLE_CODE
        rules = self._get_rules()
        if not rules:
            self.job.pyprint(
                "Not performing a policy check because there are no relevant"
                " FPR rules"
            )
            return NOT_APPLICABLE_CODE
        rule_outputs = []
        for rule in rules:
            rule_outputs.append(self._execute_rule_command(rule))
        if "failed" in rule_outputs:
            return FAIL_CODE
        else:
            return SUCCESS_CODE

    purpose = "policy_check"

    def _we_check_this_type_of_file(self) -> bool:
        """Return ``True`` if this policy checker should perform a check on
        this file; ``False`` otherwise. This will depend on ``self.file_type``
        and on whether the file is an original or a preservation/access
        derivative.
        """
        if self.file_type == "original":
            # During transfer we check all files. Is this correct or are there
            # classes of file that we do not want to perform policy checks on?
            return True
        elif self.file_type == "preservation":
            if (not self._file_is_derivative()) or self._file_is_for_access():
                self.job.pyprint(
                    f"File {self.file_uuid} is not a preservation derivative; not"
                    " performing a policy check."
                )
                return False
            return True
        elif self.file_type == "access":
            if self._file_is_derivative(for_access=True) and self._file_is_for_access():
                return True
            self.job.pyprint(
                f"File {self.file_uuid} is not an access derivative; not performing"
                " a policy check."
            )
            if not self._file_is_derivative(for_access=True):
                self.job.pyprint(f"File {self.file_uuid} is not a derivative.")
            if not self._file_is_for_access():
                self.job.pyprint(f"File {self.file_uuid} is not for access.")
            return False
        else:
            return True

    def _file_is_derivative(self, for_access: bool = False) -> bool:
        """Return ``True`` if the target file is a derivative; ``False``
        otherwise.
        """
        if self.is_manually_normalized_access_derivative:
            return True
        # Access derivatives have Derivation rows with NULL event types (cf.
        # normalize.py client script).
        event_type = None if for_access else "normalization"
        try:
            Derivation.objects.get(
                derived_file__uuid=self.file_uuid, event__event_type=event_type
            )
            return True
        except (Derivation.DoesNotExist, ValidationError):
            return False

    def _get_policies_dir(self) -> str:
        return os.path.join(
            self.shared_path, "sharedMicroServiceTasksConfigs", "policies"
        )

    def _get_is_manually_normalized_access_derivative(self) -> bool:
        """Manually normalized access derivatives are never given UUIDs.
        Therefore, we need this heuristic for determining if that is what we
        are dealing with. TODO/QUESTION: will this return false positives?
        """
        if self.file_uuid == "None" and os.path.split(self.file_path)[0].endswith(
            "/DIP/objects"
        ):
            return True
        return False

    def _file_is_for_access(self) -> bool:
        """Return ``True`` if the file with UUID ``self.file_uuid`` is "for"
        access.
        """
        if (
            self.is_manually_normalized_access_derivative
            or self.file_model.filegrpuse == "access"
        ):
            return True
        return False

    def _get_manually_normalized_access_derivative_file_uuid(self) -> Optional[File]:
        """If the file-to-be-policy-checked is a manually normalized access
        derivative it will have no file UUID in the database. We therefore have
        to retrieve the UUID of the original file that was format-identified,
        i.e., the file that was in manualNormalization/access/, which we do by
        querying the database based on the original location of the file. This
        file UUID is needed so that we can get the format (PRONOM id) in order
        to retrieve the appropriate policy-check FPR rule for this type of file
        (see ``self._get_rules()``).
        """
        manually_normalized_file_name = os.path.basename(self.file_path)[37:]
        manually_normalized_file_path = f"%transferDirectory%objects/manualNormalization/access/{manually_normalized_file_name}"
        try:
            return File.objects.get(
                originallocation=manually_normalized_file_path.encode(),
                sip_id=self.sip_uuid,
            ).uuid
        except (File.DoesNotExist, File.MultipleObjectsReturned, ValidationError):
            return None

    def _get_rules(self) -> FPRule:
        """Return the FPR rules with purpose ``self.purpose`` and that apply to
        the type/format of file given as input.
        """
        file_uuid = self.file_uuid
        if self.is_manually_normalized_access_derivative:
            file_uuid = self._get_manually_normalized_access_derivative_file_uuid()
        try:
            fmt = FormatVersion.active.get(fileformatversion__file_uuid=file_uuid)
        except (FormatVersion.DoesNotExist, ValidationError):
            rules = fmt = None
        if fmt:
            rules = FPRule.active.filter(format=fmt.uuid, purpose=self.purpose)
        # Check for default rules.
        if not rules:
            rules = FPRule.active.filter(purpose=f"default_{self.purpose}")
        return rules

    def _execute_rule_command(self, rule: FPRule) -> str:
        """Execute the FPR command of FPR rule ``rule`` against the file passed
        in to this client script. The output of that command determines what we
        print to stdout and stderr, and the nature of the validation event that
        we save to the db. We also copy the MediaConch policy file to the logs/
        directory of the AIP if it has not already been copied there.
        """
        result = "passed"
        command_to_execute, args = self._get_command_to_execute(rule)
        self.job.pyprint("Running", rule.command.description)
        exitstatus, stdout, stderr = executeOrRun(
            rule.command.script_type,
            command_to_execute,
            arguments=args,
            printing=False,
            capture_output=True,
        )
        try:
            output = json.loads(stdout)
        except ValueError:
            logger.exception(
                "Unable to load an object from the malformed JSON: \n%s", stderr
            )
            raise
        if self.file_type in ("preservation", "original"):
            self._save_to_logs_dir(output)
        if exitstatus == 0:
            self.job.pyprint(
                f"Command {rule.command.description} completed with output {stdout}"
            )
        else:
            self.job.print_error(
                f"Command {rule.command.description} failed with exit status {exitstatus}; stderr:",
                stderr,
            )
            return "failed"
        event_detail = (
            f'program="{rule.command.tool.description}";'
            f' version="{rule.command.tool.version}"'
        )
        if output.get("eventOutcomeInformation") != "pass":
            self.job.print_error(
                "Command {descr} returned a non-pass outcome "
                "for the policy check;\n\noutcome: "
                "{outcome}\n\ndetails: {details}.".format(
                    descr=rule.command.description,
                    outcome=output.get("eventOutcomeInformation"),
                    details=output.get("eventOutcomeDetailNote"),
                )
            )
            result = "failed"
        self.job.pyprint(
            f"Creating policy checking event for {self.file_path} ({self.file_uuid})"
        )
        # Manually-normalized access derivatives have no file UUID so we can't
        # create a validation event for them. TODO/QUESTION: should we use the
        # UUID that was assigned to the manually normalized derivative during
        # transfer, i.e., the one that we retrieve in
        # ``_get_manually_normalized_access_derivative_file_uuid`` above?
        if not self.is_manually_normalized_access_derivative:
            databaseFunctions.insertIntoEvents(
                fileUUID=self.file_uuid,
                eventType="validation",  # From PREMIS controlled vocab.
                eventDetail=event_detail,
                eventOutcome=output.get("eventOutcomeInformation"),
                eventOutcomeDetailNote=output.get("eventOutcomeDetailNote"),
            )
        return result

    def _get_command_to_execute(self, rule: FPRule) -> Tuple[str, List[str]]:
        """Return a 2-tuple consisting of a) the FPR rule ``rule``'s command
        and b) a list of arguments to pass to it.
        """
        if rule.command.script_type in ("bashScript", "command"):
            return (
                replace_string_values(
                    rule.command.command,
                    file_=self.file_uuid,
                    sip=self.sip_uuid,
                    type_="file",
                ),
                [],
            )
        else:
            return (rule.command.command, [self.file_path, self.policies_dir])

    def _save_to_logs_dir(self, output: Dict[str, str]) -> None:
        """Save the MediaConch policy file as well as the raw MediaConch stdout
        for the target file to the logs/ directory of the SIP.
        """
        self._save_stdout_to_logs_dir(output)
        self._save_policy_to_subm_doc_dir(output)

    def _save_stdout_to_logs_dir(self, output: Dict[str, str]) -> None:
        """Save the output of running MediaConch's policy checker against the
        input file to
        logs/policyChecks/<policy_filename>/<input_filename>.xml in the SIP.
        """
        policy_filename = output.get("policyFileName")
        mc_stdout = output.get("stdout")
        if policy_filename and mc_stdout and self.sip_policy_checks_dir:
            policy_dirname, _ = os.path.splitext(policy_filename)
            policy_dirpath = os.path.join(self.sip_policy_checks_dir, policy_dirname)
            if not os.path.isdir(policy_dirpath):
                os.makedirs(policy_dirpath)
            filename = os.path.basename(self.file_path)
            stdout_path = os.path.join(policy_dirpath, f"{filename}.xml")
            with open(stdout_path, "w") as f:
                f.write(mc_stdout)

    def _save_policy_to_subm_doc_dir(self, output: Dict[str, str]) -> None:
        """Save the policy file text in ``output['policy']`` to a file named
        ``output['policyFileName']`` in
        metadata/submissionDocumentation/policies/ in the SIP, if it is not
        there already.
        """
        policy_filename = output.get("policyFileName")
        policy = output.get("policy")
        if policy_filename and policy and self.sip_subm_doc_dir:
            sip_policies_dir = os.path.join(self.sip_subm_doc_dir, "policies")
            if not os.path.isdir(sip_policies_dir):
                os.makedirs(sip_policies_dir)
            dst = os.path.join(sip_policies_dir, policy_filename)
            if not os.path.isfile(dst):
                with open(dst, "w") as fileo:
                    fileo.write(policy)

    @property
    def sip_logs_dir(self) -> Optional[str]:
        """Return the absolute path the logs/ directory of the SIP (or
        Transfer) that the target file is a part of.
        """
        if self._sip_logs_dir:
            return self._sip_logs_dir
        model_cls = SIP
        unit_type = "SIP"
        if self.file_type == "original":
            model_cls = Transfer
            unit_type = "Transfer"
        try:
            unit_model = model_cls.objects.get(uuid=self.sip_uuid)
        except (
            model_cls.DoesNotExist,
            model_cls.MultipleObjectsReturned,
            ValidationError,
        ):
            self.job.print_error(
                f"Warning: unable to retrieve {unit_type} model corresponding"
                f" to {unit_type} UUID {self.sip_uuid}"
            )
            return None
        else:
            if unit_type == "Transfer":
                sip_path = unit_model.currentlocation.replace(
                    "%sharedPath%", self.shared_path, 1
                )
            else:
                sip_path = unit_model.currentpath.replace(
                    "%sharedPath%", self.shared_path, 1
                )
            logs_dir = os.path.join(sip_path, "logs")
            if os.path.isdir(logs_dir):
                self._sip_logs_dir = logs_dir
                return logs_dir
            self.job.print_error(
                f"Warning: unable to find a logs/ directory in the {unit_type}"
                f" with UUID {self.sip_uuid}"
            )
            return None

    @property
    def sip_subm_doc_dir(self) -> Optional[str]:
        """Return the absolute path the metadata/submissionDocumentation/
        directory of the SIP that the target file is a part of.
        """
        if self._sip_subm_doc_dir:
            return self._sip_subm_doc_dir
        try:
            sip_model = SIP.objects.get(uuid=self.sip_uuid)
        except (SIP.DoesNotExist, SIP.MultipleObjectsReturned, ValidationError):
            self.job.print_error(
                "Warning: unable to retrieve SIP model corresponding to SIP"
                f" UUID {self.sip_uuid} (when attempting to get the path to"
                " metadata/submissionDocumentation/"
            )
            return None
        else:
            sip_path = sip_model.currentpath.replace(
                "%sharedPath%", self.shared_path, 1
            )
            subm_doc_dir = os.path.join(sip_path, "metadata", "submissionDocumentation")
            if os.path.isdir(subm_doc_dir):
                self._sip_subm_doc_dir = subm_doc_dir
                return subm_doc_dir
            self.job.print_error(
                "Warning: unable to find a metadata/submissionDocumentation/"
                f" directory in the SIP with UUID {self.sip_uuid}"
            )
            return None

    @property
    def sip_policy_checks_dir(self) -> Optional[str]:
        if self._sip_policy_checks_dir:
            return self._sip_policy_checks_dir
        if self.sip_logs_dir:
            _sip_policy_checks_dir = os.path.join(self.sip_logs_dir, "policyChecks")
            if os.path.isdir(_sip_policy_checks_dir):
                self._sip_policy_checks_dir = _sip_policy_checks_dir
            else:
                try:
                    os.makedirs(_sip_policy_checks_dir)
                except OSError:
                    pass
                else:
                    self._sip_policy_checks_dir = _sip_policy_checks_dir
        return self._sip_policy_checks_dir


def call(jobs: List[Job]) -> None:
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                file_path = job.args[1]
                file_uuid = job.args[2]
                sip_uuid = job.args[3]
                shared_path = job.args[4]
                file_type = job.args[5]

                try:
                    job.set_status(
                        main(
                            job, file_path, file_uuid, sip_uuid, shared_path, file_type
                        )
                    )
                except ValueError:
                    job.set_status(FAIL_CODE)

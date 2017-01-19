from __future__ import print_function
import ast
import os
import sys

import django
django.setup()
from fpr.models import FPRule, FormatVersion
from main.models import Derivation, SIP

from executeOrRunSubProcess import executeOrRun
import databaseFunctions
from dicts import replace_string_values

SUCCESS_CODE = 0
FAIL_CODE = 1
NOT_DERIVATIVE_CODE = 0
NO_RULES_CODE = 0


class DerivativeValidator:
    """Validates a preservation derivative.

    Initialize on a file and then call the ``validate`` method to determine
    whether a given file conforms to a given specification.

    Sub-class in order to validate an access derivative. See
    validateAccessDerivative.py.
    """

    def __init__(self, file_path, file_uuid, sip_uuid, shared_path):
        self.file_path = file_path
        self.file_uuid = file_uuid
        self.sip_uuid = sip_uuid
        self.shared_path = shared_path
        self._sip_logs_dir = None
        self._sip_implementation_checks_dir = None

    def validate(self):
        if not self.is_derivative():
            print('File {uuid} {not_derivative_msg}; not validating.'.format(
                  uuid=self.file_uuid,
                  not_derivative_msg=self.not_derivative_msg))
            return NOT_DERIVATIVE_CODE
        rules = self._get_rules()
        if not rules:
            return NO_RULES_CODE
        rule_outputs = []
        for rule in rules:
            rule_outputs.append(self._execute_rule_command(rule))
        if 'failed' in rule_outputs:
            return FAIL_CODE
        else:
            return SUCCESS_CODE

    # Override the following two attributes and one method for validation of
    # access derivatives.
    purpose = 'validatePreservationDerivative'
    not_derivative_msg = 'is not a preservation derivative'

    def is_derivative(self):
        try:
            Derivation.objects.get(derived_file__uuid=self.file_uuid,
                                   event__event_type='normalization')
            return True
        except Derivation.DoesNotExist:
            return False

    def _get_rules(self):
        try:
            fmt = FormatVersion.active.get(
                fileformatversion__file_uuid=self.file_uuid)
        except FormatVersion.DoesNotExist:
            rules = fmt = None
        if fmt:
            rules = FPRule.active.filter(format=fmt.uuid, purpose=self.purpose)
        # Check default rules.
        if not rules:
            rules = FPRule.active.filter(
                purpose='default_{}'.format(self.purpose))
        return rules

    def _execute_rule_command(self, rule):
        result = 'passed'
        if rule.command.script_type in ('bashScript', 'command'):
            command_to_execute = replace_string_values(
                rule.command.command, file_=self.file_uuid, sip=self.sip_uuid,
                type_='file')
            args = []
        else:
            command_to_execute = rule.command.command
            args = [self.file_path]
        print('Running', rule.command.description)
        exitstatus, stdout, stderr = executeOrRun(
            rule.command.script_type, command_to_execute, arguments=args)
        if exitstatus != 0:
            print('Command {} failed with exit status {}; stderr:'.format(
                rule.command.description, exitstatus), stderr, file=sys.stderr)
            return 'failed'
        print('Command {} completed with output {}'.format(
              rule.command.description, stdout))
        # Parse output and generate an Event
        output = ast.literal_eval(stdout)
        event_detail = ('program="{tool.description}";'
                        'version="{tool.version}"'.format(
                            tool=rule.command.tool))
        if rule.command.description == 'Validate using MediaConch':
            if output.get('eventOutcomeInformation') != 'pass':
                result = 'failed'
            if self.purpose in ('validatePreservationDerivative',):
                self.save_mediaconch_stdout_to_logs_dir(output)

        print('Creating {} event for {} ({})'
              .format(self.purpose, self.file_path, self.file_uuid))
        databaseFunctions.insertIntoEvents(
            fileUUID=self.file_uuid,
            eventType='validation',  # From PREMIS controlled vocab.
            eventDetail=event_detail,
            eventOutcome=output.get('eventOutcomeInformation'),
            eventOutcomeDetailNote=output.get('eventOutcomeDetailNote'),
        )
        return result

    def save_mediaconch_stdout_to_logs_dir(self, output):
        """Save the output of running MediaConch's implementation checker
        against the input file to
        logs/implementationChecks/<input_filename>.xml in the SIP,
        """
        mc_stdout = output.get('stdout')
        if mc_stdout and self.sip_implementation_checks_dir:
            filename = os.path.basename(self.file_path)
            stdout_path = os.path.join(self.sip_implementation_checks_dir,
                                       '{}.xml'.format(filename))
            with open(stdout_path, 'w') as f:
                f.write(mc_stdout)

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
            print('Warning: unable to retrieve SIP model corresponding to SIP'
                  ' UUID {}'.format(self.sip_uuid), file=sys.stderr)
            return None
        else:
            sip_path = sip_model.currentpath.replace(
                '%sharedPath%', self.shared_path, 1)
            logs_dir = os.path.join(sip_path, 'logs')
            if os.path.isdir(logs_dir):
                self._sip_logs_dir = logs_dir
                return logs_dir
            print('Warning: unable to find a logs/ directory in the SIP'
                  ' with UUID {}'.format(self.sip_uuid), file=sys.stderr)
            return None

    @property
    def sip_implementation_checks_dir(self):
        if self._sip_implementation_checks_dir:
            return self._sip_implementation_checks_dir
        if self.sip_logs_dir:
            _sip_implementation_checks_dir = os.path.join(
                self.sip_logs_dir, 'policyChecks')
            if os.path.isdir(_sip_implementation_checks_dir):
                self._sip_implementation_checks_dir = \
                    _sip_implementation_checks_dir
            else:
                try:
                    os.makedirs(_sip_implementation_checks_dir)
                except OSError:
                    pass
                else:
                    self._sip_implementation_checks_dir = \
                        _sip_implementation_checks_dir
        return self._sip_implementation_checks_dir

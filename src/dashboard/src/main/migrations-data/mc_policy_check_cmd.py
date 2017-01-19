from __future__ import print_function, unicode_literals
from collections import namedtuple
import json
import os
import subprocess
import sys
import uuid
from lxml import etree


SUCCESS_CODE = 0
ERROR_CODE = 1
NS = '{https://mediaarea.net/mediaconch}'


class MediaConchException(Exception):
    pass


Parse = namedtuple('Parse', 'etree_el stdout')


class MediaConchPolicyCheckerCommand:
    """MC Policy Checker Command runs
    ``mediaconch -mc -fx -p <path_to_policy_xsl_file> <target>``,
    parses the returned XML, and prints out a JSON report summarizing the
    results of the policy check.

    Initialize with the path to a policy file then call ``check``::

        >>> checker = MediaConchPolicyCheckerCommand(
        >>>     '/path/to/policies-dir/',
        >>>     'my-policy-file.xsd')
        >>> checker.check('/path/to/file-to-be-checked')
    """

    def __init__(self, policies_path, policy_filename):
        self.policy_filename = policy_filename
        self.policy_file_path = os.path.join(policies_path, policy_filename)

    def parse_mediaconch_output(self, target):
        """Run ``mediaconch -mc -fx -p <path_to_policy_xsl_file>
        <target>`` against the file at ``path_to_target`` and return an lxml
        etree parse of the output.
        """
        if not os.path.isfile(self.policy_file_path):
            raise MediaConchException(
                'There is no policy file at {}'.format(self.policy_file_path))
        args = ['mediaconch', '-mc', '-fx', '-p',
                self.policy_file_path, target]
        try:
            output = subprocess.check_output(args)
        except subprocess.CalledProcessError:
            raise MediaConchException("MediaConch failed when running: %s" % (
                ' '.join(args),))
        try:
            return Parse(etree_el=etree.fromstring(output), stdout=output)
        except etree.XMLSyntaxError:
            raise MediaConchException(
                "The MediaConch command failed when attempting to parse the"
                " XML output by MediaConch")

    def get_policy_check_name(self, policy_check_el):
        return policy_check_el.attrib.get(
            'name', 'Unnamed Check %s' % uuid.uuid4())

    def parse_policy_check_test(self, policy_check_el):
        """Return a 3-tuple parse of the <test> element of the policy <check>
        element.

        - El1 is outcome ("pass" or "fail" or other?)
        - El2 is the relevant field (i.e., attribute of the file)
        - El3 is the actual value of the relevant attribute/field.
        - El4 is the reason for the failure.
        """
        test_el = policy_check_el.find('%stest' % NS)
        if test_el is None:
            return None
        field = 'no field'
        context_el = policy_check_el.find('%scontext' % NS)
        if context_el is not None:
            field = context_el.attrib.get('field', 'no field'),
        return (
            test_el.attrib.get('outcome', 'no outcome'),
            field,
            test_el.attrib.get('actual', 'no actual value'),
            test_el.attrib.get('reason', 'no reason')
        )

    def get_policy_checks(self, doc):
        """Get all of the policy check names and outcomes from the policy check
        output file parsed as ``doc``.
        """
        mc_xml_vrsn = doc.attrib.get('version',
                                     'No identifiable MediaConch XML version')
        if mc_xml_vrsn == '0.3':
            return self.get_policy_checks_v_0_3(doc)
        elif mc_xml_vrsn == '0.1':
            return self.get_policy_checks_v_0_1(doc)
        else:
            raise MediaConchException(
                'Unable to parse MediaConch XML files with version'
                ' "{}"'.format(mc_xml_vrsn))

    def get_policy_checks_v_0_3(self, doc):
        policy_checks = {'mc_version': '0.3', 'policies': []}
        root_policy = doc.find('.%smedia/%spolicy' % (NS, NS))
        if root_policy is None:
            raise MediaConchException('Unable to find a root policy')
        policy_checks['root_policy'] = (
            root_policy.attrib.get('name', 'No root policy name'),
            root_policy.attrib.get('outcome', 'No root policy outcome')
        )
        for el_tname in ('policy', 'rule'):
            path = './/%s%s' % (NS, el_tname)
            for policy_el in doc.iterfind(path):
                policy_name = self.get_policy_check_name(policy_el)
                policy_checks['policies'].append(
                    (policy_name,
                     policy_el.attrib.get('outcome', 'no outcome')))
        return policy_checks

    def get_policy_checks_v_0_1(self, doc):
        policy_checks = {'mc_version': '0.1', 'policy_checks': {}}
        path = '.%smedia/%spolicyChecks/%scheck' % (NS, NS, NS)
        for policy_check_el in doc.iterfind(path):
            policy_check_name = self.get_policy_check_name(policy_check_el)
            parse = self.parse_policy_check_test(policy_check_el)
            if parse:
                policy_checks['policy_checks'][policy_check_name] = parse
        return policy_checks

    def get_event_outcome_information_detail(self, policy_checks):
        """Return a 2-tuple of info and detail.
        - info: 'pass' or 'fail'
        - detail: human-readable string indicating which policy checks
        passed or failed. If the policy check as a whole passed, just return
        the passed check names; if it failed, just return the failed ones.
        """
        if policy_checks['mc_version'] == '0.3':
            return self.get_event_outcome_information_detail_v_0_3(
                policy_checks)
        return self.get_event_outcome_information_detail_v_0_1(policy_checks)

    def get_event_outcome_information_detail_v_0_3(self, policy_checks):
        failed_policy_checks = []
        passed_policy_checks = []
        info = 'fail'
        if policy_checks['root_policy'][1] == 'pass':
            info = 'pass'
        for name, outcome in policy_checks['policies']:
            if outcome == "pass":
                passed_policy_checks.append(name)
            else:
                failed_policy_checks.append('failed policy/rule: %s' % name)
        prefix = ('MediaConch policy check result against policy file'
                  ' {}:'.format(self.policy_filename))
        if info == 'fail':
            return ('fail', '{} {}'.format(
                    prefix, '; '.join(failed_policy_checks)))
        else:
            if not passed_policy_checks:
                return ('pass', '{} No checks passed, but none failed'
                        ' either.'.format(prefix))
            else:
                return ('pass', '{} All policy checks passed: {}'.format(prefix,
                        '; '.join(passed_policy_checks)))

    def get_event_outcome_information_detail_v_0_1(self, policy_checks):
        failed_policy_checks = []
        passed_policy_checks = []
        for name, (out, fie, act, rea) in policy_checks['policy_checks'].items():
            if out == "pass":
                passed_policy_checks.append(name)
            else:
                failed_policy_checks.append(
                    'The check "{name}" failed; the actual value for the'
                    ' field "{fie}" was "{act}"; the reason was'
                    ' "{rea}".'.format(
                        name=name,
                        fie=fie,
                        act=act,
                        rea=rea))
        prefix = ('MediaConch policy check result against policy file'
                  ' {}:'.format(self.policy_filename))
        if failed_policy_checks:
            return ('fail', '{} {}'.format(
                    prefix, ' '.join(failed_policy_checks)))
        elif not passed_policy_checks:
            return ('pass', '{} No checks passed, but none failed'
                    ' either.'.format(prefix))
        else:
            return ('pass', '{} All policy checks passed: {}'.format(prefix,
                    '; '.join(passed_policy_checks)))

    def check(self, target):
        """Return 0 if MediaConch can successfully assess whether the file at
        `target` passes the policy checks that are relevant to it, given its
        purpose and the state of the FPR. Parse the XML output by MediaConch
        and print a JSON representation of that output.
        """
        try:
            parse = self.parse_mediaconch_output(target)
            policy_checks = self.get_policy_checks(parse.etree_el)
            info, detail = self.get_event_outcome_information_detail(
                policy_checks)
            print(json.dumps({
                'eventOutcomeInformation': info,
                'eventOutcomeDetailNote': detail,
                'policy': self.policy_filename,
                'stdout': parse.stdout
            }))
            return SUCCESS_CODE
        except MediaConchException as e:
            print(json.dumps({
                'eventOutcomeInformation': 'fail',
                'eventOutcomeDetailNote': str(e),
                'policy': self.policy_filename,
                'stdout': None
            }), file=sys.stderr)
            return ERROR_CODE


if __name__ == '__main__':

    # A MediaConch policy file must exist at ``policy_filename`` in
    # ``%sharedDirectory%/sharedMicroServiceTasksConfigs/policies/``.
    # To create new MediaConch-based policy checker FPR commands, just copy
    # this entire script and replace the single ``policy_filename`` var with
    # the name of a different policy file.
    policy_filename = 'PLACEHOLDER_FOR_POLICY_FILE_NAME'

    target = sys.argv[1]
    policies_path = sys.argv[2]
    policy_checker = MediaConchPolicyCheckerCommand(policies_path,
                                                    policy_filename)
    sys.exit(policy_checker.check(target))

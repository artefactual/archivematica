# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from django.db import migrations


def data_migration(apps, schema_editor):
    """Migrations for MediaConch integration.

    This migration makes the following changes:

    1. MediaConch tool is available for validation (in particular for
       validating .mkv files)
    2. MediaConch command is created for validating .mkv files during transfer.
    """

    FPTool = apps.get_model('fpr', 'FPTool')
    FPCommand = apps.get_model('fpr', 'FPCommand')

    # MediaConch Tool
    mediaconch_tool_uuid = 'f79c56f1-2d42-440a-8a1f-f40888e24bca'
    mediaconch_tool = FPTool.objects.create(
        uuid=mediaconch_tool_uuid,
        description='MediaConch',
        version='16.05',
        enabled=True,
        slug='mediaconch-1605'
    )

    # MediaConch Command
    mediaconch_command_uuid = '287656fb-e58f-4967-bf72-0bae3bbb5ca8'
    FPCommand.objects.create(
        uuid=mediaconch_command_uuid,
        tool=mediaconch_tool,
        description='Validate using MediaConch',
        command=mediaconch_command_script,
        script_type='pythonScript',
        command_usage='validation'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0023_normalization_report'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]

mediaconch_command_script = '''
from __future__ import print_function, unicode_literals
import json
import subprocess
import sys
import uuid

from lxml import etree


SUCCESS_CODE = 0
ERROR_CODE = 1
NS = '{https://mediaarea.net/mediaconch}'


class MediaConchException(Exception):
    pass


def parse_mediaconch_data(target):
    """Run `mediaconch -mc -iv 4 -fx <target>` against `target` and return an
    lxml etree parse of the output.

    .. note::

        At present, MediaConch (v. 16.05) will give terse output so long as you
        provide *some* argument to the -iv option. With no -iv option, you will
        get high verbosity. To be specific, low verbosity means that only
        checks whose tests fail in the named "MediaConch EBML Implementation
        Checker" will be displayed. If none fail, the EBML element will contain
        no <check> elements.

    """

    args = ['mediaconch', '-mc', '-iv', '4', '-fx', target]
    try:
        output = subprocess.check_output(args)
    except subprocess.CalledProcessError:
        raise MediaConchException("MediaConch failed when running: %s" % (
            ' '.join(args),))
    try:
        return etree.fromstring(output)
    except etree.XMLSyntaxError:
        raise MediaConchException(
            "MediaConch failed when attempting to parse the XML output by"
            " MediaConch")


def get_impl_check_name(impl_check_el):
    name_el = impl_check_el.find('%sname' % NS)
    if name_el is not None:
        return name_el.text
    else:
        return 'Unnamed Implementation Check %s' % uuid.uuid4()


def get_check_name(check_el):
    return check_el.attrib.get(
        'name', check_el.attrib.get('icid', 'Unnamed Check %s' % uuid.uuid4()))


def get_check_tests_outcomes(check_el):
    """Return a list of outcome strings for the <check> element `check_el`."""
    outcomes = []
    for test_el in check_el.iterfind('%stest' % NS):
        outcome = test_el.attrib.get('outcome')
        if outcome:
            outcomes.append(outcome)
    return outcomes


def get_impl_check_result(impl_check_el):
    """Return a dict mapping check names to lists of test outcome strings."""
    checks = {}
    for check_el in impl_check_el.iterfind('%scheck' % NS):
        check_name = get_check_name(check_el)
        test_outcomes = get_check_tests_outcomes(check_el)
        if test_outcomes:
            checks[check_name] = test_outcomes
    return checks


def get_impl_checks(doc):
    """When not provided with a policy file, MediaConch produces a series of
    XML <implementationChecks> elements that contain <check> sub-elements. This
    function returns a dict mapping implementation check names to dicts that
    map individual check names to lists of test outcomes, i.e., 'pass' or
    'fail'.

    """

    impl_checks = {}
    path = '.%smedia/%simplementationChecks' % (NS, NS)
    for impl_check_el in doc.iterfind(path):
        impl_check_name = get_impl_check_name(impl_check_el)
        impl_check_result = get_impl_check_result(impl_check_el)
        if impl_check_result:
            impl_checks[impl_check_name] = impl_check_result
    return impl_checks


def get_event_outcome_information_detail(impl_checks):
    """Return a 2-tuple of info and detail.

    - info: 'pass' or 'fail'
    - detail: human-readable string indicating which implementation checks
      passed or failed. If implementation check as a whole passed, just return
      the passed check names; if it failed, just return the failed ones.

    """

    info = 'pass'
    failed_impl_checks = []
    passed_impl_checks = []
    for impl_check, checks in impl_checks.items():
        passed_checks = []
        failed_checks = []
        for check, outcomes in checks.items():
            for outcome in outcomes:
                if outcome == 'pass':
                    passed_checks.append(check)
                else:
                    info = 'fail'
                    failed_checks.append(check)
        if failed_checks:
            failed_impl_checks.append(
                'The implementation check %s returned'
                ' failure for the following check(s): %s.' % (
                    impl_check, ', '.join(failed_checks)))
        else:
            passed_impl_checks.append(
                'The implementation check %s returned'
                ' success for the following check(s): %s.' % (
                    impl_check, ', '.join(passed_checks)))
    prefix = 'MediaConch implementation check result:'
    if info == 'pass':
        if passed_impl_checks:
            return info, ' '.join(passed_impl_checks)
        return (info, '{} All checks passed.'.format(prefix))
    else:
        return (info, '{} {}'.format(prefix, ' '.join(failed_impl_checks)))


def main(target):
    """Return 0 if MediaConch can successfully assess whether the file at
    `target` is a valid Matroska (.mkv) file. Parse the XML output by
    MediaConch and print a JSON representation of that output.
    """

    try:
        doc = parse_mediaconch_data(target)
        impl_checks = get_impl_checks(doc)
        info, detail = get_event_outcome_information_detail(impl_checks)
        print(json.dumps({
            'eventOutcomeInformation': info,
            'eventOutcomeDetailNote': detail
        }))
        return SUCCESS_CODE
    except MediaConchException as e:
        print(json.dumps({
            'eventOutcomeInformation': 'fail',
            'eventOutcomeDetailNote': str(e)
        }), file=sys.stderr)
        return ERROR_CODE


if __name__ == '__main__':
    target = sys.argv[1]
    sys.exit(main(target))
'''.strip()

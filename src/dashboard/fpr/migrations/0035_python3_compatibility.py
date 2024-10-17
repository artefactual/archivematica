"""Update commands and rules for Python 3 compatibility."""

from django.db import migrations

OLD_JHOVE_CMD_UUID = "11036e14-78d9-4449-8360-e2da394279ad"
NEW_JHOVE_CMD_UUID = "4cac3267-453e-4456-9306-6d098dacb70d"
JHOVE_RULES = (
    "005d14f1-5b67-43fc-b3a5-5048ec915b0b",
    "085d5286-7616-4acd-88a4-ef65066362b9",
    "0cd29763-b64a-43cc-9a72-5f8e6317bbae",
    "10e514c0-e72a-4f70-afd0-4aed3bfa0ab9",
    "1386de15-3152-4a24-afa6-eab7a224da65",
    "18c019e8-ea26-49eb-a900-ec8388f1483d",
    "1a01813e-430f-4a91-bda2-182e4620d328",
    "26573246-96de-4682-bd17-f0bccb50abfe",
    "26f687fe-255a-469b-bca5-ac0992038789",
    "37a5d85d-58dc-4f4e-8be9-b9ecced85d0d",
    "40616003-8af5-48d8-94ca-1871ae2cfaf1",
    "407dcd55-71f5-4d83-8e21-6e3809a3fba8",
    "40966c69-42dd-49fb-8740-b22a85bc7e32",
    "42f3756b-7966-4a47-b029-59688bfc6e43",
    "4324a41f-6016-4b28-a0b0-c343dbaca42e",
    "471303d4-de26-435c-83b2-8e72beccc60d",
    "48086e84-a933-42e0-87fd-ce195137c48d",
    "4ea200fa-182c-4b17-9493-e9d3f7e467ff",
    "535152f5-88a5-439b-8619-6f42fc2e4468",
    "56c72d8a-139b-4cdf-8dd0-d65a373301d2",
    "57bbe864-2004-45a4-81be-d40aab02f170",
    "5bc4c892-fe7b-4d22-8a9a-ea8c3dd0d171",
    "6217dbf1-2b4f-49ce-ab87-d0ed1e1ef890",
    "62f0e3bd-a5bb-4fa0-b78b-dab15253b429",
    "662caf44-cd04-4990-8e28-9f8425dba782",
    "67c0b096-63f4-4e30-b26f-6ed9365ea67c",
    "6b3ba38b-e208-450d-9b48-07897b6b7c42",
    "6f4cbfc5-c560-4709-8d3e-aa5685bc4fd5",
    "713bf728-e583-4cb5-a079-f36baf1a77e7",
    "76bfa370-ac87-41e2-995b-e01bb8c977d0",
    "7af37625-f547-4d13-ab52-e5bddf249027",
    "802e24ec-5e63-4e92-a0cf-33f11b4edf06",
    "80ecc092-8f29-4810-8918-e81133092290",
    "87c23f92-ee9a-44b3-89b2-c024bbcc70a3",
    "8835348d-60f2-4dba-a834-cf26c57f821c",
    "88cb0134-7808-450f-a0f4-365a818d583a",
    "8a0a1d71-5e56-482e-81b4-b3d425106d49",
    "8e995eb3-4023-4168-b1e1-7b5f2b22237b",
    "913ff712-1856-48d7-85e9-415617fc9fdc",
    "95ef736c-e477-442e-86f4-4e9049be2b88",
    "981eae6c-4d7b-40ce-9bfd-1193c600a143",
    "986b53a8-3407-4d87-89ec-20575e61292a",
    "9d3325a1-cc0a-4fa8-9f3b-ccd5b8c884d1",
    "a01418ce-fcb9-4554-add5-72010c719865",
    "a0f916de-ed95-4f2a-9f6d-0cbfd8949cc2",
    "a7a6cc14-4d61-4030-b8dc-a1ca8ed97402",
    "aa4ad350-7e66-4637-a643-6e0bd037645d",
    "aa93748e-5899-4ecc-870e-3d47a38fda59",
    "ab286afc-f429-4e50-8a40-452c6331d630",
    "ab728cab-3072-4e20-a64b-ba2560467d93",
    "b1a60f26-8927-46c5-843b-7eddeef6213e",
    "b7dd794b-7618-4d13-a2f9-e01dae884cf6",
    "c5a30e3c-2100-4b5b-a9b5-27a236a345dd",
    "c6d7590f-83c1-4612-a300-3bff3d358199",
    "c799f39a-10fd-4125-b11c-1011ef1ca15c",
    "cddbffd4-4ada-4a6e-a713-82077a54e89e",
    "d4a1faba-a5a3-4955-a20a-6f71da1d35bc",
    "dc9dc6a9-82b6-44b7-866a-db3e6314922e",
    "dcc9bcd7-f085-4028-9599-bf4fd12816ee",
    "e0cdb544-97d3-4915-9b08-fffad57bda10",
    "e13d6459-a749-4d31-9dd0-e0a59aab36cd",
    "ecd66812-c89a-4231-802e-2e69b47bae2a",
    "ee56ca6d-f6d0-4948-9834-2c82f5d223d5",
    "eebc3670-6692-4daf-92a2-c8b76606049a",
    "f3d2b70b-0b9d-43f6-80e0-9b987b77719d",
    "f3f9652a-c903-491b-be89-5fc2469aaa1a",
    "f4074907-c111-4e6c-91ae-9c0526475a9a",
    "f51ed8e0-edb3-4ebc-84d5-11135cc1fe62",
    "f712b5a9-7dd5-4e39-b818-c7cda54b9366",
    "fcefa9af-322c-4c9b-afd2-82231dd953fc",
    "fdd758b0-99a6-4447-b082-3a1098f13bf6",
    "ff989185-1b11-4f96-8075-e605e4cf4be4",
    "ffa25cf6-c1a5-45f2-9bee-798aa04df172",
)
NEW_JHOVE_CMD = r"""
from __future__ import print_function
import json
import subprocess
import sys

from lxml import etree

class JhoveException(Exception):
    pass

def parse_jhove_data(target):
    args = ['jhove', '-h', 'xml', target]
    try:
        output = subprocess.check_output(args).decode("utf8")
    except subprocess.CalledProcessError:
        raise JhoveException("Jhove failed when running: " + ' '.join(args))

    return etree.fromstring(output.encode("utf8"))

def get_status(doc):
    status = doc.find('.{http://hul.harvard.edu/ois/xml/ns/jhove}repInfo/{http://hul.harvard.edu/ois/xml/ns/jhove}status')
    if status is None:
        raise JhoveException("Unable to find status!")

    return status.text

def get_outcome(status, format=None):
    # JHOVE returns "bytestream" for unrecognized file formats.
    # That can include unrecognized or malformed PDFs, JPEG2000s, etc.
    # Since we're whitelisting the formats we're passing in,
    # "bytestream" indicates that the format is not in fact well-formed
    # regardless of what the status reads.
    if format == "bytestream":
        return "partial pass"

    if status == "Well-Formed and valid":
        return "pass"
    elif status == "Well-Formed, but not valid":
        return "partial pass"
    else:
        return "fail"

def get_format(doc):
    format = doc.find('.{http://hul.harvard.edu/ois/xml/ns/jhove}repInfo/{http://hul.harvard.edu/ois/xml/ns/jhove}format')
    version = doc.find('.{http://hul.harvard.edu/ois/xml/ns/jhove}repInfo/{http://hul.harvard.edu/ois/xml/ns/jhove}version')

    if format is None:
        format = "Not detected"
    else:
        format = format.text

    if version is not None:
        version = version.text

    return (format, version)

def format_event_outcome_detail_note(format, version, result):
    note = 'format="{}";'.format(format)
    if version is not None:
        note = note + ' version="{}";'.format(version)
    note = note + ' result="{}"'.format(result)

    return note

def main(target):
    try:
        doc = parse_jhove_data(target)
        status = get_status(doc)
        format, version = get_format(doc)
        outcome = get_outcome(status, format)
        note = format_event_outcome_detail_note(format, version, status)

        out = {
            "eventOutcomeInformation": outcome,
            "eventOutcomeDetailNote": note
        }
        print(json.dumps(out))

        return 0
    except JhoveException as e:
        return e

if __name__ == '__main__':
    target = sys.argv[1]
    sys.exit(main(target))
"""

OLD_MEDIACONCH_CMD_UUID = "287656fb-e58f-4967-bf72-0bae3bbb5ca8"
NEW_MEDIACONCH_CMD_UUID = "fd8edea2-e251-4fa7-9592-f033d965696c"
MEDIACONCH_RULES = ("a2fb0477-6cde-43f8-a1c9-49834913d588",)
NEW_MEDIACONCH_CMD = r'''
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from collections import namedtuple
import json
import subprocess
import sys
import uuid

from lxml import etree


SUCCESS_CODE = 0
ERROR_CODE = 1
NS = "{https://mediaarea.net/mediaconch}"


class MediaConchException(Exception):
    pass


Parse = namedtuple("Parse", "etree_el stdout")


def parse_mediaconch_data(target):
    """Run `mediaconch -mc -fx -iv 4 <target>` against `target` and return an
    lxml etree parse of the output.
    """
    args = ["mediaconch", "-mc", "-fx", "-iv", "4", target]
    try:
        output = subprocess.check_output(args).decode("utf8")
    except subprocess.CalledProcessError:
        raise MediaConchException(
            "MediaConch failed when running: %s" % (" ".join(args),)
        )
    try:
        return Parse(etree_el=etree.fromstring(output.encode("utf8")), stdout=output)
    except etree.XMLSyntaxError:
        raise MediaConchException(
            "MediaConch failed when attempting to parse the XML output by" " MediaConch"
        )


def get_impl_check_name(impl_check_el):
    name_el = impl_check_el.find("%sname" % NS)
    if name_el is not None:
        return name_el.text
    else:
        return "Unnamed Implementation Check %s" % uuid.uuid4()


def get_check_name(check_el):
    return check_el.attrib.get(
        "name", check_el.attrib.get("icid", "Unnamed Check %s" % uuid.uuid4())
    )


def get_check_tests_outcomes(check_el):
    """Return a list of outcome strings for the <check> element `check_el`."""
    outcomes = []
    for test_el in check_el.iterfind("%stest" % NS):
        outcome = test_el.attrib.get("outcome")
        if outcome:
            outcomes.append(outcome)
    return outcomes


def get_impl_check_result(impl_check_el):
    """Return a dict mapping check names to lists of test outcome strings."""
    checks = {}
    for check_el in impl_check_el.iterfind("%scheck" % NS):
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
    path = ".%smedia/%simplementationChecks" % (NS, NS)
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
    info = "pass"
    failed_impl_checks = []
    passed_impl_checks = []
    for impl_check, checks in impl_checks.items():
        passed_checks = set()
        failed_checks = set()
        for check, outcomes in checks.items():
            for outcome in outcomes:
                if outcome == "pass":
                    passed_checks.add(check)
                else:
                    info = "fail"
                    failed_checks.add(check)
        if failed_checks:
            failed_impl_checks.append(
                "The implementation check %s returned"
                " failure for the following check(s): %s."
                % (impl_check, ", ".join(failed_checks))
            )
        else:
            passed_impl_checks.append(
                "The implementation check %s returned"
                " success for the following check(s): %s."
                % (impl_check, ", ".join(passed_checks))
            )
    prefix = "MediaConch implementation check result:"
    if info == "pass":
        if passed_impl_checks:
            return info, "{} {}".format(prefix, " ".join(passed_impl_checks))
        return (info, "{} All checks passed.".format(prefix))
    else:
        return (info, "{} {}".format(prefix, " ".join(failed_impl_checks)))


def main(target):
    """Return 0 if MediaConch can successfully assess whether the file at
    `target` is a valid Matroska (.mkv) file. Parse the XML output by
    MediaConch and print a JSON representation of that output.
    """
    try:
        parse = parse_mediaconch_data(target)
        impl_checks = get_impl_checks(parse.etree_el)
        info, detail = get_event_outcome_information_detail(impl_checks)
        print(
            json.dumps(
                {
                    "eventOutcomeInformation": info,
                    "eventOutcomeDetailNote": detail,
                    "stdout": parse.stdout,
                }
            )
        )
        return SUCCESS_CODE
    except MediaConchException as e:
        print(
            json.dumps(
                {
                    "eventOutcomeInformation": "fail",
                    "eventOutcomeDetailNote": str(e),
                    "stdout": None,
                }
            ),
            file=sys.stderr,
        )
        return ERROR_CODE


if __name__ == "__main__":
    target = sys.argv[1]
    sys.exit(main(target))
'''

OLD_TSK_RECOVER_CMD_UUID = "8f41dc6f-05eb-46d4-9b22-0a0d74673510"
NEW_TSK_RECOVER_CMD_UUID = "0de46681-43a4-424d-90d4-c6e2d5b7312f"
TSK_RECOVER_RULES = (
    "0d16fdc4-9717-4710-8edf-841df47a307b",
    "9690ce82-606e-4026-9421-002746e75d69",
    "9e502f30-ba01-4981-8377-dd01ecf2dc5c",
    "ac2c790c-2e6f-475e-b5fb-38055f0fabd4",
    "bdfc3ef8-99a6-48e2-9017-8c39010a622a",
    "ca67c6bb-e470-45b5-a47a-e66ef41fad67",
)
NEW_TSK_RECOVER_CMD = r"""
from __future__ import print_function
import re
import subprocess
import sys

def extract(package, outdir):
    # -a extracts only allocated files; we're not capturing unallocated files
    try:
        process = subprocess.Popen(['tsk_recover', package, '-a', outdir],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout = stdout.decode("utf8")
        stderr = stderr.decode("utf8")

        match = re.match(r'Files Recovered: (\d+)', stdout.splitlines()[0])
        if match:
            if match.groups()[0] == '0':
                raise Exception('tsk_recover failed to extract any files with the message: {}'.format(stdout))
            else:
                print(stdout)
    except Exception as e:
        return e

    return 0

def main(package, outdir):
    return extract(package, outdir)

if __name__ == '__main__':
    package = sys.argv[1]
    outdir = sys.argv[2]
    sys.exit(main(package, outdir))
"""

OLD_DEFAULT_THUMBNAIL_CMD_UUID = "7c2b65c7-6cea-4f81-9f3b-53375efc5bee"
NEW_DEFAULT_THUMBNAIL_CMD_UUID = "95149bc4-0620-4c20-964c-1d6c34b9400e"
DEFAULT_THUMBNAIL_RULES = ("3a19f9a3-c5d5-4934-9286-13b3ad6c24d3",)
NEW_DEFAULT_THUMBNAIL_CMD = r"""
import argparse
import base64
import sys

# http://i.imgur.com/ijwSkff.jpg
DEFAULT_THUMBNAIL = \"\"\"
/9j/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB
AQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB
AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAAwADADASIAAhEBAxEB/8QAHAABAQACAgMA
AAAAAAAAAAAACAAFCQEKAwQG/8QANBAAAAUDAgIFCwUAAAAAAAAAAQMEBQYAAgcICRESExQ5eLcV
GSExV1iVmMHS1xZScYWn/8QAFgEBAQEAAAAAAAAAAAAAAAAAAAEC/8QAKBEAAgADBgUFAAAAAAAA
AAAAAAECESESMVFhkcEiQUJxoVJystHS/9oADAMBAAIRAxEAPwDelul5RzWOsiAYeh2d8yYlgjdp
mTZLBtxBOF+PVTjLXvKcmi7iufHJjLKXPye5mj7MQhQu5yxIymJVKhjKbTnl/vdQn13Pfvpa1vmN
mf30vNzvtGIj3KWDx0n9F2gML13Pfvpa1vmNmf314znLPJBJp9+tLWwNhJRhtwW6jJkNw2l2jfcF
oCYADcIAPABEA4+sQD01nq9VcUaciWEkcnTGpVBRPSCNpfSmFX2F842gNwWc4hzCACIW8RABH0UA
xdv3cZl2K2rHuPNW85dpbjLIrexrYhqAmLkscHTGsslRFi+yIZZkj48Ozu6QV6VKRvbMivKm0uBv
Sq9reDUuNFrVZivsa10WSpLlNjhDVBXjT4dJWxsjLVHFR9kua1qNyKbW5Mg6yY3AxKxKAy5PapAm
+43oLuXlPvEsDR3HbLOsLKUyksm0c5BaXVQx4zxmom+OnWTOVy2UQ6Mx56g8SGAqHDqKW2SxxQfL
LXOJ86VrugaBtURZrPeYisizHj2TWK1B8Tud9oxEe5SweOk/ou0otzvtGIj3KWDx0n9F2qCqqqoC
pC7VicpPuS5UEouwvrGkZ5PM5LQt5zByliEq6+7gAcbhAq0BuH0iAAHqAKPVI3a07SPJfc+efFjF
FZivg9z+MRVdF23RldzvtGIj3KWDx0n9F2tru4Lt+ah9ROf4VnnT9P8AEjGvb8PW4ik0fysErbiC
EjXNHmZNrwyuMXj8sFzNdTpGqRL0S1AyeRbWNIemWPnl5QQxC7zWe5H7TNH4f3OWPricarbXS3mr
O8SfgSzS12TDnVSM81nuSe0zR/8AGcr/AImq81nuSe0zR/8AGcr/AImqWn6ItYP0JLFefoOdIzaz
HjuSZND9uj94D/V8TXfWuB2styQfVk7SAH8PGVvriUaY+3ht4ahNNeoTIef8/wCQ8UyBxkGKQxdH
o9i79TuKe9O4yaNSNxdXVxkcah1zX5LuhyBMhQpkD/e9Xv7goUODEWxpEj1Ktw8LUnOtnBqSk3Wv
a+ook6pzWeKfNZH/2Q==\"\"\"

def main(target):
    with open(target, 'wb') as f:
        f.write(base64.b64decode(DEFAULT_THUMBNAIL))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-location', required=True)
    args, _ = parser.parse_known_args()

    sys.exit(main(args.output_location))
"""

OLD_SIEGFRIED_CMD_UUID = "9402ad69-f045-4d0a-8042-9c990645910a"
NEW_SIEGFRIED_CMD_UUID = "e24cf2d5-51ac-4bed-9ff6-cb691d895ade"
SIEGFRIED_RULES = ()
NEW_SIEGFRIED_CMD = r"""
from __future__ import print_function

import json
import subprocess
import sys


class IdToolError(Exception):
    pass


class ParseError(IdToolError):
    PREFIX = 'The output produced by siegfried could not be parsed'
    def __init__(self, message=None):
        message = self.PREFIX if message is None else '{}: {}'.format(self.PREFIX, message)
        Exception.__init__(self, message)


def sf_tool(path):
    return subprocess.check_output(['sf', '-json', path]).decode("utf8")


def find_puid(sf_output):
    result = json.loads(sf_output)
    try:
        matches = result['files'][0]['matches']
    except KeyError as e:
        raise ParseError('error matching key {}'.format(e))

    if len(matches) == 0:
        raise ParseError('no matches found')

    match = matches[0]
    puid = None

    if 'puid' in match:
        puid = match['puid']
    elif 'id' in match:
        puid = match['id']
    else:
        raise ParseError

    if puid == 'UNKNOWN':
        raise IdToolError('siegfried determined that the file format is UNKNOWN')

    return puid


def main(path):
    try:
        print(find_puid(sf_tool(path)))
    except IdToolError as e:
        print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
"""

OLD_FIDO_CMD_UUID = "ff2c0b52-741d-4f7a-9b52-ba3529051af3"
NEW_FIDO_CMD_UUID = "8383e9eb-0d3c-4872-ae63-05405a156502"
FIDO_RULES = ()
NEW_FIDO_CMD = r'''
from __future__ import print_function
import os.path
import re
import subprocess
import sys

def file_tool(path):
    return subprocess.check_output(['file', path]).decode("utf8").strip()

class FidoFailed(Exception):
    def __init__(self, stdout, stderr, retcode):
        message = """
Fido exited {retcode} and no format was found.
stdout: {stdout}
---
stderr: {stderr}
""".format(stdout=stdout, stderr=stderr, retcode=retcode)
        super(FidoFailed, self).__init__(message)

def identify(file_):
    # The default buffer size fido uses, 256KB, is too small to be able to detect certain formats
    # Formats like office documents and Adobe Illustrator .ai files will be identified as other, less-specific formats
    # This larger buffer size is a bit slower and consumes more RAM, so some users may wish to customize this to reduce the buffer size
    # See: https://projects.artefactual.com/issues/5941, https://projects.artefactual.com/issues/5731
    cmd = ['fido', '-bufsize', '1048576',
           '-loadformats', '/usr/lib/archivematica/archivematicaCommon/externals/fido/archivematica_format_extensions.xml',
           os.path.abspath(file_)]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout, stderr = process.communicate()
    stdout = stdout.decode("utf8")
    stderr = stderr.decode("utf8")

    try:
        results = stdout.split('\n')[0].split(',')
    except Exception:
        raise FidoFailed(stdout, stderr, process.returncode)

    if process.returncode != 0 or results[-1] == '"fail"':
        raise FidoFailed(stdout, stderr, process.returncode)
    else:
        puid = results[2]
        if re.match('(.+)?fmt\/\d+', puid):
            return puid
        else:
            print("File identified as non-standard Fido code: {id}".format(id=puid), file=sys.stderr)
            return ""

def main(argv):
    try:
        print(identify(argv[1]))
        return 0
    except FidoFailed as e:
        file_output = file_tool(argv[1])
        # FIDO can't currently identify text files with no extension, and this
        # is a common enough usecase to special-case it
        if 'text' in file_output:
            print('x-fmt/111')
        else:
            return e
    except Exception as e:
        return e

if __name__ == '__main__':
    exit(main(sys.argv))
'''

OLD_BY_EXTENSION_CMD_UUID = "41efbe1b-3fc7-4b24-9290-d0fb5d0ea9e9"
NEW_BY_EXTENSION_CMD_UUID = "8546b624-7894-4201-8df6-f239d5e0d5ba"
BY_EXTENSION_RULES = (
    "f8c16522-7021-4f75-b0cf-76beb1a2c40d",
    "9921d772-78e8-4d7c-ac88-4165e3bbcac7",
    "48e38041-1b9d-4f36-ac1a-5ac21e76a092",
    "b0230544-3df5-428f-a716-fcf1d52a6ad1",
    "964cd6b6-31be-49f1-bc5e-1efd6218d22b",
    "26ab1c86-fcaf-461d-a8ac-9b3a24e44557",
    "5f80e6d8-8604-4528-9321-189a42ee0560",
    "b2d1246a-9798-4f06-8d4b-f5c82284b874",
    "ad6ea80e-c5e9-4c8c-91eb-af8375f8ed3d",
    "cfa34057-2752-4beb-ad60-ea813d160220",
    "e0e05247-aef2-47ca-9e25-73c1b63919d5",
    "e6a1ed6b-bd16-4388-a151-f06b66b94081",
    "f4ea5222-b048-4397-83aa-c6f4ee9306c3",
    "2ec78f73-bc9c-4955-b651-82a63af0f595",
    "a44b2ead-0449-4d86-ac41-6fdbabf6485b",
    "e34c348f-e124-4a7f-8c85-ee6aa6b42a8a",
    "36f57803-17ad-46df-9f63-2d663c32f009",
    "f805a4c8-ac16-4f09-81f3-3b490f227bef",
    "4c14970a-f0eb-4075-98d3-29c975f4e653",
    "ec6aab2f-114d-4af8-a874-535f13b83f0c",
    "54f7aca0-e22e-496c-bf15-9bbc378333c6",
    "d0ec74e1-11fa-48c2-9986-e32db3f6e39a",
    "308cb6c1-f0d9-4e05-b62e-96e8973af00c",
    "4c4384a2-493c-4fd1-8a47-3b3cadfa2720",
    "2f669bc0-89c1-4bf8-828d-815442a1376c",
    "4275d66e-2b06-40c8-9549-e2bee30c2fa5",
    "527cd04e-f892-4a02-b241-210f6cccbcd7",
    "3d9bb312-16ec-4353-9ad6-edfa6c9ffd8a",
    "15ce0326-5bda-4d6d-b403-a3a956cc60ac",
    "29514e19-2fee-4d96-844d-62840c9768e1",
    "5af7f5cc-5138-4967-afdb-68ec269dcb04",
    "879f639a-6aea-40a3-a017-360eed031d5c",
    "4bfbad23-b677-4c20-8eae-01c114cf8435",
    "13d4ceb4-53a4-4736-9cd6-358f48a94f3e",
    "681f2197-6cc6-4820-9614-d257962e3d86",
    "929b44c8-8f3c-4b5e-837d-cad214cc3165",
    "c7cbed6a-1b89-48da-a741-6751698db416",
    "cc48a644-ef0d-4e29-894b-2369acf781d2",
    "283c7c21-2cec-4992-969c-ef19742a0751",
    "9db20a1c-3c2d-484f-b400-c66db37f69e8",
    "fb808763-1177-4da1-af13-cac97a2d64f3",
    "cc4a306e-7acc-49d9-bdbb-c02430b53f3b",
    "8c3f9153-cd7a-4309-914f-3f139ee8ecf2",
    "20bb03e8-eba4-4ab6-8e0f-57fd7b195a67",
    "fe8ac137-fda6-4de6-b89f-fe6a5912afd8",
    "604a3252-3140-4e13-851e-b374b78e28ee",
    "6ebe39f2-fe48-4616-a0a3-6adc5ccf9e44",
    "10df244f-2398-40ca-b3ad-3583d939d215",
    "dd83104d-85a6-46a7-b285-a1680f1c38d9",
    "7bc1c9f2-bf9c-42b9-a323-8423b5517bbb",
    "b222ef2e-d669-4fa7-af14-96e6fb378fd3",
    "5032b26a-7b57-46d0-b97d-31f1382395df",
    "3c01f77f-d153-4cac-8141-02b373f7bdca",
    "61dc0222-7f31-4c31-9436-339a848bf69d",
    "07279923-fcec-465e-a5e5-4dab7c642106",
    "25234bbb-51c5-456f-9350-c96960abce18",
    "ac414a38-823b-4cf6-8a48-8ef5e2ab053e",
    "8cc7d103-623e-4411-8657-25f31c3f9936",
    "b5ee0bb2-d04a-4613-8159-3117e8390e54",
    "a19ef64f-f897-4e56-8973-5ba9c3e6fa99",
    "9d4f72bb-e61b-4655-bf24-86369c8b7649",
    "a1783dec-0cd6-4dd9-a5e7-43c334343c45",
    "7ae69a22-f058-4bcd-91e8-0bd7be3580c7",
    "8128b5f0-c8a1-4756-aea7-2fbeba534b85",
    "02c4fed3-92af-49a9-a0eb-54b881609ec7",
    "67fce24d-60f8-4386-8c47-0110d0518fdb",
    "b19f2941-b70a-4a7c-a103-632c055a0ede",
    "ff254d32-328d-4e8b-b5e7-d969f3d7e49c",
    "ca98564b-29c4-433d-a180-7e7f2a0f2559",
    "29ecd742-55ed-4d53-b99a-6d8b66a95fae",
    "de08804e-24db-4731-9544-2c53a45db2a6",
    "ec90f498-ae50-444c-83a2-8ca30f4a946a",
    "a909aea6-11dd-4517-a668-67ecfbd01b29",
    "9c36d21e-fe2a-4853-9455-04257437b4b2",
    "cb58fa18-cda5-48c0-809c-a4a711dcad8c",
    "bdd4daa1-26ef-4494-905d-b64f75992599",
    "9dc160c4-b54f-45cc-9989-26c3318e2540",
    "2a77e17d-6007-491a-b124-ff8201f0ad44",
    "5ed6ee2c-9be0-4e6a-b1e3-bb30f2688912",
    "6aa9d04e-9e9e-41e4-af12-05bca8b4cd20",
    "bcd1cff6-e577-4f36-9b76-f67a6757e759",
    "29c139b0-131e-4762-8728-065af294e609",
    "5eef5901-2c65-4e74-ac95-69576b2c8a31",
    "5f460230-5b46-45f9-a819-30e359205500",
    "ed48e88f-09bd-4886-88aa-e6f1f49658a8",
    "5d4aa52b-83af-4dfd-9616-b758af9e3bf9",
    "3f8f414f-52e3-4897-b4e4-223703e337e8",
    "57ab2797-7d44-465d-be06-8ad497601cb1",
    "fd2540e0-620c-4470-ac1f-5f992cd4b98c",
    "92ff2ab7-2e5f-46f8-9dd5-aa38062afee9",
    "8582a2e7-349a-46c7-a842-6a71fda06ea6",
    "d0ff43dc-33e8-4b44-8883-3a6986d0107d",
    "7ef25e78-c122-4f91-916c-68ec569feabb",
    "d5124364-da14-45ef-b2db-cce497b82c61",
    "e82e25cd-e5ed-4bef-9f0f-a919c2f9702e",
    "a22f97a5-446c-4207-8b3e-906eedead066",
    "c23deaa2-d30f-4ae7-aac9-1f2ba1cdd5d7",
    "62e55cf2-a9d4-4e51-9255-ecb1763c8837",
    "c66694ab-3c42-4b7e-ae5e-672ca3c4593c",
    "14a7c2a4-aa71-4153-897f-85f647fe88bc",
    "a1fe59b7-1fca-4f2b-bd5b-8c5581c06cef",
    "9445e3fb-45d0-450b-bdb0-fa39022051cb",
    "bef1f722-ea23-45e0-bbf7-0ded39f16b1b",
    "7f8975f9-376b-41f9-86c7-3e40437d5d2f",
    "c146adf2-79d0-490a-bd1e-9c4c1eae393f",
    "649f92a6-9cb3-47fb-a196-850e68f9b11a",
    "91a1a239-f35e-4da3-97f8-7e2e23dd6c9e",
    "397c3085-885b-4ea3-9d96-fc529367c578",
    "1138ca4c-900b-4b8b-9dca-b552f2695def",
    "4a14546b-4017-4fcc-b1cd-06a96536b096",
    "7df3d095-013d-421f-84e8-15ac25971708",
    "50bd53fc-775e-40c0-bd72-d9d1fa13a45f",
    "ed4f0530-afde-4a56-b519-9024ea561477",
    "365b980b-aa2d-415d-900c-1f78d4887728",
    "f1154d84-57f2-451c-a721-667b24ff83f7",
    "4dd46b26-7c9f-4bb0-8131-2324396dd81d",
    "0489dc3a-45a9-435f-a6ad-64ad5fd79d87",
    "292f2d8c-9a7f-4aa3-8086-d2d873947742",
    "633d0319-4731-4a02-a2d5-0dfd1b0340fa",
    "756d3d2a-75d9-4271-a7cc-2f59a1a11d74",
    "ffd3c103-225c-42b5-8569-f6ce6aecdb51",
    "f3750c40-9432-4607-a549-fd6fddd1c9cf",
    "c35d02ae-2b09-4db5-9542-bf374601055b",
    "2818884c-e6f7-43f2-aff1-e914f1f13e12",
    "ea4b4d4a-8832-4c1d-bbf1-562a83775d5a",
    "76aaa4d3-a6bb-4eb0-87dc-efeb03aebfb9",
    "32d62848-3af5-4fda-a7f6-1503e1c0b2af",
    "c4aa2cda-50ec-45ee-97dc-c3d382ddb0a6",
    "20a56d45-5520-4eca-b126-98e60753bdb1",
    "a8091251-3c42-4b9d-baaf-afa24296637d",
    "a9a39221-13c6-467d-95d9-49dfa2a63ec4",
    "0f061583-130a-4269-aada-0eb465994ffd",
    "46061587-ab26-4b69-8993-56c01ea9eee0",
    "1794dd51-4594-4275-9817-ac521868514f",
    "0c3c7b03-3b15-4e54-82c8-e98ce27aa6a3",
    "c1f03fc7-a226-49ea-b2ba-f819a5179511",
    "0592fbfd-09ed-4648-9964-060304c712bd",
    "88f8d4c8-8819-491c-aeb2-e1689ee77d9a",
    "a10ac468-76ed-4d18-9327-fe4e0718f19f",
    "49951def-5d2a-40ff-921b-9bce3378ddb6",
    "acd216f1-ea59-4048-9159-1518205a2eb5",
    "20d3dbbe-0cd6-4a9d-ae79-ee6832654478",
    "72bb4cef-b689-49a3-a71d-06ba39387239",
    "dac55f22-29ac-47b8-add2-79c5d2cb28b0",
    "49004143-126a-4a5c-b689-fb436dcc6025",
    "fa8ed2bc-550d-49b7-85bd-127f804f8abc",
    "e4bd25f5-4dd6-4800-9f04-66339219ecba",
    "49f809d4-087c-4471-9a44-b7aac673f2b8",
    "0078cabb-583a-422c-b264-1a2504e66e55",
    "8af48860-6597-4b0b-89eb-99a40046c279",
    "c0919832-72eb-4ed5-b482-79fd60a0e6b6",
    "9aaaef6c-74ac-44b4-abb7-6f144d5285c3",
    "17372992-10cf-456f-9736-78cf904e6b61",
    "ffbe8b4f-a897-4289-969b-21e2207acb01",
    "31e0dde9-d8d7-4648-bea7-a4db856a38dd",
    "434b6fed-a09b-4d98-ace5-87be6a958151",
    "226b58ef-d71b-4979-9d07-3e4ca2df6c7b",
    "d8a718f9-4039-472c-82dc-6bfcc1381e81",
    "1b05abd2-9635-41e5-ac48-1d5df6edd076",
    "0b661034-db82-4395-b7d2-dc0c00ac4f41",
    "9c15b0f1-4a2d-4cc2-9b6e-5030ec1a5e0c",
    "06448e63-5794-4242-80e7-819e6013c28d",
    "46052cb5-bdfb-49d7-99d4-b81e1fd2693a",
    "2ea127cb-7867-46a1-ba41-63acca833dcc",
    "c26daf48-a15a-4a51-84c5-57dda134d6c5",
    "cfabade1-b86a-4271-8f6a-c235fd34e48b",
    "34cdc998-d1d5-4763-8e07-cac2b4b30716",
    "0bd10dba-5d02-490d-bd3c-f73b627f1b1c",
    "d9bda379-9bf0-4110-9327-823c674fd556",
    "49be469c-6d5c-4cb4-877a-14a6f12ce8b1",
    "99e646b5-82c0-4460-a2ef-86e5f4916ea1",
    "13ccce5c-f031-413e-b6fd-2badd87b52dd",
    "c0212679-61a6-499a-b81a-61941631d8a0",
    "900d75b2-855d-4e75-8ef8-b0d154968bed",
    "f5622b15-fd6c-423a-8809-a87a2038a910",
    "6d022823-9679-4a25-9cf2-caa034274884",
    "5fa2d650-5489-4b6e-aec9-124ff8827cfb",
    "7b35d6c3-5e1b-4602-b2a6-d6098a1bca27",
    "2f6bf50f-4b22-4582-8930-f4d0f209deef",
    "581bd4ea-d057-4c72-a0d5-47091e8e599c",
    "b8b4845c-910c-4103-8883-582b6c8d7589",
    "0989afaa-a632-4e45-a9bf-5aafb0de80dd",
    "c253b884-a891-4776-850e-797330aacb39",
    "5fb34837-7e49-4347-ad9e-fe9070e8daa9",
    "804ccf61-f29c-4db5-b003-90c1e900f84c",
    "bc4b7e5e-9861-4254-9e76-39c846cae097",
    "69f43346-91b2-45b1-8a45-765c75e96c8b",
    "64df4d3f-ae6b-4b19-be49-2bda4557d274",
    "e00b071a-b7cf-4053-9732-b5278c5408a6",
    "217e4edb-d6a5-4e28-8cde-d066adc28c75",
    "bc10d780-54ba-49cc-afbd-51d1539fc1ab",
    "93906cc1-0274-434a-81bd-bb692d71be05",
    "35aaf77c-cee4-47ad-a986-07783a2f8bed",
    "74dee048-01c5-4a5e-a811-25315e57c156",
    "99931c85-088d-40b4-a2c7-687cd294d5d9",
    "692df537-225a-4e05-bf7d-de77483d38f8",
    "d7ae045a-98cd-4990-a62f-1decd06f4dc1",
    "43bfd324-d4c3-4cdc-bbb4-46b71fe525e1",
    "190ae9e8-74e7-4e79-b246-da25b628f797",
    "efd8f629-0678-4a8e-b424-a01df447cdb7",
    "2446b136-7f24-4685-95d2-7de8aaf75ab2",
    "daac56d9-b0b7-4411-92a0-1e7ff12dba9a",
    "536911a7-e5b5-4f19-915e-4e8746c1f213",
    "c6f551f4-5c92-4f20-91a5-3be2dd61e0f2",
    "78f9c836-2978-4a3f-99cd-8333cccb1fc7",
    "ebe79495-2acd-4f66-8d3f-a0838a4d1e73",
    "74786a1b-075e-4b32-9d46-a9ef8a9df113",
    "e4ff1597-9673-47b2-9cc1-8601de05a8b1",
    "76a56feb-86eb-473d-a95b-34756557a39a",
    "8c5b6a55-19dd-4d08-ba0e-95f8c32db6f9",
    "408f0507-8344-4d60-b90b-a8f9d8ac7a5b",
    "00aca583-0858-4b47-aa08-00d63ee79aa3",
    "e1b17827-7c46-4824-8269-3911e74863a6",
    "6eb71b28-2e8d-4d1f-b47a-ae2c77c5fb77",
    "acccf02d-1a3b-4e47-85c3-0ede48904e28",
    "08c988db-e1ff-4007-bdab-b3973c105cb0",
    "8548d50f-5d1f-497d-960c-15368962a3a1",
    "068a71f2-8343-4ea4-8812-e0a84dd31206",
    "9b3657c8-7602-4743-8e2d-bc6ced6c9533",
    "0f1d50d7-5c27-4f1b-89ea-8fbaa473c23d",
    "2c9282b3-a001-498f-849c-e6449d1307ed",
    "8fdc0b17-b738-40db-b56e-6cf5ccd0d833",
    "e790ce0e-6c2f-4b4b-a912-5f43d48ebd2c",
    "dff44650-e722-497f-bdac-485ee42eacb9",
    "7fa83556-e3d5-4ee2-a9eb-513b5ebac088",
    "98a4d01f-34bd-4810-afd0-8c46a7b535c1",
    "ddf2aa8a-e761-4706-ab1d-05449125195a",
    "27a9b854-a2a8-4405-af64-6879c2f4bef6",
    "943f4734-8622-4d25-97ae-c91b2b2b9420",
    "bb185ec7-f1bf-46b3-82e3-67073a4e6048",
    "f4ea37ee-7b61-4400-9ced-a60fb50a111f",
    "6ee1b29c-8b30-4e4f-9aaf-f616e9653265",
    "cabe01f0-6774-414a-b8b7-4617045457df",
    "1b4d2a63-0753-425d-af31-243a1d7ace33",
    "9cdfb553-549b-4ba9-b9b8-036e9ed510de",
    "db3aac46-f26a-44e5-9e7b-05a8b4cedd00",
    "fff18522-ba18-4280-9a8e-f0c094a9b860",
    "c65dff97-e453-4bae-9153-43dd408c4f02",
    "a1b6d5ee-9d96-453d-b76a-589ec0f60655",
    "35b4c0f2-8006-45bd-b769-fb8c8fe7b4c8",
    "49f209ec-bd34-41c2-ade3-7b12e54b29cb",
    "bd1901f3-aadf-462a-9b30-33c11e0972df",
    "6292150b-5c18-4abc-a421-3b8dcaedd016",
    "cc9b5a1b-bb1a-415f-b2a2-308f3a866dd9",
    "d1e6f92b-e61f-430d-82bc-0e88ef353e0b",
    "9750c622-cc72-4215-928d-6e128d42b56e",
    "87e471ba-6181-44f2-92b4-67e3a995ee67",
    "97ab8992-4967-4610-bb85-85844ecbad5d",
    "21a81190-6b01-4f4c-aaa7-cb8a6eee641a",
    "5d3ecf96-a48a-484e-8eed-e1609545181e",
    "9a990094-328b-42a1-a8a6-1c7a728807f5",
    "fc6e2a9d-bc10-4c46-af1e-da1affe02211",
    "f10be9ac-abe3-4298-92a1-cafa0ca52a56",
    "239a8c99-c272-4fae-a311-f84c02ae29f2",
    "367e3959-f3fe-4696-a0c2-f1b7b1a6ef42",
    "cbd157a9-fb66-40eb-bc71-308642d9fac7",
    "0a3a4454-a253-49cf-9d29-0bac4bdcc008",
    "f011f816-8f05-41df-a55b-ff26e61d7e5b",
    "494ca275-b780-4e11-8dcc-098b37d427d7",
    "4ddf4cf9-74d7-4e98-8c51-aeda3fe64299",
    "04438584-933f-4027-88b1-8088d4784c7d",
    "588b3c86-0bd2-42ba-b9d1-f3beb4b356d3",
    "316efab9-2a98-46cb-8612-43cae5c3b756",
    "d08924a5-3a09-4a4b-8788-466d8f6bf187",
    "acda970f-e4fc-4202-b3e7-0cea640655a4",
    "63962962-ee0c-425c-b3ce-4f4f4df55f81",
    "56ec4295-b554-465f-91e7-8fa66756c635",
    "8a89d18e-b3b2-49f3-8362-2717e9fca4e3",
    "bff1c6fc-f7b1-4b6a-9d39-ddfe9424b8c7",
    "1042516e-d818-4f5e-b875-c5c8c848d139",
    "6bed5b5b-4298-40ab-bd2b-f9aa302e29e4",
    "9b7264d9-396f-4a60-9239-54b4ed586422",
    "ac513042-b0ce-4a6d-9023-fc04cd76d4cc",
    "897486a1-9c6c-4c5d-8ea4-c3312c79f49a",
    "d63fbda2-e84b-4af3-aabd-bfbb69ac7040",
    "96e919b4-65b5-436b-8bbf-b5a1c59effb9",
    "76efb173-35bf-44ba-9177-1aa377dc1f52",
    "e067dd22-5901-46cf-b3bd-0c1233eebc0d",
    "2efc7649-42d7-4e5d-84da-3fdd652b4daa",
    "32a863a0-1a39-4a73-94bb-8f4eb20b87cc",
    "ffc746c8-095e-4b37-be2e-4b426f801408",
    "fa5febb0-a010-40c5-a067-a0aa79f1a80f",
    "fd78226d-8fa4-42dd-828a-dae071f0aee8",
    "fadb30df-044b-41b7-9d69-cd3c43266717",
    "44909f00-5388-45d3-9b33-a79b7846f1d1",
    "08a02f6e-5b9b-4571-8dd2-101498a5d46d",
    "294eb1ae-86f9-453a-96a0-3cc09a2883f4",
    "5b1f5f85-84d3-4984-8f13-9087e96b4d9d",
    "cdb8a5f1-9e09-4a61-a85f-fb932a7decf5",
    "c706e905-f7ca-4972-8da6-e53e807d3807",
    "f073c4ea-1342-48f5-8075-1047eeb02988",
    "dedb2b21-1816-4f36-a361-d597bfd90490",
    "0fa352d1-e6b8-4fdd-a79a-36b019165b2f",
    "acf1d27b-26c4-4f14-9dd6-9b1bc2109866",
    "00681d71-5eff-46ff-b488-036ef3547dc9",
    "70714e76-7380-4ea6-82ab-d02703387d2b",
    "00a3044a-a632-4969-8816-993f8d8db98c",
    "3720edd9-b6b1-4e7b-8d1d-9f4981d2f928",
    "e258497c-07a1-4803-b742-bd94e9ed9bf0",
    "6d5ef591-baca-44d4-8a21-c86b573a2b56",
    "8dae3b72-4e2f-4ede-bc18-550a92afe820",
    "c913d5e5-c3ef-4bfc-b510-00f61f9d3ebb",
    "cab73bcb-661d-422a-bafc-a3fe237591d0",
    "c903bc55-3b83-4dc4-8a78-bc480ca214f3",
    "fe9a029e-7a90-4136-9a57-ea8661e60fdb",
    "38f8ffbf-510a-4c1b-b048-e416b28c5f9d",
    "dc6dd312-7f02-48d9-bb98-49ef9c4419cf",
    "3937e2c8-38f9-4bbb-9c1b-2b197ff7f552",
    "94815216-9661-4d58-a81e-69a7d9cf9d77",
    "a2a7f04f-ef2a-4173-ad66-42a33cbe2a58",
    "33bfa813-6307-4e53-afbd-5d43aac399e4",
    "3193b7d9-6340-4ca2-9938-bcf3eb302cd7",
    "21ce1e6a-a9a1-4ad2-8d8f-155d1f9dd302",
    "71f24d56-190b-40d3-b51f-7b9222a1eebc",
    "bbcb946a-2ec9-4017-9795-7c582b8155b5",
    "d97fe1d1-eac2-49ac-86bb-7b5d81ed6751",
    "0651464e-1e5a-4056-a241-0ac3e5daac10",
    "b8636ac3-6606-40f5-b6bc-c7b9b6aebfc6",
    "a6a60ea3-7803-4c99-a0d0-efc612c8d126",
    "ce6d53fe-13df-4cae-a6ad-8d527d91ed1e",
    "6eb1c645-570e-4262-a027-b15864ae5c93",
    "a32f0fb8-0f83-46c4-9822-3e21f0c3890c",
    "85262ad8-7958-4971-801c-2d7baea7e095",
    "574488e3-6c79-4f77-be61-8c71b818e212",
    "f1f7c23f-2c14-4c02-964e-faf7b4790f60",
    "c372a549-5dc1-4beb-9095-489d19a67c61",
    "57716de5-7af0-4629-a604-173dddb6926b",
    "87c2b63f-824d-4b72-8cb4-72772190da50",
    "201da91e-9165-4c7e-8775-dcaa96a2ad6d",
    "d7381a8a-5802-4e14-84ca-d5e6c039ea1d",
    "dfeb0536-7ebb-4f12-899e-01797bca45a7",
    "26f8a662-07d3-4e22-86c5-b511cf33e2f1",
    "71c6fa1a-5f74-4db1-b375-d2083bbfdade",
    "6de2e4b1-8b37-40ab-9cc3-915b0d936e7e",
    "c6649393-641d-46f2-a16c-172a5997485c",
    "99b37bc5-bcbd-4128-acae-3845ab51e1fd",
    "d317dc57-9a0f-489d-b703-cd044dffbb6d",
    "78e73c32-905d-444b-a7cd-0a211a300db5",
    "86454dd2-d2a9-4a46-8b49-0f5d94b48f45",
    "6b24ae05-b4b1-4ed6-b911-fe002eed2199",
    "3c58cfa8-b7bd-4d05-9d1e-4ad5b425d3f4",
    "828a58b6-7b4d-4f5b-a378-9518de21478c",
    "cc985868-5f1a-4afa-b7cc-fd825a0ea0be",
    "2642d6f3-0514-438f-b7b4-54b8bc880336",
    "958256f7-afb4-4fb5-a915-2c063f7d14f3",
    "588c74a8-841f-47e7-894f-02f36c45bcd5",
    "070ecb86-a066-47f6-a284-201ecb2b7e58",
    "96cc3619-1aba-4b76-b8b9-18138ff3fe86",
    "59db7aa4-294a-46e8-8f30-862d0a2ab232",
    "c63601a9-f626-486f-8018-6b49081bc929",
    "64b8e0cf-83a7-4dd4-873c-82c051bc1b48",
    "85f45985-d43f-4ab3-a961-8597921da5f5",
    "e0fe6c00-5ab7-46d7-94e7-c82123dcf05b",
    "dfa16555-028e-45e0-8a50-fc84ebb9758a",
    "d96a0111-3b86-4e99-abd7-ce3705a2d94e",
    "82c4d6e4-b9ca-42e5-96e3-245a1eb7a3cb",
    "9e1cf4ae-5657-44a8-9530-b57c87c53d00",
    "c9cb09e1-a24a-4efc-b529-13447fdf6d2d",
    "8b862fc5-1b8e-462b-a134-7270c673afcc",
    "34858862-3eb6-41a5-9cbe-9c8d95d118b9",
    "7f84cdb0-375a-4105-973c-84830c709e4b",
    "a6827a92-634d-4e12-82eb-3cdbda6592e3",
    "6cfa0d4a-f002-4f6a-9de6-f4365e8128a2",
    "5e90b917-f6d8-49f2-8bce-32f76d0fefe5",
    "7d583225-574d-4eae-9912-816f4726a115",
    "03694603-3d9f-443e-a0e0-2e3497510d71",
    "c5710186-4a28-49a7-b99d-36bbdd9167eb",
    "ee99e658-af48-4ee8-ad06-6eb0bab9995d",
    "d662277f-b393-46c4-a53c-08f4d096f7ee",
    "c75b6a64-8bda-4d0b-a02d-616a2a7cc851",
    "c498333e-8cc5-4767-a72c-4c8cc225b9e9",
    "34dc6b64-4579-42e8-9cd0-7fc027e6ea95",
    "04680c2c-9cb4-4cff-86d3-43ef2d49c4fa",
    "1a61d70f-b632-46d2-88c5-b3aa8c1184c6",
    "e64a451b-d940-4a8c-a069-3a67e81c214c",
    "81d886ff-dbc2-48eb-878d-1affc237bec2",
    "53a68ad7-d6ff-498e-9c9e-9df8341ade05",
    "b62a1e82-652e-4cf6-96c2-5a963e06b928",
    "f85352f4-e561-41b4-81ba-022438cd0464",
    "00adfe03-75f3-4238-8ac9-e436eed3c820",
    "42bf7606-c3dd-4c4c-b1ad-eea90bf30f7d",
    "35194a06-61b0-4419-8bdb-1db3ecdcc3ef",
    "082e324d-315c-4bf3-9673-4e6f8e9c51ae",
    "0e06f4df-1be4-4d45-947c-c35d079c61f4",
    "3ca0aa0a-789d-458e-a32a-332e7029a817",
    "b870a6da-3bf6-4670-bd88-e7912ae66c79",
    "3c6a5899-e9f3-422b-80c9-abf68e0d482b",
    "f21ff255-4638-4f42-803a-869444b796e6",
    "8e97af43-e0cf-4cda-be64-049a297921ee",
    "aa12b727-078f-4118-ae69-c4afbbdf35b5",
    "397bf14f-5dde-4196-a0a4-f042b05fca87",
    "2a2d2fa1-35ea-48ff-a665-4acb9b5e4f3b",
    "2899f71f-96b5-45f4-9d7b-31b25125cb78",
    "884dfbf2-00ac-45bc-b35d-1c6a50a548e6",
    "8cb02433-d4bd-4866-9d7d-21e9d93cff5d",
    "9587ec63-f060-4475-81e3-edf43eaa97ed",
    "0fae9b11-22cb-4421-9aa9-db932b67e161",
    "4def4617-eb6b-4b4b-9ea6-8cb7820705d8",
    "4e6d1319-f40f-462e-b20d-c9de34314903",
    "5422efad-3a8b-4260-b199-565ea582b79b",
    "92f5ac29-4ce7-405f-a88b-5cc47dee402d",
    "21243661-bd33-4da6-87f7-d43b518a846c",
    "09fecba4-241b-4719-b0d7-b53f5d3ad48e",
    "6409f959-b368-46b8-b3f7-d48374c601ea",
    "edc491fe-9fd9-4a1d-ba70-18cce438da74",
    "3df3dc64-aab1-4743-9a7a-72f18b1c1ab0",
    "972ee537-c1b5-475c-9801-d1489d56974d",
    "5ee281c2-3655-454a-83c8-554c60c181a6",
    "e356bdf9-4f26-4029-b10d-96c9c44b5678",
    "d42abb6d-ad45-4cbc-8ff1-1340b628fc86",
    "8760f85c-edd4-4a15-864e-a4f6eaf2d5b4",
    "8e48aac0-70ec-4947-9c39-9c01a9bc5d63",
    "4a932a46-d184-4219-bba1-b55d5ff62f61",
    "13bb5f24-a4ad-4e0b-88e1-c77fb0c85f97",
    "7e61afc2-6927-4136-a510-b05d5f91d26a",
    "5a470738-d880-4bcf-98d5-600fd76cf6aa",
    "a6be7aaf-b465-4973-bf10-6e557aa9f3dd",
    "bd3619a8-73de-4240-b77e-85ef3d6f6ab5",
    "82bbd332-0633-445a-b4c4-9f4c8f8382e7",
    "1db71e6a-ca11-4c71-8920-2acbd2db9574",
    "2a5bbaca-cb2f-42ee-b284-74011de1c9be",
    "b07f65f3-8e7a-4f4d-8f6b-1c81e60e8190",
    "40570388-b721-4ca2-9248-c81163f94ce4",
    "45c64297-4f13-4f8d-87b6-c707ac5ba324",
    "511ef9a0-3568-4363-9320-b774517edbca",
    "04991462-d442-4408-bbd0-31a071cde57b",
    "d55575cc-03bf-451f-b351-c2be276323b4",
    "e25b1d8c-65ab-48ac-aa15-7b9bda7574b0",
    "48312049-e082-4e88-b767-2b052371a577",
    "16b3c3d4-d817-45bd-a63e-b3f85d26c607",
    "b89f6401-8d64-4ad7-b47c-8a54c4e68d49",
    "79429c4f-f70f-4b5c-8ce9-358195219737",
    "4c6b1dc0-8f5f-4ca6-aa40-316e7c81120e",
    "7e23f9c8-2f65-4e34-a16b-9d84194504bf",
    "801cad72-765f-403a-b3d0-329df98effd0",
    "36251437-dc79-4060-9d0f-2fa7991ecc55",
    "bf54dce6-d133-4a6a-bc47-8ae6250453ca",
    "49ba8ec7-e02b-4ab7-8eea-efa9cc10eb13",
    "a6278d5a-242b-4fbc-965c-2fe596fdb3d3",
    "f9ba922d-9d77-4d32-858c-688ce95c9799",
    "5f34b9d2-6d87-4463-9d02-82758b2e3c93",
    "cf05ec00-bc63-4c88-a45a-47feae6df2a6",
    "02428b44-41e3-4755-991a-d7480dee7275",
    "a8796b29-7c7d-4004-b74b-cb278ba2a755",
    "776ca637-e4b4-4dbc-a02a-1a90f36f1751",
    "fcd9aa2d-069f-4642-9cac-fbfc612cc05a",
    "0be215c8-2750-4df5-83e7-0591cfbedb0c",
    "4a2ea1cd-56ef-4892-977b-36f21d66a704",
    "19bcd8ea-9c3d-4347-9a7b-1b8b3c7e52dd",
    "282fe760-9d91-42ab-92e9-e9f3dbeaf0b4",
    "d6277821-97c4-430e-abc1-3b6e0558b811",
    "6836fced-2a0b-4ec9-9362-f4b87bc84822",
    "eb3e207a-2779-4223-b937-afbacad3e40e",
    "a0c2e9ae-16f0-493b-8ed1-f99b0e3facf9",
    "298d3893-23cc-4a01-9e16-1fc888f9bca0",
    "5a88ad00-1cab-4fe4-a389-d787ab91b33e",
    "f9bc6493-c21c-4c67-9ebd-761716c4950f",
    "56ac3795-cb6f-44ce-ab7a-1d5c8a97f2d5",
    "9cbe4a6f-5fd9-4216-afb6-b7525751ff32",
    "e70408ab-a4b0-44f5-bc9b-92be93c1ba15",
    "fe4fc206-e923-4775-8392-caae8019509d",
    "a9a34c53-8898-4c0a-a0c5-94f688b371e3",
    "0fbb841e-d5b5-4bb3-a857-cbe2fee43d9f",
    "fad4581a-f259-487a-bc3e-11551a823d42",
    "401251dc-6783-4b89-9fe2-55078426838f",
    "f59f2096-fe5e-497e-8509-8ae094c839c8",
    "44876f8a-634f-4fd8-80ae-497e7ddb5e91",
    "b9b7f846-27c6-4d96-930f-f29b108fcf8f",
    "8e447bfc-151a-4781-9285-5115ae6401fe",
    "4f694879-2117-45c0-8729-8d1710ef8502",
    "f68afbaa-b317-4eb9-bc94-d266b8895579",
    "0094ddfe-bd65-4f6d-afa9-05c01dc60825",
    "e6167a75-109b-4d7f-9e1e-be2a9b702878",
    "9809ac24-a60d-426d-ad31-4faa778f40ce",
    "ee79d39f-9f3f-4c6d-9d66-7354edb50913",
    "49abe958-f6e7-4ef3-9e0d-d3e59ce2eb2f",
    "8584e316-c536-48f6-a049-2362fd38cd8c",
    "ff743a7e-8e53-4b66-992c-6f2ff9b84e2a",
    "460bc998-fefa-4e84-89a5-251c65adf217",
    "bac97a68-717b-423f-920d-e75b261c0a56",
    "31432205-7dd1-4fff-bca1-9a89e17f27b2",
    "39c12980-5d1d-4945-bc15-b8e0cd37c655",
    "bd576e0f-6b80-46c2-986f-01e95bb351e7",
    "d9641959-0eb4-495f-abef-d8dd12ce4190",
    "913021a5-6581-4d69-b9e9-c912ff8dd341",
    "4e6555ee-f1c4-45c2-b81d-01452a9a407b",
    "b1292d5b-7609-4085-b943-5bc53634864f",
    "de72622c-d5fc-4516-9a6c-f7a1e6918ccf",
    "db83221a-49c2-4bc0-a5dd-de555461849f",
    "38d7be6a-4bfc-4222-a44a-b2f27c39b2ee",
    "13788819-2d1f-402c-99ec-af3083418200",
    "bfbdef74-d430-49be-bb5c-bf72c34f32d6",
    "e668de10-6cd5-43b5-a53c-685b85835d31",
    "74f9e026-b33a-4c02-a4e8-358cbd526759",
    "9a6ec5cb-91af-4e4e-a768-5c7e6ba74b6b",
    "f7c58a15-eb3e-4041-94bd-6c4c7dff6dfb",
    "f26ae0ed-c7dc-4dc5-b42f-35f46f48e16b",
    "52cb1311-a903-4869-ad95-0c0f02f62dab",
    "d518dad0-615e-49e0-a145-dc8aedb6cb27",
    "d51d059f-0f9f-462c-8039-04bcdcfd018d",
    "1c14f10e-1ff9-4cbd-a486-2cc9013bd58a",
    "dce057f2-2b96-4729-9f93-0c3efc772cf4",
    "915bc0cf-ce17-4904-afde-ec1700eef51b",
    "4c68c3c1-dcbc-4407-a06e-03e786241e48",
    "266d4f7f-6f81-4764-91da-3425d23d26b1",
    "5d66a12f-83e3-4c96-b5e3-6c1401230a51",
    "93357a8c-d120-4c78-9ba3-9f4f8c1409ea",
    "f60cf92f-9aab-4e5b-aded-f43d75d1c36e",
    "5f1970e1-f474-4258-a674-ba4986374556",
    "f9f9b8c0-4fc2-4fa5-884f-eb37e9eddb4d",
    "23d02742-29c7-446c-9905-59f08a817172",
    "c4182602-e687-4ff2-ba25-f424f251c768",
    "8d6586f4-d596-411a-a756-640812ac6718",
    "3bc10b93-3734-4c34-b432-8b4eae00864f",
    "105760ce-d9f5-4b08-ac6c-6fb916d678b2",
    "010ac864-0af3-4b30-9d35-c6612c5e3484",
    "a8daa3a1-9efb-4b3c-8371-b1fbaebbfccb",
    "d5f4cbea-dd44-430c-a530-5ff46f034bcf",
    "ed8214c2-5eda-4e4a-9f6b-de1f7d153be6",
    "4b60b0fb-4554-4912-9471-99b857a1532d",
    "1cad38b4-3789-456e-8989-172015c065a7",
    "bbd90cba-62a0-40a2-991e-f82d371da06f",
    "2b100d61-d9f7-4f40-ac5b-29e9038b4b19",
    "a92ec77a-bd93-44dc-9ac1-dca651138538",
    "f10d750c-457d-4b7b-b557-56616311ccb3",
    "b1793174-f077-49bd-a13a-322ca98965bd",
    "a56470d8-fb28-4863-83ba-f1bb9d765d6a",
    "bf3f6eff-b605-46f5-96d6-b0d953916871",
    "9e910e9a-4bbd-4961-b667-4e88b4f4086b",
    "21a4c162-5d6e-49e0-a8fd-563147ebb068",
    "597db44b-a7a7-4ab9-801a-f94b113e06dc",
    "1de24f42-4c9c-49ba-9650-398358e6e50e",
    "b9b3b498-f7b8-4a5c-93e7-e2228170c782",
    "8ef48591-224e-4ae8-b237-adccde37ea8f",
    "694410ad-26bf-4ebf-b9bd-6490a344b5d8",
    "7f8c0588-8ce6-4a4b-91e9-973655d95b2c",
    "4422f800-58eb-41a5-b9ef-ddf1474a2908",
    "6903e54f-6088-4006-83fa-2ddbfe82a984",
    "4cb23b7a-6b82-4325-b9a4-bf188bb50836",
    "f1eb621e-0b90-475a-9933-de284a59943f",
    "b6ea6256-b7b7-41a3-a878-6af9120bf104",
    "cd35b5ea-3dd6-4f3a-93c5-266c92ef9291",
    "fdae24a9-b12a-4b92-910f-f28a91fd2b4d",
    "657a473c-c49b-4708-ac23-2d2b0e645ee2",
    "adce92c0-b57d-48e2-87e8-4701e842ab51",
    "f85f11c1-bf7b-4970-b7a4-02d6e90329f3",
    "61168d5c-d9e5-48e3-bc32-0d783608abe9",
    "6febf82d-aaa9-49ff-846d-0dcbfb8ae779",
    "95de2ba3-c5fb-491b-a2cf-54f0124ae73c",
    "d9e3b26b-0794-4f11-b055-67533e88c2a3",
    "52d82ed7-d667-426a-8ce8-b46f898c9b9e",
    "5539cc33-7782-4ddf-806d-d37fd3a6c762",
    "6ff77e3d-af36-4bca-afe9-a5add49966fc",
    "a4ec3927-ab56-4f38-8f08-5aa9e452555b",
    "70289e7a-7bd9-409b-93aa-19828ca0f578",
    "be5beea6-214f-4190-9e85-ee9179d2f512",
    "a0e664d8-149d-41a4-a262-a2eae2e67d7a",
    "0ec8a366-d8f0-424b-9162-0cc1e421d9e4",
    "6669fe41-eddf-43eb-8dd7-b514810a2e5d",
    "1673b111-8f29-4a66-8c1c-863d24095f59",
    "168166bd-95a5-46af-b619-7ad6ce0ed652",
    "e24bffbe-6a06-407c-950c-56e21a859a86",
    "8011ad62-c52d-4578-a3a6-0db6d1566960",
    "ca1eeed0-0578-464f-a54f-dac545490fd3",
    "f7034685-9436-4236-9bbe-5fa061dcc799",
    "9653ac9e-5878-40ed-a29e-90da7287d99b",
    "bc305ad5-fbb5-46ee-9d50-8ed809b3ddee",
    "5c333463-556f-497d-b1cd-9591c4da97cc",
    "23be422e-7dac-4104-a645-a82d17def312",
    "a21a4a29-aa72-4d13-bc03-74d90166c206",
    "13cd9cb5-0289-4930-a796-ccb316b90268",
    "656bcfd3-3b45-461b-bab6-982797420ce6",
    "89a81a2e-7ca5-4fc6-8be3-b68a6a7260d5",
    "ebef7209-fb53-4a1f-b4fc-19b5e9b68101",
    "8c24e1f9-5ef3-4ade-93ca-89ca4adb3f6f",
    "d657088e-e609-411d-a54b-a4ac26d58ff1",
    "1cdb2e3c-7330-400b-9dcb-c3307391441d",
    "f1bd4ad4-47e4-4734-ab33-c3a70e0ac00a",
    "4d54b0c6-f989-41e2-82fd-13f6b0bfbc8b",
    "e4445785-2542-443f-9655-239add50c2e4",
    "69afcec8-9da7-4c4b-82c4-0232836fdb83",
    "f369a9d1-1aa5-45f5-a7d1-a5c36448b7e1",
    "39578f66-fdb7-4c07-b362-6fe616c1172c",
    "eb50fbfd-ac1f-4e79-b500-a3ccb99335cb",
    "683d8089-be16-4881-bce2-6170b35a89ad",
    "a8575a64-9647-44f9-9280-be4e44dc02b4",
    "a17f10ae-fb9d-4967-8b54-137419698ae8",
    "69e251bf-5627-43ce-999c-704174df066b",
    "c5602e16-bfac-4225-bf50-99d4e2bcdf04",
    "1f5e45ef-2f32-4481-9dc0-633abdbb047f",
    "df42368f-cc54-4b7a-952d-3f117f239104",
    "ff9c3a30-5141-4377-89ab-b3feb9bd2fc4",
    "08ef18a6-0364-4314-967d-154fccafe994",
    "bc81c43c-d709-486b-9a91-dcc53680a12c",
    "6d5c9e2f-852b-45dc-b974-e4752bacf67a",
    "8e8b1593-b304-4968-9552-910d5ac60cec",
    "0a9a91a8-ac8e-49cf-a3e3-13616ce41cbc",
    "20f8a08b-8d8e-4145-b2d4-a04e25a295ce",
    "ffd17115-ca9d-4572-b0b7-9a25ae9c18b4",
    "952dad72-43ea-4902-b2be-14bea187c328",
    "b5c00d33-0114-4104-bd5c-d4ec9276dc12",
    "971db86f-e136-4542-9946-70f3d478e9ef",
    "38f3950c-e7ad-4257-ab96-a611bda919bd",
    "e3daed87-23ea-4a27-8347-05fbd7880caa",
    "2ff031fe-1d3f-481e-a6e2-c16f3efb9d38",
    "797b9806-9c46-4c02-a901-7f4f98aee76c",
    "15cc9cf1-148d-4f4e-ba01-1dbe303ea724",
    "ed2f9a84-de7d-430d-b49f-086bdfbc2e91",
    "968ba06b-0297-4256-b4a8-507d9590c716",
    "4cece9fc-96da-4bcb-b8bf-dadb0879a647",
    "8bd159d2-6b26-449e-b406-b89475a20f95",
    "9d46dd26-4d4c-430b-8fc6-1b8109bbaea0",
    "52c48917-c84c-4329-9f7b-5a2cad25631f",
    "0d239487-57c5-4cab-b6e8-4a5cf0421218",
    "d261d989-d243-4157-a6d0-7085ae46de2f",
    "b4da3581-63b0-4000-aa4c-24d4e25b59d4",
    "9d24fb84-0970-4580-bc66-f3d62e381bb2",
    "bbd13650-0a88-498c-82d5-f121c0c1a939",
    "339bc14e-6cef-48bd-9fc7-592959a396c2",
    "65de7bd6-f43e-46b9-acae-63a23a2d1780",
    "cbbfeb44-813f-474a-b9f7-04a59e8d48e5",
    "b7660b0e-2259-4b79-a69f-0b5e7d827522",
    "4ee5ab25-e322-4336-913a-ced18a0e1bb6",
    "ce9f5081-7e08-461d-9efa-fd0924eea88b",
    "a11cea2d-18fc-4f86-81e1-6d0a8e719822",
    "c7e80e0a-b6c3-4809-9e3b-2ca2602f2f94",
    "7ab4b116-f3d1-499c-a75d-186f0a56c9a2",
    "434f2dae-7384-477d-941b-207dcdf1e751",
    "ed003363-eff5-4c5e-af5a-dd7592b423d2",
    "0e9f13aa-ad76-412b-970d-7b32c8c333c3",
    "041c0f35-8bf0-446c-a2b3-491ae287d98b",
    "a14ecc45-403d-4678-8241-fee30087e7b0",
    "8e097c88-05ce-41ef-b5ac-ca3e44613a5b",
    "8357751a-4665-47fa-9506-a1999a31f925",
    "052f251a-0c16-4d7e-9341-e626b5b9e111",
    "ae878800-0158-4fac-a85b-b1b3e2165fcf",
    "1a711a7f-ac3e-4d4d-8744-148950388946",
    "06d37ce3-664c-4769-8f52-fad077e3fea6",
    "a9e41828-9466-46cd-9239-97f2b30244f8",
    "3562c195-5726-4b75-9868-4709561b9478",
    "ccdeab11-c137-4bd8-94b1-dcb7cc3a49dd",
    "81736f5f-0bd9-4381-8150-c1ad3877601d",
    "f3ea1fcb-a6e8-45ed-b92d-44757017f2fc",
    "1064ed11-b3af-4859-9142-60da116aaba6",
    "d420b54d-b1f0-4afe-bdd5-ec51462d6624",
    "1e0004b1-3c19-42a3-b941-470047570cad",
    "14e64f10-82f2-46ad-97f6-95985571c8f2",
    "30964a64-3182-4314-bc9b-1807a95bfdd7",
    "674cd507-093f-415a-bcb9-d189d2f6444a",
    "a885a205-62a4-4918-a044-9f30586338d7",
    "6b78301a-6271-4cdd-8a77-6a864e784d1e",
    "4208c973-e02b-4361-9abd-95f63cd6889e",
    "cd4e33db-f0b7-4122-929d-12c102d1ad20",
    "3c546f8d-5387-4a10-96d5-acccdcd52106",
    "d882b07e-d37b-4ca0-958d-43daceb50659",
    "a821ae5d-16df-4795-bb59-f966ab0c53c2",
    "839a2d1e-1701-11e6-9243-04019c2dab01",
    "839d33b0-1701-11e6-9243-04019c2dab01",
    "839e0632-1701-11e6-9243-04019c2dab01",
    "839ec2f2-1701-11e6-9243-04019c2dab01",
    "839f8bf6-1701-11e6-9243-04019c2dab01",
    "83a0fdf6-1701-11e6-9243-04019c2dab01",
    "83a1481a-1701-11e6-9243-04019c2dab01",
    "83a1c2c2-1701-11e6-9243-04019c2dab01",
    "83a2e562-1701-11e6-9243-04019c2dab01",
    "83a32de2-1701-11e6-9243-04019c2dab01",
    "83a3a218-1701-11e6-9243-04019c2dab01",
    "83a3e872-1701-11e6-9243-04019c2dab01",
    "83a42f3a-1701-11e6-9243-04019c2dab01",
    "83a47abc-1701-11e6-9243-04019c2dab01",
    "83a4b2d4-1701-11e6-9243-04019c2dab01",
    "83a642a2-1701-11e6-9243-04019c2dab01",
    "83a6ceb6-1701-11e6-9243-04019c2dab01",
    "83a71682-1701-11e6-9243-04019c2dab01",
    "83a790bc-1701-11e6-9243-04019c2dab01",
    "83a7d81a-1701-11e6-9243-04019c2dab01",
    "83a81cee-1701-11e6-9243-04019c2dab01",
    "83a86500-1701-11e6-9243-04019c2dab01",
    "83a8a984-1701-11e6-9243-04019c2dab01",
    "83a8f402-1701-11e6-9243-04019c2dab01",
    "83a970d0-1701-11e6-9243-04019c2dab01",
    "83a9b9a0-1701-11e6-9243-04019c2dab01",
    "83a9fe24-1701-11e6-9243-04019c2dab01",
    "83aa6fe4-1701-11e6-9243-04019c2dab01",
    "83aab8fa-1701-11e6-9243-04019c2dab01",
    "83aaff04-1701-11e6-9243-04019c2dab01",
    "83ab45ae-1701-11e6-9243-04019c2dab01",
    "83abadc8-1701-11e6-9243-04019c2dab01",
    "83abe73e-1701-11e6-9243-04019c2dab01",
    "83ac1f06-1701-11e6-9243-04019c2dab01",
    "83ac5142-1701-11e6-9243-04019c2dab01",
    "83acf408-1701-11e6-9243-04019c2dab01",
    "83ad3efe-1701-11e6-9243-04019c2dab01",
    "83aea3a2-1701-11e6-9243-04019c2dab01",
    "83aee952-1701-11e6-9243-04019c2dab01",
    "83af66ca-1701-11e6-9243-04019c2dab01",
    "83b02c72-1701-11e6-9243-04019c2dab01",
    "83b0cede-1701-11e6-9243-04019c2dab01",
    "83b133ec-1701-11e6-9243-04019c2dab01",
    "83b26a64-1701-11e6-9243-04019c2dab01",
    "83b2c41e-1701-11e6-9243-04019c2dab01",
    "83b33dea-1701-11e6-9243-04019c2dab01",
    "83b389ee-1701-11e6-9243-04019c2dab01",
    "83b3d1a6-1701-11e6-9243-04019c2dab01",
    "83b41b8e-1701-11e6-9243-04019c2dab01",
    "83b46882-1701-11e6-9243-04019c2dab01",
    "83b50aee-1701-11e6-9243-04019c2dab01",
    "7d3f705e-8dd6-4f35-a121-3670590d5422",
    "cf147160-3e68-4e27-b356-5738ca983783",
    "3ccf5d35-245b-456f-b634-f75e789e7fcd",
    "8aecc04d-0702-4691-8967-f453d6561bd3",
    "039ab7e0-d78c-4fa2-a49a-4f0009a81393",
    "73acc43b-66e4-4f91-9e5b-0f7132644a3e",
    "087ccece-4955-46da-97a4-338e178aced0",
    "a61aea1f-efcc-41bc-8fd3-3e4c93fc9ee1",
    "fdd8cbb4-9460-4c29-805b-8cf7d0bcc6d0",
    "005b04ed-9187-4765-aead-d539e8a999f0",
    "d82123ed-58ab-4374-ac98-6e44fcf196e3",
    "c4633fac-6be6-4b0b-9642-350353f8750b",
    "7e5e541e-8b05-43fa-aa2f-d5eee6c5d951",
    "fb6307f0-9e34-49f7-b32f-d03eb52e472a",
    "85d3aea8-6b1a-4134-bcee-a81843e5c13f",
    "46b01a60-b5c1-40ee-b7a8-1b8f6223054f",
    "9186466f-8719-4ade-9702-517a270170ca",
    "e5fe8add-a8c9-445b-a7a4-5f16ab44f9fe",
    "7873e44a-74db-47aa-b442-d5cc72a11647",
    "ac8cd695-2a06-4fd2-b940-92bdb47c8a84",
    "d9374827-443b-478b-9c5d-5c0e44dddb36",
    "661407c0-1db8-43ed-acd0-41164e506c5b",
    "ce4445a4-2394-4312-a9a5-f531cc2a5664",
    "b4db9d90-6837-4472-98a5-b0897ffb3443",
    "402814ef-72cf-41b7-86fc-870d638f3e95",
    "940d2d61-ff48-4afd-804b-983730e7b049",
    "22bfd44f-eb9d-468d-96aa-01361740afde",
    "db7deb5d-2c88-4737-9101-b4702cbfb330",
    "33571b0b-acdf-4862-8e54-31576e32d0cf",
    "046b2f53-f2eb-4a31-a322-959c7ccad25e",
    "e359a206-032d-449d-b6ec-e571d8ddde30",
    "2b31a173-d4a1-48e2-9fe9-6994424a2cd5",
    "8dc300dd-0359-4c5a-8475-893c616a3258",
    "9212826a-f909-4794-9441-27370ea57db7",
    "f916460d-775a-46a9-bf02-9e8e0f498c7e",
    "1cc3983a-766d-4088-9177-bf0fa8716790",
    "52497476-2cd9-4a1e-9747-7f7cee7f55c9",
    "88bff8ed-6610-4dbc-a0fe-7a26adc8b9d3",
    "440e92f0-175d-4fe2-b5d7-4b1cf5d4a093",
    "c67e5d0c-14fb-459b-a379-11695528beb3",
    "809e78df-5c89-44e1-85f7-2a8498fc34fb",
    "f6df4791-db47-447f-9790-6adee3f22fbf",
    "3d70564d-140e-4a18-bb7f-e7e3e29f5265",
    "afd4c746-60e8-40be-b609-9defb0a33b5d",
    "414ce167-c5a7-4703-83c6-065058da8be3",
    "b2d6bcd1-5da5-4fdb-a6ce-194e76ad6cb8",
    "dfbbc36b-776a-4a77-8dcd-8c155050173f",
    "890865b8-68c8-4771-80c4-4da8d11a14f6",
    "9e15e00c-eff0-454b-a26f-2fede4ac5b90",
    "26cfb8e4-3276-47b6-aae1-96ec842da814",
    "f60555bb-f548-455f-80d7-5af770f2b9e1",
    "69b1e58e-91d1-4e92-8626-80d05a2f9d7e",
    "a1932f3c-4857-4cb4-90e6-05093734ae16",
    "50f0289e-d47d-4569-968c-eec8a12c3d7e",
    "56cd61bc-8a99-422f-b9c8-1ba1957068e8",
    "f30ba978-6aab-40f3-bb5a-a1d21c55b1f8",
    "7f3f1021-8a57-4c7f-b6e6-b2c534fb77fc",
    "e6d7d16f-c94b-4bb6-86f1-3e4fe0fc6e28",
    "d9f800b2-fdc3-43d6-a6e3-164bb1598350",
    "266db85f-ee68-4dad-8c81-4f0afd6dc1bb",
    "3bf15a93-8876-4c3f-bee9-10d70d98fedc",
    "905e857e-bc38-4fc3-a2e7-41f032046705",
    "270ac5de-96a1-4faa-a630-57051f8b2cfe",
    "284118b2-ce8c-4fbb-9da3-029891fc328b",
    "3186979e-93c0-4e66-b80c-a6b166dba3ac",
    "c58c5d18-f83d-4809-9f97-638770ba3d3d",
    "2ca5e84a-5d05-11e7-a8af-62fdd6d3eb2e",
    "2ca7ac2a-5d05-11e7-a8af-62fdd6d3eb2e",
    "2ca9615a-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cab9f56-5d05-11e7-a8af-62fdd6d3eb2e",
    "2caf0c04-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cafeb9c-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cb0c832-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cb19c4e-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cb4048e-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cb62c3c-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cb8712c-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cbb40fa-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cbc9b4e-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cbe02e0-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cbf72e2-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cc2c442-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cc425f8-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cc56738-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cc644f0-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cc6f88c-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cc7b132-5d05-11e7-a8af-62fdd6d3eb2e",
    "2ccba7b0-5d05-11e7-a8af-62fdd6d3eb2e",
    "2ccc5430-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cccffde-5d05-11e7-a8af-62fdd6d3eb2e",
    "2ccebf36-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cd2e37c-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cd39cf4-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cddf032-5d05-11e7-a8af-62fdd6d3eb2e",
    "2ce750a0-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cf2699a-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cf4b90c-5d05-11e7-a8af-62fdd6d3eb2e",
    "2cf5a182-5d05-11e7-a8af-62fdd6d3eb2e",
    "38c0dccc-37e1-4d66-bcfd-24aec42d300a",
    "601ffbfd-f57f-43d3-b573-43f66b036754",
    "3857d953-c879-4d2c-b188-1d238d452fa4",
    "304a7606-915f-40a0-b234-06532c5aba38",
    "074e7818-bfb0-45af-b92d-ffc0f0dacc1b",
    "20813f23-55e9-4e1e-bf44-d248556dc070",
    "a7186073-531d-4619-9d26-0d7b1efd0b39",
    "88decadd-94f1-4ec7-8895-1116ce3137d3",
    "d459e225-fda2-43a3-9a38-a09aa54038f8",
    "c7a5bdca-b299-4bae-884c-44b0fd052738",
    "bcfa5ae4-7654-4662-bfb5-27937704b993",
    "ec0cbf17-d1a0-474c-b414-5fd53ff6bda6",
    "c747c748-c172-46a6-8ef7-5a9fee6d6b58",
    "c317feaa-9ffe-457c-b5f7-14bbd04864ee",
    "2a097052-cc9b-4e3a-be05-58bfc8577627",
    "28c8978a-b3cd-4150-8e5c-cc8a22737198",
    "51c6070e-d7ee-49e1-aa5c-6639b94c0466",
    "8dc81826-c5f8-4e00-9cbe-a356e85981e1",
    "81b8f708-bac5-4e74-af14-277ba45c0bd5",
    "8daa88b8-8c0f-43ea-a5c6-37085dd0d5c1",
    "a3303847-1d9c-4ed0-ad94-24ede4e65e25",
    "7f04fa9f-76e5-4591-a962-4e8ba0f994eb",
    "13b3add2-669c-410a-b5a5-38939f57dfd9",
    "37614118-47da-4e91-b844-e666cae404af",
    "7e75c235-035b-44fc-bba1-6d6e4b354788",
    "d7576959-ea77-4833-9db6-50eee9382107",
    "dafaa886-7a89-493c-bc1a-82026ef019c0",
    "56801dd2-6c4d-4372-9db1-8563bd536674",
    "1add0346-912c-4459-9eb2-b91e183eae28",
    "9a75e0b0-9c81-4fa5-aea5-81a072fd5bb0",
    "55ce1be7-5983-4528-a0e5-7121c4494d14",
    "407388b8-cf47-45e2-a3f1-51869d69758a",
    "f2d7f880-4734-4067-ab96-56bef2f12004",
    "2d782626-19b0-4e83-922e-48ba817a7aaa",
    "f659ffe9-fa37-4b96-a225-01b4ff989390",
    "4163b6fd-6415-4c7f-bf89-dd2be5c78840",
    "11178a78-6e2f-45f1-9c04-62e2d65a1f95",
    "5e901981-a3e3-4c07-ad32-de253f7f9b33",
    "6dd08c9a-6acd-428f-ab5f-523e8b06a399",
    "fdef5a37-8680-4c79-a650-b6ecedeca632",
    "fdf6a602-1288-49cf-9349-e9df558c43ad",
    "bc123eee-d332-40f9-898f-f9babc8025ed",
    "768b694d-264f-44b3-8a63-00dac611ab39",
    "493dd20e-0fab-40fc-90ef-affb2a0710dc",
    "874de413-dab7-470e-b893-cd4c85c43183",
    "a04853eb-cd1a-4951-81cc-120df29c7557",
    "88a13347-e2a9-4454-a164-fea73635dcfa",
    "2ff9ae56-47b4-42b8-8a00-9147f6cde30f",
    "8e72db65-cead-4439-b5b3-0deec7a40d8d",
    "209575e2-7e7c-4b7e-89d4-ff861c303d1c",
    "38e02ffa-6eb0-46e1-9eab-a51e8c207d79",
    "1916a023-48de-4cec-8923-559684164500",
    "ea710cf6-4492-420b-aa4a-49672857c1f8",
    "4757c38d-d7cc-4aaa-944f-587f1b31662b",
    "57de373b-0fcd-4737-b4cc-61d8e6bd5f20",
    "bc42db6e-ec77-4c8d-8cfb-2b099162e244",
    "94959179-36a6-45a8-a036-e6ef17a1ef68",
    "2d23dac5-322a-4bd9-8b7b-b494f688ddd3",
    "29e1984f-65b9-4cf2-a9fb-2ade1e9004d2",
    "0c085c0a-d50e-4bc7-b8f7-70785bb75045",
    "c417252b-3a75-48cb-94f9-1fd7e531468d",
    "83382086-430c-4003-851d-2b75063ae78f",
    "bd77a50e-09fa-47bf-868b-65626c37ee66",
    "005c6718-5e15-404a-9380-d4a0edc34ad0",
    "f822c92e-58fc-4421-8f57-3c04bb2edba1",
    "7013397e-a469-4a33-a1a5-934bc74eeb70",
    "42b8b35b-776d-46af-a61a-1bc8598580ee",
    "47f5eb4a-31ca-4fee-9b58-fb1f0080b04b",
    "a996ffaf-8a77-4bb8-bc58-5f55e13fb069",
    "f039e13d-c48f-46ff-a73a-e82483785e29",
    "195cced4-15c4-4800-a9c9-d809ac443739",
    "7279eb22-cf06-4b5c-9a27-d47e1db9c68d",
    "7b465be9-ae10-47fb-bbe2-e5c46d0e7b25",
    "f57bd3c6-56e7-4b8d-898e-ca55c9510bba",
    "cc1ce836-578b-4257-af93-8420a15f4cea",
    "d8a641b8-8ab1-49d2-b4a1-90f8d2a9b702",
    "b3a58046-30e8-4cae-a36f-d21d547a8356",
    "5b7c582e-6398-4053-9a19-74ecb12199bc",
    "35a6bdb4-0e83-4325-a9b8-5d5c72d2c791",
    "f25172a1-a792-4cbd-9e8c-9ebba20f37b0",
    "73905b19-57dc-436e-ad78-78eb10833084",
    "0c51a77a-1c22-4107-b62c-98dc6ea55743",
    "dc5094bf-72b5-4e0d-b05f-afcc580c288a",
    "730cae18-772c-4866-9561-c60775e38431",
    "363e6637-b31b-4599-a4a3-6d2f80c1cd72",
    "2d75ef33-9f3c-446a-9c55-e0f16dbcb67e",
    "69d5f171-8923-4296-9566-cbcbcd069872",
    "316ba01b-c101-4918-95b0-7056feafef66",
    "a72d39df-54b3-4f9f-98dc-d3cc493ed784",
    "724aca0c-74ea-4308-b922-ba0dc3576056",
    "ab23596b-1f13-49da-b791-00c2c25c468c",
    "9a2e104d-2c84-4c99-b52c-304ec3c67851",
    "46b5bade-8c06-400a-8ef0-93da992925d7",
    "9442a961-5770-4a71-a470-8ca7c319225a",
    "5aa86a19-316e-4615-b84e-ab5dade0d2f5",
    "b9424ad4-a088-4d5b-bb35-4060c48992ee",
    "294782c2-6e19-4b54-8969-90b526a6d7aa",
    "e0aa2df3-b777-4597-8aef-5be130a7548c",
    "7e88fab9-2b1c-403c-85e9-3302d00d9952",
    "837bae33-de8c-447d-bac0-76c78c9b6b3f",
    "d7a366a4-e886-48f1-bcaf-3719fa85269b",
    "54751ec2-9c79-44e9-b531-2d8b68d09159",
    "f1c9141b-e340-4096-add0-1ec48b403470",
    "ca31c79d-3a1d-4970-b047-726863bf212c",
    "5f740fbc-1b83-45ce-a405-760b63e8b274",
    "2782b320-0518-46c9-b0a1-0302ec1f1013",
    "6e8f3a96-675d-4623-8074-fe3270897e3e",
    "99bade99-bd48-4cee-a981-fee1dbd027f3",
    "878f4874-63f9-422b-94d7-370dde8484b8",
    "0b3f7a64-0519-41b8-b3d3-a3b248124656",
    "1a445a3e-4a05-4022-9a4b-2c1f49f851e9",
    "ccc66573-e540-4e39-bd5b-10e8ab60d37c",
    "70599ff8-647a-4955-b75f-2f5e4d1554ab",
    "04c08c01-cc2a-44b6-9165-7cc216499efe",
    "29fb943d-9157-4840-8b54-aa1c5d1d6984",
    "5ee7c3f1-83b7-47ec-8757-d01b4d6d9e26",
    "f8ad47e1-8db4-4365-a6e9-b2c90ecc00d9",
    "51686920-6ea2-4e4e-972d-1f296c409dc3",
    "197f33ad-a24a-4a15-8b09-b4d4c1893c0b",
    "376ff675-2d6f-438d-93fc-1211b31ef3ae",
    "a9050400-9af8-45cc-a86d-6d30cf532cef",
    "4d8fcf8a-50f9-437c-8ee0-bc67643d71b2",
    "69878444-c053-433d-9b4a-4b9d12917042",
    "6fda098b-bc23-4a0e-b71e-fdd851f45828",
    "da78c052-0cef-4e64-a9f5-da3724e1df11",
    "20aeb559-d5fb-4776-a5ef-1f4c6d622792",
    "7d3e7f06-2201-4563-a8a0-7e15737ba973",
    "e2252b83-c39e-4fb2-a484-1dc93396b70b",
    "180c82b9-fcfa-4d7f-9666-cd328825fceb",
    "5527c7f2-a037-4d55-9d15-74c4e4b92949",
    "f0a9f71d-96bd-4a9e-962f-0257353de948",
    "2bfcd740-277c-4ca0-b08a-69da5a4a2413",
    "226c50de-63ca-4bb0-88bb-3a16613d41fa",
    "a9ae0c4c-8235-4ea9-8a2b-7657cbf8253b",
    "b2fad270-e33e-41f0-9fab-b27fa7ee1d26",
    "7aab642c-da57-463b-b137-3445e27d857e",
    "e1e754b0-51c7-470f-aa26-66a4a5a4b442",
    "25648eac-7baf-456f-93c9-ce05f7afeafe",
    "25d26394-c648-42b4-964f-f7075afb14dc",
    "258aa1b9-ce36-42db-97ed-e27d31030bca",
    "0ad4a07f-dcad-49ef-84ff-3abf1c899148",
    "5d1d79e4-b1b0-46a0-ba13-b160eb3c53cf",
    "59e445f0-0b82-41ce-8330-2efd5a751f9e",
    "ca07311a-a346-4b3a-a859-3d12aae53f8c",
    "eb5a6d04-a3fd-4fd4-9894-c2840dcf6c4b",
    "3f7b44a5-773a-4d46-99a9-14c9837928f2",
    "ddbc3233-378b-4d2e-b2e2-cc431adf0056",
    "3d35f5cd-044e-425c-ad03-ecac0709be50",
    "a5646920-7872-4658-a61d-186923bf8f1a",
    "bf44e999-bc89-47e5-b720-e5edabb7871c",
    "ffa62fbf-d99a-441b-8a06-c4db6c1a619f",
    "a6c96937-1751-4eaf-aed6-ec5212fdaaa4",
    "ca2738ef-23e8-44ab-a43a-6c2147e3677e",
    "711de29e-f99e-4eb6-b0d0-ac2776d4b383",
)
NEW_BY_EXTENSION_CMD = r"""
from __future__ import print_function
import os.path
import subprocess
import sys

def file_tool(path):
    return subprocess.check_output(['file', path]).decode("utf8").strip()

(_, extension) = os.path.splitext(sys.argv[1])
if extension:
    print(extension.lower())
else:
    # Plaintext files frequently have no extension, but are common to identify.
    # file is pretty smart at figuring these out.
    file_output = file_tool(sys.argv[1])
    if 'text' in file_output:
        print('.txt')
"""


def data_migration_up(apps, schema_editor):
    """Update commands and rules."""
    _upgrade_fp_command(
        apps,
        NEW_JHOVE_CMD_UUID,
        OLD_JHOVE_CMD_UUID,
        NEW_JHOVE_CMD,
        JHOVE_RULES,
    )
    _upgrade_fp_command(
        apps,
        NEW_MEDIACONCH_CMD_UUID,
        OLD_MEDIACONCH_CMD_UUID,
        NEW_MEDIACONCH_CMD,
        MEDIACONCH_RULES,
    )
    _upgrade_fp_command(
        apps,
        NEW_TSK_RECOVER_CMD_UUID,
        OLD_TSK_RECOVER_CMD_UUID,
        NEW_TSK_RECOVER_CMD,
        TSK_RECOVER_RULES,
    )
    _upgrade_fp_command(
        apps,
        NEW_DEFAULT_THUMBNAIL_CMD_UUID,
        OLD_DEFAULT_THUMBNAIL_CMD_UUID,
        NEW_DEFAULT_THUMBNAIL_CMD,
        DEFAULT_THUMBNAIL_RULES,
    )
    _upgrade_id_command(
        apps,
        NEW_SIEGFRIED_CMD_UUID,
        OLD_SIEGFRIED_CMD_UUID,
        NEW_SIEGFRIED_CMD,
        SIEGFRIED_RULES,
    )
    _upgrade_id_command(
        apps,
        NEW_FIDO_CMD_UUID,
        OLD_FIDO_CMD_UUID,
        NEW_FIDO_CMD,
        FIDO_RULES,
    )
    _upgrade_id_command(
        apps,
        NEW_BY_EXTENSION_CMD_UUID,
        OLD_BY_EXTENSION_CMD_UUID,
        NEW_BY_EXTENSION_CMD,
        BY_EXTENSION_RULES,
    )


def _upgrade_id_command(
    apps,
    new_cmd_uuid,
    old_cmd_uuid,
    new_cmd,
    rule_uuids,
):
    IDCommand = apps.get_model("fpr", "IDCommand")
    IDRule = apps.get_model("fpr", "IDRule")

    # Get the old command
    old_command = IDCommand.objects.get(uuid=old_cmd_uuid)

    # Replace the existing command with the following
    IDCommand.objects.create(
        uuid=new_cmd_uuid,
        replaces_id=old_cmd_uuid,
        tool_id=old_command.tool_id,
        enabled=old_command.enabled,
        script=new_cmd,
        script_type=old_command.script_type,
        config=old_command.config,
        description=old_command.description,
    )

    # Update existing rules
    IDRule.objects.filter(uuid__in=rule_uuids).update(
        command_id=new_cmd_uuid,
    )

    # Disable the old command
    old_command.enabled = False
    old_command.save()


def _upgrade_fp_command(
    apps,
    new_cmd_uuid,
    old_cmd_uuid,
    new_cmd,
    rule_uuids,
):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    # Get the old command
    old_command = FPCommand.objects.get(uuid=old_cmd_uuid)

    # Replace the existing command with the following
    FPCommand.objects.create(
        uuid=new_cmd_uuid,
        replaces_id=old_cmd_uuid,
        tool_id=old_command.tool_id,
        enabled=old_command.enabled,
        command=new_cmd,
        script_type=old_command.script_type,
        command_usage=old_command.command_usage,
        description=old_command.description,
        output_location=old_command.output_location,
        output_format_id=old_command.output_format_id,
        event_detail_command_id=old_command.event_detail_command_id,
        verification_command_id=old_command.verification_command_id,
    )

    # Update existing rules
    FPRule.objects.filter(uuid__in=rule_uuids).update(
        command_id=new_cmd_uuid,
    )

    # Disable the old command
    old_command.enabled = False
    old_command.save()


def data_migration_down(apps, schema_editor):
    _downgrade_fp_command(
        apps,
        OLD_JHOVE_CMD_UUID,
        NEW_JHOVE_CMD_UUID,
        JHOVE_RULES,
    )
    _downgrade_fp_command(
        apps,
        OLD_MEDIACONCH_CMD_UUID,
        NEW_MEDIACONCH_CMD_UUID,
        MEDIACONCH_RULES,
    )
    _downgrade_fp_command(
        apps,
        OLD_TSK_RECOVER_CMD_UUID,
        NEW_TSK_RECOVER_CMD_UUID,
        TSK_RECOVER_RULES,
    )
    _downgrade_fp_command(
        apps,
        OLD_DEFAULT_THUMBNAIL_CMD_UUID,
        NEW_DEFAULT_THUMBNAIL_CMD_UUID,
        DEFAULT_THUMBNAIL_RULES,
    )
    _downgrade_id_command(
        apps,
        OLD_SIEGFRIED_CMD_UUID,
        NEW_SIEGFRIED_CMD_UUID,
        SIEGFRIED_RULES,
    )
    _downgrade_id_command(
        apps,
        OLD_FIDO_CMD_UUID,
        NEW_FIDO_CMD_UUID,
        FIDO_RULES,
    )
    _downgrade_id_command(
        apps,
        OLD_BY_EXTENSION_CMD_UUID,
        NEW_BY_EXTENSION_CMD_UUID,
        BY_EXTENSION_RULES,
    )


def _downgrade_fp_command(apps, old_cmd_uuid, new_cmd_uuid, rule_uuids):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    # The order matters. We make sure that the rules point to the previous
    # command before the latter is deleted. Otherwise our rules would be
    # deleted by Django's on cascade mechanism
    FPRule.objects.filter(uuid__in=rule_uuids).update(
        command_id=old_cmd_uuid,
    )

    # Enable the old command. At this point we do not know if the
    # command was in fact enabled before the migration was run, so
    # this may have unexpected consequences
    old_command = FPCommand.objects.get(uuid=old_cmd_uuid)
    old_command.enabled = True
    old_command.save()

    # Delete the new command
    FPCommand.objects.filter(uuid=new_cmd_uuid).delete()


def _downgrade_id_command(apps, old_cmd_uuid, new_cmd_uuid, rule_uuids):
    IDCommand = apps.get_model("fpr", "IDCommand")
    IDRule = apps.get_model("fpr", "IDRule")

    # The order matters. We make sure that the rules point to the previous
    # command before the latter is deleted. Otherwise our rules would be
    # deleted by Django's on cascade mechanism
    IDRule.objects.filter(uuid__in=rule_uuids).update(
        command_id=old_cmd_uuid,
    )

    # Enable the old command. At this point we do not know if the
    # command was in fact enabled before the migration was run, so
    # this may have unexpected consequences
    old_command = IDCommand.objects.get(uuid=old_cmd_uuid)
    old_command.enabled = True
    old_command.save()

    # Delete the new command
    IDCommand.objects.filter(uuid=new_cmd_uuid).delete()


class Migration(migrations.Migration):
    dependencies = [("fpr", "0034_delete_unused_models")]
    operations = [migrations.RunPython(data_migration_up, data_migration_down)]

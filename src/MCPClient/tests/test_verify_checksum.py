# -*- coding: utf-8 -*-

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

"""Test Verify Checksum Job in Archivematica.

Tests for the verify checksum Job in Archivematica which makes calls out to the
hashsum checksum utilities. We need to ensure that the output of the tool is
mapped consistently to something that can be understood by users when
debugging their preservation workflow.
"""

from __future__ import unicode_literals
import os
import subprocess
import sys
from uuid import UUID

import pytest

from main.models import Transfer, File, Event, User

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))

from job import Job
from verify_checksum import (
    Hashsum,
    NoHashCommandAvailable,
    write_premis_event_per_file,
    get_file_queryset,
    PREMISFailure,
)


class TestHashsum(object):
    """Hashsum test runner object."""

    assert_exception_string = "Hashsum exception string returned is incorrect"
    assert_return_value = "Hashsum comparison returned something other than 1: {}"

    @pytest.fixture()
    def user(self, db):
        return User.objects.create(
            id=1,
            username="kmindelan",
            first_name="Keladry",
            last_name="Mindelan",
            is_active=True,
            is_superuser=True,
            is_staff=True,
            email="keladry@mindelan.com",
        )

    @pytest.fixture
    def transfer(self, db, user):
        transfer = Transfer.objects.create(
            uuid="e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6",
            type="Standard",
            currentlocation="%sharedPath%currentlyProcessing/ユニコード-e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6/",
        )
        transfer.update_active_agent(user_id=user.id)
        File.objects.create(
            uuid="8a1f0b59-cf94-47ef-8078-647b77c8a147",
            checksumtype="sha256",
            transfer=transfer,
            filegrpuse="original",
            checksum="f78615cd834f7fb84832177e73f13e3479f5b5b22ae7a9506c7fa0a14fd9df9e",
            enteredsystem="2017-01-04T19:35:20Z",
            modificationtime="2017-01-04T19:35:20Z",
            originallocation="%transferDirectory%objects/has space/lion.svg",
            currentlocation="%transferDirectory%objects/has space/lion.svg",
            size=18324,
        )
        return transfer

    @staticmethod
    def setup_hashsum(path, job):
        """Return a hashsum instance to calling functions and perform any
        other additional setup as necessary.
        """
        return Hashsum(path, job)

    def test_invalid_initialisation(self):
        """Test that we don't return a Hashsum object if there isn't a tool
        configured to work with the file path provided.
        """
        with pytest.raises(NoHashCommandAvailable):
            Hashsum("checksum.invalid_hash")
            pytest.fail("Expecting NoHashCommandAvailable for invalid checksum type")

    @pytest.mark.parametrize(
        "fixture",
        [
            ("metadata/checksum.md5", True),
            ("metadata/checksum.sha1", True),
            ("metadata/checksum.sha256", True),
            ("metadata/checksum.sha512", True),
            ("metadata/checksum_md5", False),
            ("metadata/checksum_sha1", False),
            ("metadata/checksum_sha256", False),
            ("metadata/checksum_sha512", False),
        ],
    )
    def test_valid_initialisation(self, fixture):
        """Test that we don't return a Hashsum object if there isn't a tool
        configured to work with the file path provided.
        """
        if fixture[1]:
            assert isinstance(
                Hashsum(fixture[0]), Hashsum
            ), "Hashsum object not instantiated correctly"
        else:
            with pytest.raises(NoHashCommandAvailable):
                Hashsum(fixture[0])
                pytest.fail(
                    "Expecting NoHashCommandAvailable for a filename we shouldn't be able to handle"
                )

    def test_provenance_string(self, mocker):
        """Test to ensure that the string output to the PREMIS event for this
        microservice Job is consistent with what we're expecting. Provenance
        string includes the command called, plus the utility's version string.
        """
        hash_file = "metadata/checksum.md5"
        hashsum = self.setup_hashsum(hash_file, Job("stub", "stub", ["", ""]))
        version_string = [
            "md5sum (GNU coreutils) 8.28",
            "Copyright (C) 2017 Free Software Foundation, Inc.",
        ]
        mock = mocker.patch.object(hashsum, "_call", return_value=version_string)
        assert (
            hashsum.version() == "md5sum (GNU coreutils) 8.28"
        ), "Hashsum version retrieved is incorrect"
        mock.assert_called_once_with("--version")
        mocker.patch.object(
            hashsum,
            "command_called",
            (hashsum.COMMAND,) + ("-c", "--strict", hash_file),
        )
        expected_provenance = 'program="md5sum -c --strict metadata/checksum.md5"; version="md5sum (GNU coreutils) 8.28"'
        provenance_output = hashsum.get_command_detail()
        assert (
            provenance_output == expected_provenance
        ), "Provenance output is incorrect: {}".format(provenance_output)

    def test_provenance_string_no_command(self):
        """When nothing has happened, e.g. the checksums haven't been validated
        then it should be practically impossible to write to the database and
        generate some form of false-positive.
        """
        hash_file = "metadata/checksum.sha1"
        hashsum = self.setup_hashsum(hash_file, Job("stub", "stub", ["", ""]))
        try:
            hashsum.get_command_detail()
        except PREMISFailure:
            pass

    def test_compare_hashes_failed(self, mocker):
        """Ensure we get consistent output when the checksum comparison fails."""
        hash_file = "metadata/checksum.sha256"
        job = Job("stub", "stub", ["", ""])
        hashsum = self.setup_hashsum(hash_file, job)
        toolname = "sha256sum"
        objects_dir = "objects"
        output_string = (
            b"objects/file1.bin: OK\n"
            b"objects/file2.bin: FAILED\n"
            b"objects/nested/\xe3\x83\x95\xe3\x82\xa1\xe3\x82\xa4\xe3\x83\xab"
            b"3.bin: FAILED\n"
            b"objects/readonly.file: FAILED open or read"
        )
        exception_string = (
            "sha256: comparison exited with status: 1. Please check the formatting of the checksums or integrity of the files.\n"
            "sha256: objects/file2.bin: FAILED\n"
            "sha256: objects/nested/ファイル3.bin: FAILED\n"
            "sha256: objects/readonly.file: FAILED open or read"
        )
        mock = mocker.patch.object(hashsum, "_call", return_value=output_string)
        mocker.patch.object(hashsum, "count_and_compare_lines", return_value=True)
        mock.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=toolname, output=output_string
        )
        ret = hashsum.compare_hashes("")
        mock.assert_called_once_with(
            "-c", "--strict", hash_file, transfer_dir=objects_dir
        )
        assert ret == 1, self.assert_return_value.format(ret)
        assert (
            job.get_stderr().strip() == exception_string
        ), self.assert_exception_string

    def test_compare_hashes_with_bad_files(self, mocker):
        """Ensure that the formatting of errors is consistent if improperly
        formatted files are provided to hashsum.
        """
        hash_file = "metadata/checksum.sha1"
        job = Job("stub", "stub", ["", ""])
        hashsum = self.setup_hashsum(hash_file, job)
        toolname = "sha1sum"
        objects_dir = "objects"
        no_proper_output = (
            b"sha1sum: metadata/checksum.sha1: no properly formatted SHA1 "
            b"checksum lines found"
        )
        except_string_no_proper_out = (
            "sha1: comparison exited with status: 1. Please check the formatting of the checksums or integrity of the files.\n"
            "sha1: sha1sum: metadata/checksum.sha1: no properly formatted "
            "SHA1 checksum lines found"
        )
        improper_formatting = b"sha1sum: WARNING: 1 line is improperly formatted"
        except_string_improper_format = (
            "sha1: comparison exited with status: 1. Please check the formatting of the checksums or integrity of the files.\n"
            "sha1: sha1sum: WARNING: 1 line is improperly formatted"
        )
        mock = mocker.patch.object(hashsum, "_call", return_value=no_proper_output)
        mocker.patch.object(hashsum, "count_and_compare_lines", return_value=True)
        mock.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=toolname, output=no_proper_output
        )
        ret = hashsum.compare_hashes("")
        mock.assert_called_once_with(
            "-c", "--strict", hash_file, transfer_dir=objects_dir
        )
        assert (
            job.get_stderr().strip() == except_string_no_proper_out
        ), self.assert_exception_string
        assert ret == 1, self.assert_return_value.format(ret)
        # Flush job.error as it isn't flushed automatically.
        job.error = b""
        mock = mocker.patch.object(hashsum, "_call", return_value=improper_formatting)
        mock.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="sha1sum", output=improper_formatting
        )
        ret = hashsum.compare_hashes("")
        assert (
            job.get_stderr().strip() == except_string_improper_format
        ), self.assert_exception_string
        mock.assert_called_once_with(
            "-c", "--strict", hash_file, transfer_dir=objects_dir
        )
        assert ret == 1, self.assert_return_value.format(ret)

    def test_line_comparison_fail(self, mocker):
        """If the checksum line and object comparison function fails then
        we want to return early and _call shouldn't be called.
        """
        hash_file = "metadata/checksum.sha1"
        hashsum = self.setup_hashsum(hash_file, Job("stub", "stub", ["", ""]))
        toolname = "sha1sum"
        mock = mocker.patch.object(hashsum, "_call", return_value=None)
        mocker.patch.object(hashsum, "count_and_compare_lines", return_value=False)
        mock.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=toolname, output=None
        )
        ret = hashsum.compare_hashes("")
        mock.assert_not_called()
        assert ret == 1, self.assert_return_value.format(ret)

    @pytest.mark.parametrize(
        "fixture",
        [
            ("checksum.md5", "md5"),
            ("checksum.sha1", "sha1"),
            ("checksum.sha256", "sha256"),
            ("checksum_md5", "checksum_md5"),
            ("checksum_sha1", "checksum_sha1"),
            ("checksum_sha256", "checksum_sha256"),
        ],
    )
    def test_get_ext(self, fixture):
        """get_ext helps to format usefully."""
        assert (
            Hashsum.get_ext(fixture[0]) == fixture[1]
        ), "Incorrect extension returned from Hashsum"

    @staticmethod
    def test_decode_and_version_string():
        """Test that we can separate the version and license information
        correctly from {command} --version.
        """
        version_string = (
            b"sha256sum (GNU coreutils) 8.28\n"
            b"Copyright (C) 2017 Free Software Foundation, Inc."
        )
        assert Hashsum._decode(version_string)[
            0
        ], "Version string incorrectly decoded by Hashsum"
        assert (
            Hashsum._decode(version_string)[0] == "sha256sum (GNU coreutils) 8.28"
        ), "Invalid version string decoded by Hashsum"

    @pytest.mark.django_db
    def test_write_premis_event_to_db(self, transfer):
        """Test that the microservice job connects to the database as
        anticipated, writes its data, and that data can then be retrieved.
        """
        # Values the job will write.
        algorithms = ["md5", "sha512", "sha1"]
        event_type = "fixity check"
        event_outcome = "pass"
        # Values we will write.
        detail = "suma de verificación validada: OK"
        number_of_expected_agents = 2
        # Agent values we can test against. Three agents, which should be,
        # preservation system, repository, and user.
        identifier_values = ["1", "ORG"]

        identifier_types = [
            "repository code",
            "Archivematica user pk",
        ]

        agent_names = [
            "Your Organization Name Here",
            'username="kmindelan", first_name="Keladry", last_name="Mindelan"',
        ]

        agent_types = ["organization", "Archivematica user"]
        package_uuid = "e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6"
        kwargs = {"removedtime__isnull": True, "transfer_id": package_uuid}
        file_objs_queryset = File.objects.filter(**kwargs)
        for algorithm in algorithms:
            event_detail = "{}: {}".format(algorithm, detail)
            write_premis_event_per_file(file_objs_queryset, package_uuid, event_detail)
        file_uuids = File.objects.filter(**kwargs).values_list("uuid")
        assert (
            file_uuids
        ), "Files couldn't be retrieved for the transfer from the database"
        event_algorithms = []
        for uuid_ in file_uuids:
            events = Event.objects.filter(file_uuid=uuid_, event_type=event_type)
            assert len(events) == len(
                algorithms
            ), "Length of the event objects is not '1', it is: {}".format(len(events))
            assert (
                events[0].event_outcome == event_outcome
            ), "Event outcome retrieved from the database is incorrect: {}".format(
                events[0].event_outcome
            )
            assert (
                detail in events[0].event_detail
            ), "Event detail retrieved from the database is incorrect: {}".format(
                events[0].event_detail
            )
            # Ensure that UUID creation has happened as anticipated. Will raise
            # a TypeError if otherwise.
            UUID(events[0].event_id, version=4)
            # Test the linked agents associated with our events.
            for event in events:
                idvalues = []
                idtypes = []
                agentnames = []
                agenttypes = []
                for agent_count, agent in enumerate(event.agents.all(), 1):
                    idvalues.append(agent.identifiervalue)
                    idtypes.append(agent.identifiertype)
                    agentnames.append(agent.name)
                    agenttypes.append(agent.agenttype)
                assert set(idvalues) == set(
                    identifier_values
                ), "agent identifier values returned don't match"
                assert set(idtypes) == set(
                    identifier_types
                ), "agent type values returned don't match"
                assert set(agentnames) == set(
                    agent_names
                ), "agent name values returned don't match"
                assert set(agenttypes) == set(agent_types), "agent types don't match"
                assert (
                    agent_count == number_of_expected_agents
                ), "Number of agents is incorrect: {} expected: {}".format(
                    agent_count, number_of_expected_agents
                )
            # Collect the different checksum algorithms written to ensure they
            # were all written independently in the function.
            for event in events:
                event_algorithms.append(event.event_detail.split(":", 1)[0])
        assert set(event_algorithms) == set(
            algorithms
        ), "No all algorithms written to PREMIS events"

    @pytest.mark.django_db
    def test_get_file_obj_queryset(self, transfer):
        """Test the retrieval and failure of the queryset used for creating
        events for all the file objects associated with the transfer checksums.
        """
        package_uuid = "e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6"
        assert get_file_queryset(package_uuid)
        invalid_package_uuid = "badf00d1-9c84-45d5-a3ca-1b0b3f58d9b6"
        with pytest.raises(PREMISFailure):
            get_file_queryset(invalid_package_uuid)
            pytest.fail(
                "Unable to find the transfer objects for the SIP: '{}' in the database".format(
                    invalid_package_uuid
                )
            )

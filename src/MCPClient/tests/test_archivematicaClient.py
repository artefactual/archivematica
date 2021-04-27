# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import six

from archivematicaClient import handle_batch_task


@pytest.mark.django_db
def test_handle_batch_task_replaces_non_ascii_arguments(mocker):
    # We are only interested in verifying the string replacement logic
    # for task arguments and mock the remaining functionality
    mocker.patch("archivematicaClient.Job")
    mocker.patch("archivematicaClient.Task")
    mocker.patch("archivematicaClient.retryOnFailure")
    mocker.patch(
        "six.moves.cPickle.loads",
        return_value={
            "tasks": {
                "some_task_uuid": {
                    "uuid": "some_task_uuid",
                    "arguments": "montréal %taskUUID% %jobCreatedDate%",
                    "createdDate": "some montréal datetime",
                    "wants_output": False,
                }
            }
        },
    )

    # The mocked module will not have a `concurrent_instances` attribute
    mocker.patch(
        "importlib.import_module", return_value=mocker.MagicMock(spec=["call"])
    )

    # This is the only function that uses the arguments after the replacements
    _parse_command_line = mocker.patch("archivematicaClient._parse_command_line")

    # Mock the two parameters sent to handle_batch_task
    gearman_job_mock = mocker.Mock()
    supported_modules_mock = mocker.Mock(**{"get.side_effect": "some_module_name"})
    handle_batch_task(gearman_job_mock, supported_modules_mock)

    # Check that string replacement were successful
    _parse_command_line.assert_called_once_with(
        six.ensure_str("montréal some_task_uuid some montréal datetime")
    )

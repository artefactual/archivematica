from unittest import mock

import pytest
from main.models import Event
from validate_file import main


@pytest.mark.django_db
@mock.patch("validate_file.executeOrRun")
def test_main(
    execute_or_run,
    sip,
    sip_file,
    format_version,
    fprule_validation,
    fpcommand,
    file_format_version,
    mcp_job,
):
    exit_status = 0
    stdout = '{"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}'
    stderr = ""
    execute_or_run.return_value = (exit_status, stdout, stderr)
    file_type = "original"

    main(
        job=mcp_job,
        file_path=sip_file.currentlocation,
        file_uuid=sip_file.uuid,
        sip_uuid=sip.uuid,
        shared_path=sip.currentpath,
        file_type=file_type,
    )

    # Check the executed script.
    execute_or_run.assert_called_once_with(
        type=fpcommand.script_type,
        text=fpcommand.command,
        printing=False,
        arguments=[sip_file.currentlocation],
    )

    # Verify a PREMIS validation event was created with the output of the
    # validation command.
    assert (
        Event.objects.filter(
            file_uuid=sip_file.uuid,
            event_type="validation",
            event_outcome="pass",
            event_outcome_detail="a note",
        ).count()
        == 1
    )

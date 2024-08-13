from unittest import mock

import pytest
import validate_file
from client.job import Job
from fpr import models as fprmodels
from main import models


@pytest.mark.django_db
@mock.patch("validate_file.executeOrRun")
def test_main(
    execute_or_run: mock.Mock,
    sip: models.SIP,
    sip_file: models.File,
    format_version: fprmodels.FormatVersion,
    fprule_validation: fprmodels.FPRule,
    fpcommand: fprmodels.FPCommand,
    sip_file_format_version: models.FileFormatVersion,
    mcp_job: Job,
) -> None:
    exit_status = 0
    stdout = '{"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}'
    stderr = ""
    execute_or_run.return_value = (exit_status, stdout, stderr)
    file_type = "original"

    validate_file.main(
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
        models.Event.objects.filter(
            file_uuid=sip_file.uuid,
            event_type="validation",
            event_outcome="pass",
            event_outcome_detail="a note",
        ).count()
        == 1
    )

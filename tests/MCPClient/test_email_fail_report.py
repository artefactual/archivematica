from smtplib import SMTPException
from unittest import mock

import email_fail_report
import pytest
from django.core import mail


def fake_send_email_with_exception(
    subject,
    message,
    from_email,
    recipient_list,
    fail_silently=False,
    auth_user=None,
    auth_password=None,
    connection=None,
    html_message=None,
):
    from smtplib import SMTPException

    raise SMTPException("Something really bad happened!")


def test_send_email_ok(settings):
    settings.DEFAULT_FROM_EMAIL = "foo@bar.tld"
    total = email_fail_report.send_email(
        "Foobar", ["to@domain.tld"], "<html>...</html>"
    )

    assert total == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Foobar"
    assert mail.outbox[0].from_email == "foo@bar.tld"
    assert mail.outbox[0].to == ["to@domain.tld"]
    assert mail.outbox[0].body == "Please see the attached HTML document"
    assert len(mail.outbox[0].alternatives) == 1
    assert mail.outbox[0].alternatives[0] == ("<html>...</html>", "text/html")


def test_send_email_err(monkeypatch):
    monkeypatch.setattr(
        "django.core.mail.send_mail.__code__",
        fake_send_email_with_exception.__code__,
    )
    with pytest.raises(SMTPException):
        email_fail_report.send_email("Foobar", ["to@domain.tld"], "<html>...</html>")


@pytest.mark.parametrize(
    "test_case",
    [
        {
            "users": [],
            "send_email_result": None,
            "send_email_calls": [],
            "set_status_calls": [(1,)],
        },
        {
            "users": ["User 1"],
            "send_email_result": None,
            "send_email_calls": [
                (
                    "Archivematica Fail Report for Transfer: My transfer-uuid",
                    ["User 1"],
                    "my report",
                )
            ],
            "set_status_calls": [],
        },
        {
            "users": ["User 1"],
            "send_email_result": Exception("error sending email"),
            "send_email_calls": [],
            "set_status_calls": [(1,)],
        },
    ],
    ids=["no-users-exist", "users-exist", "send-email-fails"],
)
@pytest.mark.django_db
@mock.patch("argparse.ArgumentParser")
@mock.patch("email_fail_report.get_emails_from_dashboard_users")
@mock.patch("email_fail_report.get_content_for", return_value="my report")
@mock.patch("email_fail_report.send_email")
@mock.patch("email_fail_report.store_report")
def test_report_is_always_stored(
    store_report_mock,
    send_email_mock,
    get_content_for,
    get_emails_from_dashboard_users,
    argument_parser,
    test_case,
):
    args_mock = mock.Mock(
        unit_type="Transfer", unit_name="My transfer", unit_uuid="uuid", stdout=False
    )
    argument_parser.return_value = mock.Mock(**{"parse_args.return_value": args_mock})
    get_emails_from_dashboard_users.return_value = test_case["users"]

    send_email_mock.side_effect = test_case["send_email_result"]

    job = mock.MagicMock()
    email_fail_report.call([job])
    store_report_mock.assert_called_once_with(
        "my report", args_mock.unit_type, args_mock.unit_name, args_mock.unit_uuid
    )
    send_email_mock.assert_has_calls(
        [mock.call(*a) for a in test_case["send_email_calls"]]
    )
    job.set_status.assert_has_calls(
        [mock.call(*a) for a in test_case["set_status_calls"]]
    )

# -*- coding: utf8

import os
import sys

from django.core import mail

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(
    os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))

from lib.job_email_report import send_email


def test_send_email_ok(settings):
    settings.DEFAULT_FROM_EMAIL = "test@testy.com"
    total = send_email("Test Completion", ["to@testy.com"],
                       "This is the email content", "Attachment text")

    assert total == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Test Completion"
    assert mail.outbox[0].from_email == "test@testy.com"
    assert mail.outbox[0].to == ["to@testy.com"]
    assert mail.outbox[0].body == "This is the email content"
    assert len(mail.outbox[0].attachments) == 1

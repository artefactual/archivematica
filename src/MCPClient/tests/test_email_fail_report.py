# -*- coding: utf8

from __future__ import print_function

import os
from smtplib import SMTPException
import sys

from django.core import mail
import pytest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))

from emailFailReport import send_email


def fake_send_email_with_exception(subject, message, from_email, recipient_list,
                                   fail_silently=False, auth_user=None,
                                   auth_password=None, connection=None,
                                   html_message=None):
    from smtplib import SMTPException
    raise SMTPException('Something really bad happened!')


def test_send_email_ok(settings):
    settings.DEFAULT_FROM_EMAIL = "foo@bar.tld"
    total = send_email("Foobar", ["to@domain.tld"], "<html>...</html>")

    assert total == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Foobar"
    assert mail.outbox[0].from_email == "foo@bar.tld"
    assert mail.outbox[0].to == ["to@domain.tld"]
    assert mail.outbox[0].body == "Please see the attached HTML document"
    assert len(mail.outbox[0].alternatives) == 1
    assert mail.outbox[0].alternatives[0] == ("<html>...</html>", "text/html")


def test_send_email_err(monkeypatch):
    monkeypatch.setattr('django.core.mail.send_mail.func_code',
                        fake_send_email_with_exception.func_code)
    with pytest.raises(SMTPException):
        send_email("Foobar", ["to@domain.tld"], "<html>...</html>")

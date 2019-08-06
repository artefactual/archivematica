# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.contrib.auth.models import User
from django.test import TestCase
from tastypie.models import ApiKey

from main.templatetags.user import api_key, logout_link


class TestAPIKeyTemplateTag(TestCase):
    fixtures = ["test_user"]

    def setUp(self):
        self.user = User.objects.get(username="test")

    def test_shows_api_key_when_set(self):
        assert api_key(self.user) == "<no API key generated>"

    def test_shows_message_when_no_api_key(self):
        ApiKey.objects.create(user=self.user, key="my-api-key")

        assert api_key(self.user) == "my-api-key"


class TestLogoutLinkTemplateTag(TestCase):
    def test_uses_logout_link_from_context_when_available(self):
        context = {"logout_link": "/shibboleth/logout"}
        assert logout_link(context) == "/shibboleth/logout"

    def test_uses_django_logout_when_logout_link_not_set(self):
        context = {}
        assert logout_link(context) == "/administration/accounts/logout/"

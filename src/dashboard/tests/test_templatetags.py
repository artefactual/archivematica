import os

from django.contrib.auth.models import User
from django.test import TestCase
from tastypie.models import ApiKey

from main.templatetags.user import api_key

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestAPIKeyTemplateTag(TestCase):
    fixture_files = ['test_user.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    def setUp(self):
        self.user = User.objects.get(username='test')

    def test_shows_api_key_when_set(self):
        assert api_key(self.user) == '<no API key generated>'

    def test_shows_message_when_no_api_key(self):
        ApiKey.objects.create(user=self.user, key='my-api-key')

        assert api_key(self.user) == 'my-api-key'

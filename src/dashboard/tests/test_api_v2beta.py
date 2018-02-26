import base64
import json
import os

from django.test import TestCase, Client
import mock

from components import helpers


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class MCPClientMock(object):

    def __init__(self, fails=False):
        self.fails = fails

    def create_package(self, name, type_, accession, path, metadata_set_id):
        if self.fails:
            raise Exception('Something bad happened!')
        return b'59402c61-3aba-4af7-966a-996073c0601d'


class TestAPIv2(TestCase):
    fixture_files = ['test_user.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    # This is valid path value that we're going to pass to the API server.
    path = base64.b64encode('{location_uuid}:{relative_path}'.format(**{
        'location_uuid': '671643e1-5bec-4a5f-b244-abb76fedb0c4',
        'relative_path': 'foo/bar.jpg',
    }))

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')
        helpers.set_setting('dashboard_uuid', 'test-uuid')

    def test_package_list(self):
        resp = self.client.get('/api/v2beta/package/')
        assert resp.status_code == 501  # Not implemented yet.

    def test_package_create_with_errors(self):
        # Missing payload
        resp = self.client.post(
            '/api/v2beta/package/',
            content_type='application/json')
        assert resp.status_code == 400

        # Invalid document
        resp = self.client.post(
            '/api/v2beta/package/',
            'INVALID-JSON',
            content_type='application/json')
        assert resp.status_code == 400

        # Invalid path
        resp = self.client.post(
            '/api/v2beta/package/',
            json.dumps({'path': 'invalid'}),
            content_type='application/json')
        assert resp.status_code == 400

    @mock.patch('components.api.views.MCPClient',
                return_value=MCPClientMock())
    def test_package_create_mcpclient_ok(self, patcher):
        resp = self.client.post(
            '/api/v2beta/package/',
            json.dumps({'path': self.path}),
            content_type='application/json')
        assert resp.status_code == 202
        assert resp.content == json.dumps({
            'id': '59402c61-3aba-4af7-966a-996073c0601d'
        })

    @mock.patch('components.api.views.MCPClient',
                return_value=MCPClientMock(fails=True))
    def test_package_create_mcpclient_fails(self, patcher):
        resp = self.client.post(
            '/api/v2beta/package/',
            json.dumps({'path': self.path}),
            content_type='application/json')
        assert resp.status_code == 500
        payload = json.loads(resp.content)
        assert payload['error'] is True
        assert payload['message'] == 'Package cannot be created'

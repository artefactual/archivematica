from django.contrib.auth.models import User
from django.test import TestCase


class TestShibbolethLogin(TestCase):
    def test_with_no_shibboleth_headers(self):
        response = self.client.get('/transfer/')

        # If no shibboleth headers, no user is created - so installer middleware
        # kicks in and redirects to welcome page
        assert response.status_code == 302
        assert '/welcome/' in response.url

    def test_auto_creates_user(self):
        shib_headers = {
            'HTTP_EPPN': 'testuser',
            'HTTP_GIVENNAME': 'Test',
            'HTTP_SN': 'User',
            'HTTP_MAIL': 'test@example.com',
            'HTTP_ENTITLEMENT': 'preservation-user',
        }

        response = self.client.get('/transfer/', **shib_headers)

        assert response.status_code == 200
        user = response.context['user']
        assert user.username == 'testuser'
        assert user.get_full_name() == 'Test User'
        assert user.email == 'test@example.com'
        assert not user.has_usable_password()
        assert user.api_key
        assert not user.is_superuser

    def test_uses_existing_user(self):
        user = User.objects.create(username='testuser')
        shib_headers = {
            'HTTP_EPPN': 'testuser',
            'HTTP_GIVENNAME': 'Test',
            'HTTP_SN': 'User',
            'HTTP_MAIL': 'test@example.com',
            'HTTP_ENTITLEMENT': 'preservation-user',
        }

        response = self.client.get('/transfer/', **shib_headers)

        assert response.status_code == 200
        assert response.context['user'] == user

    def test_long_username(self):
        long_email = 'person-with-very-long-name@long-institution-name.ac.uk'
        shib_headers = {
            'HTTP_EPPN': long_email,
            'HTTP_GIVENNAME': 'Test',
            'HTTP_SN': 'User',
            'HTTP_MAIL': 'test@example.com',
            'HTTP_ENTITLEMENT': 'preservation-user',
        }

        response = self.client.get('/transfer/', **shib_headers)

        assert response.status_code == 200
        assert response.context['user'].username == long_email

    def test_creates_superuser_based_on_entitlement(self):
        shib_headers = {
            'HTTP_EPPN': 'testuser',
            'HTTP_GIVENNAME': 'Test',
            'HTTP_SN': 'User',
            'HTTP_MAIL': 'test@example.com',
            'HTTP_ENTITLEMENT': 'preservation-admin;some-other-entitlement',
        }

        response = self.client.get('/transfer/', **shib_headers)

        assert response.status_code == 200
        user = response.context['user']
        assert user.is_superuser

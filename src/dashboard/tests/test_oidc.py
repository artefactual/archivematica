import pytest
from django.conf import settings
from django.test import TestCase

from components.accounts.backends import CustomOIDCBackend


@pytest.mark.skipif(
    not settings.OIDC_AUTHENTICATION, reason="tests will only pass if OIDC is enabled"
)
class TestOIDC(TestCase):
    def test_create_user(self):
        backend = CustomOIDCBackend()
        user = backend.create_user(
            {"email": "test@example.com", "first_name": "Test", "last_name": "User"}
        )

        user.refresh_from_db()
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.email == "test@example.com"
        assert user.username == "test@example.com"
        assert user.api_key

    def test_get_userinfo(self):
        # Encoded at https://www.jsonwebtoken.io/
        # {"email": "test@example.com"}
        id_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJqdGkiOiI1M2QyMzUzMy04NDk0LTQyZWQtYTJiZC03Mzc2MjNmMjUzZjciLCJpYXQiOjE1NzMwMzE4NDQsImV4cCI6MTU3MzAzNTQ0NH0.m3nHgvj_DyVJMcW5eyYuUss1Y0PNzJV2O3bX0b_DCmI"
        # {"given_name": "Test", "family_name": "User"}
        access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJnaXZlbl9uYW1lIjoiVGVzdCIsImZhbWlseV9uYW1lIjoiVXNlciIsImp0aSI6ImRhZjIwNTNiLWE4MTgtNDE1Yy1hM2Y1LTkxYWVhMTMxYjljZCIsImlhdCI6MTU3MzAzMTk3OSwiZXhwIjoxNTczMDM1NTc5fQ.cGcmt7d9IuKndvrqPpAH3Dvb3KyCOMqixUWgS7sg8r4"

        backend = CustomOIDCBackend()
        info = backend.get_userinfo(
            access_token=access_token, id_token=id_token, verified_id=None
        )
        assert info["email"] == "test@example.com"
        assert info["first_name"] == "Test"
        assert info["last_name"] == "User"

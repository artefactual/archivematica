from components.accounts.backends import CustomOIDCBackend
from django.test import TestCase
from django.test import override_settings


@override_settings(OIDC_OP_TOKEN_ENDPOINT="https://example.com/token")
@override_settings(OIDC_OP_USER_ENDPOINT="https://example.com/user")
@override_settings(OIDC_RP_CLIENT_ID="rp_client_id")
@override_settings(OIDC_RP_CLIENT_SECRET="rp_client_secret")
@override_settings(
    OIDC_ACCESS_ATTRIBUTE_MAP={
        "given_name": "first_name",
        "family_name": "last_name",
    }
)
@override_settings(OIDC_ID_ATTRIBUTE_MAP={"email": "email"})
@override_settings(OIDC_USERNAME_ALGO=lambda email: email)
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

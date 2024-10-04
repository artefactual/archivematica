from urllib.parse import parse_qs
from urllib.parse import urlparse

import pytest
from components.accounts.views import get_oidc_logout_url


def test_get_oidc_logout_url_fails_if_token_is_not_set(rf):
    request = rf.get("/")
    request.session = {}

    with pytest.raises(ValueError, match="ID token not found in session."):
        get_oidc_logout_url(request)


def test_get_oidc_logout_url_fails_if_logout_endpoint_is_not_set(rf):
    request = rf.get("/")
    request.session = {"oidc_id_token": "mytoken"}

    with pytest.raises(
        ValueError, match="OIDC logout endpoint not configured for provider."
    ):
        get_oidc_logout_url(request)


def test_get_oidc_logout_url_returns_logout_url(rf, settings):
    settings.OIDC_OP_LOGOUT_ENDPOINT = "http://example.com/logout"
    token = "mytoken"
    request = rf.get("/")
    request.session = {"oidc_id_token": token}

    result = get_oidc_logout_url(request)

    assert result.startswith(settings.OIDC_OP_LOGOUT_ENDPOINT)
    query_dict = parse_qs(urlparse(result).query)
    assert set(query_dict) == {"id_token_hint", "post_logout_redirect_uri"}
    assert query_dict["id_token_hint"] == [token]
    assert query_dict["post_logout_redirect_uri"] == ["http://testserver/"]

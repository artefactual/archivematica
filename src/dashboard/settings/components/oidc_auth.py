import os

from archivematicaFunctions import get_oidc_secondary_providers

OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID", "")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", "")

OIDC_OP_AUTHORIZATION_ENDPOINT = ""
OIDC_OP_TOKEN_ENDPOINT = ""
OIDC_OP_USER_ENDPOINT = ""
OIDC_OP_JWKS_ENDPOINT = ""
OIDC_OP_LOGOUT_ENDPOINT = ""

AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID", "")
if AZURE_TENANT_ID:
    OIDC_OP_AUTHORIZATION_ENDPOINT = (
        "https://login.microsoftonline.com/%s/oauth2/v2.0/authorize" % AZURE_TENANT_ID
    )
    OIDC_OP_TOKEN_ENDPOINT = (
        "https://login.microsoftonline.com/%s/oauth2/v2.0/token" % AZURE_TENANT_ID
    )
    OIDC_OP_USER_ENDPOINT = (
        "https://login.microsoftonline.com/%s/openid/userinfo" % AZURE_TENANT_ID
    )
    OIDC_OP_JWKS_ENDPOINT = (
        "https://login.microsoftonline.com/%s/discovery/v2.0/keys" % AZURE_TENANT_ID
    )
else:
    OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get(
        "OIDC_OP_AUTHORIZATION_ENDPOINT", ""
    )
    OIDC_OP_TOKEN_ENDPOINT = os.environ.get("OIDC_OP_TOKEN_ENDPOINT", "")
    OIDC_OP_USER_ENDPOINT = os.environ.get("OIDC_OP_USER_ENDPOINT", "")
    OIDC_OP_JWKS_ENDPOINT = os.environ.get("OIDC_OP_JWKS_ENDPOINT", "")
    OIDC_OP_LOGOUT_ENDPOINT = os.environ.get("OIDC_OP_LOGOUT_ENDPOINT", "")

OIDC_SECONDARY_PROVIDER_NAMES = os.environ.get(
    "OIDC_SECONDARY_PROVIDER_NAMES", ""
).split(",")
OIDC_PROVIDER_QUERY_PARAM_NAME = os.environ.get(
    "OIDC_PROVIDER_QUERY_PARAM_NAME", "secondary"
)
OIDC_PROVIDERS = get_oidc_secondary_providers(OIDC_SECONDARY_PROVIDER_NAMES)

if OIDC_OP_LOGOUT_ENDPOINT:
    OIDC_OP_LOGOUT_URL_METHOD = "components.accounts.views.get_oidc_logout_url"

OIDC_RP_SIGN_ALGO = os.environ.get("OIDC_RP_SIGN_ALGO", "HS256")


# Username is email address
def _get_email(email):
    return email


OIDC_USERNAME_ALGO = _get_email

# map attributes from access token
OIDC_ACCESS_ATTRIBUTE_MAP = {"given_name": "first_name", "family_name": "last_name"}

# map attributes from id token
OIDC_ID_ATTRIBUTE_MAP = {"email": "email"}

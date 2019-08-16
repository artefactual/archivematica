import os


# AUTH_SERVER = 'https://login.microsoftonline.com/common/v2.0/'
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID", "")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", "")

OIDC_OP_AUTHORIZATION_ENDPOINT = ""
OIDC_OP_TOKEN_ENDPOINT = ""
OIDC_OP_USER_ENDPOINT = ""
OIDC_OP_JWKS_ENDPOINT = ""

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

OIDC_RP_SIGN_ALGO = os.environ.get("OIDC_RP_SIGN_ALGO", "HS256")

# Username is email address
OIDC_USERNAME_ALGO = lambda email: email

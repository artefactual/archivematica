# Shibboleth authentication settings

SHIBBOLETH_LOGOUT_URL = "/Shibboleth.sso/Logout?target=%s"
SHIBBOLETH_LOGOUT_REDIRECT_URL = "/administration/accounts/logged-out"

SHIBBOLETH_REMOTE_USER_HEADER = "HTTP_EPPN"
SHIBBOLETH_ATTRIBUTE_MAP = {
    # Automatic user fields
    "HTTP_GIVENNAME": (False, "first_name"),
    "HTTP_SN": (False, "last_name"),
    "HTTP_MAIL": (False, "email"),
    # Entitlement field (which we handle manually)
    "HTTP_ENTITLEMENT": (True, "entitlement"),
}

# If the user has this entitlement, they will be a superuser/admin
SHIBBOLETH_ADMIN_ENTITLEMENT = "preservation-admin"

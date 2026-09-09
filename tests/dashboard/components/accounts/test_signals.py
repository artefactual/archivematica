import pytest
import pytest_django

from archivematica.dashboard.components.accounts.signals import (
    _cas_user_is_administrator,
)

ADMIN_ATTRIBUTE = "memberOf"
ADMIN_ATTRIBUTE_VALUE = "administrators"


@pytest.mark.parametrize(
    "attributes,expected",
    [
        # The CAS client hands over a single group as a string and several
        # groups as a list, so both shapes have to be understood.
        ({ADMIN_ATTRIBUTE: ADMIN_ATTRIBUTE_VALUE}, True),
        ({ADMIN_ATTRIBUTE: "users"}, False),
        ({ADMIN_ATTRIBUTE: [ADMIN_ATTRIBUTE_VALUE, "users"]}, True),
        ({ADMIN_ATTRIBUTE: ["users", "staff"]}, False),
        ({}, False),
    ],
)
def test_cas_user_is_administrator(
    settings: pytest_django.Settings,
    attributes: dict[str, object],
    expected: bool,
) -> None:
    settings.CAS_ADMIN_ATTRIBUTE = ADMIN_ATTRIBUTE
    settings.CAS_ADMIN_ATTRIBUTE_VALUE = ADMIN_ATTRIBUTE_VALUE

    assert _cas_user_is_administrator(attributes) is expected


@pytest.mark.parametrize(
    "unset_setting", ["CAS_ADMIN_ATTRIBUTE", "CAS_ADMIN_ATTRIBUTE_VALUE"]
)
def test_unconfigured_admin_settings_grant_nobody_the_role(
    settings: pytest_django.Settings, unset_setting: str
) -> None:
    settings.CAS_ADMIN_ATTRIBUTE = ADMIN_ATTRIBUTE
    settings.CAS_ADMIN_ATTRIBUTE_VALUE = ADMIN_ATTRIBUTE_VALUE
    setattr(settings, unset_setting, None)

    assert _cas_user_is_administrator({ADMIN_ATTRIBUTE: ADMIN_ATTRIBUTE_VALUE}) is False

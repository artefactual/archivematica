import pytest
from django.contrib.auth.models import User

from archivematica.dashboard.components.accounts.forms import UserChangeForm


@pytest.mark.django_db
def test_current_password_is_not_required_when_not_changing_password(
    admin_user: User,
) -> None:
    # Create a user to edit.
    user_to_edit = User.objects.create_user(username="testuser", password="oldpass")

    # Form data without passwords.
    form_data = {
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
    }

    form = UserChangeForm(
        data=form_data, instance=user_to_edit, requesting_user=admin_user
    )

    # Form should be valid even if current_password is not provided.
    assert form.is_valid()


@pytest.mark.django_db
def test_current_password_is_required_when_changing_password(admin_user: User) -> None:
    # Create a user to edit.
    user_to_edit = User.objects.create_user(username="testuser", password="oldpass")

    # Form data with password change request but missing current_password.
    form_data = {
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
        "password": "newpass123",
        "password_confirmation": "newpass123",
    }

    form = UserChangeForm(
        data=form_data, instance=user_to_edit, requesting_user=admin_user
    )

    # Form should be invalid due to missing current_password.
    assert not form.is_valid()
    assert form.errors["current_password"] == [
        "Your current password is required when setting a new password."
    ]


@pytest.mark.django_db
def test_current_password_is_required_when_only_password_confirmation_provided(
    admin_user: User,
) -> None:
    # Create a user to edit.
    user_to_edit = User.objects.create_user(username="testuser", password="oldpass")

    # Form data with only password_confirmation but missing current_password.
    form_data = {
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
        "password": "",  # Empty password
        "password_confirmation": "newpass123",
    }

    form = UserChangeForm(
        data=form_data, instance=user_to_edit, requesting_user=admin_user
    )

    # Form should be invalid due to missing current_password.
    assert not form.is_valid()
    assert form.errors["current_password"] == [
        "Your current password is required when setting a new password."
    ]

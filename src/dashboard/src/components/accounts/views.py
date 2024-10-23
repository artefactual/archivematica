# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
from urllib.parse import urlencode

import components.decorators as decorators
from components.accounts.forms import ApiKeyForm
from components.accounts.forms import UserChangeForm
from components.accounts.forms import UserCreationForm
from components.accounts.forms import UserProfileForm
from components.helpers import generate_api_key
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import logout_then_login
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _
from main.models import UserProfile
from mozilla_django_oidc.views import OIDCAuthenticationRequestView
from mozilla_django_oidc.views import OIDCLogoutView
from tastypie.models import ApiKey


@user_passes_test(lambda u: u.is_superuser, login_url="/forbidden/")
def list(request):
    users = User.objects.all()
    return render(request, "accounts/list.html", locals())


@user_passes_test(lambda u: u.is_superuser, login_url="/forbidden/")
def add(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        userprofileform = UserProfileForm(request.POST)
        if form.is_valid():
            newuser = form.save(commit=False)
            newuser.is_staff = True
            newuser.save()
            api_key = ApiKey.objects.create(user=newuser)
            api_key.key = api_key.generate_key()
            api_key.save()
            user_profile = UserProfile.objects.get(user=newuser)
            userprofileform = UserProfileForm(request.POST, instance=user_profile)
            userprofileform.save()

            messages.info(request, _("Saved."))
            return redirect("accounts:accounts_index")
    else:
        # Clearing out values that are getting inherited from currently logged in user
        data = {"email": ""}
        form = UserCreationForm(initial=data)
        userprofileform = UserProfileForm()

    return render(
        request, "accounts/add.html", {"form": form, "userprofileform": userprofileform}
    )


def profile(request):
    # If users are editable in this setup, go to the editable profile view
    if settings.ALLOW_USER_EDITS:
        return edit(request)

    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    title = _("Your profile (%s)") % user

    if request.method == "POST":
        form = ApiKeyForm(request.POST)
        userprofileform = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid() and userprofileform.is_valid():
            if form.cleaned_data["regenerate_api_key"]:
                generate_api_key(user)
            userprofileform.save()

            return redirect("accounts:profile")
    else:
        form = ApiKeyForm()
        userprofileform = UserProfileForm(instance=user_profile)

    return render(
        request,
        "accounts/profile.html",
        {"form": form, "userprofileform": userprofileform, "title": title},
    )


def edit(request, id=None):
    # Forbidden if user isn't an admin and is trying to edit another user
    if str(request.user.id) != str(id) and id is not None:
        if request.user.is_superuser is False:
            return redirect("main:forbidden")

    # Load user
    if id is None:
        user = request.user
        title = "Edit your profile (%s)" % user
    else:
        user = get_object_or_404(User, pk=id)
        title = "Edit user %s" % user

    user_profile = UserProfile.objects.get(user=user)

    # Form
    if request.method == "POST":
        form = UserChangeForm(request.POST, instance=user)
        userprofileform = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid() and userprofileform.is_valid():
            user = form.save(commit=False)

            # change password if requested
            password = request.POST.get("password", "")
            if password != "":
                user.set_password(password)

            # prevent non-admin from self-promotion
            if not request.user.is_superuser:
                user.is_superuser = False

            user.save()
            userprofileform.save()

            # regenerate API key if requested
            regenerate_api_key = request.POST.get("regenerate_api_key", "")
            if regenerate_api_key != "":
                generate_api_key(user)

            # determine where to redirect to
            if request.user.is_superuser:
                return_view = "accounts:accounts_index"
            else:
                return_view = "accounts:profile"

            messages.info(request, _("Saved."))
            return redirect(return_view)
    else:
        suppress_administrator_toggle = True
        if request.user.is_superuser:
            suppress_administrator_toggle = False
        form = UserChangeForm(
            instance=user, suppress_administrator_toggle=suppress_administrator_toggle
        )
        userprofileform = UserProfileForm(instance=user_profile)

    return render(
        request,
        "accounts/edit.html",
        {
            "form": form,
            "userprofileform": userprofileform,
            "user": user,
            "title": title,
        },
    )


def delete_context(request, id):
    user = User.objects.get(pk=id)
    prompt = "Delete user " + user.username + "?"
    cancel_url = reverse("accounts:accounts_index")
    return {"action": "Delete", "prompt": prompt, "cancel_url": cancel_url}


@user_passes_test(lambda u: u.is_superuser, login_url="/forbidden/")
@decorators.confirm_required("simple_confirm.html", delete_context)
def delete(request, id):
    # Security check
    if request.user.id != id:
        if request.user.is_superuser is False:
            return redirect("main:forbidden")
    # Avoid removing the last user
    if 1 == User.objects.count():
        return redirect("main:forbidden")
    # Delete
    try:
        user = User.objects.get(pk=id)
        if request.user.username == user.username:
            raise Http404
        user.delete()
        return redirect("accounts:accounts_index")
    except Exception:
        raise Http404


class CustomOIDCAuthenticationRequestView(OIDCAuthenticationRequestView):
    """
    Provide OpenID Connect authentication
    """

    def get_settings(self, attr, *args):
        if attr in [
            "OIDC_RP_CLIENT_ID",
            "OIDC_RP_CLIENT_SECRET",
            "OIDC_OP_AUTHORIZATION_ENDPOINT",
            "OIDC_OP_TOKEN_ENDPOINT",
            "OIDC_OP_USER_ENDPOINT",
            "OIDC_OP_JWKS_ENDPOINT",
            "OIDC_OP_LOGOUT_ENDPOINT",
        ]:
            # Retrieve the request object stored in the instance.
            request = getattr(self, "request", None)

            if request:
                provider_name = request.session.get("providername")

                if provider_name and provider_name in settings.OIDC_PROVIDERS:
                    provider_settings = settings.OIDC_PROVIDERS.get(provider_name, {})
                    value = provider_settings.get(attr)

                    if value is None:
                        raise ImproperlyConfigured(
                            f"Setting {attr} for provider {provider_name} not found"
                        )
                    return value

        # If request is None or provider_name session var is not set or attr is
        # not in the list, call the superclass's get_settings method.
        return OIDCAuthenticationRequestView.get_settings(attr, *args)

    def get(self, request):
        self.request = request
        self.OIDC_RP_CLIENT_ID = self.get_settings("OIDC_RP_CLIENT_ID")
        self.OIDC_RP_CLIENT_SECRET = self.get_settings("OIDC_RP_CLIENT_SECRET")
        self.OIDC_OP_AUTH_ENDPOINT = self.get_settings("OIDC_OP_AUTHORIZATION_ENDPOINT")

        return super().get(request)


class CustomOIDCLogoutView(OIDCLogoutView):
    """
    Provide OpenID Logout capability
    """

    def get(self, request):
        self.request = request

        if "oidc_id_token" in request.session:
            # If the user authenticated via OIDC, perform the OIDC logout.
            redirect = super().post(request)

            if "providername" in request.session:
                del request.session["providername"]

            return redirect
        else:
            # If the user did not authenticate via OIDC, perform a local logout and redirect to login.
            return logout_then_login(request)


def get_oidc_logout_url(request):
    """
    Constructs the OIDC logout URL used in OIDCLogoutView.
    """
    # Retrieve the ID token from the session.
    id_token = request.session.get("oidc_id_token")

    if not id_token:
        raise ValueError("ID token not found in session.")

    # Get the end session endpoint.
    end_session_endpoint = getattr(settings, "OIDC_OP_LOGOUT_ENDPOINT", None)

    # Override the end session endpoint from the provider settings if available.
    if request:
        provider_name = request.session.get("providername")

        if provider_name and provider_name in settings.OIDC_PROVIDERS:
            provider_settings = settings.OIDC_PROVIDERS.get(provider_name, {})
            end_session_endpoint = provider_settings.get("OIDC_OP_LOGOUT_ENDPOINT")

            if end_session_endpoint is None:
                raise ImproperlyConfigured(
                    f"Setting OIDC_OP_LOGOUT_ENDPOINT for provider {provider_name} not found"
                )

    if not end_session_endpoint:
        raise ValueError("OIDC logout endpoint not configured for provider.")

    # Define the post logout redirect URL.
    post_logout_redirect_uri = request.build_absolute_uri("/")

    # Construct the logout URL with required parameters.
    params = {
        "id_token_hint": id_token,
        "post_logout_redirect_uri": post_logout_redirect_uri,
    }
    logout_url = f"{end_session_endpoint}?{urlencode(params)}"

    return logout_url

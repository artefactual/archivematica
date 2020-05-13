# -*- coding: utf-8 -*-
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
from __future__ import absolute_import

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _

from tastypie.models import ApiKey

from components.accounts.forms import UserCreationForm, UserProfileForm
from components.accounts.forms import UserChangeForm
from components.accounts.forms import ApiKeyForm
import components.decorators as decorators
from components.helpers import generate_api_key
from main.models import UserProfile


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
            if form["regenerate_api_key"] != "":
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
    except:
        raise Http404

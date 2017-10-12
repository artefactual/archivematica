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

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template import RequestContext
from django.utils.translation import ugettext as _

from tastypie.models import ApiKey

from components.accounts.forms import UserCreationForm
from components.accounts.forms import UserChangeForm
from components.accounts.forms import ApiKeyForm
import components.decorators as decorators
from components.helpers import generate_api_key


@user_passes_test(lambda u: u.is_superuser, login_url='/forbidden/')
def list(request):
    users = User.objects.all()
    return render(request, 'accounts/list.html', locals())


@user_passes_test(lambda u: u.is_superuser, login_url='/forbidden/')
def add(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            newuser = form.save(commit=False)
            newuser.is_staff = True
            newuser.save()
            api_key = ApiKey.objects.create(user=newuser)
            api_key.key = api_key.generate_key()
            api_key.save()

            messages.info(request, _('Saved.'))
            return redirect('components.accounts.views.list')
    else:
        # Clearing out values that are getting inherited from currently logged in user
        data = {'email': ''}
        form = UserCreationForm(initial=data)

    return render(request, 'accounts/add.html', {
        'form': form
    })


def profile(request):
    # If users are editable in this setup, go to the editable profile view
    if settings.ALLOW_USER_EDITS:
        return edit(request)

    user = request.user
    title = _('Your profile (%s)') % user

    if request.method == 'POST':
        form = ApiKeyForm(request.POST)
        if form.is_valid():
            if form['regenerate_api_key'] != '':
                generate_api_key(user)

            return redirect('profile')
    else:
        form = ApiKeyForm()

    return render(request, 'accounts/profile.html', {
        'form': form,
        'title': title
    })


def edit(request, id=None):
    # Forbidden if user isn't an admin and is trying to edit another user
    if str(request.user.id) != str(id) and id is not None:
        if request.user.is_superuser is False:
            return redirect('main.views.forbidden')

    # Load user
    if id is None:
        user = request.user
        title = 'Edit your profile (%s)' % user
    else:
        user = get_object_or_404(User, pk=id)
        title = 'Edit user %s' % user

    # Form
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)

            # change password if requested
            password = request.POST.get('password', '')
            if password != '':
                user.set_password(password)

            # prevent non-admin from self-promotion
            if not request.user.is_superuser:
                user.is_superuser = False

            user.save()

            # regenerate API key if requested
            regenerate_api_key = request.POST.get('regenerate_api_key', '')
            if regenerate_api_key != '':
                generate_api_key(user)

            # determine where to redirect to
            if request.user.is_superuser:
                return_view = 'components.accounts.views.list'
            else:
                return_view = 'profile'

            messages.info(request, _('Saved.'))
            return redirect(return_view)
    else:
        suppress_administrator_toggle = True
        if request.user.is_superuser:
            suppress_administrator_toggle = False
        form = UserChangeForm(instance=user, suppress_administrator_toggle=suppress_administrator_toggle)

    return render(request, 'accounts/edit.html', {
        'form': form,
        'user': user,
        'title': title
    })


def delete_context(request, id):
    user = User.objects.get(pk=id)
    prompt = 'Delete user ' + user.username + '?'
    cancel_url = reverse("components.accounts.views.list")
    return RequestContext(request, {'action': 'Delete', 'prompt': prompt, 'cancel_url': cancel_url})


@user_passes_test(lambda u: u.is_superuser, login_url='/forbidden/')
@decorators.confirm_required('simple_confirm.html', delete_context)
def delete(request, id):
    # Security check
    if request.user.id != id:
        if request.user.is_superuser is False:
            return redirect('main.views.forbidden')
    # Avoid removing the last user
    if 1 == User.objects.count():
        return redirect('main.views.forbidden')
    # Delete
    try:
        user = User.objects.get(pk=id)
        if request.user.username == user.username:
            raise Http404
        user.delete()
        return redirect('components.accounts.views.list')
    except:
        raise Http404

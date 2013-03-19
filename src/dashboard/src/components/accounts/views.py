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

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
import components.decorators as decorators
from django.template import RequestContext
from tastypie.models import ApiKey

from components.accounts.forms import UserCreationForm
from components.accounts.forms import UserChangeForm

@user_passes_test(lambda u: u.is_superuser, login_url='/forbidden/')
def list(request):
    users = User.objects.all()
    return render(request, 'accounts/list.html', locals())

@user_passes_test(lambda u: u.is_superuser, login_url='/forbidden/')
def add(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.save()
            api_key = ApiKey.objects.create(user=user)
            api_key.key = api_key.generate_key()
            api_key.save()
            return HttpResponseRedirect(reverse('components.accounts.views.list'))
    else:
        form = UserCreationForm()

    return render(request, 'accounts/add.html', {'form': form })

def edit(request, id=None):
    # Security check
    if request.user.id != id:
        if request.user.is_superuser is False:
            return HttpResponseRedirect(reverse('main.views.forbidden'))
    # Load user
    if id is None:
        user = request.user
        title = 'Edit your profile (%s)' % user
    else:
        try:
            user = User.objects.get(pk=id)
            title = 'Edit user %s' % user
        except:
            raise Http404
    # Form
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)

            # change password if requested
            password = request.POST.get('password', '')
            if password != '':
                user.set_password(password)
            user.save()

            # regenerate API key if requested
            regenerate_api_key = request.POST.get('regenerate_api_key', '')
            if regenerate_api_key != '':
                api_key = ApiKey.objects.get(user_id=user.pk)
                api_key.key = api_key.generate_key()
                api_key.save()
            return HttpResponseRedirect(reverse('components.accounts.views.list'))
    else:
        api_key_data = ApiKey.objects.get(user_id=user.pk)
        api_key = api_key_data.key
        form = UserChangeForm(instance=user)

    return render(request, 'accounts/edit.html', {
      'form': form,
      'user': user,
      'api_key': api_key,
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
            return HttpResponseRedirect(reverse('main.views.forbidden'))
    # Avoid removing the last user
    if 1 == User.objects.count():
        return HttpResponseRedirect(reverse('main.views.forbidden'))
    # Delete
    try:
        user = User.objects.get(pk=id)
        if request.user.username == user.username:
            raise Http404
        user.delete()
        return HttpResponseRedirect(reverse('components.accounts.views.list'))
    except:
        raise Http404

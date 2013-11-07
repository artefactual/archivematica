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
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
import components.decorators as decorators
from django.template import RequestContext
from tastypie.models import ApiKey
from components.accounts.forms import UserCreationForm
from components.accounts.forms import UserChangeForm
from components.helpers import hidden_features
from components.helpers import get_client_config_value

@user_passes_test(lambda u: u.is_superuser, login_url='/forbidden/')
def list(request):
    users = User.objects.all()
    hide_features = hidden_features()
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

            messages.info(request, 'Saved.')
            return redirect('components.accounts.views.list')
        else:
            print "%s" % repr(form.errors)   
    else:
        #clearing out values that are getting inherited from currently logged in user
        data = {'email':' '} 
        form = UserCreationForm(initial=data)

    return render(request, 'accounts/add.html', {
        'hide_features': hidden_features(),
        'form': form
    })

def edit(request, id=None):
    if get_client_config_value('kioskMode') == 'True':
        return redirect('main.views.forbidden')

    # Forbidden if user isn't an admin and is trying to edit another user
    if str(request.user.id) != str(id) and id != None:
        if request.user.is_superuser is False:
            return redirect('main.views.forbidden')

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

            # prevent non-admin from self-promotion
            if not request.user.is_superuser:
                user.is_superuser = False

            user.save()

            # regenerate API key if requested
            regenerate_api_key = request.POST.get('regenerate_api_key', '')
            if regenerate_api_key != '':
                try:
                    api_key = ApiKey.objects.get(user_id=user.pk)
                except ApiKey.DoesNotExist:
                    api_key = ApiKey.objects.create(user=user)
                api_key.key = api_key.generate_key()
                api_key.save()

            # determine where to redirect to
            if request.user.is_superuser is False:
                return_view = 'components.accounts.views.edit'
            else:
                return_view = 'components.accounts.views.list'

            messages.info(request, 'Saved.')
            return redirect(return_view)
    else:
        suppress_administrator_toggle = True
        if request.user.is_superuser:
            suppress_administrator_toggle = False
        form = UserChangeForm(instance=user, suppress_administrator_toggle=suppress_administrator_toggle)

    # load API key for display
    try:
        api_key_data = ApiKey.objects.get(user_id=user.pk)
        api_key = api_key_data.key
    except:
        api_key = '<no API key generated>'

    return render(request, 'accounts/edit.html', {
      'hide_features': hidden_features(),
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

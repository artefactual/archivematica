# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactua# Archivematica is free software: you can redistribute it and/or modify
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

from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.template import RequestContext
from main import forms
from main import models
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes
from django.contrib.auth.decorators import user_passes_test
import urllib
import components.decorators as decorators

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Administration
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def administration(request):
    return HttpResponseRedirect(reverse('components.administration.views.administration_dip'))

def administration_search(request):
    message = request.GET.get('message', '')
    aip_files_indexed = archival_storage_indexed_count('aips')
    return render(request, 'main/administration/search.html', locals())

def administration_search_flush_aips_context(request):
    prompt = 'Flush AIP search index?'
    cancel_url = reverse("main.views.administration_search")
    return RequestContext(request, {'action': 'Flush', 'prompt': prompt, 'cancel_url': cancel_url})

@decorators.confirm_required('simple_confirm.html', administration_search_flush_aips_context)
@user_passes_test(lambda u: u.is_superuser, login_url='/forbidden/')
def administration_search_flush_aips(request):
    conn = pyes.ES('127.0.0.1:9200')
    index = 'aips'

    try:
        conn.delete_index(index)
        message = 'AIP search index flushed.'
        try:
            conn.create_index(index)
        except pyes.exceptions.IndexAlreadyExistsException:
            message = 'Error recreating AIP search index.'

    except:
        message = 'Error flushing AIP search index.'
        pass

    params = urllib.urlencode({'message': message})
    return HttpResponseRedirect(reverse("main.views.administration_search") + "?%s" % params)

def administration_dip(request):
    upload_setting = models.StandardTaskConfig.objects.get(execute="upload-qubit_v0.0")
    return render(request, 'main/administration/dip.html', locals())

def administration_dip_edit(request, id):
    if request.method == 'POST':
        upload_setting = models.StandardTaskConfig.objects.get(pk=id)
        form = forms.AdministrationForm(request.POST)
        if form.is_valid():
            upload_setting.arguments = form.cleaned_data['arguments']
            upload_setting.save()

    return HttpResponseRedirect(reverse("components.administration.views.administration_dip"))

def administration_atom_dips(request):
    link_id = administration_atom_dip_destination_select_link_id()
    ReplaceDirChoices = models.MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=link_id)

    ReplaceDirChoiceFormSet = administration_dips_formset()

    valid_submission, formset = administration_dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet)

    if request.method != 'POST' or valid_submission:
        formset = ReplaceDirChoiceFormSet(queryset=ReplaceDirChoices)

    return render(request, 'main/administration/dips_edit.html', locals())

def administration_contentdm_dips(request):
    link_id = administration_contentdm_dip_destination_select_link_id()
    ReplaceDirChoices = models.MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=link_id)

    ReplaceDirChoiceFormSet = administration_dips_formset()

    valid_submission, formset = administration_dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet)

    if request.method != 'POST' or valid_submission:
        formset = ReplaceDirChoiceFormSet(queryset=ReplaceDirChoices)

    return render(request, 'main/administration/dips_contentdm_edit.html', locals())

def administration_atom_dip_destination_select_link_id():
    taskconfigs = models.TaskConfig.objects.filter(description='Select DIP upload destination')
    taskconfig = taskconfigs[0]
    links = models.MicroServiceChainLink.objects.filter(currenttask=taskconfig.id)
    link = links[0]
    return link.id

def administration_contentdm_dip_destination_select_link_id():
    taskconfigs = models.TaskConfig.objects.filter(description='Select target CONTENTdm server')
    taskconfig = taskconfigs[0]
    links = models.MicroServiceChainLink.objects.filter(currenttask=taskconfig.id)
    link = links[0]
    return link.id

def administration_dips_formset():
    return modelformset_factory(
        models.MicroServiceChoiceReplacementDic,
        form=forms.MicroServiceChoiceReplacementDicForm,
        extra=1,
        can_delete=True
    )

def administration_dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet):
    valid_submission = True
    formset = None

    if request.method == 'POST':
        formset = ReplaceDirChoiceFormSet(request.POST)

        # take note of formset validity because if submission was successful
        # we reload it to reflect
        # deletions, etc.
        valid_submission = formset.is_valid()

        if valid_submission:
            # save/delete partial data (without association with specific link)
            instances = formset.save()

            # restore link association
            for instance in instances:
                instance.choiceavailableatlink = link_id
                instance.save()
    return valid_submission, formset

def administration_sources(request):
    return render(request, 'main/administration/sources.html', locals())

def administration_sources_json(request):
    message = ''
    if request.method == 'POST':
         path = request.POST.get('path', '')
         if path != '':
              try:
                  models.SourceDirectory.objects.get(path=path)
              except models.SourceDirectory.DoesNotExist:
                  # save dir
                  source_dir = models.SourceDirectory()
                  source_dir.path = path
                  source_dir.save()
                  message = 'Directory added.'
              else:
                  message = 'Directory already added.'
         else:
              message = 'Path is empty.'

    response = {}
    response['message'] = message
    response['directories'] = []

    for directory in models.SourceDirectory.objects.all():
      response['directories'].append({
        'id':   directory.id,
        'path': directory.path
      })
    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def administration_sources_delete_json(request, id):
    models.SourceDirectory.objects.get(pk=id).delete()
    response = {}
    response['message'] = 'Deleted.'
    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')
    #return HttpResponseRedirect(reverse('main.views.administration_sources'))

def administration_processing(request):
    file_path = '/var/archivematica/sharedDirectory/sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml'

    if request.method == 'POST':
        xml = request.POST.get('xml', '')
        file = open(file_path, 'w')
        file.write(xml)
    else:
        file = open(file_path, 'r')
        xml = file.read()

    return render(request, 'main/administration/processing.html', locals())

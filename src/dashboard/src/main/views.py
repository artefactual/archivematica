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

from django.conf import settings as django_settings
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from contrib.mcp.client import MCPClient
from main import models
from lxml import etree
import os, subprocess
from components import helpers

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Home
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def home(request):
    if 'first_login' in request.session and request.session['first_login']:
        request.session.first_login = False
        redirectUrl = reverse('components.administration.views.administration')
    else:
        redirectUrl = reverse('components.transfer.views.transfer_grid')
    return HttpResponseRedirect(redirectUrl)

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Status
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

# TODO: hide removed elements
def status(request):
    client = MCPClient()
    xml = etree.XML(client.list())

    sip_count = len(xml.xpath('//choicesAvailableForUnits/choicesAvailableForUnit/unit/type[text()="SIP"]'))
    transfer_count = len(xml.xpath('//choicesAvailableForUnits/choicesAvailableForUnit/unit/type[text()="Transfer"]'))
    dip_count = len(xml.xpath('//choicesAvailableForUnits/choicesAvailableForUnit/unit/type[text()="DIP"]'))

    response = {'sip': sip_count, 'transfer': transfer_count, 'dip': dip_count}

    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Access
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def access_list(request):
    access = models.Access.objects.all()
    for item in access:
        semicolon_position = item.resource.find(';')
        if semicolon_position != -1:
            target = item.resource.split('/').pop()
            remove_length = len(item.resource) - semicolon_position
            chunk = item.resource[:-remove_length] + target
            item.destination = chunk
        else:
            item.destination = item.resource
    return render(request, 'main/access.html', locals())

def access_delete(request, id):
    access = get_object_or_404(models.Access, pk=id)
    access.delete()
    return HttpResponseRedirect(reverse('main.views.access_list'))

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Misc
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def forbidden(request):
    return render(request, 'forbidden.html')

def task(request, uuid):
    task = models.Task.objects.get(taskuuid=uuid)
    task.duration = helpers.task_duration_in_seconds(task)
    objects = [task]
    return render(request, 'main/tasks.html', locals())

def tasks(request, uuid):
    job = models.Job.objects.get(jobuuid=uuid)
    objects = job.task_set.all().order_by('-exitcode', '-endtime', '-starttime', '-createdtime')

    if (len(objects) == 0):
        return tasks_subjobs(request, uuid)

    page    = helpers.pager(objects, django_settings.TASKS_PER_PAGE, request.GET.get('page', None))
    objects = page['objects']

    # figure out duration in seconds
    for object in objects:
         object.duration = helpers.task_duration_in_seconds(object)

    return render(request, 'main/tasks.html', locals())

def tasks_subjobs(request, uuid):
    jobs = []
    possible_jobs = models.Job.objects.filter(subjobof=uuid)

    for job in possible_jobs:
        subjobs = models.Job.objects.filter(subjobof=job.jobuuid)
        job.total_subjobs = len(subjobs)
        job.path_to_file = job.directory.replace('%SIPDirectory%', '', 1)
        jobs.append(job)

    if len(jobs) == 1:
        return tasks(request, jobs[0].jobuuid)
    else:
        return render(request, 'main/tasks_subjobs.html', locals())

def jobs_list_objects(request, uuid):
    response = []
    job = models.Job.objects.get(jobuuid=uuid)

    for root, dirs, files in os.walk(job.directory + '/objects', False):
        for name in files:
            directory = root.replace(job.directory + '/objects', '')
            response.append(os.path.join(directory, name))

    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def jobs_explore(request, uuid):
    # Database query
    job = models.Job.objects.get(jobuuid=uuid)
    # Prepare response object
    contents = []
    response = {}
    response['contents'] = contents
    # Parse request
    if 'path' in request.REQUEST and len(request.REQUEST['path']) > 0:
        directory = os.path.join(job.directory, request.REQUEST['path'])
        response['base'] = request.REQUEST['path'].replace('.', '')
    else:
        directory = job.directory
        response['base'] = ''
    # Build directory
    directory = os.path.abspath(directory)
    # Security check
    tmpDirectory = os.path.realpath(directory)
    while True:
        if tmpDirectory == os.path.realpath(job.directory):
            break
        elif tmpDirectory == '/':
            raise Http404
        else:
            tmpDirectory = os.path.dirname(tmpDirectory)
    # If it is a file, return the contents
    if os.path.isfile(directory):
        mime = subprocess.Popen('/usr/bin/file --mime-type ' + directory, shell=True, stdout=subprocess.PIPE).communicate()[0].split(' ')[-1].strip()
        response = HttpResponse(mimetype=mime)
        response['Content-Disposition'] = 'attachment; filename=%s' %  os.path.basename(directory)
        with open(directory) as resource:
            response.write(resource.read())
        return response
    # Cleaning path
    parentDir = os.path.dirname(directory)
    parentDir = parentDir.replace('%s/' % job.directory, '')
    parentDir = parentDir.replace('%s' % job.directory, '')
    response['parent'] = parentDir
    # Check if it is or not the root dir to add the "Go parent" link
    if os.path.realpath(directory) != os.path.realpath(job.directory):
        parent = {}
        parent['name'] = 'Go to parent directory...'
        parent['type'] = 'parent'
        contents.append(parent)
    # Add contents of the directory
    for item in os.listdir(directory):
        newItem = {}
        newItem['name'] = item
        if os.path.isdir(os.path.join(directory, item)):
            newItem['type'] = 'dir'
        else:
            newItem['type'] = 'file'
            newItem['size'] = os.path.getsize(os.path.join(directory, item))
        contents.append(newItem)
    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def formdata_delete(request, type, parent_id, delete_id):
  return formdata(request, type, parent_id, delete_id)

def formdata(request, type, parent_id, delete_id = None):
    model    = None
    results  = None
    response = {}

    # define types handled
    if (type == 'rightsnote'):
        model = models.RightsStatementRightsGrantedNote
        parent_model = models.RightsStatementRightsGranted
        model_parent_field = 'rightsgranted'
        model_value_fields = ['rightsgrantednote']

        results = model.objects.filter(rightsgranted=parent_id)

    if (type == 'rightsrestriction'):
        model = models.RightsStatementRightsGrantedRestriction
        parent_model = models.RightsStatementRightsGranted
        model_parent_field = 'rightsgranted'
        model_value_fields = ['restriction']

        results = model.objects.filter(rightsgranted=parent_id)

    if (type == 'licensenote'):
        model = models.RightsStatementLicenseNote
        parent_model = models.RightsStatementLicense
        model_parent_field = 'rightsstatementlicense'
        model_value_fields = ['licensenote']

        results = model.objects.filter(rightsstatementlicense=parent_id)

    if (type == 'statutenote'):
        model = models.RightsStatementStatuteInformationNote
        parent_model = models.RightsStatementStatuteInformation
        model_parent_field = 'rightsstatementstatute'
        model_value_fields = ['statutenote']

        results = model.objects.filter(rightsstatementstatute=parent_id)

    if (type == 'copyrightnote'):
        model = models.RightsStatementCopyrightNote
        parent_model = models.RightsStatementCopyright
        model_parent_field = 'rightscopyright'
        model_value_fields = ['copyrightnote']

        results = model.objects.filter(rightscopyright=parent_id)

    if (type == 'copyrightdocumentationidentifier'):
        model = models.RightsStatementCopyrightDocumentationIdentifier
        parent_model = models.RightsStatementCopyright
        model_parent_field = 'rightscopyright'
        model_value_fields = [
          'copyrightdocumentationidentifiertype',
          'copyrightdocumentationidentifiervalue',
          'copyrightdocumentationidentifierrole'
        ]

        results = model.objects.filter(rightscopyright=parent_id)

    if (type == 'statutedocumentationidentifier'):
        model = models.RightsStatementStatuteDocumentationIdentifier
        parent_model = models.RightsStatementStatuteInformation
        model_parent_field = 'rightsstatementstatute'
        model_value_fields = [
          'statutedocumentationidentifiertype',
          'statutedocumentationidentifiervalue',
          'statutedocumentationidentifierrole'
        ]

        results = model.objects.filter(rightsstatementstatute=parent_id)

    if (type == 'licensedocumentationidentifier'):
        model = models.RightsStatementLicenseDocumentationIdentifier
        parent_model = models.RightsStatementLicense
        model_parent_field = 'rightsstatementlicense'
        model_value_fields = [
          'licensedocumentationidentifiertype',
          'licensedocumentationidentifiervalue',
          'licensedocumentationidentifierrole'
        ]

        results = model.objects.filter(rightsstatementlicense=parent_id)

    if (type == 'otherrightsdocumentationidentifier'):
        model = models.RightsStatementOtherRightsDocumentationIdentifier
        parent_model = models.RightsStatementOtherRightsInformation
        model_parent_field = 'rightsstatementotherrights'
        model_value_fields = [
          'otherrightsdocumentationidentifiertype',
          'otherrightsdocumentationidentifiervalue',
          'otherrightsdocumentationidentifierrole'
        ]

        results = model.objects.filter(rightsstatementotherrights=parent_id)

    if (type == 'otherrightsnote'):
        model = models.RightsStatementOtherRightsInformationNote
        parent_model = models.RightsStatementOtherRightsInformation
        model_parent_field = 'rightsstatementotherrights'
        model_value_fields = ['otherrightsnote']

        results = model.objects.filter(rightsstatementotherrights=parent_id)

    # handle creation
    if (request.method == 'POST'):
        # load or initiate model instance
        id = request.POST.get('id', 0)
        if id > 0:
            instance = model.objects.get(pk=id)
        else:
            instance = model()

        # set instance parent
        parent = parent_model.objects.filter(pk=parent_id)
        setattr(instance, model_parent_field, parent[0])

        # set instance field values using request data
        for field in model_value_fields:
            value = request.POST.get(field, '')
            setattr(instance, field, value)
        instance.save()

        if id == 0:
          response['new_id']  = instance.pk

        response['message'] = 'Added.'

    # handle deletion
    if (request.method == 'DELETE'):
        if (delete_id == None):
            response['message'] = 'Error: no delete ID supplied.'
        else:
            model.objects.filter(pk=delete_id).delete()
            response['message'] = 'Deleted.'

    # send back revised data
    if (results != None):
        response['results'] = []
        for result in results:
            values = {}
            for field in model_value_fields:
                values[field] = result.__dict__[field]
            response['results'].append({
              'id': result.pk,
              'values': values
            });

    if (model == None):
        response['message'] = 'Incorrect type.'

    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def chain_insert():
    # first choice
    standardTaskConfig = models.StandardTaskConfig()
    standardTaskConfig.save()

    taskConfig = models.TaskConfig()
    taskConfig.tasktype = 5
    taskConfig.tasktypepkreference = standardTaskConfig.id
    taskConfig.description = 'Select DIP upload destination'
    taskConfig.save()

    link = models.MicroServiceChainLink()
    link.microservicegroup = 'Upload DIP'
    link.currenttask = taskConfig.id
    link.save()
    choice_link_id = link.id

    choice = models.MicroServiceChoiceReplacementDic()
    choice.choiceavailableatlink = link.id
    choice.description = 'Test dict 1'
    choice.replacementdic = '{}'
    choice.save()

    choice = models.MicroServiceChoiceReplacementDic()
    choice.choiceavailableatlink = link.id
    choice.description = 'Test dict 2'
    choice.replacementdic = '{}'
    choice.save()

    # take note of ID of existing chain to points to ICA AtoM DIP upload links
    #chains = models.MicroServiceChain.objects.filter(description='Upload DIP to ICA-ATOM')
    #chain = chains[0]
    #upload_start_link_id = chain.startinglink
    #chain.startinglink = choice_link_id
    #chain.description = 'Select Upload Destination'
    #chain.save()


    # make new chain to point to ICA AtoM DIP upload links
    chain = models.MicroServiceChain()
    chain.startinglink = choice_link_id
    chain.description = 'Select DIP destination'
    chain.save()

    # rewire old choice to point to new chain
    choices = models.MicroServiceChainChoice.objects.filter(chainavailable=23)
    choice = choices[0]
    choice.chainavailable = chain.id
    choice.save()

    # add exit code to the choice link that points to the Qubit upload link
    code = models.MicroServiceChainLinkExitCode()
    code.exitcode = 0
    code.microservicechainlink = choice_link_id
    code.nextmicroservicechainlink = 4
    code.exitmessage = 'Completed successfully'
    code.save()

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

from django.shortcuts import render_to_response
from django.http import Http404
from django.utils.functional import wraps
from django.template import RequestContext

from contrib import utils
from main import models


# Try to update context instead of sending new params
def load_jobs(view):
    @wraps(view)
    def inner(request, uuid, *args, **kwargs):
        jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
        if 0 == jobs.count:
            raise Http404
        kwargs['jobs'] = jobs
        kwargs['name'] = utils.get_directory_name_from_job(jobs)
        return view(request, uuid, *args, **kwargs)
    return inner


# Requires confirmation from a prompt page before executing a request
# (see http://djangosnippets.org/snippets/1922/)
def confirm_required(template_name, context_creator, key='__confirm__'):
    def decorator(func):
        def inner(request, *args, **kwargs):
            if key in request.POST:
                return func(request, *args, **kwargs)
            else:
                context = context_creator and context_creator(request, *args, **kwargs) \
                    or RequestContext(request)
                return render_to_response(template_name, context)
        return wraps(func)(inner)
    return decorator

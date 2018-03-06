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


import os
import re
from glob import iglob
import logging

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404

from components import helpers
from processing import install_builtin_config
from .forms import ProcessingConfigurationForm


logger = logging.getLogger('archivematica.dashboard')


def list(request):
    files = []
    ignored = []
    for item in iglob('{}/*ProcessingMCP.xml'.format(helpers.processing_config_path())):
        basename = os.path.basename(item)
        name = re.sub('ProcessingMCP\.xml$', '', basename)
        if re.match(r'^\w{1,16}$', name) is None:
            ignored.append((basename, name, item))
            continue
        files.append((basename, name, item))
    return render(request, 'administration/processing.html', {'files': files, 'ignored': ignored})


def edit(request, name=None):
    if request.method == 'POST':
        form = ProcessingConfigurationForm(request.POST)
        if form.is_valid():
            try:
                form.save_config()
            except Exception:
                msg = 'Failed to save processing config.'
                logger.exception(msg)
                messages.error(request, msg)
            else:
                messages.info(request, 'Saved!')
            return redirect('components.administration.views_processing.list')
    else:
        form = ProcessingConfigurationForm()
        if name is not None:
            try:
                form.load_config(name)
            except IOError:
                raise Http404
    return render(request, 'administration/processing_edit.html', {'form': form})


def delete(request, name):
    if name == 'default':
        return redirect('components.administration.views_processing.list')
    config_path = os.path.join(helpers.processing_config_path(), '{}ProcessingMCP.xml'.format(name))
    try:
        os.remove(config_path)
    except OSError:
        pass
    return redirect('components.administration.views_processing.list')


def reset(request, name):
    try:
        install_builtin_config(name, force=True)
        messages.info(request, 'Configuration "%s" was reset' % name)
    except Exception:
        msg = 'Failed to reset processing config "%s".' % name
        logger.exception(msg)
        messages.error(request, msg)

    return redirect('components.administration.views_processing.list')

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

import os
import re
from glob import iglob
import logging

from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _

from components import helpers
from processing import install_builtin_config
from .forms import ProcessingConfigurationForm


logger = logging.getLogger("archivematica.dashboard")


def list(request):
    files = []
    ignored = []
    for item in iglob("{}/*ProcessingMCP.xml".format(helpers.processing_config_path())):
        basename = os.path.basename(item)
        name = re.sub("ProcessingMCP\.xml$", "", basename)
        if re.match(ProcessingConfigurationForm.NAME_REGEX, name) is None:
            ignored.append((basename, name, item))
            continue
        files.append((basename, name, item))
    return render(
        request, "administration/processing.html", {"files": files, "ignored": ignored}
    )


def edit(request, name=None):
    def _report_error(error=None, error_msg=None):
        if error is not None:
            logger.exception("{} {}".format(error_msg, error))
            messages.error(request, error_msg)
        return redirect("administration:processing")

    def _render_form():
        return render(request, "administration/processing_edit.html", {"form": form})

    # Initialize form.
    try:
        form = ProcessingConfigurationForm(request.POST or None, user=request.user)
    except Exception as err:
        return _report_error(err, _("Unable to load processing configuration page."))

    # Process form post.
    if request.method == "POST":
        if form.is_valid() is False:
            return _render_form()
        try:
            form.save_config()
        except Exception as err:
            return _report_error(err, _("Failed to save processing configuration."))
        messages.info(request, _("Saved!"))
        return redirect("administration:processing")

    # New configuration.
    if name is None:
        return _render_form()

    # Load existing configuration.
    try:
        form.load_config(name)
    except IOError:
        raise Http404
    except Exception as err:
        return _report_error(err, _("Failed to load processing configuration."))
    return _render_form()


def delete(request, name):
    if name == "default":
        return redirect("administration:processing")
    config_path = os.path.join(
        helpers.processing_config_path(), "{}ProcessingMCP.xml".format(name)
    )
    try:
        os.remove(config_path)
    except OSError:
        pass
    return redirect("administration:processing")


def download(request, name):
    config_path = os.path.join(
        helpers.processing_config_path(), "{}ProcessingMCP.xml".format(name)
    )
    if not os.path.isfile(config_path):
        raise Http404
    return helpers.send_file(request, config_path, force_download=True)


def reset(request, name):
    try:
        install_builtin_config(name, force=True)
        messages.info(request, 'Configuration "%s" was reset' % name)
    except Exception:
        msg = 'Failed to reset processing config "%s".' % name
        logger.exception(msg)
        messages.error(request, msg)

    return redirect("administration:processing")

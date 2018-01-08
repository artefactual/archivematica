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

import collections
import logging
import os
import shutil
import subprocess

from django.conf import settings as django_settings
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Max, Min
from django.http import Http404, HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template import RequestContext
from django.utils.translation import ugettext as _

from main import models
from components.administration.forms import AgentForm, StorageSettingsForm, ChecksumSettingsForm, TaxonomyTermForm
import components.administration.views_processing as processing_views
import components.decorators as decorators
import components.helpers as helpers
import storageService as storage_service

from version import get_version


logger = logging.getLogger('archivematica.dashboard')

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Administration
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def administration(request):
    return redirect('components.administration.views_processing.list')


def failure_report(request, report_id=None):
    if report_id is not None:
        report = models.Report.objects.get(pk=report_id)
        return render(request, 'administration/reports/failure_detail.html', locals())
    else:
        current_page_number = request.GET.get('page', '1')
        items_per_page = 10

        reports = models.Report.objects.all().order_by('-created')
        page = helpers.pager(reports, items_per_page, current_page_number)
        return render(request, 'administration/reports/failures.html', locals())


def delete_context(request, report_id):
    report = models.Report.objects.get(pk=report_id)
    prompt = 'Delete failure report for ' + report.unitname + '?'
    cancel_url = reverse("components.administration.views.failure_report")
    return RequestContext(request, {'action': 'Delete', 'prompt': prompt, 'cancel_url': cancel_url})


@decorators.confirm_required('simple_confirm.html', delete_context)
def failure_report_delete(request, report_id):
    models.Report.objects.get(pk=report_id).delete()
    messages.info(request, _('Deleted.'))
    return redirect('components.administration.views.failure_report')


def failure_report_detail(request):
    return render(request, 'administration/reports/failure_report_detail.html', locals())


def atom_levels_of_description(request):
    if request.method == 'POST':
        level_operation = request.POST.get('operation')
        level_id = request.POST.get('id')

        if level_operation == 'promote':
            if _atom_levels_of_description_sort_adjust(level_id, 'promote'):
                messages.info(request, _('Promoted.'))
            else:
                messages.error(request, _('Error attempting to promote level of description.'))
        elif level_operation == 'demote':
            if _atom_levels_of_description_sort_adjust(level_id, 'demote'):
                messages.info(request, _('Demoted.'))
            else:
                messages.error(request, _('Error attempting to demote level of description.'))
        elif level_operation == 'delete':
            try:
                level = models.LevelOfDescription.objects.get(id=level_id)
                level.delete()
                messages.info(request, _('Deleted.'))
            except models.LevelOfDescription.DoesNotExist:
                messages.error(request, _('Level of description not found.'))

    levels = models.LevelOfDescription.objects.order_by('sortorder')
    sortorder_min = models.LevelOfDescription.objects.aggregate(min=Min('sortorder'))['min']
    sortorder_max = models.LevelOfDescription.objects.aggregate(max=Max('sortorder'))['max']

    return render(request, 'administration/atom_levels_of_description.html', {
        'levels': levels,
        'sortorder_min': sortorder_min,
        'sortorder_max': sortorder_max,
    })


def _atom_levels_of_description_sort_adjust(level_id, sortorder='promote'):
    """
    Move LevelOfDescription with level_id up or down one.

    :param int level_id: ID of LevelOfDescription to adjust
    :param string sortorder: 'promote' to demote level_id, 'demote' to promote level_id
    :returns: True if success, False otherwise.
    """
    try:
        level = models.LevelOfDescription.objects.get(id=level_id)
        # Get object with next highest/lowest sortorder
        if sortorder == 'demote':
            previous_level = models.LevelOfDescription.objects.order_by('sortorder').filter(sortorder__gt=level.sortorder)[:1][0]
        elif sortorder == 'promote':
            previous_level = models.LevelOfDescription.objects.order_by('-sortorder').filter(sortorder__lt=level.sortorder)[:1][0]
    except (models.LevelOfDescription.DoesNotExist, IndexError):
        return False

    # Swap
    level.sortorder, previous_level.sortorder = previous_level.sortorder, level.sortorder
    level.save()
    previous_level.save()
    return True


def storage(request):
    try:
        locations = storage_service.get_location(purpose="AS")
    except:
        messages.warning(request, _('Error retrieving locations: is the storage server running? Please contact an administrator.'))

    system_directory_description = 'Available storage'
    return render(request, 'administration/locations.html', locals())


def usage(request):
    """
    Return page summarizing storage usage
    """
    usage_dirs = _usage_dirs()

    context = {'usage_dirs': usage_dirs}
    return render(request, 'administration/usage.html', context)


def _usage_dirs(calculate_usage=True):
    """
    Provide usage data

    Return maximum size and, optionally, current usage of a number of directories

    :param bool calculate_usage: True if usage should be calculated.
    :returns OrderedDict: Dict where key is a descriptive handle and value is a dict with the path, description, parent directory ID, and optionally size and usage.
    """
    # Put spaces before directories contained by the spaces
    #
    # Description is optional, but either a path or a location purpose (used to
    # look up the path) should be specified
    #
    # If only certain sudirectories within a path should be deleted, set
    # 'subdirectories' to a list of them
    dir_defs = (
        ('shared', {
            'path': django_settings.SHARED_DIRECTORY,
        }),
        ('dips', {
            'description': 'DIP uploads',
            'path': os.path.join('watchedDirectories', 'uploadedDIPs'),
            'contained_by': 'shared'
        }),
        ('rejected', {
            'description': 'Rejected',
            'path': 'rejected',
            'contained_by': 'shared'
        }),
        ('failed', {
            'description': 'Failed',
            'path': 'failed',
            'contained_by': 'shared'
        }),
        ('tmp', {
            'description': 'Temporary file storage',
            'path': 'tmp',
            'contained_by': 'shared'
        })
    )

    dirs = collections.OrderedDict(dir_defs)

    # Resolve location paths and make relative paths absolute
    for __, dir_spec in dirs.items():
        if 'contained_by' in dir_spec:
            # If contained, make path absolute
            space = dir_spec['contained_by']
            absolute_path = os.path.join(dirs[space]['path'], dir_spec['path'])
            dir_spec['path'] = absolute_path

            if calculate_usage:
                dir_spec['size'] = dirs[space]['size']
                dir_spec['used'] = _usage_get_directory_used_bytes(dir_spec['path'])
        elif calculate_usage:
            # Get size/usage of space
            space_path = dir_spec['path']
            dir_spec['size'] = _usage_check_directory_volume_size(space_path)
            dir_spec['used'] = _usage_get_directory_used_bytes(space_path)

    return dirs


def _usage_check_directory_volume_size(path):
    """
    Check the size of the volume containing a given path

    :param str path: path to check
    :returns: size in bytes, or 0 on error
    """
    # Get volume size (in 1K blocks)
    try:
        output = subprocess.check_output(["df", '--block-size', '1024', path])

        # Second line returns disk usage-related values
        usage_summary = output.split("\n")[1]

        # Split value by whitespace and size (in blocks)
        size = usage_summary.split()[1]

        return int(size) * 1024
    except OSError:
        logger.exception('No such directory: %s', path)
        return 0
    except subprocess.CalledProcessError:
        logger.exception('Unable to determine size of %s', path)
        return 0


def _usage_get_directory_used_bytes(path):
    """
    Check the spaced used at a given path

    :param string path: path to check
    :returns: usage in bytes
    """
    try:
        output = subprocess.check_output(["du", "--bytes", "--summarize", path])
        return output.split("\t")[0]
    except OSError:
        logger.exception('No such directory: %s', path)
        return 0
    except subprocess.CalledProcessError:
        logger.exception('Unable to determine usage of %s.', path)
        return 0


def clear_context(request, dir_id):
    """
    Confirmation context for emptying a directory

    :param dir_id: Key for the directory in _usage_dirs
    """
    usage_dirs = _usage_dirs(False)
    prompt = 'Clear ' + usage_dirs[dir_id]['description'] + '?'
    cancel_url = reverse("components.administration.views.usage")
    return RequestContext(request, {'action': 'Delete', 'prompt': prompt, 'cancel_url': cancel_url})


@user_passes_test(lambda u: u.is_superuser, login_url='/forbidden/')
@decorators.confirm_required('simple_confirm.html', clear_context)
def usage_clear(request, dir_id):
    """
    Empty a directory

    :param dir_id: Descriptive shorthand for the directory, key for _usage_dirs
    """
    if request.method == 'POST':
        usage_dirs = _usage_dirs(False)
        dir_info = usage_dirs[dir_id]

        # Prevent shared directory from being cleared
        if dir_id == 'shared' or not dir_info:
            raise Http404

        # Determine if specific subdirectories need to be cleared, rather than
        # whole directory
        if 'subdirectories' in dir_info:
            dirs_to_empty = [os.path.join(dir_info['path'], subdir) for subdir in dir_info['subdirectories']]
        else:
            dirs_to_empty = [dir_info['path']]

        # Attempt to clear directories
        successes = []
        errors = []

        for directory in dirs_to_empty:
            try:
                for entry in os.listdir(directory):
                    entry_path = os.path.join(directory, entry)
                    if os.path.isfile(entry_path):
                        os.unlink(entry_path)
                    else:
                        shutil.rmtree(entry_path)
                successes.append(directory)
            except OSError:
                message = 'No such file or directory: {}'.format(directory)
                logger.exception(message)
                errors.append(message)

        # If any deletion attempts successed, summarize in flash message
        if len(successes):
            message = 'Cleared %s.' % ', '.join(successes)
            messages.info(request, message)

        # Show flash message for each error encountered
        for error in errors:
            messages.error(request, error)

        return redirect('components.administration.views.usage')
    else:
        return HttpResponseNotAllowed()


def sources(request):
    try:
        locations = storage_service.get_location(purpose="TS")
    except:
        messages.warning(request, _('Error retrieving locations: is the storage server running? Please contact an administrator.'))

    system_directory_description = 'Available transfer source'
    return render(request, 'administration/locations.html', locals())


def processing(request):
    return processing_views.index(request)


def premis_agent(request):
    agent = models.Agent.objects.get(pk=2)
    if request.POST:
        form = AgentForm(request.POST, instance=agent)
        if form.is_valid():
            messages.info(request, _('Saved.'))
            form.save()
    else:
        form = AgentForm(instance=agent)

    return render(request, 'administration/premis_agent.html', locals())


def api(request):
    if request.method == 'POST':
        whitelist = request.POST.get('whitelist', '')
        helpers.set_setting('api_whitelist', whitelist)
        messages.info(request, _('Saved.'))
    else:
        whitelist = helpers.get_setting('api_whitelist', '')

    return render(request, 'administration/api.html', locals())


def taxonomy(request):
    taxonomies = models.Taxonomy.objects.all().order_by('name')
    page = helpers.pager(taxonomies, 20, request.GET.get('page', 1))
    return render(request, 'administration/taxonomy.html', locals())


def terms(request, taxonomy_uuid):
    taxonomy = models.Taxonomy.objects.get(pk=taxonomy_uuid)
    terms = taxonomy.taxonomyterm_set.order_by('term')
    page = helpers.pager(terms, 20, request.GET.get('page', 1))
    return render(request, 'administration/terms.html', locals())


def term_detail(request, term_uuid):
    term = models.TaxonomyTerm.objects.get(pk=term_uuid)
    taxonomy = term.taxonomy
    if request.POST:
        form = TaxonomyTermForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            messages.info(request, _('Saved.'))
    else:
        form = TaxonomyTermForm(instance=term)

    return render(request, 'administration/term_detail.html', locals())


def term_delete_context(request, term_uuid):
    term = models.TaxonomyTerm.objects.get(pk=term_uuid)
    prompt = 'Delete term ' + term.term + '?'
    cancel_url = reverse("components.administration.views.term_detail", args=[term_uuid])
    return RequestContext(request, {'action': 'Delete', 'prompt': prompt, 'cancel_url': cancel_url})


@decorators.confirm_required('simple_confirm.html', term_delete_context)
def term_delete(request, term_uuid):
    if request.method == 'POST':
        term = models.TaxonomyTerm.objects.get(pk=term_uuid)
        term.delete()
        return HttpResponseRedirect(reverse('components.administration.views.terms', args=[term.taxonomy_id]))


def _intial_settings_data():
    return dict(models.DashboardSetting.objects.all().values_list(
        'name', 'value'))


def general(request):
    initial_data = _intial_settings_data()
    storage_form = StorageSettingsForm(request.POST or None, prefix='storage', initial=initial_data)
    checksum_form = ChecksumSettingsForm(request.POST or None, prefix='checksum algorithm', initial=initial_data)

    if storage_form.is_valid() and checksum_form.is_valid():
        storage_form.save()
        checksum_form.save()
        messages.info(request, _('Saved.'))

    dashboard_uuid = helpers.get_setting('dashboard_uuid')
    try:
        pipeline = storage_service.get_pipeline(dashboard_uuid)
    except Exception:
        messages.warning(request, _("Storage server inaccessible. Please contact an administrator or update storage service URL below."))
    else:
        if not pipeline:
            messages.warning(request, _("This pipeline is not registered with the storage service or has been disabled in the storage service. Please contact an administrator."))
    return render(request, 'administration/general.html', locals())


def version(request):
    version = get_version()
    agent_code = models.Agent.objects.get(identifiertype="preservation system").identifiervalue
    return render(request, 'administration/version.html', locals())

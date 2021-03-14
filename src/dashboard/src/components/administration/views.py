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

import collections
import logging
import os
import shutil
import subprocess

from django.conf import settings as django_settings
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Max, Min
from django.http import Http404, HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext as _

from main import models
from components.administration.forms import (
    AgentForm,
    HandleForm,
    GeneralSettingsForm,
    StorageSettingsForm,
    ChecksumSettingsForm,
    TaxonomyTermForm,
)
import components.administration.views_processing as processing_views
import components.decorators as decorators
import components.helpers as helpers
from installer.steps import setup_pipeline_in_ss
import storageService as storage_service

from version import get_full_version, get_preservation_system_identifier


logger = logging.getLogger("archivematica.dashboard")


""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Administration
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def administration(request):
    return redirect("administration:processing")


def failure_report(request, report_id=None):
    if report_id is not None:
        report = models.Report.objects.get(pk=report_id)
        return render(request, "administration/reports/failure_detail.html", locals())
    else:
        current_page_number = request.GET.get("page", "1")
        items_per_page = 10

        reports = models.Report.objects.all().order_by("-created")
        page = helpers.pager(reports, items_per_page, current_page_number)
        return render(request, "administration/reports/failures.html", locals())


def delete_context(request, report_id):
    report = models.Report.objects.get(pk=report_id)
    prompt = "Delete failure report for " + report.unitname + "?"
    cancel_url = reverse("administration:reports_failures_index")
    return {"action": "Delete", "prompt": prompt, "cancel_url": cancel_url}


@decorators.confirm_required("simple_confirm.html", delete_context)
def failure_report_delete(request, report_id):
    models.Report.objects.get(pk=report_id).delete()
    messages.info(request, _("Deleted."))
    return redirect("administration:failure_report_index")


def failure_report_detail(request):
    return render(
        request, "administration/reports/failure_report_detail.html", locals()
    )


def atom_levels_of_description(request):
    if request.method == "POST":
        level_operation = request.POST.get("operation")
        level_id = request.POST.get("id")

        if level_operation == "promote":
            if _atom_levels_of_description_sort_adjust(level_id, "promote"):
                messages.info(request, _("Promoted."))
            else:
                messages.error(
                    request, _("Error attempting to promote level of description.")
                )
        elif level_operation == "demote":
            if _atom_levels_of_description_sort_adjust(level_id, "demote"):
                messages.info(request, _("Demoted."))
            else:
                messages.error(
                    request, _("Error attempting to demote level of description.")
                )
        elif level_operation == "delete":
            try:
                level = models.LevelOfDescription.objects.get(id=level_id)
                level.delete()
                messages.info(request, _("Deleted."))
            except models.LevelOfDescription.DoesNotExist:
                messages.error(request, _("Level of description not found."))

    levels = models.LevelOfDescription.objects.order_by("sortorder")
    sortorder_min = models.LevelOfDescription.objects.aggregate(min=Min("sortorder"))[
        "min"
    ]
    sortorder_max = models.LevelOfDescription.objects.aggregate(max=Max("sortorder"))[
        "max"
    ]

    return render(
        request,
        "administration/atom_levels_of_description.html",
        {
            "levels": levels,
            "sortorder_min": sortorder_min,
            "sortorder_max": sortorder_max,
        },
    )


def _atom_levels_of_description_sort_adjust(level_id, sortorder="promote"):
    """
    Move LevelOfDescription with level_id up or down one.

    :param int level_id: ID of LevelOfDescription to adjust
    :param string sortorder: 'promote' to demote level_id, 'demote' to promote level_id
    :returns: True if success, False otherwise.
    """
    try:
        level = models.LevelOfDescription.objects.get(id=level_id)
        # Get object with next highest/lowest sortorder
        if sortorder == "demote":
            previous_level = models.LevelOfDescription.objects.order_by(
                "sortorder"
            ).filter(sortorder__gt=level.sortorder)[:1][0]
        elif sortorder == "promote":
            previous_level = models.LevelOfDescription.objects.order_by(
                "-sortorder"
            ).filter(sortorder__lt=level.sortorder)[:1][0]
    except (models.LevelOfDescription.DoesNotExist, IndexError):
        return False

    # Swap
    level.sortorder, previous_level.sortorder = (
        previous_level.sortorder,
        level.sortorder,
    )
    level.save()
    previous_level.save()
    return True


def storage(request):
    """Return storage service locations related with this pipeline.

    Exclude locations for currently processing, AIP recovery and SS internal
    purposes and disabled locations. Format used, quota and purpose values to
    human readable form.
    """
    try:
        response_locations = storage_service.get_location()
    except:
        messages.warning(
            request,
            _(
                "Error retrieving locations: is the storage server running? "
                "Please contact an administrator."
            ),
        )
        return render(request, "administration/locations.html")

    # Currently processing, AIP recovery and SS internal locations
    # are intentionally not included to not display them in the table.
    purposes = {
        "AS": _("AIP Storage"),
        "DS": _("DIP Storage"),
        "SD": _("FEDORA Deposits"),
        "BL": _("Transfer Backlog"),
        "TS": _("Transfer Source"),
        "RP": _("Replicator"),
    }

    # Filter and format locations
    locations = []
    for loc in response_locations:
        # Skip disabled locations
        if not loc["enabled"]:
            continue
        # Skip unwanted purposes
        if not loc["purpose"] or loc["purpose"] not in list(purposes.keys()):
            continue
        # Only show usage of AS and DS locations
        loc["show_usage"] = loc["purpose"] in ["AS", "DS"]
        if loc["show_usage"]:
            # Show unlimited for unset quotas
            if not loc["quota"]:
                loc["quota"] = _("unlimited")
            # Format bytes to human readable filesize
            else:
                loc["quota"] = filesizeformat(loc["quota"])
            if loc["used"]:
                loc["used"] = filesizeformat(loc["used"])
        # Format purpose
        loc["purpose"] = purposes[loc["purpose"]]
        locations.append(loc)

    # Sort by purpose
    locations.sort(key=lambda loc: loc["purpose"])

    return render(request, "administration/locations.html", {"locations": locations})


def usage(request):
    """Return page summarizing storage usage.

    To avoid timeouts on the first load of this page, the usage data is only
    calculated when the `calculate` get parameter is evaluated as `True` (true
    values are "true", "yes", "on" and "1", case insensitive). When the usage data
    is not calculated, the page shows a description and a button to reload the page
    calculating the usage. When the usage is calculated, the page will display a
    general information section and a table of clearable directories from within
    the shared path.
    """
    calculate = request.GET.get("calculate", "")
    calculate_usage = calculate.lower() in ["true", "yes", "on", "1"]
    if calculate_usage:
        root_path = _get_mount_point_path(django_settings.SHARED_DIRECTORY)
        root = {
            "path": root_path,
            "size": _usage_check_directory_volume_size(root_path),
            "used": _usage_get_directory_used_bytes(root_path),
        }
        shared = {
            "path": django_settings.SHARED_DIRECTORY,
            "used": _usage_get_directory_used_bytes(django_settings.SHARED_DIRECTORY),
        }
        usage_dirs = _get_shared_dirs(calculate_usage=True)

    return render(request, "administration/usage.html", locals())


def _get_shared_dirs(calculate_usage=False):
    """Get shared directories information.

    Get information about directories that can be cleared manually whitin the
    SHARED_DIRECTORY setting path.

    :param bool calculate_usage: True if usage should be calculated.
    :returns OrderedDict: Dict where key is a descriptive handle and value is a
                          dict with the path, description and optionally usage.
    """
    shared_path = django_settings.SHARED_DIRECTORY
    dirs = collections.OrderedDict(
        (
            (
                "transfers",
                {
                    "description": "Transfers",
                    "path": os.path.join(shared_path, "completed", "transfers"),
                },
            ),
            (
                "dip_backups",
                {
                    "description": "DIP backups",
                    "path": os.path.join(shared_path, "DIPbackups"),
                },
            ),
            (
                "failed",
                {"description": "Failed", "path": os.path.join(shared_path, "failed")},
            ),
            (
                "rejected",
                {
                    "description": "Rejected",
                    "path": os.path.join(shared_path, "rejected"),
                },
            ),
            (
                "sip_backups",
                {
                    "description": "SIP backups",
                    "path": os.path.join(shared_path, "SIPbackups"),
                },
            ),
            (
                "tmp",
                {
                    "description": "Temporary file storage",
                    "path": os.path.join(shared_path, "tmp"),
                },
            ),
            (
                "uploaded_dips",
                {
                    "description": "Uploaded DIPs",
                    "path": os.path.join(
                        shared_path, "watchedDirectories", "uploadedDIPs"
                    ),
                },
            ),
        )
    )

    if calculate_usage:
        for id, dir_spec in dirs.items():
            dir_spec["used"] = _usage_get_directory_used_bytes(dir_spec["path"])

    return dirs


def _get_mount_point_path(path):
    """Get the mount point path from a directory.

    :param str path: path to check.
    :returns: mount point path.
    """
    path = os.path.realpath(os.path.abspath(path))
    while path != os.path.sep:
        if os.path.ismount(path):
            return path
        path = os.path.abspath(os.path.join(path, os.pardir))
    return path


def _usage_check_directory_volume_size(path):
    """Check the size of the volume containing a given path.

    :param str path: path to check.
    :returns: size in bytes, or 0 on error.
    """
    try:
        # Get volume size (in 1K blocks)
        output = subprocess.check_output(["df", "--block-size", "1024", path]).decode(
            "utf8"
        )
        # Second line returns disk usage-related values
        usage_summary = output.split("\n")[1]
        # Split value by whitespace and size (in blocks)
        size = usage_summary.split()[1]
        return int(size) * 1024
    except OSError:
        logger.exception("No such directory: %s", path)
        return 0
    except subprocess.CalledProcessError:
        logger.exception("Unable to determine size of %s", path)
        return 0


def _usage_get_directory_used_bytes(path):
    """Check the space used at a given path.

    :param string path: path to check.
    :returns: usage in bytes.
    """
    try:
        output = subprocess.check_output(
            ["du", "--one-file-system", "--bytes", "--summarize", path]
        ).decode("utf8")
        return output.split("\t")[0]
    except OSError:
        logger.exception("No such directory: %s", path)
        return 0
    except subprocess.CalledProcessError as err:
        # CalledProcessErrors are typically the result of du returning
        # 1 because there were some directories in the path for which
        # the archivematica user doesn't have permissions. In this case
        # du still prints an output to stdout so we try to catch it
        # from CalledProcessError.output.
        byte_count = 0
        try:
            byte_count = int(err.output.split("\t")[0])
            logger.warning(
                "Non-zero exit code while determining usage of %s. "
                "Some directories may be missing from total.",
                path,
            )
        except (AttributeError, ValueError):
            logger.exception("Unable to determine usage of %s.", path)
        return byte_count


def _usage_clear_context(request, dir_id):
    """Confirmation context for emptying a directory from _get_shared_dirs.

    :param dir_id: Key for the directory in _get_shared_dirs.
    """
    usage_dirs = _get_shared_dirs()
    dir_info = usage_dirs.get(dir_id, None)
    if not dir_info:
        raise Http404

    prompt = _("Clear %(dir)s?") % {"dir": dir_info["description"]}
    cancel_url = reverse("administration:usage")
    return {"action": _("Clear"), "prompt": prompt, "cancel_url": cancel_url}


@user_passes_test(lambda u: u.is_superuser, login_url="/forbidden/")
@decorators.confirm_required("simple_confirm.html", _usage_clear_context)
def usage_clear(request, dir_id):
    """Clears a directory from _get_shared_dirs.

    :param dir_id: Descriptive shorthand for the dir, key for _get_shared_dirs.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed()

    usage_dirs = _get_shared_dirs()
    dir_info = usage_dirs.get(dir_id, None)
    if not dir_info:
        raise Http404

    try:
        for entry in os.listdir(dir_info["path"]):
            entry_path = os.path.join(dir_info["path"], entry)
            if os.path.isfile(entry_path):
                os.unlink(entry_path)
            else:
                shutil.rmtree(entry_path)
        message = _("Cleared: %(path)s") % {"path": dir_info["path"]}
        messages.info(request, message)
    except OSError:
        message = _("No such file or directory: %(path)s") % {"path": dir_info["path"]}
        messages.error(request, message)
        logger.exception(message)

    return redirect("administration:usage")


def processing(request):
    return processing_views.index(request)


def handle_config(request):
    """Display or save the Handle configuration form, which allows for the
    specification of configuration values for Handle PID creation and binding
    using the ``bindpid`` module. State is stored in DashboardSettings table.
    """
    if request.method == "POST":
        form = HandleForm(request.POST)
        if form.is_valid():
            models.DashboardSetting.objects.set_dict("handle", form.cleaned_data)
            messages.info(request, _("Saved."))
    else:
        settings_dict = models.DashboardSetting.objects.get_dict("handle")
        settings_dict["pid_request_verify_certs"] = {"False": False}.get(
            settings_dict.get("pid_request_verify_certs", True), True
        )
        form = HandleForm(initial=settings_dict)
    return render(request, "administration/handle_config.html", {"form": form})


def premis_agent(request):
    agent = models.Agent.objects.default_organization_agent()
    if request.POST:
        form = AgentForm(request.POST, instance=agent)
        if form.is_valid():
            messages.info(request, _("Saved."))
            form.save()
    else:
        form = AgentForm(instance=agent)

    return render(request, "administration/premis_agent.html", locals())


def api(request):
    if request.method == "POST":
        allowlist = request.POST.get("allowlist", "")
        helpers.set_api_allowlist(allowlist)
        messages.info(request, _("Saved."))
    else:
        allowlist = helpers.get_api_allowlist()

    return render(request, "administration/api.html", locals())


def taxonomy(request):
    taxonomies = models.Taxonomy.objects.all().order_by("name")
    page = helpers.pager(taxonomies, 20, request.GET.get("page", 1))
    return render(request, "administration/taxonomy.html", locals())


def terms(request, taxonomy_uuid):
    taxonomy = models.Taxonomy.objects.get(pk=taxonomy_uuid)
    terms = taxonomy.taxonomyterm_set.order_by("term")
    page = helpers.pager(terms, 20, request.GET.get("page", 1))
    return render(request, "administration/terms.html", locals())


def term_detail(request, term_uuid):
    term = models.TaxonomyTerm.objects.get(pk=term_uuid)
    taxonomy = term.taxonomy
    if request.POST:
        form = TaxonomyTermForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            messages.info(request, _("Saved."))
    else:
        form = TaxonomyTermForm(instance=term)

    return render(request, "administration/term_detail.html", locals())


def term_delete_context(request, term_uuid):
    term = models.TaxonomyTerm.objects.get(pk=term_uuid)
    prompt = "Delete term " + term.term + "?"
    cancel_url = reverse("administration:term", args=[term_uuid])
    return {"action": "Delete", "prompt": prompt, "cancel_url": cancel_url}


@decorators.confirm_required("simple_confirm.html", term_delete_context)
def term_delete(request, term_uuid):
    if request.method == "POST":
        term = models.TaxonomyTerm.objects.get(pk=term_uuid)
        term.delete()
        return HttpResponseRedirect(
            reverse("administration:terms", args=[term.taxonomy_id])
        )


def _intial_settings_data():
    return dict(models.DashboardSetting.objects.all().values_list("name", "value"))


def general(request):
    initial_data = _intial_settings_data()
    initial_data["storage_service_use_default_config"] = {"False": False}.get(
        initial_data.get("storage_service_use_default_config", True), True
    )
    general_form = GeneralSettingsForm(
        request.POST or None, prefix="general", initial=initial_data
    )
    storage_form = StorageSettingsForm(
        request.POST or None, prefix="storage", initial=initial_data
    )
    checksum_form = ChecksumSettingsForm(
        request.POST or None, prefix="checksum algorithm", initial=initial_data
    )

    forms = (general_form, storage_form, checksum_form)
    if all([form.is_valid() for form in forms]):
        for item in forms:
            item.save()
        messages.info(request, _("Saved."))

    dashboard_uuid = helpers.get_setting("dashboard_uuid")

    not_created_yet = False
    try:
        pipeline = storage_service.get_pipeline(dashboard_uuid)
    except Exception as err:
        if err.response is not None and err.response.status_code == 404:
            # The server has returned a 404, we're going to assume that this is
            # the Storage Service telling us that the pipeline is unknown.
            not_created_yet = True
        else:
            messages.warning(
                request,
                _(
                    "Storage Service inaccessible. Please"
                    " contact an administrator or update"
                    " the Storage Sevice URL below."
                    "<hr />%(error)s" % {"error": err}
                ),
            )

    if not_created_yet:
        if storage_form.is_valid():
            try:
                setup_pipeline_in_ss(
                    storage_form.cleaned_data["storage_service_use_default_config"]
                )
            except Exception as err:
                messages.warning(
                    request,
                    _(
                        "Storage Service failed to create the"
                        " pipeline. This can happen if"
                        " the pipeline exists but it is"
                        " disabled. Please contact an"
                        " administrator."
                        "<hr />%(error)s" % {"error": err}
                    ),
                )
        else:
            messages.warning(
                request,
                _(
                    "Storage Service returned a 404 error."
                    " Has the pipeline been disabled or is"
                    " it not registered yet? Submitting"
                    " form will attempt to register the"
                    " pipeline."
                ),
            )

    return render(request, "administration/general.html", locals())


def version(request):
    return render(
        request,
        "administration/version.html",
        {
            "version": get_full_version(),
            "agent_code": get_preservation_system_identifier(),
        },
    )

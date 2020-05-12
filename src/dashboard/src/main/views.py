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

from django.conf import settings as django_settings
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import get_language, ugettext as _
from django.views.decorators.cache import cache_page
from django.views.decorators.http import last_modified
from django.views.i18n import JavaScriptCatalog
from shibboleth.views import ShibbolethLogoutView, LOGOUT_SESSION_KEY

from contrib.mcp.client import MCPClient
from main import models
from lxml import etree
from components import helpers
from archivematicaFunctions import escape


@cache_page(86400, key_prefix="js18n-%s" % get_language())
@last_modified(lambda req, **kw: timezone.now())
def cached_javascript_catalog(request, domain="djangojs", packages=None):
    return JavaScriptCatalog.as_view(domain=domain, packages=packages)(request)


""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Home
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def home(request):
    # clean up user's session-specific data
    if "user_temp_data_cleanup_ran" not in request.session:
        # create all transfer metadata sets created by user
        transfer_metadata_sets = models.TransferMetadataSet.objects.filter(
            createdbyuserid=1
        )

        # check each set to see if, and related data, should be deleted
        for set in transfer_metadata_sets:
            # delete transfer metadata set and field values if no corresponding transfer exists
            try:
                models.Transfer.objects.get(transfermetadatasetrow=set)
            except models.Transfer.DoesNotExist:
                for field_value in set.transfermetadatafieldvalue_set.iterator():
                    field_value.delete()
                set.delete()
        request.session["user_temp_data_cleanup_ran"] = True

    if "first_login" in request.session and request.session["first_login"]:
        request.session.first_login = False
    return redirect(reverse("transfer:transfer_index"))


""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Status
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


# TODO: hide removed elements
def status(request):
    client = MCPClient(request.user)
    xml = etree.XML(client.list())

    sip_count = len(
        xml.xpath(
            '//choicesAvailableForUnits/choicesAvailableForUnit/unit/type[text()="SIP"]'
        )
    )
    transfer_count = len(
        xml.xpath(
            '//choicesAvailableForUnits/choicesAvailableForUnit/unit/type[text()="Transfer"]'
        )
    )
    dip_count = len(
        xml.xpath(
            '//choicesAvailableForUnits/choicesAvailableForUnit/unit/type[text()="DIP"]'
        )
    )

    response = {"sip": sip_count, "transfer": transfer_count, "dip": dip_count}

    return helpers.json_response(response)


""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Access
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def access_list(request):
    access = models.Access.objects.all()
    for item in access:
        semicolon_position = item.resource.find(";")
        if semicolon_position != -1:
            target = item.resource.split("/").pop()
            remove_length = len(item.resource) - semicolon_position
            chunk = item.resource[:-remove_length] + target
            item.destination = chunk
        else:
            item.destination = item.resource
    return render(request, "main/access.html", locals())


def access_delete(request, id):
    access = get_object_or_404(models.Access, pk=id)
    access.delete()
    return redirect("main:access_index")


""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Misc
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def forbidden(request):
    return render(request, "forbidden.html")


def task(request, uuid):
    task = models.Task.objects.get(taskuuid=uuid)
    task.duration = helpers.task_duration_in_seconds(task)
    objects = [task]
    return render(request, "main/tasks.html", locals())


def tasks(request, uuid):
    job = models.Job.objects.get(jobuuid=uuid)
    objects = job.task_set.all().order_by(
        "-exitcode", "-endtime", "-starttime", "-createdtime"
    )

    # Filenames can be any encoding - we want to be able to display
    # unicode, while just displaying unicode replacement characters
    # for any other encoding present.
    for item in objects:
        item.filename = escape(item.filename)
        item.arguments = escape(item.arguments)
        item.stdout = escape(item.stdout)
        item.stderror = escape(item.stderror)

    page = helpers.pager(
        objects, django_settings.TASKS_PER_PAGE, request.GET.get("page", None)
    )
    objects = page.object_list

    # figure out duration in seconds
    for object in objects:
        object.duration = helpers.task_duration_in_seconds(object)

    return render(request, "main/tasks.html", locals())


def formdata_delete(request, type, parent_id, delete_id):
    return formdata(request, type, parent_id, delete_id)


def formdata(request, type, parent_id, delete_id=None):
    model = None
    results = None
    response = {}

    # define types handled
    if type == "rightsnote":
        model = models.RightsStatementRightsGrantedNote
        parent_model = models.RightsStatementRightsGranted
        model_parent_field = "rightsgranted"
        model_value_fields = ["rightsgrantednote"]

        results = model.objects.filter(rightsgranted=parent_id)

    if type == "rightsrestriction":
        model = models.RightsStatementRightsGrantedRestriction
        parent_model = models.RightsStatementRightsGranted
        model_parent_field = "rightsgranted"
        model_value_fields = ["restriction"]

        results = model.objects.filter(rightsgranted=parent_id)

    if type == "licensenote":
        model = models.RightsStatementLicenseNote
        parent_model = models.RightsStatementLicense
        model_parent_field = "rightsstatementlicense"
        model_value_fields = ["licensenote"]

        results = model.objects.filter(rightsstatementlicense=parent_id)

    if type == "statutenote":
        model = models.RightsStatementStatuteInformationNote
        parent_model = models.RightsStatementStatuteInformation
        model_parent_field = "rightsstatementstatute"
        model_value_fields = ["statutenote"]

        results = model.objects.filter(rightsstatementstatute=parent_id)

    if type == "copyrightnote":
        model = models.RightsStatementCopyrightNote
        parent_model = models.RightsStatementCopyright
        model_parent_field = "rightscopyright"
        model_value_fields = ["copyrightnote"]

        results = model.objects.filter(rightscopyright=parent_id)

    if type == "copyrightdocumentationidentifier":
        model = models.RightsStatementCopyrightDocumentationIdentifier
        parent_model = models.RightsStatementCopyright
        model_parent_field = "rightscopyright"
        model_value_fields = [
            "copyrightdocumentationidentifiertype",
            "copyrightdocumentationidentifiervalue",
            "copyrightdocumentationidentifierrole",
        ]

        results = model.objects.filter(rightscopyright=parent_id)

    if type == "statutedocumentationidentifier":
        model = models.RightsStatementStatuteDocumentationIdentifier
        parent_model = models.RightsStatementStatuteInformation
        model_parent_field = "rightsstatementstatute"
        model_value_fields = [
            "statutedocumentationidentifiertype",
            "statutedocumentationidentifiervalue",
            "statutedocumentationidentifierrole",
        ]

        results = model.objects.filter(rightsstatementstatute=parent_id)

    if type == "licensedocumentationidentifier":
        model = models.RightsStatementLicenseDocumentationIdentifier
        parent_model = models.RightsStatementLicense
        model_parent_field = "rightsstatementlicense"
        model_value_fields = [
            "licensedocumentationidentifiertype",
            "licensedocumentationidentifiervalue",
            "licensedocumentationidentifierrole",
        ]

        results = model.objects.filter(rightsstatementlicense=parent_id)

    if type == "otherrightsdocumentationidentifier":
        model = models.RightsStatementOtherRightsDocumentationIdentifier
        parent_model = models.RightsStatementOtherRightsInformation
        model_parent_field = "rightsstatementotherrights"
        model_value_fields = [
            "otherrightsdocumentationidentifiertype",
            "otherrightsdocumentationidentifiervalue",
            "otherrightsdocumentationidentifierrole",
        ]

        results = model.objects.filter(rightsstatementotherrights=parent_id)

    if type == "otherrightsnote":
        model = models.RightsStatementOtherRightsInformationNote
        parent_model = models.RightsStatementOtherRightsInformation
        model_parent_field = "rightsstatementotherrights"
        model_value_fields = ["otherrightsnote"]

        results = model.objects.filter(rightsstatementotherrights=parent_id)

    # handle creation
    if request.method == "POST":
        # load or initiate model instance
        id = request.POST.get("id", 0)
        if id > 0:
            instance = model.objects.get(pk=id)
        else:
            instance = model()

        # set instance parent
        parent = parent_model.objects.filter(pk=parent_id)
        setattr(instance, model_parent_field, parent[0])

        # set instance field values using request data
        for field in model_value_fields:
            value = request.POST.get(field, "")
            setattr(instance, field, value)
        instance.save()

        if id == 0:
            response["new_id"] = instance.pk

        response["message"] = _("Added.")

    # handle deletion
    if request.method == "DELETE":
        if delete_id is None:
            response["message"] = _("Error: no delete ID supplied.")
        else:
            model.objects.filter(pk=delete_id).delete()
            response["message"] = _("Deleted.")

    # send back revised data
    if results is not None:
        response["results"] = []
        for result in results:
            values = {}
            for field in model_value_fields:
                values[field] = result.__dict__[field]
            response["results"].append({"id": result.pk, "values": values})

    if model is None:
        response["message"] = _("Incorrect type.")

    return helpers.json_response(response)


class CustomShibbolethLogoutView(ShibbolethLogoutView):
    def get(self, request, *args, **kwargs):
        response = super(CustomShibbolethLogoutView, self).get(request, *args, **kwargs)
        # LOGOUT_SESSION_KEY is set by the standard logout to prevent re-login
        # which is useful to prevent bouncing straight back to login under
        # certain setups, but not here where we want the Django session state
        # to reflect the SP session state
        if LOGOUT_SESSION_KEY in request.session:
            del request.session[LOGOUT_SESSION_KEY]
        return response

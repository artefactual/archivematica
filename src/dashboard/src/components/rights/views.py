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

from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.shortcuts import redirect, render
from django.http import HttpResponse
from contrib import utils
from components.rights import forms
from main import models
from components import helpers
import re
from components import decorators
from django.template import RequestContext

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Rights-related
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def transfer_rights_list(request, uuid):
    return rights_list(request, uuid, 'transfer')

def transfer_rights_edit(request, uuid, id=None):
    return rights_edit(request, uuid, id, 'transfer')

def transfer_rights_delete(request, uuid, id):
    return rights_delete(request, uuid, id, 'transfer')

def transfer_grant_delete_context(request, uuid, id):
    prompt = 'Delete rights grant?'
    cancel_url = reverse("components.rights.views.transfer_rights_list", args=[uuid])
    return RequestContext(request, {'action': 'Delete', 'prompt': prompt, 'cancel_url': cancel_url})

@decorators.confirm_required('simple_confirm.html', transfer_grant_delete_context)
def transfer_rights_grant_delete(request, uuid, id):
    return rights_grant_delete(request, uuid, id, 'transfer')

def transfer_rights_grants_edit(request, uuid, id):
    return rights_grants_edit(request, uuid, id, 'transfer')

def ingest_rights_list(request, uuid):
    return rights_list(request, uuid, 'ingest')

def ingest_rights_edit(request, uuid, id=None):
    return rights_edit(request, uuid, id, 'ingest')

def ingest_rights_delete(request, uuid, id):
    return rights_delete(request, uuid, id, 'ingest')

def ingest_grant_delete_context(request, uuid, id):
    prompt = 'Delete rights grant?'
    cancel_url = reverse("components.rights.views.ingest_rights_list", args=[uuid])
    return RequestContext(request, {'action': 'Delete', 'prompt': prompt, 'cancel_url': cancel_url})

@decorators.confirm_required('simple_confirm.html', ingest_grant_delete_context)
def ingest_rights_grant_delete(request, uuid, id):
    return rights_grant_delete(request, uuid, id, 'ingest')

def ingest_rights_grants_edit(request, uuid, id):
    return rights_grants_edit(request, uuid, id, 'ingest')

def rights_parse_agent_id(input):
    return 0
    if input == '':
        agentId = 0
    else:
        agentRaw = input
        try:
            int(agentRaw)
            agentId = int(agentRaw)
        except ValueError:
            agentRe = re.compile('(.*)\[(\d*)\]')
            match = agentRe.match(agentRaw)
            if match:
                agentId = match.group(2)
            else:
                agentId = 0
    return agentId

def rights_edit(request, uuid, id=None, section='ingest'):
    jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
    name = utils.get_directory_name_from_job(jobs[0])

    # flag indicating what kind of new content, if any, has been created
    new_content_type_created = None

    max_notes = 1

    if id:
        viewRights = models.RightsStatement.objects.get(pk=id)
        agentId = None
        if request.method == 'POST':
            postData = request.POST.copy()
            """
            agentId = rights_parse_agent_id(postData.get('rightsholder'))
            if agentId == 0 and postData.get('rightsholder') != '0' and postData.get('rightsholder') != '':
                agent = models.RightsStatementLinkingAgentIdentifier()
                agent.rightsstatement = viewRights
                agent.linkingagentidentifiervalue = postData.get('rightsholder')
                agent.save()
                agentId = agent.id
            postData.__setitem__('rightsholder', agentId)
            """
            form = forms.RightsForm(postData, instance=viewRights)
            form.cleaned_data = postData
            viewRights = form.save()
        else:
            form = forms.RightsForm(instance=viewRights)
            form.cleaned_data = viewRights
            form.save()

        # determine how many empty forms should be shown for children
        extra_copyright_forms = max_notes - models.RightsStatementCopyright.objects.filter(rightsstatement=viewRights).count()
        extra_statute_forms = max_notes - models.RightsStatementStatuteInformation.objects.filter(rightsstatement=viewRights).count()
        extra_license_forms = max_notes - models.RightsStatementLicense.objects.filter(rightsstatement=viewRights).count()
        extra_other_forms = max_notes - models.RightsStatementOtherRightsInformation.objects.filter(rightsstatement=viewRights).count()
    else:
        if request.method == 'POST':
            postData = request.POST.copy()
            agentId = rights_parse_agent_id(postData.get('rightsholder'))
            postData.__setitem__('rightsholder', agentId)
            form = forms.RightsForm(postData)
        else:
            form = forms.RightsForm()
            viewRights = models.RightsStatement()

        extra_copyright_forms = max_notes
        extra_statute_forms   = max_notes
        extra_license_forms   = max_notes
        extra_license_notes   = max_notes
        extra_other_forms     = max_notes

    # create inline formsets for child elements
    CopyrightFormSet = inlineformset_factory(
        models.RightsStatement,
        models.RightsStatementCopyright,
        extra=extra_copyright_forms,
        can_delete=False,
        form=forms.RightsCopyrightForm
    )

    StatuteFormSet = inlineformset_factory(
        models.RightsStatement,
        models.RightsStatementStatuteInformation,
        extra=extra_statute_forms,
        can_delete=False,
        form=forms.RightsStatuteForm
    )

    LicenseFormSet = inlineformset_factory(
        models.RightsStatement,
        models.RightsStatementLicense,
        extra=extra_license_forms,
        can_delete=False,
        form=forms.RightsLicenseForm
    )

    OtherFormSet = inlineformset_factory(
        models.RightsStatement,
        models.RightsStatementOtherRightsInformation,
        extra=extra_other_forms,
        can_delete=False,
        form=forms.RightsOtherRightsForm
    )

    # handle form creation/saving
    if request.method == 'POST':
        if id:
            createdRights = viewRights
        else:
            sectionTypeID = {'transfer': 'Transfer', 'ingest': 'SIP'}
            type_id = helpers.get_metadata_type_id_by_description(sectionTypeID[section])
            newRights = models.RightsStatement(metadataappliestotype=type_id, metadataappliestoidentifier=uuid)
            form = forms.RightsForm(request.POST, instance=newRights)
            createdRights = form.save()

        copyrightFormset = CopyrightFormSet(request.POST, instance=createdRights)
        createdCopyrightSet = copyrightFormset.save()

        # establish whether or not there is a copyright information instance to use as a parent
        if len(createdCopyrightSet) == 1:
            createdCopyright = createdCopyrightSet[0]
        else:
            createdCopyright = False

        # handle creation of new copyright notes, creating parent if necessary
        if request.POST.get('copyright_note', '') != '':
            # make new copyright record if it doesn't exist
            if not createdCopyright:
                try:
                    createdCopyright = models.RightsStatementCopyright.objects.get(rightsstatement=createdRights)
                except:
                    createdCopyright = models.RightsStatementCopyright(rightsstatement=createdRights)
                    createdCopyright.save()

            copyrightNote = models.RightsStatementCopyrightNote(rightscopyright=createdCopyright)
            copyrightNote.copyrightnote = request.POST.get('copyright_note', '')
            copyrightNote.save()

            new_content_type_created = 'copyright'

        # handle creation of new documentation identifiers
        if request.POST.get('copyright_documentation_identifier_type', '') != '' or request.POST.get('copyright_documentation_identifier_value', '') != '' or request.POST.get('copyright_documentation_identifier_role', ''):
            # make new copyright record if it doesn't exist
            if not createdCopyright:
                try:
                    createdCopyright = models.RightsStatementCopyright.objects.get(rightsstatement=createdRights)
                except:
                    createdCopyright = models.RightsStatementCopyright(rightsstatement=createdRights)
                    createdCopyright.save()

            copyrightDocIdentifier = models.RightsStatementCopyrightDocumentationIdentifier(rightscopyright=createdCopyright)
            copyrightDocIdentifier.copyrightdocumentationidentifiertype  = request.POST.get('copyright_documentation_identifier_type', '')
            copyrightDocIdentifier.copyrightdocumentationidentifiervalue = request.POST.get('copyright_documentation_identifier_value', '')
            copyrightDocIdentifier.copyrightdocumentationidentifierrole  = request.POST.get('copyright_documentation_identifier_role', '')
            copyrightDocIdentifier.save()

            new_content_type_created = 'copyright'

        licenseFormset = LicenseFormSet(request.POST, instance=createdRights)
        createdLicenseSet = licenseFormset.save()

        # establish whether or not there is a license instance to use as a parent
        if len(createdLicenseSet) == 1:
            createdLicense = createdLicenseSet[0]
        else:
            createdLicense = False

        # handle creation of new copyright notes, creating parent if necessary
        if request.POST.get('license_note', '') != '':
            # make new copyright record if it doesn't exist
            if not createdLicense:
                try:
                    createdLicense = models.RightsStatementLicense.objects.get(rightsstatement=createdRights)
                except:
                    createdLicense = models.RightsStatementLicense(rightsstatement=createdRights)
                    createdLicense.save()

            licenseNote = models.RightsStatementLicenseNote(rightsstatementlicense=createdLicense)
            licenseNote.licensenote = request.POST.get('license_note', '')
            licenseNote.save()

            new_content_type_created = 'license'

        # handle creation of new documentation identifiers
        if request.POST.get('license_documentation_identifier_type', '') != '' or request.POST.get('license_documentation_identifier_value', '') != '' or request.POST.get('license_documentation_identifier_role', ''):
            # make new license record if it doesn't exist
            if not createdLicense:
                try:
                    createdLicense = models.RightsStatementLicense.objects.get(rightsstatement=createdRights)
                except:
                    createdLicense = models.RightsStatementLicense(rightsstatement=createdRights)
                    createdLicense.save()

            licenseDocIdentifier = models.RightsStatementLicenseDocumentationIdentifier(rightsstatementlicense=createdLicense)
            licenseDocIdentifier.licensedocumentationidentifiertype  = request.POST.get('license_documentation_identifier_type', '')
            licenseDocIdentifier.licensedocumentationidentifiervalue = request.POST.get('license_documentation_identifier_value', '')
            licenseDocIdentifier.licensedocumentationidentifierrole  = request.POST.get('license_documentation_identifier_role', '')
            licenseDocIdentifier.save()

            new_content_type_created = 'license'

        statuteFormset = StatuteFormSet(request.POST, instance=createdRights)
        createdStatuteSet = statuteFormset.save()
        if request.POST.get('statute_previous_pk', '') == 'None' and len(createdStatuteSet) == 1:
            new_content_type_created = 'statute'

        noteCreated = False
        for form in statuteFormset.forms:
            statuteCreated = False

            # handle documentation identifier creation for a parent that's a blank statute
            if (request.POST.get('statute_documentation_identifier_type_None', '') != '' or request.POST.get('statute_documentation_identifier_value_None', '') != '' or request.POST.get('statute_documentation_identifier_role_None', '') != ''):
                if form.instance.pk:
                    statuteCreated = form.instance
                else:
                    statuteCreated = models.RightsStatementStatuteInformation(rightsstatement=createdRights)
                    statuteCreated.save()

                statuteDocIdentifier = models.RightsStatementStatuteDocumentationIdentifier(rightsstatementstatute=statuteCreated)
                statuteDocIdentifier.statutedocumentationidentifiertype = request.POST.get('statute_documentation_identifier_type_None', '')
                statuteDocIdentifier.statutedocumentationidentifiervalue = request.POST.get('statute_documentation_identifier_value_None', '')
                statuteDocIdentifier.statutedocumentationidentifierrole = request.POST.get('statute_documentation_identifier_role_None', '')
                statuteDocIdentifier.save()
                new_content_type_created = 'statute'
            else:
                # handle documentation identifier creation for a parent statute that already exists
                if request.POST.get('statute_documentation_identifier_type_' + str(form.instance.pk), '') != '' or request.POST.get('statute_documentation_identifier_value_' + str(form.instance.pk), '') or request.POST.get('statute_documentation_identifier_role_' + str(form.instance.pk), ''):
                    statuteDocIdentifier = models.RightsStatementStatuteDocumentationIdentifier(rightsstatementstatute=form.instance)
                    statuteDocIdentifier.statutedocumentationidentifiertype = request.POST.get('statute_documentation_identifier_type_' +  str(form.instance.pk), '')
                    statuteDocIdentifier.statutedocumentationidentifiervalue = request.POST.get('statute_documentation_identifier_value_' +  str(form.instance.pk), '')
                    statuteDocIdentifier.statutedocumentationidentifierrole = request.POST.get('statute_documentation_identifier_role_' +  str(form.instance.pk), '')
                    statuteDocIdentifier.save()
                    new_content_type_created = 'statute'

            # handle note creation for a parent that's a blank grant
            if request.POST.get('new_statute_note_None', '') != '' and not form.instance.pk:
                if not statuteCreated:
                    statuteCreated = models.RightsStatementStatuteInformation(rightsstatement=createdRights)
                    statuteCreated.save()
                noteCreated = models.RightsStatementStatuteInformationNote(rightsstatementstatute=statuteCreated)
                noteCreated.statutenote = request.POST.get('new_statute_note_None', '')
                noteCreated.save()
                new_content_type_created = 'statue'
            else:
                # handle note creation for a parent grant that already exists 
                if request.POST.get('new_statute_note_' + str(form.instance.pk), '') != '':
                    noteCreated = models.RightsStatementStatuteInformationNote(rightsstatementstatute=form.instance)
                    noteCreated.statutenote = request.POST.get('new_statute_note_' + str(form.instance.pk), '')
                    noteCreated.save()
                    new_content_type_created = 'statute'

        # handle note creation for a parent that's just been created
        if request.POST.get('new_statute_note_None', '') != '' and not noteCreated:
            noteCreated = models.RightsStatementStatuteInformationNote(rightsstatementstatute=form.instance)
            noteCreated.statutenote = request.POST.get('new_statute_note_None', '')
            noteCreated.save()

        # display (possibly revised) formset
        statuteFormset = StatuteFormSet(instance=createdRights)

        otherFormset = OtherFormSet(request.POST, instance=createdRights)
        createdOtherSet = otherFormset.save()

        # establish whether or not there is an "other" instance to use as a parent
        if len(createdOtherSet) == 1:
            createdOther = createdOtherSet[0]
        else:
            createdOther = False

        # handle creation of new "other" notes, creating parent if necessary
        if request.POST.get('otherrights_note', '') != '':
            # make new "other" record if it doesn't exist
            if not createdOther:
                try:
                    createdOther = models.RightsStatementOtherRightsInformation.objects.get(rightsstatement=createdRights)
                except:
                    createdOther = models.RightsStatementOtherRightsInformation(rightsstatement=createdRights)
                    createdOther.save()

            otherNote = models.RightsStatementOtherRightsInformationNote(rightsstatementotherrights=createdOther)
            otherNote.otherrightsnote = request.POST.get('otherrights_note', '')
            otherNote.save()

            new_content_type_created = 'other'

        # handle creation of new documentation identifiers
        if request.POST.get('other_documentation_identifier_type', '') != '' or request.POST.get('other_documentation_identifier_value', '') != '' or request.POST.get('other_documentation_identifier_role', ''):
            # make new other record if it doesn't exist
            if not createdOther:
                try:
                    createdOther = models.RightsStatementOtherRightsInformation.objects.get(rightsstatement=createdRights)
                except:
                    createdOther = models.RightsStatementOtherRightsInformation(rightsstatement=createdRights)
                    createdOther.save()

            otherDocIdentifier = models.RightsStatementOtherRightsDocumentationIdentifier(rightsstatementotherrights=createdOther)
            otherDocIdentifier.otherrightsdocumentationidentifiertype  = request.POST.get('other_documentation_identifier_type', '')
            otherDocIdentifier.otherrightsdocumentationidentifiervalue = request.POST.get('other_documentation_identifier_value', '')
            otherDocIdentifier.otherrightsdocumentationidentifierrole  = request.POST.get('other_documentation_identifier_role', '')
            otherDocIdentifier.save()

            new_content_type_created = 'other'

        if request.POST.get('next_button', '') != None and request.POST.get('next_button', '') != '':
            return redirect('components.rights.views.%s_rights_grants_edit' % section, uuid, createdRights.pk)
        else:
            url = reverse('components.rights.views.%s_rights_edit' % section, args=[uuid, createdRights.pk])
            try:
                new_content_type_created                
                url = url + '?created=' + new_content_type_created
            except:
                pass
            return redirect(url)
    else:
        copyrightFormset = CopyrightFormSet(instance=viewRights)
        statuteFormset   = StatuteFormSet(instance=viewRights)
        licenseFormset   = LicenseFormSet(instance=viewRights)
        otherFormset     = OtherFormSet(instance=viewRights)

    # show what content's been created after a redirect
    if request.GET.get('created', '') != '':
        new_content_type_created = request.GET.get('created', '')

    return render(request, 'rights/rights_edit.html', locals())

def rights_grants_edit(request, uuid, id, section='ingest'):
    jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
    name = utils.get_directory_name_from_job(jobs[0])

    viewRights = models.RightsStatement.objects.get(pk=id)

    # determine how many empty forms should be shown for children
    extra_grant_forms = 1

    # create inline formsets for child elements
    GrantFormSet = inlineformset_factory(
      models.RightsStatement,
      models.RightsStatementRightsGranted,
      extra=extra_grant_forms,
      can_delete=False,
      form=forms.RightsGrantedForm
    )

    # handle form creation/saving
    if request.method == 'POST':
        grantFormset = GrantFormSet(request.POST, instance=viewRights)
        grantFormset.save()
        restrictionCreated = False
        noteCreated = False
        for form in grantFormset.forms:
            grantCreated = False

            # handle restriction creation for a parent that's a blank grant
            if request.POST.get('new_rights_restriction_None', '') != '' and not form.instance.pk:
                grantCreated = models.RightsStatementRightsGranted(rightsstatement=viewRights)
                grantCreated.save()
                restrictionCreated = models.RightsStatementRightsGrantedRestriction(rightsgranted=grantCreated)
                restrictionCreated.restriction = request.POST.get('new_rights_restriction_None', '')
                restrictionCreated.save()
            else:
                # handle restriction creation for a parent grant that already exists
                if request.POST.get('new_rights_restriction_' + str(form.instance.pk), '') != '':
                    restrictionCreated = models.RightsStatementRightsGrantedRestriction(rightsgranted=form.instance)
                    restrictionCreated.restriction = request.POST.get('new_rights_restriction_' + str(form.instance.pk), '')
                    restrictionCreated.save()

            # handle note creation for a parent that's a blank grant
            if request.POST.get('new_rights_note_None', '') != '' and not form.instance.pk:
                if not grantCreated:
                    grantCreated = models.RightsStatementRightsGranted(rightsstatement=viewRights)
                    grantCreated.save()
                noteCreated = models.RightsStatementRightsGrantedNote(rightsgranted=grantCreated)
                noteCreated.rightsgrantednote = request.POST.get('new_rights_note_None', '')
                noteCreated.save()
            else:
                # handle note creation for a parent grant that already exists 
                if request.POST.get('new_rights_note_' + str(form.instance.pk), '') != '':
                    noteCreated = models.RightsStatementRightsGrantedNote(rightsgranted=form.instance)
                    noteCreated.rightsgrantednote = request.POST.get('new_rights_note_' + str(form.instance.pk), '')
                    noteCreated.save()

    # handle restriction creation for a parent that's just been created
    if request.POST.get('new_rights_restriction_None', '') != '' and not restrictionCreated:
        restrictionCreated = models.RightsStatementRightsGrantedRestriction(rightsgranted=form.instance)
        restrictionCreated.restriction = request.POST.get('new_rights_restriction_None', '')
        restrictionCreated.save()

    # handle note creation for a parent that's just been created
    if request.POST.get('new_rights_note_None', '') != '' and not noteCreated:
        noteCreated = models.RightsStatementRightsGrantedNote(rightsgranted=form.instance)
        noteCreated.rightsgrantednote = request.POST.get('new_rights_note_None', '')
        noteCreated.save()

    # display (possibly revised) formset
    grantFormset = GrantFormSet(instance=viewRights)

    if request.method == 'POST':
        if request.POST.get('next_button', '') != None and request.POST.get('next_button', '') != '':
            return redirect('components.rights.views.%s_rights_list' % section, uuid)
        else:
            url = reverse('components.rights.views.%s_rights_grants_edit' % section, args=[uuid, viewRights.pk])
            try:
                new_content_type_created
                url = url + '?created=' + new_content_type_created
            except:
                pass
            return redirect(url)
    else:
        return render(request, 'rights/rights_grants_edit.html', locals())

def rights_delete(request, uuid, id, section):
    models.RightsStatement.objects.get(pk=id).delete()
    return redirect('components.rights.views.%s_rights_list' % section, uuid)

def rights_grant_delete(request, uuid, id, section):
    models.RightsStatementRightsGranted.objects.get(pk=id).delete()
    return redirect('components.rights.views.%s_rights_list' % section, uuid)

def rights_holders_lookup(request, id):
    try:
        agent = models.RightsStatementLinkingAgentIdentifier.objects.get(pk=id)
        result = agent.linkingagentidentifiervalue + ' [' + str(agent.id) + ']'
    except:
        result = ''
    return HttpResponse(result)

def rights_holders_autocomplete(request):

    search_text = ''

    try:
        search_text = request.REQUEST['text']
    except Exception: pass

    response = {}

    agents = models.RightsStatementLinkingAgentIdentifier.objects.filter(linkingagentidentifiervalue__icontains=search_text)
    for agent in agents:
        value = agent.linkingagentidentifiervalue + ' [' + str(agent.id) + ']'
        response[value] = value

    return helpers.json_response(response)

def rights_list(request, uuid, section):
    jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
    name = utils.get_directory_name_from_job(jobs[0])

    # See MetadataAppliesToTypes table
    types = {'transfer': 'Transfer', 'ingest': 'SIP', 'file': 'File'}
    type_id = helpers.get_metadata_type_id_by_description(types[section])

    grants = models.RightsStatementRightsGranted.objects.filter(
        rightsstatement__metadataappliestotype__exact=type_id,
        rightsstatement__metadataappliestoidentifier__exact=uuid
    )

    # create result list that incorporates multiple restriction records
    modifiedGrants = []
    for grant in grants:
        item = {
            'id':           grant.pk,
            'act':          grant.act,
            'basis':        grant.rightsstatement.rightsbasis,
            'restrictions': [],
            'startdate':    grant.startdate,
            'enddate':      grant.enddate,
            'rightsstatement': grant.rightsstatement
        }

        if (grant.enddateopen):
            item['enddate'] = '(open)'

        restriction_data = models.RightsStatementRightsGrantedRestriction.objects.filter(rightsgranted=grant)
        restrictions = []
        for restriction in restriction_data:
            #return HttpResponse(restriction.restriction)
            restrictions.append(restriction.restriction)
        item['restrictions'] = restrictions

        modifiedGrants.append(item)
    grants = modifiedGrants

    # When listing ingest rights we also want to show transfer rights
    # The only way I've found to get the related transfer of a SIP is looking into the File table
    if section is "ingest":
        try:
            transfer_uuid = models.File.objects.filter(sip__uuid__exact=uuid)[0].transfer.uuid
            transfer_grants = models.RightsStatementRightsGranted.objects.filter(
                rightsstatement__metadataappliestotype__exact=types['transfer'],
                rightsstatement__metadataappliestoidentifier__exact=transfer_uuid
            )
        except:
            pass

    return render(request, 'rights/rights_list.html', locals())

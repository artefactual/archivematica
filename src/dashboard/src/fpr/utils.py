# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.contrib import messages
from django.db import models
from django.utils.translation import ugettext as _


# ########## DEPENDENCIES ############


def dependent_objects(object_):
    """ Returns all the objects that rely on 'object_'. """
    links = [rel.get_accessor_name() for rel in object_._meta.get_all_related_objects()]
    dependent_objects = []
    for link in links:
        linked_objects = getattr(object_, link).all()
        for linked_object in linked_objects:
            dependent_objects.append(
                {"model": linked_object._meta.verbose_name, "value": linked_object}
            )
    return dependent_objects


def update_references_to_object(
    model_referenced, key_field_name, old_object, new_object
):
    """ Update references to an object, introspecting models, finding foreign
    key relations to the referenced model, and updating the references. """

    # don't need to update references if it's a newly created object
    if old_object is not None:
        for model in models.get_models():
            for field in model._meta.fields:
                type = field.get_internal_type()
                # update each foreign key reference to the target model
                if (
                    field.name != "replaces"
                    and type == "ForeignKey"
                    and field.rel is not None
                    and field.rel.to == model_referenced
                    and field.rel.field_name == key_field_name
                ):
                    filter_criteria = {field.name: old_object}
                    parent_objects = model.objects.filter(**filter_criteria)
                    for parent in parent_objects:
                        setattr(parent, field.name, new_object)
                        parent.save()


# ########## REVISIONS ############


def determine_what_replaces_model_instance(model, instance):
    """ Determine what object, if any, will be replaced by creating a new
    revision. """
    if instance:
        # if replacing the latest version or base on old version
        if instance.enabled:
            replaces = model.objects.get(pk=instance.pk)
        else:
            replaces = get_current_revision_using_ancestor(model, instance.uuid)
    else:
        replaces = None

    return replaces


def warn_if_replacing_with_old_revision(request, replaces):
    if replaces is not None and not replaces.enabled:
        messages.warning(
            request,
            _(
                "You are replacing the current revision with data from an older revision."
            ),
        )


def warn_if_viewing_disabled_revision(request, revision):
    if not revision.enabled:
        messages.warning(request, _("You are viewing a disabled revision."))


def get_revision_ancestors(model, uuid, ancestors):
    """ Get revisions that a given revision has replaced. """
    revision = model.objects.get(uuid=uuid)
    if revision.replaces:
        ancestors.append(revision.replaces)
        get_revision_ancestors(model, revision.replaces.uuid, ancestors)
    return ancestors


def get_revision_descendants(model, uuid, decendants):
    """ Get revisions that have replaces a given revision. """
    revision = model.objects.get(uuid=uuid)
    try:
        descendant = model.objects.get(replaces=revision)
    except model.DoesNotExist:
        pass
    else:
        decendants.append(descendant)
        get_revision_descendants(model, descendant.uuid, decendants)
    return decendants


def get_current_revision_using_ancestor(model, ancestor_uuid):
    """ Get the final (active) revision replacing a given revision. """
    descendants = get_revision_descendants(model, ancestor_uuid, [])
    descendants.reverse()
    if len(descendants):
        return descendants[0]
    else:
        return None

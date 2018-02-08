# -*- coding: utf-8 -*-

"""Management command that dumps the workflow contents as JSON."""

# This file is part of the Archivematica development tools.
#
# Copyright 2010-2018 Artefactual Systems Inc. <http://artefactual.com>
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

from __future__ import unicode_literals

import ast
import io
import json
import logging
import os
import sys
import tempfile


import django
from django.conf import settings as django_settings
from django.core.management.base import BaseCommand

# Workflow models
from main.models import (
    WatchedDirectory,
    MicroServiceChain,
    MicroServiceChainLink,
    MicroServiceChainChoice,
    MicroServiceChainLinkExitCode,
    MicroServiceChoiceReplacementDic,
    StandardTaskConfig,
    TaskConfigUnitVariableLinkPull,
    TaskConfigSetUnitVariable,
)

# Processing models
from main.models import Job


# This dict was extracted from the TaskTypes table, attributes: model,
# deprecated, description.
# More info here: https://wiki.archivematica.org/MCP/TaskTypes
TASK_TYPES = {
    '01b748fe-2e9d-44e4-ae5d-113f74c9a0ba': (
        StandardTaskConfig,
        'Get user choice from microservice generated list',
        'linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList'),
    '36b2e239-4a57-4aa5-8ebc-7a29139baca6': (
        StandardTaskConfig,
        'One instance',
        'linkTaskManagerDirectories'),
    'a19bfd9f-9989-4648-9351-013a10b382ed': (
        StandardTaskConfig,
        'Get microservice generated list in stdout',
        'linkTaskManagerGetMicroserviceGeneratedListInStdOut'),
    'a6b1c323-7d36-428e-846a-e7e819423577': (
        StandardTaskConfig,
        'For each file', 'linkTaskManagerFiles'),
    '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c': (
        MicroServiceChainChoice,
        'Get user choice to proceed with',
        'linkTaskManagerChoice'),
    '9c84b047-9a6d-463f-9836-eafa49743b84': (
        MicroServiceChoiceReplacementDic,
        'Get replacement dic from user choice',
        'linkTaskManagerReplacementDicFromChoice'),
    '6f0b612c-867f-4dfd-8e43-5b35b7f882d7': (
        TaskConfigSetUnitVariable,
        'linkTaskManagerSetUnitVariable',
        'linkTaskManagerSetUnitVariable'),
    'c42184a3-1a7f-4c4d-b380-15d8d97fdd11': (
        TaskConfigUnitVariableLinkPull,
        'linkTaskManagerUnitVariableLinkPull',
        'linkTaskManagerUnitVariableLinkPull'),
}


def process_chain_link_task_details(link_dict, link, task_config):
    try:
        ttype = TASK_TYPES[task_config.tasktype_id]
    except KeyError:
        # I could just make this an error but it's pretty bad
        raise ValueError('Unknown task type: %s', task_config.tasktype_id)
    else:
        model, description, manager_class_name = ttype

    link_config = {
        '@model': model.__name__,
        '@manager': manager_class_name,
    }
    link_dict['config'] = link_config

    if model == StandardTaskConfig:
        try:
            stdtask_config = StandardTaskConfig.objects.get(
                id=task_config.tasktypepkreference)
        except StandardTaskConfig.DoesNotExist:
            logging.error('Link %s points to a StandardTaskConfig tuple '
                          'that is missing!', link.id)
        else:
            link_config['execute'] = stdtask_config.execute
            link_config['arguments'] = stdtask_config.arguments
            link_config['filter_subdir'] = stdtask_config.filter_subdir
            link_config['filter_file_start'] = stdtask_config.filter_file_start
            link_config['filter_file_end'] = stdtask_config.filter_file_end
            link_config['stdout_file'] = stdtask_config.stdout_file
            link_config['stderr_file'] = stdtask_config.stderr_file
            link_config['requires_output_lock'] = \
                stdtask_config.requires_output_lock

    elif model == MicroServiceChainChoice:
        choices = MicroServiceChainChoice.objects.filter(
            choiceavailableatlink_id=link.id)
        link_config['chain_choices'] = [
            item.chainavailable_id for item in choices
        ]
        if not choices.count():
            logging.error('Link %s has zero MicroServiceChoiceReplacementDic '
                          'tuples', link.id)

    elif model == TaskConfigSetUnitVariable:
        try:
            config = TaskConfigSetUnitVariable.objects.get(
                id=task_config.tasktypepkreference)
        except TaskConfigSetUnitVariable.DoesNotExist:
            logging.error('Link %s points to a TaskConfigSetUnitVariable '
                          'tuple that is missing!', link.id)
        else:
            link_config['variable'] = config.variable
            link_config['variable_value'] = config.variablevalue
            link_config['chain_id'] = config.microservicechainlink_id

    elif model == MicroServiceChoiceReplacementDic:
        dicts = MicroServiceChoiceReplacementDic.objects.filter(
            choiceavailableatlink_id=link.id)
        link_config['replacements'] = list()
        if not dicts.count():
            logging.error('Link %s has zero MicroServiceChoiceReplacementDic '
                          'tuples', link.id)
        for item in dicts:
            rep = {}
            link_config['replacements'].append(rep)
            rep['id'] = item.id
            rep['description'] = i18nize_field(
                item.description,
                description='Link choice (replacement dict)')
            try:
                rep['items'] = {
                    key.strip('%'): value
                    for key, value in ast.literal_eval(
                        item.replacementdic).items()
                }
            except (SyntaxError, ValueError):
                logging.error('Link %s points to a '
                              'MicroServiceChoiceReplacementDic with syntax '
                              'issues', link.id)

    elif model == TaskConfigUnitVariableLinkPull:
        try:
            unit_var = TaskConfigUnitVariableLinkPull.objects.get(
                id=task_config.tasktypepkreference)
        except TaskConfigUnitVariableLinkPull.DoesNotExist:
            logging.error('Link %s points to a TaskConfigUnitVariableLinkPull '
                          'that is missing', link.id)
        else:
            link_config['variable'] = unit_var.variable
            link_config['chain_id'] = unit_var.defaultmicroservicechainlink_id

    else:
        raise ValueError('Unexpected link configuration type '
                         '(type_id={})'.format(task_config.tasktype_id))


def job_status_unicode(value):
    status = dict(Job.STATUS)
    try:
        return unicode(status[int(value)])
    except ValueError:
        # https://github.com/artefactual/archivematica/issues/784
        d = {
            'Failed': 4,
            'Completed successfully': 2,
        }
        if value in d:
            return unicode(status[d[value]])
        raise
    except KeyError:
        logging.error('Job status %s cannot be recognized', value)
        return job_status_unicode(Job.STATUS_UNKNOWN)


def link_exit_codes(link_id):
    exit_codes = MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id=link_id)
    ret = {}
    for item in exit_codes:
        props = {}
        ret[int(item.exitcode)] = props
        props['job_status'] = job_status_unicode(item.exitmessage)
        if item.nextmicroservicechainlink_id is None:
            logging.warning('Link %s with exit code %s has no next link '
                            'assigned', link_id, item.exitcode)
        props['link_id'] = item.nextmicroservicechainlink_id
    return ret


def i18nize_field(field, description):
    """Return a i18n dictionary with the existing translations.

    Side effect: update global catalogue.
    """
    value = unicode(field)
    if not hasattr(sys.modules[__name__], 'i18n_catalogues'):
        return dict(en=value)
    catalogues = getattr(sys.modules[__name__], 'i18n_catalogues')

    # Update English with the source message
    catalogues['en'][value] = dict(message=value, description=description)

    # Build translation object
    translations = dict()
    for lang, messages in catalogues.items():
        if field in messages:
            translations[lang] = messages[field]['message']
    return translations


def i18n_load_locales(path, catalogues):
    for item in os.listdir(path):
        if not item.endswith('.json'):
            continue
        lang = item[:len(item) - len('.json')]
        with open(os.path.join(path, item), 'r') as fh:
            catalogues[lang] = json.load(fh)


def i18n_write_locale_json(path, catalogue):
    try:
        with io.open(path, 'w', encoding='utf-8') as fh:
            logging.info("Writing i18n JSON: %s", path)
            blob = json.dumps(catalogue, ensure_ascii=False, sort_keys=True,
                              separators=(',', ': '), indent=4)
            fh.write(blob)
    except IOError:
        logging.exception('Error writing to %s', path)
        return 1


def main(locale_dir=None):
    # export is going to be our container to dump the three main types we need
    # to export: watched directories, chains and links. We realize these types
    # may not be ideal to describe a workflow but it is the way we originally
    # did in Archivematica. Watched directories are responsible for starting
    # new chains of processing when new directories or files are added to it.
    # Chains are basically entry points to a series of links.
    export = dict(watched_directories=list(), chains=dict(), links=dict())

    if locale_dir:
        locale_dir = os.path.abspath(locale_dir)
        catalogues = dict(en={})
        i18n_load_locales(locale_dir, catalogues)
        setattr(sys.modules[__name__], 'i18n_catalogues', catalogues)

    #
    # Watched directories
    #
    for item in WatchedDirectory.objects.all():
        logging.info('Adding watched directory: %s',
                     item.watched_directory_path)
        wd = {
            'path': item.watched_directory_path.replace(
                '%watchDirectoryPath%', '/'),
            'unit_type': item.expected_type.description,
            'chain_id': item.chain.pk,
            'only_dirs': item.only_act_on_directories
        }
        export['watched_directories'].append(wd)

    #
    # Chains
    #
    for item in MicroServiceChain.objects.all():
        logging.info('Adding chain: %s', item.description)
        msc = {
            'description': i18nize_field(item.description,
                                         description='Chain description'),
            'link_id': item.startinglink_id,
        }
        export['chains'][item.id] = msc

    #
    # Tasks
    #
    for item in MicroServiceChainLink.objects.all():
        logging.info('Adding link: %s', item.id)

        link = {}
        export['links'][item.id] = link
        link['group'] = i18nize_field(item.microservicegroup,
                                      description='Link group')
        link['fallback_job_status'] = \
            job_status_unicode(item.defaultexitmessage)
        link['fallback_link_id'] = item.defaultnextchainlink_id

        # Exit codes
        link['exit_codes'] = link_exit_codes(item.id)
        if not len(link['exit_codes']):
            logging.warning('Link %s has no connections with exit codes',
                            item.id)

        # Link configuration details (TaskConfig stuff)
        try:
            task_config = item.currenttask
        except django.core.exceptions.ObjectDoesNotExist:
            logging.error('Found orphan task (MicroServiceChainLink.pk=%s), '
                          'currenttask foreign key cannot be found', item.id)
        else:
            link['description'] = i18nize_field(task_config.description,
                                                description='Link description')
            process_chain_link_task_details(link, item, task_config)

    #
    # Save output
    #

    fd, path = tempfile.mkstemp(suffix=".json", prefix="json-links-",
                                dir=os.path.join(
                                    django_settings.SHARED_DIRECTORY, 'tmp'))
    with open(path, 'w') as fd:
        json.dump(export, fd, ensure_ascii=False, sort_keys=True,
                  separators=(',', ': '), indent=4)
        print(path)

    if locale_dir:
        # Update en.json with new messages
        i18n_write_locale_json(
            os.path.abspath(
                os.path.join(locale_dir, 'en.json')), catalogues['en'])

    return 0


def setup_logging(verbosity):
    """Impose the logging settings used in the dashboard.

    That may be convenient in some cases but in this particular script I need
    logging events to be sent to stderr instead.
    """
    # Undo Archivematica's logging settings
    root = logging.getLogger()
    map(root.removeHandler, root.handlers[:])
    map(root.removeFilter, root.filters[:])

    # Set level
    root.setLevel(logging.DEBUG
                  if verbosity > 1 else logging.WARNING
                  if verbosity == 1 else logging.ERROR)

    # Set up local logger
    logging.basicConfig(
        stream=sys.stderr,
        format='[%(asctime)s] [%(levelname)8s] -'
               ' %(message)s (%(filename)s:%(lineno)s)')


class Command(BaseCommand):
    def handle(self, *args, **options):
        main()

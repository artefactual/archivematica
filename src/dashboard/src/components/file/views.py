# Standard library, alphabetical by import source
import json
import logging
import os

# Django Core, alphabetical by import source
from django.conf import settings as django_settings
from django.views.generic import View

# External dependencies, alphabetical
import requests

# This project, alphabetical by import source
from components import helpers
from main import models

import elasticSearchFunctions
import storageService as storage_service

logger = logging.getLogger('archivematica.dashboard')


class TransferFileTags(View):
    """
    Fetch, set or remove tags from a record.
    This view's methods operate on the file data indexed in Elasticsearch, and do not affect the database.
    All methods return 404 if a record can't be retrieved for the given UUID, and 400 if more than one file was found for a given UUID.
    """

    def get(self, request, fileuuid):
        """
        Requires a file UUID.
        Returns a JSON-encoded list of the file's tags on success.
        """
        try:
            es_client = elasticSearchFunctions.get_client()
            tags = elasticSearchFunctions.get_file_tags(es_client, fileuuid)
        except elasticSearchFunctions.ElasticsearchError as e:
            response = {
                'success': False,
                'message': str(e),
            }
            if isinstance(e, elasticSearchFunctions.EmptySearchResultError):
                status_code = 404
            else:
                status_code = 400
            return helpers.json_response(response, status_code=status_code)

        return helpers.json_response(tags)

    def put(self, request, fileuuid):
        """
        Requires a file UUID, and document body must be a JSON-encoded list.
        Replaces the list of tags in the record with the provided list.
        Returns {"success": true} on success.
        Returns 400 if no JSON document is provided in the request body, if the body can't be decoded, or if the body is any JSON object other than a list.
        """
        try:
            tags = json.load(request)
        except ValueError:
            response = {
                'success': False,
                'message': 'No JSON document could be decoded from the request.'
            }
            return helpers.json_response(response, status_code=400)
        if not isinstance(tags, list):
            response = {
                'success': False,
                'message': 'The request body must be an array.'
            }
            return helpers.json_response(response, status_code=400)

        try:
            es_client = elasticSearchFunctions.get_client()
            elasticSearchFunctions.set_file_tags(es_client, fileuuid, tags)
        except elasticSearchFunctions.ElasticsearchError as e:
            response = {
                'success': False,
                'message': str(e),
            }
            if isinstance(e, elasticSearchFunctions.EmptySearchResultError):
                status_code = 404
            else:
                status_code = 400
            return helpers.json_response(response, status_code=status_code)
        return helpers.json_response({'success': True})

    def delete(self, request, fileuuid):
        """
        Request a file UUID.
        Deletes all tags for the given file.
        """
        try:
            es_client = elasticSearchFunctions.get_client()
            elasticSearchFunctions.set_file_tags(es_client, fileuuid, [])
        except elasticSearchFunctions.ElasticsearchError as e:
            response = {
                'success': False,
                'message': str(e),
            }
            if isinstance(e, elasticSearchFunctions.EmptySearchResultError):
                status_code = 404
            else:
                status_code = 400
            return helpers.json_response(response, status_code=status_code)
        return helpers.json_response({'success': True})


def bulk_extractor(request, fileuuid):
    """
    Fetch bulk_extractor reports for a given file, and return a parsed copy of them as JSON.

    Supports the 'reports' query parameter; this is a comma-separated list of reports to return.
    If not specified, then the 'ccn' and 'pii' reports are returned.

    If no reports are requested, or if the requested file is missing at least one of the requested reports, returns 400.
    If no file can be found for the given UUID, returns 404.

    Data structure looks like:
        {
            "report": [
                {
                    "content": "",
                    "context": "",
                    "offset": 0
                }
            ]
        }
    It will have one key for each parsed report, with each report's list of features containing zero or more objects.
    """
    reports = request.GET.get('reports', 'ccn,pii').split(',')

    if len(reports) == 0:
        response = {
            'success': False,
            'message': 'No reports were requested.'
        }
        return helpers.json_response(response, status_code=400)

    try:
        es_client = elasticSearchFunctions.get_client()
        record = elasticSearchFunctions.get_transfer_file_info(es_client, 'fileuuid', fileuuid)
    except elasticSearchFunctions.ElasticsearchError as e:
        message = str(e)
        response = {
            'success': False,
            'message': message,
        }
        if 'no exact results' in message:
            status_code = 404
        else:
            status_code = 500
        return helpers.json_response(response, status_code=status_code)

    bulk_extractor_reports = record.get('bulk_extractor_reports', [])
    missing_reports = []
    for report in reports:
        if report not in bulk_extractor_reports:
            missing_reports.append(report)

    if len(missing_reports) > 0:
        response = {
            'success': False,
            'message': 'Requested file is missing the following requested reports: ' + ', '.join(missing_reports),
        }
        return helpers.json_response(response, status_code=400)

    f = models.File.objects.get(uuid=fileuuid)
    features = {}

    for report in reports:
        relative_path = os.path.join('logs', 'bulk-' + fileuuid, report + '.txt')
        url = storage_service.extract_file_url(f.transfer_id, relative_path)
        response = requests.get(url, timeout=django_settings.STORAGE_SERVICE_CLIENT_TIMEOUT)

        if response.status_code != 200:
            message = 'Unable to retrieve ' + report + ' report for file with UUID ' + fileuuid
            logger.error(message + '; response: %s', (response.text,))
            response = {
                'success': False,
                'message': message,
            }
            helpers.json_response(response, status_code=500)

        features[report] = _parse_bulk_extractor_report(response.text)

    return helpers.json_response(features)


def _parse_bulk_extractor_report(data):
    headers = ['offset', 'content', 'context']
    return [dict(zip(headers, l.split('\t'))) for l in data.splitlines() if not l.startswith('#')]


def file_details(request, fileuuid):
    try:
        es_client = elasticSearchFunctions.get_client()
        source = elasticSearchFunctions.get_transfer_file_info(es_client, 'fileuuid', fileuuid)
    except elasticSearchFunctions.ElasticsearchError as e:
        message = str(e)
        response = {
            'success': False,
            'message': message,
        }
        if 'no exact results' in message:
            status_code = 404
        else:
            status_code = 500
        return helpers.json_response(response, status_code=status_code)

    format_info = source.get('format', [{}])[0]
    record = {
        'id': source['fileuuid'],
        'type': 'file',
        'title': source['filename'],
        'size': source['size'],
        'bulk_extractor_reports': source.get('bulk_extractor_reports', []),
        'tags': source.get('tags', []),
        'format': format_info.get('format'),
        'group': format_info.get('group'),
        'puid': format_info.get('puid'),
    }
    return helpers.json_response(record)

import json
import logging
import os
import re
import requests
from urlparse import urlparse

__all__ = ['ArchivesSpaceError', 'ConnectionError', 'AuthenticationError', 'ArchivesSpaceClient']

LOGGER = logging.getLogger(__name__)


class ArchivesSpaceError(Exception):
    pass


class ConnectionError(ArchivesSpaceError):
    pass


class AuthenticationError(ArchivesSpaceError):
    pass


class CommunicationError(ArchivesSpaceError):
    def __init__(self, status_code, response):
        message = "ArchivesSpace server responded {}".format(status_code)
        self.response = response
        super(CommunicationError, self).__init__(message)


class ArchivesSpaceClient(object):
    """
    Client to communicate with a remote ArchivesSpace installation using its backend API.

    Note that, while functions follow the same API as the ArchivistsToolkitClient, one major difference is the handling of resource and component IDs.
    In ArchivistsToolkitClient, resource IDs are longs representing the database row ID.
    In this client, resource IDs are instead URI fragments representing the location of the record, for instance:
        /repositories/2/resource/1
    This change is due to the fact that the integer IDs are not unique across the collection in ArchivesSpace, as they were in Archivist's Toolkit.
    """

    RESOURCE = 'resource'
    RESOURCE_COMPONENT = 'resource_component'

    def __init__(self, host, user, passwd, port=8089, repository=2):
        parsed = urlparse(host)
        if not parsed.scheme:
            host = 'http://' + host

        self.host = host + ':' + str(port)
        self.user = user
        self.passwd = passwd
        self.repository = '/repositories/{}'.format(repository)
        self._login()

    def _login(self):
        try:
            response = requests.post(self.host + '/users/' + self.user + '/login',
                                     data={'password': self.passwd})
        except requests.ConnectionError as e:
            raise ConnectionError("Unable to connect to ArchivesSpace server: " + str(e))

        try:
            output = response.json()
        except Exception:
            raise ArchivesSpaceError("ArchivesSpace server responded with status {}, but returned a non-JSON document".format(response.status_code))

        if 'error' in output:
            raise AuthenticationError("Unable to log into ArchivesSpace installation; message from server: {}".format(output['error']))
        else:
            token = output['session']

        self.session = requests.Session()
        self.session.headers.update({'X-ArchivesSpace-Session': token})

    def _request(self, method, url, params, expected_response, data=None, retry=True):
        if not url.startswith('/'):
            url = '/' + url

        response = method(self.host + url, params=params, data=data)
        if response.status_code != expected_response:
            LOGGER.error('Response code: %s', response.status_code)
            LOGGER.error('Response body: %s', response.text)
            # session has expired; acquire a new session, then retry once
            if retry and response.status_code == 412 and "SESSION_GONE" in response.text:
                self._login()
                return self._request(method, url, params, expected_response, data=data, retry=False)
            raise CommunicationError(response.status_code, response)

        try:
            output = response.json()
        except Exception:
            raise ArchivesSpaceError("ArchivesSpace server responded with status {}, but returned a non-JSON document".format(response.status_code))

        if 'error' in output:
            raise ArchivesSpaceError(output['error'])

        return response

    def _get(self, url, params={}, expected_response=200):
        return self._request(self.session.get, url,
                             params=params,
                             expected_response=expected_response)

    def _put(self, url, params={}, data=None, expected_response=200):
        return self._request(self.session.put, url,
                             params=params, data=data,
                             expected_response=expected_response)

    def _post(self, url, params={}, data=None, expected_response=200):
        return self._request(self.session.post, url,
                             params=params, data=data,
                             expected_response=expected_response)

    def resource_type(self, resource_id):
        """
        Given an ID, determines whether a given resource is a resource or a resource_component.

        :param resource_id string: The URI of the resource whose type to determine.
        :raises ArchivesSpaceError: if the resource_id does not appear to be either type.
        """
        match = re.search(r'repositories/\d+/(resources|archival_objects)/\d+', resource_id)
        if match and match.groups():
            type_ = match.groups()[0]
            return 'resource' if type_ == 'resources' else 'resource_component'
        else:
            raise ArchivesSpaceError('Unable to determine type of provided ID: {}'.format(resource_id))

    def get_record(self, record_id):
        return self._get(record_id).json()

    def collection_list(self, resource_id, resource_type='collection'):
        """
        Fetches a list of all resource IDs within the specified resource ID.

        :param resource_id long: The URI of the resource to fetch children from.
        :param resource_type str: no-op; not required or used in this implementation.

        :return list: A list of strings representing the record URIs for all children of the requested record.
        """
        def fetch_children(children):
            results = []

            for child in children:
                results.append(child['record_uri'])

                if child['has_children']:
                    results.extend(fetch_children(child['children']))

            return results

        response = self._get(resource_id + '/tree')
        tree = response.json()
        return fetch_children(tree['children'])

    def get_resource_component_children(self, resource_component_id):
        """
        Given a resource component, fetches detailed metadata for it and all of its children.

        This is implemented using ArchivesSpaceClient.get_resource_component_children and uses its default options when fetching children.

        :param string resource_component_id: The URL of the resource component from which to fetch metadata.
        """
        resource_type = self.resource_type(resource_component_id)
        return self.get_resource_component_and_children(resource_component_id, resource_type)

    def _format_dates(self, start, end=None):
        if end is not None:
            return "{}-{}".format(start, end)
        else:
            return start

    def _fetch_dates_from_record(self, record):
        if not record.get('dates'):
            return ''
        elif 'expression' in record['dates'][0]:
            return record['dates'][0]['expression']
        # use the first date, though there can be multiple sets
        else:
            start_date = record['dates'][0]['begin']
            end_date = record['dates'][0].get('end')
            return self._format_dates(start_date, end_date)

    def _get_resources(self, resource_id, level=1, recurse_max_level=False, sort_by=None):
        def format_record(record, level):
            descend = recurse_max_level != level
            level += 1

            full_record = self._get(record['record_uri']).json()
            dates = self._fetch_dates_from_record(full_record)

            identifier = full_record['id_0'] if 'id_0' in full_record else full_record.get('component_id', '')

            result = {
                'id': record['record_uri'],
                'sortPosition': level,
                'identifier': identifier,
                'title': record.get('title', ''),
                'dates': dates,
                'levelOfDescription': record['level']
            }
            if record['children'] and descend:
                result['children'] = [format_record(child, level) for child in record['children']]
                if sort_by is not None:
                    kwargs = {'reverse': True} if sort_by == 'desc' else {}
                    result['children'] = sorted(result['children'], key=lambda c: c['title'], **kwargs)
            else:
                result['children'] = False

            return result

        response = self._get(resource_id + '/tree')
        tree = response.json()
        return format_record(tree, 1)

    def _get_components(self, resource_id, level=1, recurse_max_level=False, sort_by=None):
        def fetch_children(resource_id):
            return self._get(resource_id + '/children').json()

        def format_record(record, level):
            level += 1
            dates = self._fetch_dates_from_record(record)

            result = {
                'id': record['uri'],
                'sortPosition': level,
                'identifier': record.get('component_id', ''),
                'title': record.get('title', ''),
                'dates': dates,
                'levelOfDescription': record['level']
            }

            children = fetch_children(record['uri'])
            if children and not recurse_max_level == level:
                result['children'] = [format_record(child, level) for child in children]
                if sort_by is not None:
                    kwargs = {'reverse': True} if sort_by == 'desc' else {}
                    result['children'] = sorted(children, key=lambda c: c['title'], **kwargs)
            else:
                result['children'] = False

            return result

        return format_record(self._get(resource_id).json(), level)

    def get_resource_component_and_children(self, resource_id, resource_type='collection', level=1, sort_data={}, recurse_max_level=False, sort_by=None, **kwargs):
        """
        Fetch detailed metadata for the specified resource_id and all of its children.

        :param long resource_id: The resource for which to fetch metadata.
        :param str resource_type: no-op; not required or used in this implementation.
        :param int recurse_max_level: The maximum depth level to fetch when fetching children.
            Default is to fetch all of the resource's children, descending as deeply as necessary.
            Pass 1 to fetch no children.
        :param string search_pattern: If specified, limits fetched children to those whose titles or IDs match the provided query.
            See ArchivistsToolkitClient.find_collection_ids for documentation of the query format.

        :return dict: A dict containing detailed metadata about both the requested resource and its children.
            Consult ArchivistsToolkitClient.get_resource_component_and_children for the output format.
        """
        resource_type = self.resource_type(resource_id)
        if resource_type == 'resource':
            return self._get_resources(resource_id, recurse_max_level=recurse_max_level, sort_by=sort_by)
        else:
            return self._get_components(resource_id, recurse_max_level=recurse_max_level, sort_by=sort_by)

    def find_resource_id_for_component(self, component_id):
        """
        Given the URL to a component, returns the parent resource's URL.

        :param string component_id: The URL of the resource.
        :return string: The URL of the component's parent resource.
        """
        response = self._get(component_id)
        return response.json()['resource']['ref']

    def find_parent_id_for_component(self, component_id):
        """
        Given the URL to a component, returns the parent component's URL.

        :param string component_id: The URL of the component.
        :return tuple: A tuple containing:
            * The type of the parent record; valid values are ArchivesSpaceClient.RESOURCE and ArchivesSpaceClient.RESOURCE_COMPONENT.
            * The URL of the parent record.
            If the provided URL fragment references a resource, this method will simply return the same URL.
        """
        response = self.get_record(component_id)
        if 'parent' in response:
            return (ArchivesSpaceClient.RESOURCE_COMPONENT, response['parent']['ref'])
        # if this is the top archival object, return the resource instead
        elif 'resource' in response:
            return (ArchivesSpaceClient.RESOURCE, response['resource']['ref'])
        # resource was passed in, which has no higher-up record;
        # return the same ID
        else:
            return (ArchivesSpaceClient.RESOURCE, component_id)

    def find_collection_ids(self, search_pattern='', identifier='', fetched=0, page=1):
        """
        Fetches a list of resource URLs for every resource in the database.

        :param string search_pattern: A search pattern to use in looking up resources by title or resourceid.
            The search will match any title containing this string;
            for example, "text" will match "this title has this text in it".
            If omitted, then all resources will be fetched.
        :param string identifier: Only records containing this identifier will be returned.
            Substring matching will not be performed; however, wildcards are supported.
            For example, searching "F1" will only return records with the identifier "F1", while searching "F*" will return "F1", "F2", etc.

        :return list: A list containing every matched resource's URL.
        """
        params = {
            'page': page,
            'q': 'primary_type:resource'
        }

        if search_pattern != '':
            params['q'] = params['q'] + ' AND title:{}'.format(search_pattern)

        if identifier != '':
            params['q'] = params['q'] + ' AND identifier:{}'.format(identifier)

        response = self._get(self.repository + '/search', params=params)
        hits = response.json()
        results = [r['uri'] for r in hits['results']]

        results_so_far = fetched + hits['this_page']
        if hits['total_hits'] > results_so_far:
            results.extend(self.find_collection_ids(fetched=results_so_far, page=page + 1))

        return results

    def count_collections(self, search_pattern='', identifier=''):
        params = {
            'page': 1,
            'q': 'primary_type:resource'
        }

        if search_pattern != '':
            params['q'] = params['q'] + ' AND title:{}'.format(search_pattern)

        if identifier != '':
            params['q'] = params['q'] + ' AND identifier:{}'.format(identifier)

        return self._get(self.repository + '/search', params=params).json()['total_hits']

    def find_collections(self, search_pattern='', identifier='', fetched=0, page=1, page_size=30, sort_by=None):
        def format_record(record):
            dates = self._fetch_dates_from_record(record)
            identifier = record['id_0'] if 'id_0' in record else record.get('component_id', '')
            return {
                'id': record['uri'],
                'sortPosition': 1,
                'identifier': identifier,
                'title': record.get('title', ''),
                'dates': dates,
                'levelOfDescription': record['level']
            }

        params = {
            'page': page,
            'page_size': page_size,
            'q': 'primary_type:resource'
        }

        if search_pattern != '':
            params['q'] = params['q'] + ' AND title:{}'.format(search_pattern)

        if identifier != '':
            params['q'] = params['q'] + ' AND identifier:{}'.format(identifier)

        if sort_by is not None:
            params['sort'] = 'title_sort ' + sort_by

        response = self._get(self.repository + '/search', params=params)
        hits = response.json()
        return [format_record(json.loads(r['json'])) for r in hits['results']]

    def find_by_field(self, field, search_pattern, fetched=0, page=1, page_size=30, sort_by=None):
        """
        Find resource when searching by field exact value.

        Results are a dict in the format:
        {
            'id': <resource URI fragment>,
            'identifier': <resource identifier>,
            'title': <title of the resource>,
            'levelOfDescription': <level of description>,
        }

        :param str field: Name of the field to search
        :param search_pattern: Value of the field to search for
        :return: List of dicts containing results.
        """
        def format_record(record):
            return {
                'id': record['uri'],
                'identifier': record['identifier'],
                'title': record.get('title', ''),
                'levelOfDescription': record['level']
            }

        params = {
            'page': page,
            'page_size': page_size,
            'q': '{}:{}'.format(field, search_pattern)
        }

        if sort_by is not None:
            params['sort'] = 'title_sort ' + sort_by

        response = self._get(self.repository + '/search', params=params)
        hits = response.json()
        return [format_record(r) for r in hits['results']]

    def augment_resource_ids(self, resource_ids):
        """
        Given a list of resource IDs, returns a list of dicts containing detailed information about the specified resources and their children.

        This function recurses to a maximum of two levels when fetching children from the specified resources.
        Consult the documentation of ArchivistsToolkitClient.get_resource_component_children for the format of the returned dicts.

        :param list resource_ids: A list of one or more resource IDs.
        :return list: A list containing metadata dicts.
        """
        resources_augmented = []
        for id in resource_ids:
            resources_augmented.append(
                self.get_resource_component_and_children(id, recurse_max_level=2)
            )

        return resources_augmented

    def add_digital_object(self, parent_archival_object, dashboard_uuid, title="", identifier=None, uri=None, object_type="text", xlink_show="embed", xlink_actuate="onLoad", restricted=False, use_statement="", use_conditions=None, access_conditions=None, size=None, format_name=None, format_version=None):
        """
        Creates a new digital object.

        :param string parent_archival_object: The archival object to which the newly-created digital object will be parented.
        :param string title: The title of the digital object.
        :param string uri: The URI to an instantiation of the digital object.
        :param string object_type: The type of the digital object.
            Defaults to "text".
        :param string xlink_show: Controls how the file will be displayed.
            For supported values, see: http://www.w3.org/TR/xlink/#link-behaviors
        :param string xlink_actuate:
        :param string use_statement:
        :param string use_conditions: A paragraph of human-readable text to specify conditions of use for the digital object.
            If provided, creates a "conditions governing use" note in the digital object.
        :param string access_conditions: A paragraph of human-readable text to specify conditions of use for the digital object.
            If provided, creates a "conditions governing access" note in the digital object.
        :param int size: Size in bytes of the digital object
        :param str format_name: Name of the digital object's format
        :param str format_version: Name of the digital object's format version
        """
        parent_record = self.get_record(parent_archival_object)
        repository = parent_record['repository']['ref']
        language = parent_record.get('language', '')

        if not title:
            filename = os.path.basename(uri) if uri is not None else 'Untitled'
            title = parent_record.get('title', filename)

        if identifier is None:
            identifier = os.path.dirname(uri)

        new_object = {
            "title": title,
            "digital_object_id": identifier,
            "digital_object_type": object_type,
            "file_versions": [
                {
                    "file_uri": uri,
                    "use_statement": use_statement,
                    "xlink_show_attribute": xlink_show,
                    "xlink_actuate_attribute": xlink_actuate,
                },
            ],
            "language": language,
            "notes": [{
                "jsonmodel_type": "note_digital_object",
                "type": "originalsloc",
                "content": [dashboard_uuid]
            }],
            "restrictions": restricted,
            "subjects": parent_record['subjects'],
            "linked_agents": parent_record['linked_agents'],
        }

        if use_conditions:
            new_object["notes"].append({
                "jsonmodel_type": "note_digital_object",
                "type": "userestrict",
                "content": [use_conditions],
            })
        if access_conditions:
            new_object["notes"].append({
                "jsonmodel_type": "note_digital_object",
                "type": "accessrestrict",
                "content": [access_conditions],
            })
        if not restricted:
            new_object["file_versions"][0]["publish"] = True

        if size:
            new_object['file_versions'][0]['file_size_bytes'] = size
        if format_name:
            new_object['file_versions'][0]['file_format_name'] = format_name
        if format_version:
            new_object['file_versions'][0]['file_format_version'] = format_version

        new_object_uri = self._post(repository + '/digital_objects', data=json.dumps(new_object)).json()["uri"]

        # Now we need to update the parent object with a link to this instance
        parent_record["instances"].append({
            "instance_type": "digital_object",
            "digital_object": {"ref": new_object_uri}
        })
        self._post(parent_archival_object, data=json.dumps(parent_record))

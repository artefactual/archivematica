import logging

import MySQLdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ArchivistsToolkitError(Exception):
    pass


class ArchivistsToolkitClient(object):
    RESOURCE = 'resource'
    RESOURCE_COMPONENT = 'resource_component'

    def __init__(self, host, user, passwd, db):
        try:
            self.db = MySQLdb.connect(host=host,
                                      user=user,
                                      passwd=passwd,
                                      db=db)
            logger.debug('Connected to ATK database: %s', db)
        except Exception:
            logger.exception('Error connecting to ATK database')
            raise

    def resource_type(self, resource_id):
        cursor = self.db.cursor()
        cursor.execute("SELECT resourceId FROM Resources WHERE resourceId=%s", (resource_id,))
        if cursor.fetchone() is not None:
            return ArchivistsToolkitClient.RESOURCE

        cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE resourceComponentId=%s", (resource_id,))
        if cursor.fetchone() is not None:
            return ArchivistsToolkitClient.RESOURCE_COMPONENT

    def edit_record(self, new_record):
        """
        Update a record in Archivist's Toolkit using the provided new_record.

        The format of new_record is identical to the format returned by get_resource_component_and_children and related methods.
        This means it's possible, for example, to request a record, modify the returned dict, and pass that dict to this method to update the server.

        Currently supported fields are:
            * title
            * targetfield

        :raises ValueError: if the 'id' field isn't specified, or no fields to edit were specified.
        """
        try:
            record_id = new_record['id']
        except KeyError:
            raise ValueError('No record ID provided!')

        record_type = self.resource_type(record_id)
        if record_type is None:
            raise ArchivistsToolkitError('Could not determine type for record with ID {}; not in database?'.format(record_id))

        clause = []
        values = []
        if 'title' in new_record:
            clause.append('title=%s')
            values.append(new_record['title'])
        if 'levelOfDescription' in new_record:
            clause.append('resourceLevel=%s')
            values.append(new_record['levelOfDescription'])

        # nothing to update
        if not clause:
            raise ValueError('No fields to update specified!')

        clause = ', '.join(clause)
        if record_type == ArchivistsToolkitClient.RESOURCE:
            db_type = 'Resources'
            db_id_field = 'resourceId'
        else:
            db_type = 'ResourcesComponents'
            db_id_field = 'resourceComponentId'
        sql = "UPDATE {} SET {} WHERE {}=%s".format(db_type, clause, db_id_field)
        cursor = self.db.cursor()
        cursor.execute(sql, tuple(values))

    def get_levels_of_description(self):
        """
        Returns an array of all levels of description defined in this Archivist's Toolkit instance.
        """
        if not hasattr(self, 'levels_of_description'):
            cursor = self.db.cursor()
            levels = set()
            cursor.execute("SELECT distinct(resourceLevel) FROM Resources")
            for row in cursor:
                levels.add(row)
            cursor.execute("SELECT distinct(resourceLevel) FROM ResourcesComponents")
            for row in cursor:
                levels.add(row)
            self.levels_of_description = list(levels)

        return self.levels_of_description

    def collection_list(self, resource_id, resource_type='collection'):
        """
        Fetches a list of all resource and component IDs within the specified resource.

        :param long resource_id: The ID of the resource to fetch children from.
        :param string resource_type: Specifies whether the resource to fetch is a collection or a child element.
            Defaults to 'collection'.

        :return: A list of longs representing the database resource IDs for all children of the requested record.
        :rtype list:
        """
        ret = []

        cursor = self.db.cursor()
        if resource_type == 'collection':
            cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId IS NULL AND resourceId=%s", (resource_id))
        else:
            ret.append(resource_id)
            cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId=%s", (resource_id))

        rows = cursor.fetchall()
        if len(rows):
            for row in rows:
                ret.extend(self.collection_list(row[0], 'description'))

        return ret

    def get_resource_component_children(self, resource_component_id):
        """
        Given a resource component, fetches detailed metadata for it and all of its children.

        This is implemented using ArchivistsToolkitClient.get_resource_component_children and uses its default options when fetching children.

        :param long resource_component_id: The ID of the resource component from which to fetch metadata.
        """
        return self.get_resource_component_and_children(resource_component_id, 'resource')

    def get_resource_component_and_children(self, resource_id, resource_type='collection', level=1, sort_data={}, **kwargs):
        """
        Fetch detailed metadata for the specified resource_id and all of its children.

        :param long resource_id: The resource for which to fetch metadata.
        :param string resource_type: The level of description of the record.
        :param int recurse_max_level: The maximum depth level to fetch when fetching children.
            Default is to fetch all of the resource's children, descending as deeply as necessary.
            Pass 1 to fetch no children.
        :param string search_pattern: If specified, limits fetched children to those whose titles or IDs match the provided query.
            See ArchivistsToolkitClient.find_collection_ids for documentation of the query format.

        :return: A dict containing detailed metadata about both the requested resource and its children.
            The dict follows this format:
        {
          'id': '31',
          'sortPosition': '1',
          'identifier': 'PR01',
          'title': 'Parent',
          'levelOfDescription': 'collection',
          'dates': '1880-1889',
          'children': [{
            'id': '23',
            'sortPosition': '2',
            'identifier': 'CH01',
            'title': 'Child A',
            'levelOfDescription': 'Sousfonds',
            'dates': '1880-1888',
            'children': [{
              'id': '24',
              'sortPosition': '3',
              'identifier': 'GR01',
              'title': 'Grandchild A',
              'levelOfDescription': 'Item',
              'dates': '1880-1888',
              'children': False
            },
            {
              'id': '25',
              'sortPosition': '4',
              'identifier': 'GR02',
              'title': 'Grandchild B',
              'levelOfDescription': 'Item',
              'children': False
            }]
          },
          {
            'id': '26',
            'sortPosition': '5',
            'identifier': 'CH02',
            'title': 'Child B',
            'levelOfDescription': 'Sousfonds',
            'dates': '1889',
            'children': False
          }]
        }
        :rtype list:
        """
        # we pass the sort position as a dict so it passes by reference and we
        # can use it to share state during recursion

        recurse_max_level = kwargs.get('recurse_max_level', False)
        query             = kwargs.get('search_pattern', '')

        # intialize sort position if this is the beginning of recursion
        if level == 1:
            sort_data['position'] = 0

        sort_data['position'] = sort_data['position'] + 1

        resource_data = {}

        cursor = self.db.cursor()

        if resource_type == 'collection':
            cursor.execute("SELECT title, dateExpression, resourceIdentifier1, resourceLevel FROM Resources WHERE resourceid=%s", (resource_id))

            for row in cursor.fetchall():
                resource_data['id']                 = resource_id
                resource_data['sortPosition']       = sort_data['position']
                resource_data['title']              = row[0]
                resource_data['dates']              = row[1]
                resource_data['identifier']         = row[2]
                resource_data['levelOfDescription'] = row[3]
        else:
            cursor.execute("SELECT title, dateExpression, persistentID, resourceLevel FROM ResourcesComponents WHERE resourceComponentId=%s", (resource_id))

            for row in cursor.fetchall():
                resource_data['id']                 = resource_id
                resource_data['sortPosition']       = sort_data['position']
                resource_data['title']              = row[0]
                resource_data['dates']              = row[1]
                resource_data['identifier']         = row[2]
                resource_data['levelOfDescription'] = row[3]

        # fetch children if we haven't reached the maximum recursion level
        if resource_type == 'collection':
            if query == '':
                cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId IS NULL AND resourceId=%s ORDER BY FIND_IN_SET(resourceLevel, 'subseries,file'), title ASC", (resource_id))
            else:
                cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId IS NULL AND resourceId=%s AND (title LIKE %s OR persistentID LIKE %s) ORDER BY FIND_IN_SET(resourceLevel, 'subseries,file'), title ASC", (resource_id, '%' + query + '%', '%' + query + '%'))
        else:
            if query == '':
                cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId=%s ORDER BY FIND_IN_SET(resourceLevel, 'subseries,file'), title ASC", (resource_id))
            else:
                cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId=%s AND (title LIKE %s OR persistentID LIKE %s) ORDER BY FIND_IN_SET(resourceLevel, 'subseries,file'), title ASC", (resource_id, '%' + query + '%', '%' + query + '%'))

        rows = cursor.fetchall()

        if (not recurse_max_level) or level < recurse_max_level:
            if len(rows):
                resource_data['children'] = []
                resource_data['has_children'] = True

                for row in rows:
                    resource_data['children'].append(
                        self.get_resource_component_and_children(
                            row[0],
                            'description',
                            level + 1,
                            sort_data
                        )
                    )
        else:
            if len(rows):
                resource_data['children'] = []
                resource_data['has_children'] = True
            else:
                resource_data['children'] = False
                resource_data['has_children'] = False

        return resource_data

    def find_resource_id_for_component(self, component_id):
        """
        Given the ID of a component, returns the parent resource ID.

        If the immediate parent of the component is itself a component, this method will progress up the tree until a resource is found.

        :param long component_id: The ID of the ResourceComponent.
        :return: The ID of the component's parent resource.
        :rtype: long
        """
        cursor = self.db.cursor()

        sql = "SELECT resourceId, parentResourceComponentId FROM ResourcesComponents WHERE resourceComponentId=%s"
        cursor.execute(sql, (component_id,))
        resource_id, parent_id = cursor.fetchone()

        if resource_id is None:
            return self.find_resource_id_for_component(parent_id)
        else:
            return resource_id

    def find_parent_id_for_component(self, component_id):
        """
        Given the ID of a component, returns the parent component's ID.

        :param string component_id: The ID of the component.
        :return: A tuple containing:
            * The type of the parent record; valid values are ArchivesSpaceClient.RESOURCE and ArchivesSpaceClient.RESOURCE_COMPONENT.
            * The ID of the parent record.
        :rtype tuple:
        """
        cursor = self.db.cursor()

        sql = "SELECT parentResourceComponentId FROM ResourcesComponents WHERE resourceComponentId=%s"
        count = cursor.execute(sql, (component_id,))
        if count > 0:
            return (ArchivistsToolkitClient.RESOURCE_COMPONENT, cursor.fetchone())

        return (ArchivistsToolkitClient.RESOURCE, self.find_resource_id_for_component(component_id))

    def find_collection_ids(self, search_pattern='', identifier='', page=None, page_size=30):
        """
        Fetches a list of all resource IDs for every resource in the database.

        :param string search_pattern: A search pattern to use in looking up resources by title or resourceid.
            The search will match any title or resourceid containing this string;
            for example, "text" will match "this title has this text in it".
            If omitted, then all resources will be fetched.
        :param string identifier: Restrict records to only those with this identifier.
            This refers to the human-assigned record identifier, not the automatically generated internal ID.
            Unlike the ArchivesSpaceClient version of this method, wildcards are not supported; however, identifiers which begin or end with this string will be returned.
            For example, if the passed identifier is "A1", then records with an identifier of "A1", "SAA1", "A10", and "SAA10" will all be returned.

        :return: A list containing every matched resource's ID.
        :rtype: list
        """
        cursor = self.db.cursor()

        if search_pattern == '' and identifier == '':
            sql = "SELECT resourceId FROM Resources ORDER BY title"
            params = ()
        else:
            clause = 'resourceid LIKE %s'
            params = ['%' + search_pattern + '%']

            if search_pattern != '':
                clause = 'title LIKE %s OR' + clause
                params.insert(0, '%' + search_pattern + '%')

            if identifier != '':
                clause = 'resourceIdentifier1 LIKE %s OR ' + clause
                params.insert(0, '%' + identifier + '%')

            params = tuple(params)

            sql = "SELECT resourceId FROM Resources WHERE ({}) AND resourceLevel in ('recordgrp', 'collection') ORDER BY title".format(clause)

        if page is not None:
            start = (page - 1) * page_size
            sql = sql + " LIMIT {},{}".format(start, page_size)

        cursor.execute(sql, params)

        return [r[0] for r in cursor]

    def find_by_id(self, object_type, field, value):
        """ Find resource by a specific ID. """
        raise NotImplementedError("Archivist's Toolkit does not implement find_by_id")

    def augment_resource_ids(self, resource_ids):
        """
        Given a list of resource IDs, returns a list of dicts containing detailed information about the specified resources and their children.

        Consult the documentation of ArchivistsToolkitClient.get_resource_component_children for the format of the returned dicts.

        :param list resource_ids: A list of one or more resource IDs.
        :return: A list containing metadata dicts.
        :rtype: list
        """
        resources_augmented = []
        for id in resource_ids:
            resources_augmented.append(
                self.get_resource_component_and_children(id, recurse_max_level=2)
            )

        return resources_augmented

    def count_collections(self, search_pattern='', identifier=''):
        return len(self.find_collection_ids(search_pattern, identifier))

    def find_collections(self, search_pattern='', identifier='', page=1, page_size=30):
        return self.augment_resource_ids(self.find_collection_ids(search_pattern, identifier, page=page, page_size=page_size))

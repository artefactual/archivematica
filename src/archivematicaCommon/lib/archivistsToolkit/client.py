import logging

import MySQLdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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

    def collection_list(self, resource_id, resource_type='collection'):
        """
        Fetches a list of all resource and component IDs within the specified resource.

        :param long resource_id: The ID of the resource to fetch children from.
        :param string resource_type: Specifies whether the resource to fetch is a collection or a child element.
            Defaults to 'collection'.

        :return list: A list of longs representing the database resource IDs for all children of the requested record.
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

        :return dict: A dict containing detailed metadata about both the requested resource and its children.
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
            cursor.execute("SELECT title, dateExpression, resourceIdentifier1 FROM Resources WHERE resourceid=%s", (resource_id))

            for row in cursor.fetchall():
                resource_data['id']                 = resource_id
                resource_data['sortPosition']       = sort_data['position']
                resource_data['title']              = row[0]
                resource_data['dates']              = row[1]
                resource_data['identifier']         = row[2]
                resource_data['levelOfDescription'] = 'collection'
        else:
            cursor.execute("SELECT title, dateExpression, persistentID, resourceLevel FROM ResourcesComponents WHERE resourceComponentId=%s", (resource_id))

            for row in cursor.fetchall():
                resource_data['id']                 = resource_id
                resource_data['sortPosition']       = sort_data['position']
                resource_data['title']              = row[0]
                resource_data['dates']              = row[1]
                resource_data['identifier']         = row[2]
                resource_data['levelOfDescription'] = row[3]

        resource_data['children'] = False

        # fetch children if we haven't reached the maximum recursion level
        if (not recurse_max_level) or level < recurse_max_level:
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

            if len(rows):
                resource_data['children'] = []

                for row in rows:
                    resource_data['children'].append(
                        self.get_resource_component_and_children(
                            row[0],
                            'description',
                            level + 1,
                            sort_data
                        )
                    )

        return resource_data

    def find_resource_id_for_component(self, component_id):
        """
        Given the ID of a component, returns the parent resource ID.

        If the immediate parent of the component is itself a component, this method will progress up the tree until a resource is found.

        :param long component_id: The ID of the ResourceComponent.
        :return long: The ID of the component's parent resource.
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
        :return tuple: A tuple containing:
            * The type of the parent record; valid values are ArchivesSpaceClient.RESOURCE and ArchivesSpaceClient.RESOURCE_COMPONENT.
            * The ID of the parent record.
        """
        cursor = self.db.cursor()

        sql = "SELECT parentResourceComponentId FROM ResourcesComponents WHERE resourceComponentId=%s"
        count = cursor.execute(sql, (component_id,))
        if count > 0:
            return (ArchivistsToolkitClient.RESOURCE_COMPONENT, cursor.fetchone())

        return (ArchivistsToolkitClient.RESOURCE, self.find_resource_id_for_component(component_id))

    def find_collection_ids(self, search_pattern=''):
        """
        Fetches a list of all resource IDs for every collection in the database.

        :param string search_pattern: A search pattern to use in looking up collections by title or resourceid.
            The search will match any title or resourceid containing this string;
            for example, "text" will match "this title has this text in it".
            If omitted, then all collections will be fetched.

        :return list: A list containing every matched collection's ID.
        """
        cursor = self.db.cursor()

        if search_pattern == '':
            sql = "SELECT resourceId FROM Resources WHERE resourceLevel = 'collection' ORDER BY title"
            params = ()
        else:
            sql = "SELECT resourceId FROM Resources WHERE (title LIKE %s OR resourceid LIKE %s) AND resourceLevel in ('recordgrp', 'collection') ORDER BY title"
            params = ('%' + search_pattern + '%', '%' + search_pattern + '%')

        cursor.execute(sql, params)

        return [r[0] for r in cursor]

    def augment_resource_ids(self, resource_ids):
        """
        Given a list of resource IDs, returns a list of dicts containing detailed information about the specified resources and their children.

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

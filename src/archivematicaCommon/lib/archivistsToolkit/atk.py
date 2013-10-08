import MySQLdb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def connect_db(atdbhost, atdbport, atdbuser, atpass, atdb):
    try:
        db = MySQLdb.connect(atdbhost,atdbuser,atpass,atdb)
        logger.debug('connected to db' + atdb)
        return db 
    except Exception:
        logger.error('db error')
        raise

def collection_list(db, resource_id, ret=None, resource_type='collection'):
    if ret is None:
        ret = []
        
    cursor = db.cursor() 
    if resource_type == 'collection':
        cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId IS NULL AND resourceId=%s", (resource_id))
    else:
        ret.append(resource_id)
        cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId=%s", (resource_id))

    rows = cursor.fetchall()
    if len(rows):
        #print ("found children: {}".format(len(rows)))
        for row in rows:
            collection_list(db,row[0],ret,'description')
    
    return ret

def get_resource_children(db, resource_id):
    return get_resource_component_and_children(db, resource_id)

def get_resource_component_children(db, resource_component_id):
    return get_resource_component_and_children(db, resource_component_id, 'resource')

def get_resource_component_and_children(db, resource_id, resource_type='collection', level=1, sort_data={}, **kwargs):
    # we pass the sort position as a dict so it passes by reference and we
    # can use it to share state during recursion

    recurse_max_level = kwargs.get('recurse_max_level', False)
    query             = kwargs.get('search_pattern', '')

    # intialize sort position if this is the beginning of recursion
    if level == 1:
        sort_data['position'] = 0

    sort_data['position'] = sort_data['position'] + 1

    resource_data = {}

    cursor = db.cursor() 

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
                    get_resource_component_and_children(
                        db,
                        row[0],
                        'description',
                        level + 1,
                        sort_data
                    )
                 )

    return resource_data

    """
    Example data:

    return {
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

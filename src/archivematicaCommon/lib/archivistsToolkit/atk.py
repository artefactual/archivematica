import MySQLdb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def connect_db(atdbhost, atdbport, atdbuser, atpass, atdb):
    try:
        db = MySQLdb.connect(atdbhost,atdbuser,atpass,atdb)
        logger.info('connected to db' + atdb)
        return db 
    except Exception:
        logger.error('db error')
        raise

def collection_list(db, resource_id, ret=None, resource_type='collection'):
    if ret is None:
        ret = []
        
    cursor = db.cursor() 
    print "looging for resouce: {}".format(resource_id)
    if resource_type == 'collection':
        cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId IS NULL AND resourceId=%s", (resource_id))
    else:
        ret.append(resource_id)
        cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId=%s", (resource_id))

    rows = cursor.fetchall()
    if len(rows):
        print ("found children: {}".format(len(rows)))
        for row in rows:
            collection_list(db,row[0],ret,'description')
    
    return ret
        
def flatten(d, ret=None):
    if ret is None:
        ret = []
    for k in d['children']:
        if k == 'resourcesComponentsId':
            ret.append(k)
        if k == 'children':
            flatten(v, ret)
    return ret
    
def ingest_upload_atk_get_resource_component_and_children(db, resource_id, resource_type='collection'):
    resource_data = {};

    cursor = db.cursor() 

    if resource_type == 'collection':
        cursor.execute("SELECT title, dateExpression, resourceId FROM Resources WHERE resourceid=%s", (resource_id))

        for row in cursor.fetchall():
            resource_data['title']              = row[0]
            resource_data['dates']              = row[1]
            resource_data['resourceId']         = row[2]
            resource_data['levelOfDescription'] = 'Fonds'
    else:
        cursor.execute("SELECT title, dateExpression, persistentId, resourceLevel, resourceComponentId FROM ResourcesComponents WHERE resourceComponentId=%s", (resource_id))

        for row in cursor.fetchall():
            resource_data['title']              = row[0]
            resource_data['dates']              = row[1]
            resource_data['identifier']         = row[2]
            resource_data['levelOfDescription'] = row[3]
            resource_data['resourcesComponentId'] = row[4]

    resource_data['children'] = False

    if resource_type == 'collection':
        cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId IS NULL AND resourceId=%s", (resource_id))
    else:
        cursor.execute("SELECT resourceComponentId FROM ResourcesComponents WHERE parentResourceComponentId=%s", (resource_id))

    rows = cursor.fetchall()

    if len(rows):
        resource_data['children'] = []

        for row in rows:
            resource_data['children'].append(
                ingest_upload_atk_get_resource_component_and_children(
                    db,
                    row[0],
                    'description'
                )
            )

    return resource_data

    """
    Example data:

    return {
      'identifier': 'PR01',
      'title': 'Parent',
      'levelOfDescription': 'Fonds',
      'dates': '1880-1889',
      'children': [{
        'identifier': 'CH01',
        'title': 'Child A',
        'levelOfDescription': 'Sousfonds',
        'dates': '1880-1888',
        'children': [{
          'identifier': 'GR01',
          'title': 'Grandchild A',
          'levelOfDescription': 'Item',
          'dates': '1880-1888',
          'children': False
        },
        {
          'identifier': 'GR02',
          'title': 'Grandchild B',
          'levelOfDescription': 'Item',
          'children': False
        }]
      },
      {
        'identifier': 'CH02',
        'title': 'Child B',
        'levelOfDescription': 'Sousfonds',
        'dates': '1889',
        'children': False
      }]
    }
    """
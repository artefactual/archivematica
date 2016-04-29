#!/usr/bin/env python2

from argparse import ArgumentParser
from collections import defaultdict
from csv import DictWriter
from glob import iglob
import os
import sys
from uuid import uuid4

from main.models import ArchivesSpaceDOComponent

# archivematicaCommon
from elasticSearchFunctions import getDashboardUUID

from agentarchives.archivesspace import ArchivesSpaceClient


def process_digital_object_components(client, writer, current_location):
    dashboard_uuid = getDashboardUUID()

    component_ids = [os.path.basename(path).split('digital_object_component_')[1] for path in
                     iglob(os.path.join(current_location, 'digital_object_component_*'))]

    components = ArchivesSpaceDOComponent.objects.filter(id__in=component_ids)
    # exit early to avoid the expense of hitting up ASpace
    if components.count() == 0:
        return

    # In most circumstances an AIP being processed will be associated
    # with only a single archival object, but since that isn't guaranteed at
    # the database level let's operate with the assumption this could happen.
    archival_object_map = defaultdict(list)
    for component in components:
        archival_object_map[component.resourceid].append(component)

    for resource_id, components in archival_object_map.iteritems():
        do_id = client.add_digital_object(resource_id, dashboard_uuid, str(uuid4))['id']
        for component in components:
            if component.digitalobjectid:
                continue  # already created

            doc = client.add_digital_object_component(do_id,
                                                      label=component.label,
                                                      title=component.title)
            # Track status about this component having been created for future use
            component.digitalobjectid = do_id
            component.remoteid = doc['id']
            component.save()

            writer.writerow({
                'component_id': component.id,
                'digital_object_component_id': component.remoteid,
            })

            yield 'Created digital object component "{}" associated with record "{}"'.format(doc['id'], resource_id)


def main(current_location, host, port, user, passwd):
    with open(os.path.join(current_location, 'metadata', 'digital_object_components.csv'), 'w') as csvfile:
        writer = DictWriter(csvfile, ['component_id', 'digital_object_component_id'])
        writer.writeheader()

        client = ArchivesSpaceClient(host=host, port=port, user=user, passwd=passwd)

        for message in process_digital_object_components(client, writer, current_location):
            print(message)

        return 0

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--current-location',
                        type=str, help='%SIPDirectory%')
    parser.add_argument('--host', default="localhost",
                        metavar="host", help="hostname of ArchivesSpace")
    parser.add_argument('--port', type=int, default=8089,
                        metavar="port", help="Port used by ArchivesSpace backend API")
    parser.add_argument('--user', metavar="Administrative user")
    parser.add_argument('--passwd', metavar="Administrative user password")

    args = parser.parse_args()

    sys.exit(main(args.current_location, args.host, args.port, args.user, args.passwd))

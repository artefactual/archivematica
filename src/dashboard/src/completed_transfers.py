from django.db import connection
q = ('SELECT t.transferUUID, j.jobType FROM Transfers as t'
     ' INNER JOIN Jobs as j'
     ' ON j.SIPUUID = t.transferUUID'
     ' WHERE t.hidden = 0'
     ' ORDER BY t.transferUUID, j.createdTime, j.createdTimeDec DESC;')
transfers = {}
with connection.cursor() as cursor:
    cursor.execute(q)
    for index, (uuid, job_type) in enumerate(cursor.fetchall()):
        transfers.setdefault(uuid, 'NOT COMPLETE')
        if (    (job_type in ('Create SIP from transfer objects',
                              'Move transfer to backlog')) or
                (index == 0 and
                 job_type == 'Remove the processing directory')):
            transfers[uuid] = 'COMPLETE'

with open('completed_transfers_output.txt', 'w') as fileo:
    for transfer, result in transfers.items():
        fileo.write('{} {}\n'.format(transfer, result))


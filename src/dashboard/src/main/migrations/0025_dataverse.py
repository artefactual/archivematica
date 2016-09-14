# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def data_migration(apps, schema_editor):
    # TEMPORARY
    # TODO Update this so it
    # A) autodetects transfer type OR
    # B) add a Dataverse type that sets postExtractSpecializedProcessing
    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')
    MicroServiceChainLinkExitCode = apps.get_model('main', 'MicroServiceChainLinkExitCode')
    TaskConfig = apps.get_model('main', 'TaskConfig')
    StandardTaskConfig = apps.get_model('main', 'StandardTaskConfig')
    TaskConfigUnitVariableLinkPull = apps.get_model('main', 'TaskConfigUnitVariableLinkPull')

    parse_dataverse_mscl = '830f7002-e644-456b-8cba-fddaad7f1fbf'
    fail_transfer = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd'

    StandardTaskConfig.objects.create(id='7cba173b-a631-4a2f-b49e-0627e779a7ed', requires_output_lock=0, execute='parseDataverse', arguments='%SIPDirectory% %SIPUUID%')
    TaskConfig.objects.create(id='99718d08-8867-42f3-b74c-a75dc8d4c61a', tasktype_id='36b2e239-4a57-4aa5-8ebc-7a29139baca6', tasktypepkreference='7cba173b-a631-4a2f-b49e-0627e779a7ed', description='Parse Dataverse METS')
    MicroServiceChainLink.objects.create(id=parse_dataverse_mscl, microservicegroup='Parse external files', defaultexitmessage='Failed', currenttask_id='99718d08-8867-42f3-b74c-a75dc8d4c61a', defaultnextchainlink_id=fail_transfer)
    MicroServiceChainLinkExitCode.objects.create(id='c28944e8-362c-4db7-858d-f1a10ab0317c', microservicechainlink_id=parse_dataverse_mscl, exitcode=0, nextmicroservicechainlink_id='db99ab43-04d7-44ab-89ec-e09d7bbdc39d', exitmessage='Completed successfully')
    MicroServiceChainLinkExitCode.objects.filter(microservicechainlink_id='8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc').update(nextmicroservicechainlink_id=parse_dataverse_mscl)
    # Update default MCL for postExtractSpecializedProcessing to point at dataverse parsing
    TaskConfigUnitVariableLinkPull.objects.filter(id='49d853a9-646d-4e9f-b825-d1bcc3ba77f0').update(defaultmicroservicechainlink_id=parse_dataverse_mscl)

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0024_agent_m2m_event'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]

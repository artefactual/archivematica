# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def data_migration(apps, schema_editor):
    MicroServiceChain = apps.get_model('main', 'MicroServiceChain')
    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')
    MicroServiceChainLinkExitCode = apps.get_model('main', 'MicroServiceChainLinkExitCode')
    TaskConfig = apps.get_model('main', 'TaskConfig')
    StandardTaskConfig = apps.get_model('main', 'StandardTaskConfig')
    MicroServiceChainChoice = apps.get_model('main', 'MicroServiceChainChoice')

    # Create new Upload to Binder chain

    # Add copy to NetX link
    StandardTaskConfig.objects.create(id='5b4b5329-c19c-4120-a7d7-290ff8e3410f', requires_output_lock=0, execute='copyToNetX_v0.0', arguments='--uuid %SIPUUID%')

    TaskConfig.objects.create(id='a498e816-b263-4dda-8592-8e232509730e', tasktype_id='36b2e239-4a57-4aa5-8ebc-7a29139baca6', tasktypepkreference='5b4b5329-c19c-4120-a7d7-290ff8e3410f', description='Copy DIP to NetX')

    MicroServiceChainLink.objects.create(id='7f4e18eb-cf37-418b-b6db-d6f4e0aa9c27', microservicegroup='Upload DIP', defaultexitmessage='Failed', currenttask_id='a498e816-b263-4dda-8592-8e232509730e', defaultnextchainlink_id='e3efab02-1860-42dd-a46c-25601251b930')

    MicroServiceChainLinkExitCode.objects.create(id='4facf5ea-b0fe-4374-8651-1fa3f9ac0bb8', microservicechainlink_id='7f4e18eb-cf37-418b-b6db-d6f4e0aa9c27', exitcode=0, nextmicroservicechainlink_id='e3efab02-1860-42dd-a46c-25601251b930', exitmessage='Completed successfully')

    # Add chain that does a copy to NetX
    MicroServiceChain.objects.create(id='f79080c5-f9a5-4b05-9d13-3880015c6f02', startinglink_id='7f4e18eb-cf37-418b-b6db-d6f4e0aa9c27', description='Copy DIP to NetX', replaces=None)

    # Add chain that doesn't copy to NetX
    MicroServiceChain.objects.create(id='3eee99e4-2532-43ec-bc5f-3c021182b265', startinglink_id='e3efab02-1860-42dd-a46c-25601251b930', description='No Copy to NetX', replaces=None)

    # Add chain choice link and options
    TaskConfig.objects.create(id='52553a08-1c1d-4efa-baf9-d57698608c8a', tasktype_id='61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', tasktypepkreference='6ddac748-a6ec-410f-b5c1-89712bb0c2a3', description='Upload to NetX?')
    MicroServiceChainLink.objects.create(id='884fc8aa-b1dc-484a-8ecc-abe828e04b89', microservicegroup='Upload DIP', defaultexitmessage='Failed', currenttask_id='52553a08-1c1d-4efa-baf9-d57698608c8a', defaultnextchainlink_id='e3efab02-1860-42dd-a46c-25601251b930')
    MicroServiceChainChoice.objects.create(id='db70f543-26e1-4505-8d9f-0003e7ef2359', choiceavailableatlink_id='884fc8aa-b1dc-484a-8ecc-abe828e04b89', chainavailable_id='f79080c5-f9a5-4b05-9d13-3880015c6f02', replaces=None)
    MicroServiceChainChoice.objects.create(id='ca8a274f-deb0-4ab4-8b2b-8bf88f08fbe3', choiceavailableatlink_id='884fc8aa-b1dc-484a-8ecc-abe828e04b89', chainavailable_id='3eee99e4-2532-43ec-bc5f-3c021182b265', replaces=None)

    # Add upload to AtoM MSCL for Binder chain
    MicroServiceChainLink.objects.create(id='28479bb3-0de8-45c2-96a1-f303f7b4ab9d', microservicegroup='Upload DIP', defaultexitmessage='Failed', currenttask_id='7058a655-82f3-455c-9245-ad8e87e77a4f', defaultnextchainlink_id='884fc8aa-b1dc-484a-8ecc-abe828e04b89')
    MicroServiceChainLinkExitCode.objects.create(id='04a1751d-5249-43ef-bffd-7c371b01c04d', microservicechainlink_id='28479bb3-0de8-45c2-96a1-f303f7b4ab9d', exitcode=0, nextmicroservicechainlink_id='884fc8aa-b1dc-484a-8ecc-abe828e04b89', exitmessage='Completed successfully')

    # Add Upload to Binder chain & chainchoice
    MicroServiceChain.objects.create(id='7e5f3f3b-2f99-4488-898d-c5e1dea32562', startinglink_id='28479bb3-0de8-45c2-96a1-f303f7b4ab9d', description='Upload DIP to Binder', replaces=None)
    MicroServiceChainChoice.objects.create(id='6105dcd7-e193-4b6d-bdc0-6d71b0f38a88', choiceavailableatlink_id='92879a29-45bf-4f0b-ac43-e64474f0f2f9', chainavailable_id='7e5f3f3b-2f99-4488-898d-c5e1dea32562', replaces=None)

    # MOMA CUSTOMIZATION - Normalization failures, issue 6845
    # Find ExitCodes where the return value is 1 (rule failed) and the associated MSCL is a Normalize link
    # Updated to be a 'Failed' exit message
    MicroServiceChainLinkExitCode.objects.filter(microservicechainlink__currenttask__description__startswith='Normalize').filter(exitcode=1).update(exitmessage='Failed')


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_full_reingest'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]

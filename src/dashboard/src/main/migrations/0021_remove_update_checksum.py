# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')
    MicroServiceChainLinkExitCode = apps.get_model('main', 'MicroServiceChainLinkExitCode')
    TaskConfig = apps.get_model('main', 'TaskConfig')
    StandardTaskConfig = apps.get_model('main', 'StandardTaskConfig')

    # Change MSCLEC MSCL pointers to point to successor of updateSizeAndChecksum micro-service

    next_msclecs = ['f0f64c7e-30fa-47c1-9877-43955680c0d0', 'cb48ef2a-3394-4936-af1f-557b39620efa', \
                    '5e4bd4e8-d158-4c2a-be89-51e3e9bd4a06', '10c40e41-fb10-48b5-9d01-336cd958afe8', \
                    '7c6a0b72-f37b-4512-87f3-267644de6f80', '11033dbd-e4d4-4dd6-8bcf-48c424e222e3', \
                    'b21018df-f67d-469a-9ceb-ac92ac68654e', '8c8bac29-4102-4fd2-9d0a-a3bd2e607566']

    previous_msclecs = ['88a36d00-af47-4845-8bcf-a72529ae78f8', '800259c7-f6d2-4ac6-af69-07985f23efec', \
                        '1462359e-72c8-467f-b08a-02e4e3dfede1', 'e090fea3-2e44-4dd9-b17d-73c4d2088e0c', \
                        '8bec6c39-8b98-4e2c-9a91-f7a9c8130f2e', '18db3a8a-ee5f-47c2-b5a7-7d223c3023c0', \
                        '4de0e894-8eda-49eb-a915-124b4f6c3608', '5e481248-543b-463d-b0a4-eee87c79e71f']

    for prev_msclec in previous_msclecs:
        for next_msclec in next_msclecs:
            MicroServiceChainLinkExitCode.objects.filter(microservicechainlink_id=prev_msclec).update(nextmicroservicechainlink_id=next_msclec)

    # Delete all MSCLECs corresponding to updateSizeAndChecksum
    msclecs_delete = ['c4c7ff3c-3eef-42e3-a68d-f11ca3e7c6dd', 'ea5b8e14-519e-473b-818c-e62879559816', \
                      'd5690bcf-1c0f-44a1-846e-e63cea2b9087', '5cd0e0ee-75a1-419f-817c-4edd6adce857', \
                      'ad09d973-5c5d-44e9-84a2-a7dbb27dd23d', 'fe188831-76b3-4487-8712-5d727a50e8ce', \
                      'a0f33c59-081b-4427-b430-43b811cf0594', 'e0d9e83b-89e1-4711-89e4-14dbe15bea4c']
    for msclec in msclecs_delete:
        MicroServiceChainLinkExitCode.objects.filter(pk=msclec).delete()

    # Delete all MSCLs corresponding to updateSizeAndChecksum
    mscls_delete = ['c77fee8c-7c4e-4871-a72e-94d499994869', 'd2035da2-dfe1-4a56-8524-84d5732fd3a3', \
                    '28a9f8a8-0006-4828-96d5-892e6e279f72', 'e76aec15-5dfa-4b14-9405-735863e3a6fa', \
                    '2714cd07-b99f-40e3-9ae8-c97281d0d429', '5bd51fcb-6a68-4c5f-b99e-4fc36f51c40c', \
                    'bd9769ba-4182-4dd4-ba85-cff24ea8733e']
    for mscl in mscls_delete:
        MicroServiceChainLink.objects.filter(pk=mscl).delete()

    # Delete all TaskConfigs corresponding to updateSizeAndChecksum
    tcs__delete = ['6405c283-9eed-410d-92b1-ce7d938ef080', '1c7de28f-8f18-41c7-b03a-19f900d38f34', \
                   'ded09ddd-2deb-4d62-bfe3-84703f60c522', 'bf5a1f0c-1b3e-4196-b51f-f6d509091346', \
                   'abeaa79e-668b-4de0-b8cb-70f8ab8056b6', '5bd51fcb-6a68-4c5f-b99e-4fc36f51c40c', \
                   'bd9769ba-4182-4dd4-ba85-cff24ea8733e']
    for tc in tcs__delete:
        TaskConfig.objects.filter(pk=tc).delete()

    # Delete all StandardTaskConfigs corresponding to updateSizeAndChecksum
    stcs_delete = ['c06ecc19-8f75-4ccf-a549-22fde3972f28', '0bdecdc8-f5ef-48dd-8a89-f937d2b3f2f9', \
                   '45df6fd4-9200-4ec7-bd31-ba0338c07806', 'c8f93c3d-b078-428d-bd53-1b5789cde598', \
                   'e377b543-d9b8-47a9-8297-4f95ca7600b3', 'ec54a7cb-690f-4dd6-ad2b-979ae9f8d25a']
    for stc in stcs_delete:
        StandardTaskConfig.objects.filter(pk=stc).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_remove_unneeded_files_speedup'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]

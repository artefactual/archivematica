# -*- coding: utf-8 -*-
"""Migration for adding end states after Store DIP decision."""

from __future__ import print_function, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """This migration modifies the workflow so that all Upload-DIP-type chain
    links exit directly to the "Move to the uploadedDIPs directory" chain link.
    This is needed in order to allow processing configuration of the subsequent
    choice "Store DIP?". This is because if the DIP/SIP is moved to the
    uploadedDIPs directory before the "Store DIP?" choice, then the MCPServer
    does not know where the DIP is when it goes to look for the
    processingMCP.xml config file.

    Steps:

    1. Set upload DIP-type links to exit to "Store DIP?"
    2. Set subsequent "Store DIP" and "Completed" links to exit to "Move to the
       Uploaded DIPs directory" link.
    """

    ###########################################################################
    # Model Classes
    ###########################################################################

    MicroServiceChainLink = apps.get_model(
        'main', 'MicroServiceChainLink')
    MicroServiceChainLinkExitCode = apps.get_model(
        'main', 'MicroServiceChainLinkExitCode')
    StandardTaskConfig = apps.get_model(
        'main', 'StandardTaskConfig')

    ###########################################################################
    # Useful Model Instances
    ###########################################################################

    move_uploaded_dir_link_uuid = '2e31580d-1678-474b-83e5-a53d97d150f6'

    # These need to stop exiting to the above and start exiting to the below.
    upload_as_link_uuid = 'ff89a530-0540-4625-8884-5a2198dea05a'  # ArchiveSpace
    upload_at_link_uuid = 'bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1'  # Archivists Toolkit
    upload_cdb_link_uuid = 'f12ece2c-fb7e-44de-ba87-7e3c5b6feb74'  # ContentDM
    upload_a_link_uuid = '651236d2-d77f-4ca7-bfe9-6332e96608ff'  # Atom
    upload_links = (upload_as_link_uuid,
                    upload_at_link_uuid,
                    upload_cdb_link_uuid,
                    upload_a_link_uuid)

    store_dip_question_link_uuid = '5e58066d-e113-4383-b20b-f301ed4d751c'

    # These need to exit to the first (i.e., ``move_uploaded_dir_link_uuid``)
    store_dip_link_uuid = '653b134f-4a37-4578-a286-7f2072e89f9e'
    completed_link_uuid = 'f8ee488b-5667-4417-ae15-bed9e42ee97d'
    leaves = (store_dip_link_uuid, completed_link_uuid)

    # The StandardTaskConfig UUID for the "Store DIP" link. Will need a minor
    # mod.
    store_dip_stc_uuid = '1e4ccd56-a076-4aa2-9642-1ed8944b306a'

    ###########################################################################
    # 1. Set upload DIP-type links to exit to "Store DIP?"
    ###########################################################################

    MicroServiceChainLinkExitCode.objects\
        .filter(microservicechainlink_id__in=upload_links)\
        .update(nextmicroservicechainlink_id=store_dip_question_link_uuid)
    MicroServiceChainLink.objects\
        .filter(id__in=upload_links)\
        .update(defaultnextchainlink_id=store_dip_question_link_uuid)

    ###########################################################################
    # 2. Set "Store DIP" and "Completed" exit to "Move to the Uploaded ..."
    ###########################################################################

    MicroServiceChainLinkExitCode.objects\
        .filter(microservicechainlink_id__in=leaves)\
        .update(nextmicroservicechainlink_id=move_uploaded_dir_link_uuid)

    # Also delete any paths exiting from the "Move to the uploadedDIPs
    # directory" since we want it to be an end state.
    MicroServiceChainLinkExitCode.objects\
        .filter(microservicechainlink_id=move_uploaded_dir_link_uuid)\
        .delete()

    # Next, create an exit code for the final state that returns an
    # ``exitMessage`` of ``2``, which means "Completed successfully".
    MicroServiceChainLinkExitCode.objects.create(
        id='f8e6ddf9-0485-4fab-928e-d2a286663811',
        exitcode=0,
        exitmessage=2,
        microservicechainlink_id=move_uploaded_dir_link_uuid,
        nextmicroservicechainlink=None,
        replaces=None)

    # Finally, update the arguments to the "Create DIP" task config so that it
    # knows to look for the DIP in the uploadDIP/ directory rather than the
    # uploadedDIPs/ directory.
    StandardTaskConfig.objects\
        .filter(id=store_dip_stc_uuid)\
        .update(
            arguments=('"%DIPsStore%" '
                       '"%watchDirectoryPath%uploadDIP/%SIPName%-%SIPUUID%" '
                       '"%SIPUUID%" '
                       '"%SIPName%" '
                       '"DIP"'))


class Migration(migrations.Migration):

    dependencies = [('main', '0035_fix_workflow_dip_generation')]
    operations = [migrations.RunPython(data_migration)]

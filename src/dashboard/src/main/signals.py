from django.db.models.signals import post_delete
from django.dispatch import receiver

from main.models import RightsStatementRightsGranted, RightsStatement


@receiver(post_delete, sender=RightsStatementRightsGranted)
def delete_rights_statement(sender, **kwargs):
    """
    Delete a RightsStatement if it has no RightsGranted.

    Rights are displayed in the GUI based on their RightsGranted, but the RightsStatement tracks their reingest status.
    When a RightsGranted is deleted, also delete the RightsStatement if this was the last RightsGranted.
    """
    instance = kwargs.get('instance')
    try:
        # If the statement has no other RightsGranted delete the RightsStatement
        if not instance.rightsstatement.rightsstatementrightsgranted_set.all():
            instance.rightsstatement.delete()
    except RightsStatement.DoesNotExist:
        # The RightsGranted is being deleted as part of a cascasde delete from the RightsStatement
        pass

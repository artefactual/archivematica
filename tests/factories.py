"""Factories of the database rows that the tests create with their own data.

The defaults of each factory describe the plainest object of its model, and the
keyword arguments override any field, including the ones the factory derives.
The fixtures of the same name build on the factories and add what a complete
object needs, for example the ``transfer`` fixture also records the user as the
active agent of the transfer.
"""

from collections.abc import Iterable

from django.utils import timezone

from archivematica.dashboard.main import models

Unit = models.Transfer | models.SIP


class TransferFactory:
    """Creates transfers at the transfer directory placeholder."""

    def __call__(self, **fields: object) -> models.Transfer:
        defaults: dict[str, object] = {"currentlocation": r"%transferDirectory%"}

        return models.Transfer.objects.create(**{**defaults, **fields})


class SIPFactory:
    """Creates SIPs at the SIP directory placeholder."""

    def __call__(self, **fields: object) -> models.SIP:
        defaults: dict[str, object] = {"currentpath": r"%SIPDirectory%"}

        return models.SIP.objects.create(**{**defaults, **fields})


class FileFactory:
    """Creates the files of a transfer and/or a SIP from their paths relative
    to the unit directory.

    A file lives in the SIP directory when it has a SIP and in the transfer
    directory otherwise. The original files of a transfer keep their transfer
    location as their original location, every other file was created where it
    lives; ``origin`` is the path of the original location when it differs from
    the current one.
    """

    def __call__(
        self,
        path: str,
        /,
        *,
        transfer: models.Transfer | None = None,
        sip: models.SIP | None = None,
        origin: str | None = None,
        **fields: object,
    ) -> models.File:
        filegrpuse = fields.get("filegrpuse", "original")
        current_prefix = r"%SIPDirectory%" if sip else r"%transferDirectory%"
        original_prefix = (
            r"%transferDirectory%"
            if transfer and filegrpuse == "original"
            else current_prefix
        )
        defaults: dict[str, object] = {
            "transfer": transfer,
            "sip": sip,
            "filegrpuse": filegrpuse,
            "originallocation": f"{original_prefix}{origin or path}".encode(),
            "currentlocation": f"{current_prefix}{path}".encode(),
        }

        return models.File.objects.create(**{**defaults, **fields})


class JobFactory:
    """Creates the jobs of a unit, created now and in the unknown step."""

    def __call__(self, unit: Unit | None = None, /, **fields: object) -> models.Job:
        defaults: dict[str, object] = {"createdtime": timezone.now()}
        if unit is not None:
            defaults["sipuuid"] = unit.pk
            defaults["unittype"] = (
                "unitSIP" if isinstance(unit, models.SIP) else "unitTransfer"
            )

        return models.Job.objects.create(**{**defaults, **fields})


class TaskFactory:
    """Creates the tasks of a job, created now."""

    def __call__(self, job: models.Job, /, **fields: object) -> models.Task:
        defaults: dict[str, object] = {"job": job, "createdtime": timezone.now()}

        return models.Task.objects.create(**{**defaults, **fields})


class EventFactory:
    """Creates the PREMIS events of a file, linked to the given agents."""

    def __call__(
        self,
        file: models.File,
        event_type: str,
        /,
        *,
        agents: Iterable[models.Agent] = (),
        **fields: object,
    ) -> models.Event:
        defaults: dict[str, object] = {"file_uuid": file, "event_type": event_type}
        result = models.Event.objects.create(**{**defaults, **fields})
        result.agents.add(*agents)

        return result


class RightsStatementFactory:
    """Creates the rights statements of files and units, and their grants."""

    def __init__(self, types: dict[str, models.MetadataAppliesToType]) -> None:
        self.types = types

    def __call__(
        self, applies_to: str, identifier: object, /, **fields: object
    ) -> models.RightsStatement:
        """A rights statement of the file, transfer or SIP with the identifier."""
        defaults: dict[str, object] = {
            "metadataappliestotype": self.types[applies_to],
            "metadataappliestoidentifier": str(identifier),
        }

        return models.RightsStatement.objects.create(**{**defaults, **fields})

    def grant(
        self,
        statement: models.RightsStatement,
        act: str,
        /,
        *,
        restriction: str | None = None,
        notes: Iterable[str] = (),
        **fields: object,
    ) -> models.RightsStatementRightsGranted:
        """A right granted by the statement, with its restriction and notes."""
        defaults: dict[str, object] = {"rightsstatement": statement, "act": act}
        result = models.RightsStatementRightsGranted.objects.create(
            **{**defaults, **fields}
        )
        if restriction is not None:
            models.RightsStatementRightsGrantedRestriction.objects.create(
                rightsgranted=result, restriction=restriction
            )
        for note in notes:
            models.RightsStatementRightsGrantedNote.objects.create(
                rightsgranted=result, rightsgrantednote=note
            )

        return result


class DublinCoreFactory:
    """Creates the Dublin Core metadata of files and units."""

    def __init__(self, types: dict[str, models.MetadataAppliesToType]) -> None:
        self.types = types

    def __call__(
        self, applies_to: str, identifier: object, /, **fields: object
    ) -> models.DublinCore:
        """The Dublin Core metadata of the file, transfer or SIP with the identifier."""
        defaults: dict[str, object] = {
            "metadataappliestotype": self.types[applies_to],
            "metadataappliestoidentifier": str(identifier),
        }

        return models.DublinCore.objects.create(**{**defaults, **fields})

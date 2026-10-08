import pytest

from archivematica.dashboard.fpr.forms import FPRuleForm
from archivematica.dashboard.fpr.forms import IDToolForm
from archivematica.dashboard.fpr.models import Format
from archivematica.dashboard.fpr.models import FormatGroup
from archivematica.dashboard.fpr.models import FormatVersion
from archivematica.dashboard.fpr.models import FPCommand
from archivematica.dashboard.fpr.models import FPRule


@pytest.mark.django_db
def test_id_tool_form_rejects_duplicate_description_and_version() -> None:
    data = {"description": "Foobar", "version": "v1.2.3"}
    form = IDToolForm(data)
    assert form.is_valid()
    form.save()

    # Our second attempt should not validate.
    form = IDToolForm(data)

    assert not form.is_valid()
    assert form.non_field_errors() == [
        "An ID tool with this description and version already exists"
    ]


@pytest.fixture
def fprule(db: None) -> FPRule:
    fmt_group = FormatGroup.objects.create(description="My group")
    fmt = Format.objects.create(
        uuid="b99dcf12-f28a-4aa3-8fc7-8a6fc2c67b61",
        description="My format",
        group=fmt_group,
    )
    fmt_version = FormatVersion.objects.create(
        uuid="1f628739-d670-487e-9658-8229837e4d2b",
        format=fmt,
        version="v1.2.3",
        description="My format version",
    )
    cmd = FPCommand.objects.create(uuid="223a24cd-6697-4361-b8e7-72d081319a84")

    return FPRule.objects.create(
        uuid="37f3bd7c-bb24-4899-b7c4-785ff1c764ac",
        purpose="validation",
        format=fmt_version,
        command=cmd,
    )


def test_fprule_form_rejects_identical_rule(fprule: FPRule) -> None:
    form = FPRuleForm(
        {
            "purpose": fprule.purpose,
            "format": fprule.format.uuid,
            "command": fprule.command.uuid,
        }
    )

    assert not form.is_valid()
    assert form.non_field_errors() == [
        f"An identical FP rule already exists. See rule {fprule.uuid}."
    ]

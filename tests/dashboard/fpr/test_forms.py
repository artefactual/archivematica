import pytest

from archivematica.dashboard.fpr.forms import FPRuleForm
from archivematica.dashboard.fpr.forms import IDToolForm
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


@pytest.mark.django_db
def test_fprule_form_rejects_identical_rule(fprule_validation: FPRule) -> None:
    form = FPRuleForm(
        {
            "purpose": fprule_validation.purpose,
            "format": fprule_validation.format.uuid,
            "command": fprule_validation.command.uuid,
        }
    )

    assert not form.is_valid()
    assert form.non_field_errors() == [
        f"An identical FP rule already exists. See rule {fprule_validation.uuid}."
    ]

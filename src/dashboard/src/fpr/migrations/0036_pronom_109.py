import os

from django.core.management import call_command
from django.db import migrations


def data_migration(apps, schema_editor):
    fixture_file = os.path.join(os.path.dirname(__file__), "pronom_109.json")
    call_command("loaddata", fixture_file, app_label="fpr")

    Format = apps.get_model("fpr", "Format")

    Format.objects.filter(uuid="618739c5-fe0a-4728-883f-0c3ed27f1bd9").update(
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf"
    )

    Format.objects.filter(uuid="376dbe02-6986-4ec5-b643-947ac7ad948d").update(
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf"
    )

    Format.objects.filter(uuid="f8a74cb2-3035-4359-9b86-33dc68809acc").update(
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf"
    )

    Format.objects.filter(uuid="fe82092a-2d87-4e3a-b4d6-02fa394a261a").update(
        group_id="b1aab542-cc95-4eef-96e9-1a8c09196f73"
    )

    Format.objects.filter(uuid="38f38ac3-c985-4864-974d-0ed239ec3fc6").update(
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf"
    )

    Format.objects.filter(uuid="3be95ba5-581f-4002-924b-18b502e2a5f1").update(
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e"
    )

    Format.objects.filter(uuid="781f315e-cd6a-4d8e-a8ac-301b897fd954").update(
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e"
    )

    Format.objects.filter(uuid="46496986-d7a5-4671-b192-e2e08ab227e7").update(
        group_id="901b79ad-4107-42f8-93d6-a28b631ada05"
    )

    Format.objects.filter(uuid="6e828574-c3a6-4c8b-a1e1-b6ef89919592").update(
        group_id="901b79ad-4107-42f8-93d6-a28b631ada05"
    )

    Format.objects.filter(uuid="2b6660e8-22b0-4548-b234-683848e5a8c5").update(
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf"
    )

    Format.objects.filter(uuid="f689631e-c032-4de5-a412-31a221e9fdc9").update(
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf"
    )

    Format.objects.filter(uuid="5c6e0640-4290-435c-8ef2-ccaba6f28ac0").update(
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf"
    )

    Format.objects.filter(uuid="e1a0ebc4-c771-4ddc-ba7a-6195d617be0a").update(
        group_id="901b79ad-4107-42f8-93d6-a28b631ada05"
    )

    Format.objects.filter(uuid="d75fdc87-7cb9-40c8-88eb-e0bb729efb5e").update(
        group_id="901b79ad-4107-42f8-93d6-a28b631ada05"
    )


class Migration(migrations.Migration):
    dependencies = [("fpr", "0035_python3_compatibility")]

    operations = [migrations.RunPython(data_migration)]

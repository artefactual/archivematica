from django.db import migrations


def data_migration_up(apps, schema_editor):
    Format = apps.get_model("fpr", "Format")
    FormatVersion = apps.get_model("fpr", "FormatVersion")
    IDRule = apps.get_model("fpr", "IDRule")

    Format.objects.create(
        description="""CityGML File""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="ea978711-b3f5-430f-bcd3-f041cc808eca",
    )
    FormatVersion.objects.create(
        format_id="ea978711-b3f5-430f-bcd3-f041cc808eca",
        pronom_id="fmt/2040",
        description="""CityGML File""",
        version="1.0",
        uuid="5d3ed9eb-5e95-41d4-acdf-358154ecba9e",
    )
    IDRule.objects.filter(command_output=".gml").delete()

    Format.objects.create(
        description="""Android Package File""",
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf",
        uuid="90d6ead2-de93-43b2-976f-63058f3d2f8d",
    )
    FormatVersion.objects.create(
        format_id="90d6ead2-de93-43b2-976f-63058f3d2f8d",
        pronom_id="fmt/2041",
        description="""Android Package File""",
        version="None",
        uuid="a20a4184-7db0-4ea1-8597-9a7345c949b5",
    )
    IDRule.objects.create(
        format_id="a20a4184-7db0-4ea1-8597-9a7345c949b5",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".apk",
    )

    Format.objects.create(
        description="""Android App Bundle File""",
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf",
        uuid="9a076928-917d-4c3f-be68-010068293d57",
    )
    FormatVersion.objects.create(
        format_id="9a076928-917d-4c3f-be68-010068293d57",
        pronom_id="fmt/2042",
        description="""Android App Bundle File""",
        version="None",
        uuid="659f2a2c-f7e9-44f0-a088-66808a4cfb3c",
    )
    IDRule.objects.create(
        format_id="659f2a2c-f7e9-44f0-a088-66808a4cfb3c",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".aab",
    )

    Format.objects.create(
        description="""Android Archive File""",
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf",
        uuid="e73d6f29-a2ad-40de-8170-ee13d2c2b92a",
    )
    FormatVersion.objects.create(
        format_id="e73d6f29-a2ad-40de-8170-ee13d2c2b92a",
        pronom_id="fmt/2043",
        description="""Android Archive File""",
        version="None",
        uuid="eb3f0de1-bdd0-4e90-a983-cc52cb39ddcd",
    )
    IDRule.objects.create(
        format_id="eb3f0de1-bdd0-4e90-a983-cc52cb39ddcd",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".aar",
    )

    FormatVersion.objects.create(
        format_id="1a5bf0b8-8d9a-43c2-8517-6de08f396626",
        pronom_id="fmt/2044",
        description="""OpenDocument Text""",
        version="1.4",
        uuid="1db41344-0bd9-4995-a1c1-6aa53abfba21",
    )
    IDRule.objects.filter(command_output=".odt").delete()

    FormatVersion.objects.create(
        format_id="39dbbf34-0035-4379-8e06-7d505a536658",
        pronom_id="fmt/2045",
        description="""OpenDocument Spreadsheet""",
        version="1.4",
        uuid="b71ff446-3f33-4a23-90cf-466c5f551373",
    )
    IDRule.objects.filter(command_output=".ods").delete()

    FormatVersion.objects.create(
        format_id="6ef95e39-3f60-4817-89c7-a96d2e73b0ca",
        pronom_id="fmt/2046",
        description="""OpenDocument Presentation""",
        version="1.4",
        uuid="88af6521-bf2d-438e-8213-3c5db992e5ec",
    )
    IDRule.objects.filter(command_output=".odp").delete()

    Format.objects.create(
        description="""OpenDocument Database""",
        group_id="7d161ac1-2879-445d-8e6d-cbc9eff5c225",
        uuid="d1350133-dae8-4ada-872c-86eca1b065da",
    )
    FormatVersion.objects.create(
        format_id="d1350133-dae8-4ada-872c-86eca1b065da",
        pronom_id="fmt/2047",
        description="""OpenDocument Database""",
        version="1.4",
        uuid="17698810-ad2f-4fc9-aadb-406de599e44c",
    )
    IDRule.objects.filter(command_output=".odb").delete()

    FormatVersion.objects.create(
        format_id="454e0424-a133-415b-ab0f-51f2986f44b4",
        pronom_id="fmt/2048",
        description="""OpenDocument Graphics""",
        version="1.4",
        uuid="49c12395-9ac5-4aca-ae5f-9d702ac43891",
    )
    IDRule.objects.filter(command_output=".odg").delete()

    Format.objects.create(
        description="""ArcGIS Pro Layer File""",
        group_id="e8d06de7-f66c-4792-b7d4-3f17a22ab313",
        uuid="e03306c8-9cbc-4905-9c5d-3b67aa5852a4",
    )
    FormatVersion.objects.create(
        format_id="e03306c8-9cbc-4905-9c5d-3b67aa5852a4",
        pronom_id="fmt/2049",
        description="""ArcGIS Pro Layer File""",
        version="None",
        uuid="6bad5012-6cf9-4842-818d-73f4e7e011bb",
    )
    IDRule.objects.create(
        format_id="6bad5012-6cf9-4842-818d-73f4e7e011bb",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".lyrx",
    )

    Format.objects.create(
        description="""PDF/UA Portable Document Format""",
        group_id="df5d5107-c803-48ba-844d-feba093a571c",
        uuid="ee182278-380e-4842-95c9-c4e7c6828810",
    )
    FormatVersion.objects.create(
        format_id="ee182278-380e-4842-95c9-c4e7c6828810",
        pronom_id="fmt/2050",
        description="""PDF/UA-1""",
        version="1",
        uuid="241f84b1-c6fa-4072-aa91-492659e0aacf",
    )
    IDRule.objects.filter(command_output=".pdf").delete()

    FormatVersion.objects.create(
        format_id="ee182278-380e-4842-95c9-c4e7c6828810",
        pronom_id="fmt/2052",
        description="""PDF/UA-2""",
        version="2",
        uuid="3cccbf23-7992-437c-9847-e7ebfdf84cbe",
    )
    IDRule.objects.create(
        format_id="3cccbf23-7992-437c-9847-e7ebfdf84cbe",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".pdf",
    )

    Format.objects.create(
        description="""Cineon""",
        group_id="be86edbf-f62c-431f-b549-300d23c7cd0d",
        uuid="235c6b34-52da-4b94-a828-1e64a2d02b56",
    )
    FormatVersion.objects.create(
        format_id="235c6b34-52da-4b94-a828-1e64a2d02b56",
        pronom_id="fmt/2051",
        description="""Cineon""",
        version="None",
        uuid="db21d57e-6b8f-422b-93bd-e9ccd77ac35e",
    )
    IDRule.objects.filter(command_output=".cin").delete()

    Format.objects.create(
        description="""Apache Arrow IPC Format""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="792d0b72-36b1-4a46-80bb-2755aa0eb37d",
    )
    FormatVersion.objects.create(
        format_id="792d0b72-36b1-4a46-80bb-2755aa0eb37d",
        pronom_id="fmt/2053",
        description="""Apache Arrow IPC Format""",
        version="None",
        uuid="82c96eb3-727d-4a7d-a4d9-2982e2514f26",
    )
    IDRule.objects.create(
        format_id="82c96eb3-727d-4a7d-a4d9-2982e2514f26",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".arrow",
    )

    Format.objects.create(
        description="""JSON Lines Text Format""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="f8e0a845-80a9-4c49-a56c-f0d062044fae",
    )
    FormatVersion.objects.create(
        format_id="f8e0a845-80a9-4c49-a56c-f0d062044fae",
        pronom_id="fmt/2054",
        description="""JSON Lines Text Format""",
        version="None",
        uuid="281654f7-bca2-4246-beaa-f436eb1ba7ca",
    )
    IDRule.objects.create(
        format_id="281654f7-bca2-4246-beaa-f436eb1ba7ca",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".jsonl",
    )

    Format.objects.create(
        description="""Apple Mail EMLX Format""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="2e212c65-5089-4404-b258-22ded7700926",
    )
    FormatVersion.objects.create(
        format_id="2e212c65-5089-4404-b258-22ded7700926",
        pronom_id="fmt/2055",
        description="""Apple Mail EMLX Format""",
        version="None",
        uuid="e43f78aa-3812-4918-8fda-7195277d16fa",
    )
    IDRule.objects.create(
        format_id="e43f78aa-3812-4918-8fda-7195277d16fa",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".emlx",
    )

    Format.objects.create(
        description="""Immersive Audio Model Format""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="b46ff079-af49-4dd9-9a9d-ad707c5007bb",
    )
    FormatVersion.objects.create(
        format_id="b46ff079-af49-4dd9-9a9d-ad707c5007bb",
        pronom_id="fmt/2056",
        description="""Immersive Audio Model Format""",
        version="None",
        uuid="ab621c7f-25fa-4d46-bfa7-0c264a9d3017",
    )
    IDRule.objects.create(
        format_id="ab621c7f-25fa-4d46-bfa7-0c264a9d3017",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".iamf",
    )

    Format.objects.create(
        description="""A2R Disk Image File""",
        group_id="3616a69f-e9c4-4357-b366-57082cf75a3e",
        uuid="c5d4b021-e54d-4e57-8e7f-6a96c5393bde",
    )
    FormatVersion.objects.create(
        format_id="c5d4b021-e54d-4e57-8e7f-6a96c5393bde",
        pronom_id="fmt/2057",
        description="""A2R Disk Image File v.2 (little endian)""",
        version="2",
        uuid="7d948aa0-a61f-45a3-a9ef-aa3348b686de",
    )
    IDRule.objects.create(
        format_id="7d948aa0-a61f-45a3-a9ef-aa3348b686de",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".a2r",
    )

    FormatVersion.objects.create(
        format_id="c5d4b021-e54d-4e57-8e7f-6a96c5393bde",
        pronom_id="fmt/2058",
        description="""A2R Disk Image File v.3 (little endian)""",
        version="3",
        uuid="28b01675-f1b8-4ee1-b753-b5b6fba0c16e",
    )
    IDRule.objects.filter(command_output=".a2r").delete()

    Format.objects.create(
        description="""WOZ Disk Image File""",
        group_id="3616a69f-e9c4-4357-b366-57082cf75a3e",
        uuid="cafffdb9-829d-4f05-8317-aff5c28d428b",
    )
    FormatVersion.objects.create(
        format_id="cafffdb9-829d-4f05-8317-aff5c28d428b",
        pronom_id="fmt/2059",
        description="""WOZ Disk Image File v.1 (little endian)""",
        version="1",
        uuid="bbb9ed04-da1c-41de-bffa-adc086aec3d2",
    )
    IDRule.objects.create(
        format_id="bbb9ed04-da1c-41de-bffa-adc086aec3d2",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".woz",
    )

    FormatVersion.objects.create(
        format_id="cafffdb9-829d-4f05-8317-aff5c28d428b",
        pronom_id="fmt/2060",
        description="""WOZ Disk Image File v.2 (little endian)""",
        version="2",
        uuid="afd8e3ec-3e6d-4875-8000-f4f915202c2c",
    )
    IDRule.objects.filter(command_output=".woz").delete()

    Format.objects.create(
        description="""MOOF Disk Image File""",
        group_id="3616a69f-e9c4-4357-b366-57082cf75a3e",
        uuid="c5034e1c-1f1d-4415-8e7f-2dec44a89cf2",
    )
    FormatVersion.objects.create(
        format_id="c5034e1c-1f1d-4415-8e7f-2dec44a89cf2",
        pronom_id="fmt/2061",
        description="""MOOF Disk Image v.1 (little endian)""",
        version="1",
        uuid="6f9c064c-984c-4854-ac35-b65605912c13",
    )
    IDRule.objects.create(
        format_id="6f9c064c-984c-4854-ac35-b65605912c13",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".moof",
    )

    Format.objects.create(
        description="""AV1 Image File Format""",
        group_id="be86edbf-f62c-431f-b549-300d23c7cd0d",
        uuid="5e4f55c2-83fd-4227-9a47-15dc4e945fca",
    )
    FormatVersion.objects.create(
        format_id="5e4f55c2-83fd-4227-9a47-15dc4e945fca",
        pronom_id="fmt/2062",
        description="""AV1 Image File Format""",
        version="None",
        uuid="a80730b4-28ac-4824-8d80-ef9d21f18093",
    )
    IDRule.objects.create(
        format_id="a80730b4-28ac-4824-8d80-ef9d21f18093",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".avif",
    )

    Format.objects.create(
        description="""DaVinci Resolve Timeline File""",
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf",
        uuid="d7fc0b69-129a-4f52-adcc-cf675fa11ae8",
    )
    FormatVersion.objects.create(
        format_id="d7fc0b69-129a-4f52-adcc-cf675fa11ae8",
        pronom_id="fmt/2063",
        description="""DaVinci Resolve Timeline File""",
        version="9+",
        uuid="b2520987-ad43-4e2c-9744-4451b78551b9",
    )
    IDRule.objects.create(
        format_id="b2520987-ad43-4e2c-9744-4451b78551b9",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".drt",
    )

    Format.objects.create(
        description="""DaVinci Resolve Project File""",
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf",
        uuid="65dab8f0-dd39-4cbf-9d46-d8d4030e90d9",
    )
    FormatVersion.objects.create(
        format_id="65dab8f0-dd39-4cbf-9d46-d8d4030e90d9",
        pronom_id="fmt/2064",
        description="""DaVinci Resolve Project File""",
        version="9+",
        uuid="868f4e2c-48e5-4962-852c-df9c60f6b0a3",
    )
    IDRule.objects.create(
        format_id="868f4e2c-48e5-4962-852c-df9c60f6b0a3",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".drp",
    )

    Format.objects.create(
        description="""TOML""",
        group_id="89961b53-4d5c-49e2-9910-8825d96c8640",
        uuid="9302706c-1198-4bae-8c01-83d5cb9c91e2",
    )
    FormatVersion.objects.create(
        format_id="9302706c-1198-4bae-8c01-83d5cb9c91e2",
        pronom_id="fmt/2065",
        description="""TOML""",
        version="None",
        uuid="ebb61615-e914-4347-8528-76cf7bc23d93",
    )
    IDRule.objects.create(
        format_id="ebb61615-e914-4347-8528-76cf7bc23d93",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".toml",
    )

    Format.objects.create(
        description="""Rust Source File""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="a3d49af0-7580-4743-83a0-af8324300810",
    )
    FormatVersion.objects.create(
        format_id="a3d49af0-7580-4743-83a0-af8324300810",
        pronom_id="fmt/2066",
        description="""Rust Source File""",
        version="None",
        uuid="ef42afde-cd24-4afc-a201-0d8d4d34a563",
    )
    IDRule.objects.create(
        format_id="ef42afde-cd24-4afc-a201-0d8d4d34a563",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".rs",
    )

    Format.objects.create(
        description="""XYZ Coordinate Data""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="ed4727ce-fdc5-4f35-bf41-17e165e5a62e",
    )
    FormatVersion.objects.create(
        format_id="ed4727ce-fdc5-4f35-bf41-17e165e5a62e",
        pronom_id="fmt/2067",
        description="""XYZ Coordinate Data""",
        version="None",
        uuid="e99c6237-b62c-4ddf-b0c2-4ae2f3ea480d",
    )
    IDRule.objects.create(
        format_id="e99c6237-b62c-4ddf-b0c2-4ae2f3ea480d",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".xyz",
    )

    Format.objects.create(
        description="""Macintosh File System""",
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf",
        uuid="13ab4a57-d898-402a-83a6-836c5c68161d",
    )
    FormatVersion.objects.create(
        format_id="13ab4a57-d898-402a-83a6-836c5c68161d",
        pronom_id="fmt/2068",
        description="""Macintosh File System""",
        version="None",
        uuid="0fa59106-8027-4f76-98b0-6780471c294b",
    )
    IDRule.objects.create(
        format_id="0fa59106-8027-4f76-98b0-6780471c294b",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".mfs",
    )

    Format.objects.create(
        description="""Draco""",
        group_id="8d32bf98-b569-4469-8953-10416b53b920",
        uuid="b5efa1e6-49f1-4338-8531-8ed6110b1c08",
    )
    FormatVersion.objects.create(
        format_id="b5efa1e6-49f1-4338-8531-8ed6110b1c08",
        pronom_id="fmt/2069",
        description="""Draco v.2""",
        version="2",
        uuid="5354427d-a5f0-46d8-b93f-e8ea7c7c7392",
    )
    IDRule.objects.filter(command_output=".drc").delete()

    Format.objects.create(
        description="""Autodesk ReCap RCS Indexed Point Cloud Data""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="a92dcf69-7233-45b6-b7a0-c429764b88b8",
    )
    FormatVersion.objects.create(
        format_id="a92dcf69-7233-45b6-b7a0-c429764b88b8",
        pronom_id="fmt/2070",
        description="""Autodesk ReCap RCS Indexed Point Cloud Data""",
        version="None",
        uuid="0980baa1-2ca5-419c-bda2-56e3fe686f0e",
    )
    IDRule.objects.create(
        format_id="0980baa1-2ca5-419c-bda2-56e3fe686f0e",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".rcs",
    )

    Format.objects.create(
        description="""SuperCard Pro Image File""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="5db7513a-d953-4cb4-9302-827e344c43d1",
    )
    FormatVersion.objects.create(
        format_id="5db7513a-d953-4cb4-9302-827e344c43d1",
        pronom_id="fmt/2071",
        description="""SuperCard Image Pro""",
        version="None",
        uuid="31152042-8b50-463c-adc0-98ce3b1d86c4",
    )
    IDRule.objects.create(
        format_id="31152042-8b50-463c-adc0-98ce3b1d86c4",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".scp",
    )

    Format.objects.create(
        description="""Weaving Information File (WIF)""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="e125be9f-8fcf-4a86-bb79-8c9b014fb9d0",
    )
    FormatVersion.objects.create(
        format_id="e125be9f-8fcf-4a86-bb79-8c9b014fb9d0",
        pronom_id="fmt/2072",
        description="""Weaving Information File""",
        version="1.1",
        uuid="6026585b-025a-44ef-a986-662f66bb7547",
    )
    IDRule.objects.create(
        format_id="6026585b-025a-44ef-a986-662f66bb7547",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".wif",
    )

    Format.objects.create(
        description="""Tilt Brush""",
        group_id="8d32bf98-b569-4469-8953-10416b53b920",
        uuid="333adf8e-fe29-4a11-8ff7-3456f8e512b6",
    )
    FormatVersion.objects.create(
        format_id="333adf8e-fe29-4a11-8ff7-3456f8e512b6",
        pronom_id="fmt/2073",
        description="""Tilt Brush""",
        version="None",
        uuid="572608b6-60c9-413d-8598-d2966dba6d5a",
    )
    IDRule.objects.create(
        format_id="572608b6-60c9-413d-8598-d2966dba6d5a",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".tilt",
    )

    Format.objects.create(
        description="""MRtrix File Format""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="8545c720-139f-48ce-ae60-c9966d01fb37",
    )
    FormatVersion.objects.create(
        format_id="8545c720-139f-48ce-ae60-c9966d01fb37",
        pronom_id="fmt/2074",
        description="""MRtrix""",
        version="None",
        uuid="b71a6713-dd83-42b4-a052-5099ecb1036f",
    )
    IDRule.objects.filter(command_output=".mif").delete()

    Format.objects.create(
        description="""ACE""",
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf",
        uuid="46b1d6df-1a3f-41e2-9058-78b1000b4ec9",
    )
    FormatVersion.objects.create(
        format_id="46b1d6df-1a3f-41e2-9058-78b1000b4ec9",
        pronom_id="fmt/2075",
        description="""ACE Archive 1""",
        version="1",
        uuid="d5b8747b-29e6-4b13-ab70-012073ea3d5f",
    )
    IDRule.objects.create(
        format_id="d5b8747b-29e6-4b13-ab70-012073ea3d5f",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".ace",
    )

    FormatVersion.objects.create(
        format_id="46b1d6df-1a3f-41e2-9058-78b1000b4ec9",
        pronom_id="fmt/2076",
        description="""ACE Archive 2""",
        version="2",
        uuid="a0bcbe48-71c9-49eb-827d-e8d90f44f193",
    )
    IDRule.objects.filter(command_output=".ace").delete()

    Format.objects.create(
        description="""Common Ground Digital Paper""",
        group_id="3616a69f-e9c4-4357-b366-57082cf75a3e",
        uuid="099c7079-f43a-4d70-b7e1-ab6753139cd8",
    )
    FormatVersion.objects.create(
        format_id="099c7079-f43a-4d70-b7e1-ab6753139cd8",
        pronom_id="fmt/2077",
        description="""Common Ground Digital Paper 1""",
        version="1",
        uuid="01712ce5-e468-433e-b4da-0aef96971310",
    )
    IDRule.objects.create(
        format_id="01712ce5-e468-433e-b4da-0aef96971310",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".dp",
    )

    FormatVersion.objects.create(
        format_id="099c7079-f43a-4d70-b7e1-ab6753139cd8",
        pronom_id="fmt/2078",
        description="""Common Ground Digital Paper 3""",
        version="3",
        uuid="5121d730-bbe1-4fe0-a553-b1faedbeb177",
    )
    IDRule.objects.filter(command_output=".dp").delete()

    FormatVersion.objects.create(
        format_id="099c7079-f43a-4d70-b7e1-ab6753139cd8",
        pronom_id="fmt/2079",
        description="""Common Ground Digital Paper 4""",
        version="4",
        uuid="b2e8d3db-8965-48a3-b174-892a655198e1",
    )
    IDRule.objects.create(
        format_id="b2e8d3db-8965-48a3-b174-892a655198e1",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".dp",
    )

    FormatVersion.objects.create(
        format_id="2261d5f9-f994-4503-8e99-c3ddf24b89fa",
        pronom_id="fmt/2080",
        description="""xdomea v.3.1.0""",
        version="3.1.0",
        uuid="d24e1f7a-af4a-4b3c-b205-53f42447062b",
    )
    IDRule.objects.filter(command_output=".xml").delete()

    FormatVersion.objects.create(
        format_id="2261d5f9-f994-4503-8e99-c3ddf24b89fa",
        pronom_id="fmt/2081",
        description="""xdomea 4.0.0""",
        version="4.0.0",
        uuid="0bfa0399-87e1-4ea2-94f5-dd3f12a1d551",
    )
    IDRule.objects.create(
        format_id="0bfa0399-87e1-4ea2-94f5-dd3f12a1d551",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".xml",
    )

    Format.objects.create(
        description="""3DM 6""",
        group_id="8d32bf98-b569-4469-8953-10416b53b920",
        uuid="7fa6ebd9-1f3a-4811-a223-80fdeda81af9",
    )
    FormatVersion.objects.create(
        format_id="7fa6ebd9-1f3a-4811-a223-80fdeda81af9",
        pronom_id="fmt/2082",
        description="""3DM 6""",
        version="6",
        uuid="be383e5e-93bb-46ba-886f-989ce25a8e6c",
    )
    IDRule.objects.filter(command_output=".3dm").delete()

    Format.objects.create(
        description="""3DM 7""",
        group_id="8d32bf98-b569-4469-8953-10416b53b920",
        uuid="257049ae-b9f1-41d9-bb00-bb9c1f2cc464",
    )
    FormatVersion.objects.create(
        format_id="257049ae-b9f1-41d9-bb00-bb9c1f2cc464",
        pronom_id="fmt/2083",
        description="""3DM 7""",
        version="7",
        uuid="24d02df5-cd49-4184-93cb-3459ef2ca6ce",
    )
    IDRule.objects.create(
        format_id="24d02df5-cd49-4184-93cb-3459ef2ca6ce",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".3dm",
    )

    Format.objects.create(
        description="""3DM 8""",
        group_id="8d32bf98-b569-4469-8953-10416b53b920",
        uuid="5e50489f-896f-4703-bc1f-bf0c49b64daf",
    )
    FormatVersion.objects.create(
        format_id="5e50489f-896f-4703-bc1f-bf0c49b64daf",
        pronom_id="fmt/2084",
        description="""3DM 8""",
        version="8",
        uuid="da24bf1c-42ad-47ea-8200-11f8764d6494",
    )
    IDRule.objects.filter(command_output=".3dm").delete()

    Format.objects.create(
        description="""FieldWorks Language Explorer FWData XML""",
        group_id="89961b53-4d5c-49e2-9910-8825d96c8640",
        uuid="2d8989f8-c5a3-4eff-ae1e-18f719a4fce5",
    )
    FormatVersion.objects.create(
        format_id="2d8989f8-c5a3-4eff-ae1e-18f719a4fce5",
        pronom_id="fmt/2085",
        description="""FieldWorks Language Explorer FWData XML""",
        version="None",
        uuid="9ea745e6-b34d-470d-a877-da011c2f1986",
    )
    IDRule.objects.create(
        format_id="9ea745e6-b34d-470d-a877-da011c2f1986",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".fwdata",
    )

    Format.objects.create(
        description="""FieldWorks Language Explorer FWBackup""",
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf",
        uuid="d4de870b-6176-46a3-ad9a-73da4215b658",
    )
    FormatVersion.objects.create(
        format_id="d4de870b-6176-46a3-ad9a-73da4215b658",
        pronom_id="fmt/2086",
        description="""FieldWorks Language Explorer FWBackup""",
        version="None",
        uuid="bf20cb95-bb6a-4b62-8851-3f64a69cfc5a",
    )
    IDRule.objects.create(
        format_id="bf20cb95-bb6a-4b62-8851-3f64a69cfc5a",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".fwbackup",
    )

    Format.objects.create(
        description="""Final Cut Pro Project File""",
        group_id="f22e9c29-9d4a-429e-adaf-38f3aecaff99",
        uuid="801e2240-31d5-49ea-9c33-49ef8147ee74",
    )
    FormatVersion.objects.create(
        format_id="801e2240-31d5-49ea-9c33-49ef8147ee74",
        pronom_id="fmt/2087",
        description="""Final Cut Pro Project File""",
        version="None",
        uuid="4e544a16-a072-41b1-a224-7033e5f8b3cd",
    )
    IDRule.objects.create(
        format_id="4e544a16-a072-41b1-a224-7033e5f8b3cd",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".fcp",
    )

    Format.objects.create(
        description="""Final Cut Pro XML Interchange Format""",
        group_id="89961b53-4d5c-49e2-9910-8825d96c8640",
        uuid="d9f4c073-13d9-4232-a844-cb362d9915af",
    )
    FormatVersion.objects.create(
        format_id="d9f4c073-13d9-4232-a844-cb362d9915af",
        pronom_id="fmt/2088",
        description="""Final Cut Pro XML Interchange Format""",
        version="None",
        uuid="819a3237-7ff6-4761-8dd7-541303913c7d",
    )
    IDRule.objects.filter(command_output=".xml").delete()

    Format.objects.create(
        description="""FCPXML Interchange Format""",
        group_id="89961b53-4d5c-49e2-9910-8825d96c8640",
        uuid="f6915c81-063a-4b75-af04-c7a131721f81",
    )
    FormatVersion.objects.create(
        format_id="f6915c81-063a-4b75-af04-c7a131721f81",
        pronom_id="fmt/2089",
        description="""FCPXML Interchange Format""",
        version="None",
        uuid="3a6a6cbc-5cda-43bf-8ce9-48d84c905f5c",
    )
    IDRule.objects.create(
        format_id="3a6a6cbc-5cda-43bf-8ce9-48d84c905f5c",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".fcpxml",
    )

    Format.objects.create(
        description="""Kodak DCS RAW Image""",
        group_id="be86edbf-f62c-431f-b549-300d23c7cd0d",
        uuid="89b71411-a091-4e9a-8fcb-bc0f27fd8618",
    )
    FormatVersion.objects.create(
        format_id="89b71411-a091-4e9a-8fcb-bc0f27fd8618",
        pronom_id="fmt/2090",
        description="""Kodak DCS RAW Image""",
        version="None",
        uuid="848735fe-eb9b-4eb0-a476-39cfc008c00b",
    )
    IDRule.objects.filter(command_output=".tif").delete()

    FormatVersion.objects.create(
        format_id="89b71411-a091-4e9a-8fcb-bc0f27fd8618",
        pronom_id="fmt/2091",
        description="""Kodak DCS RAW Image v.3""",
        version="3",
        uuid="1944b901-4607-4a8a-9e3c-a4db16dfac1f",
    )
    IDRule.objects.create(
        format_id="1944b901-4607-4a8a-9e3c-a4db16dfac1f",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".tif",
    )

    Format.objects.create(
        description="""Canadian Avalanche Association MarkUp Language""",
        group_id="89961b53-4d5c-49e2-9910-8825d96c8640",
        uuid="b6d9b7ff-8fe0-487d-a8bf-3f865c63ea0a",
    )
    FormatVersion.objects.create(
        format_id="b6d9b7ff-8fe0-487d-a8bf-3f865c63ea0a",
        pronom_id="fmt/2092",
        description="""Canadian Avalanche Association Markup Language""",
        version="6.0.3",
        uuid="364fb4c0-dea1-4177-a02b-496af51e99c5",
    )
    IDRule.objects.create(
        format_id="364fb4c0-dea1-4177-a02b-496af51e99c5",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".caaml",
    )

    Format.objects.create(
        description="""ROS Bag Format""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="68a99263-61c7-45e7-8718-619aaeab6d83",
    )
    FormatVersion.objects.create(
        format_id="68a99263-61c7-45e7-8718-619aaeab6d83",
        pronom_id="fmt/2093",
        description="""ROS Bag v.2""",
        version="2.0",
        uuid="cbca7626-0e71-4c8c-8b69-333b5d7af584",
    )
    IDRule.objects.create(
        format_id="cbca7626-0e71-4c8c-8b69-333b5d7af584",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".bag",
    )

    Format.objects.create(
        description="""M4A Audio""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="89108783-01d5-4803-92f2-23a5ce9f8abc",
    )
    FormatVersion.objects.create(
        format_id="89108783-01d5-4803-92f2-23a5ce9f8abc",
        pronom_id="fmt/2094",
        description="""M4A Audio""",
        version="None",
        uuid="ea5e3440-b9ae-463d-a106-b833e3f0e2da",
    )
    IDRule.objects.filter(command_output=".m4a").delete()

    Format.objects.create(
        description="""Hasselblad FFF Raw Image""",
        group_id="be86edbf-f62c-431f-b549-300d23c7cd0d",
        uuid="aaa0bc43-6279-436d-96e9-dd9ab52cf846",
    )
    FormatVersion.objects.create(
        format_id="aaa0bc43-6279-436d-96e9-dd9ab52cf846",
        pronom_id="fmt/2095",
        description="""Hasselblad FFF Raw Image""",
        version="None",
        uuid="c88430fa-1e5a-4610-92fb-f15b6c377926",
    )
    IDRule.objects.filter(command_output=".fff").delete()

    Format.objects.create(
        description="""GGML Universal File (GGUF)""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="5c14a45d-cc61-40e0-8646-dc97ec7c3a2d",
    )
    FormatVersion.objects.create(
        format_id="5c14a45d-cc61-40e0-8646-dc97ec7c3a2d",
        pronom_id="fmt/2096",
        description="""GGUF 1""",
        version="1",
        uuid="54183ec0-ca08-4916-8673-12bbb2c606c5",
    )
    IDRule.objects.create(
        format_id="54183ec0-ca08-4916-8673-12bbb2c606c5",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".gguf",
    )

    FormatVersion.objects.create(
        format_id="5c14a45d-cc61-40e0-8646-dc97ec7c3a2d",
        pronom_id="fmt/2097",
        description="""GGUF 2""",
        version="2",
        uuid="02eab109-6b09-440d-9078-5b36cf38c1c9",
    )
    IDRule.objects.filter(command_output=".gguf").delete()

    FormatVersion.objects.create(
        format_id="5c14a45d-cc61-40e0-8646-dc97ec7c3a2d",
        pronom_id="fmt/2098",
        description="""GGUF 3""",
        version="3",
        uuid="9b9555a0-f480-4803-8c40-5e16ea22026d",
    )
    IDRule.objects.create(
        format_id="9b9555a0-f480-4803-8c40-5e16ea22026d",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".gguf",
    )

    Format.objects.create(
        description="""iZotope RX Document""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="5211269c-a724-485f-899d-58853a6e6e32",
    )
    FormatVersion.objects.create(
        format_id="5211269c-a724-485f-899d-58853a6e6e32",
        pronom_id="fmt/2099",
        description="""iZotope RX Document""",
        version="None",
        uuid="33c49c9c-239e-4826-8208-1ac2b6da813a",
    )
    IDRule.objects.create(
        format_id="33c49c9c-239e-4826-8208-1ac2b6da813a",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".rxdoc",
    )

    FormatVersion.objects.create(
        format_id="02234cb1-2615-47d5-9ccd-ea1c60b9a877",
        pronom_id="fmt/2100",
        description="""Visualization Toolkit 4""",
        version="4.0",
        uuid="31b9c6b6-37b4-4add-a32a-da5c366bff2c",
    )
    IDRule.objects.filter(command_output=".vtk").delete()

    Format.objects.create(
        description="""ChemStation Gas Chromatography/Mass Spectrum (GC/MS) Data File""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="60f650ad-fc94-4971-b4fc-6fd0276448e9",
    )
    FormatVersion.objects.create(
        format_id="60f650ad-fc94-4971-b4fc-6fd0276448e9",
        pronom_id="fmt/2101",
        description="""GC/MS Data File 2""",
        version="2",
        uuid="74cfaba6-51cd-4b03-a957-0ab981957ea3",
    )
    IDRule.objects.create(
        format_id="74cfaba6-51cd-4b03-a957-0ab981957ea3",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".ms",
    )

    Format.objects.create(
        description="""BioSemi Data Format""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="40ba8337-5b2a-462f-a5b6-e7b7c05ad57d",
    )
    FormatVersion.objects.create(
        format_id="40ba8337-5b2a-462f-a5b6-e7b7c05ad57d",
        pronom_id="fmt/2102",
        description="""BioSemi Data Format""",
        version="None",
        uuid="00f9cb40-6de0-482f-bcf4-6bf7711fee7d",
    )
    IDRule.objects.create(
        format_id="00f9cb40-6de0-482f-bcf4-6bf7711fee7d",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".bdf",
    )

    Format.objects.create(
        description="""Discus Project""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="57a144d9-c5b6-4dbf-b310-c96227410af8",
    )
    FormatVersion.objects.create(
        format_id="57a144d9-c5b6-4dbf-b310-c96227410af8",
        pronom_id="fmt/2103",
        description="""Discus Project 2-3""",
        version="2-3",
        uuid="1671c149-9d05-4026-b249-0260ee16b130",
    )
    IDRule.objects.create(
        format_id="1671c149-9d05-4026-b249-0260ee16b130",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".cdl",
    )

    Format.objects.create(
        description="""Discus Project File""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="eb14f9c2-16cf-46e2-86d0-ffb6d2b80916",
    )
    FormatVersion.objects.create(
        format_id="eb14f9c2-16cf-46e2-86d0-ffb6d2b80916",
        pronom_id="fmt/2104",
        description="""Discus Project 4""",
        version="4",
        uuid="66661810-afbc-4d0a-a39d-aa5bb95c2968",
    )
    IDRule.objects.create(
        format_id="66661810-afbc-4d0a-a39d-aa5bb95c2968",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".cd4",
    )


class Migration(migrations.Migration):
    dependencies = [("fpr", "0053_update_jhove_tool")]
    operations = [migrations.RunPython(data_migration_up, migrations.RunPython.noop)]

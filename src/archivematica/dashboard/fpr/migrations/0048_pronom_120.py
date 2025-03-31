from django.db import migrations


def data_migration_up(apps, schema_editor):
    Format = apps.get_model("fpr", "Format")
    FormatVersion = apps.get_model("fpr", "FormatVersion")
    IDRule = apps.get_model("fpr", "IDRule")

    Format.objects.create(
        description="""Draw.io Diagram (XML) File""",
        group_id="fdf9e267-a18c-46a4-a162-b81bcba6322f",
        uuid="d002c654-a010-43bb-8782-733af0a0a43b",
    )
    FormatVersion.objects.create(
        format_id="d002c654-a010-43bb-8782-733af0a0a43b",
        pronom_id="fmt/1946",
        description="""Draw.io Diagram""",
        version="None",
        uuid="258b1a5f-8a46-469e-b17e-d6964e1c4af4",
    )
    IDRule.objects.create(
        format_id="258b1a5f-8a46-469e-b17e-d6964e1c4af4",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".drawio",
    )

    Format.objects.create(
        description="""OpenWayback CDXJ File Format""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="34448b47-cc4d-4c99-b081-a7b1673f4d35",
    )
    FormatVersion.objects.create(
        format_id="34448b47-cc4d-4c99-b081-a7b1673f4d35",
        pronom_id="fmt/1947",
        description="""OpenWayback CDXJ""",
        version="None",
        uuid="634e1cb1-8999-4c3f-84ed-e218c2cc3421",
    )
    IDRule.objects.filter(command_output=".cdx").delete()

    Format.objects.create(
        description="""Common Data Format dotCDF""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="e778d72f-db63-431c-bfd7-b38191b30ba2",
    )
    FormatVersion.objects.create(
        format_id="e778d72f-db63-431c-bfd7-b38191b30ba2",
        pronom_id="fmt/1948",
        description="""CDF 2.0-2.5""",
        version="2.0-2.5",
        uuid="b9d7a274-7738-47f1-9d26-a1e77dfa67c9",
    )
    IDRule.objects.create(
        format_id="b9d7a274-7738-47f1-9d26-a1e77dfa67c9",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".cdf",
    )

    FormatVersion.objects.create(
        format_id="e778d72f-db63-431c-bfd7-b38191b30ba2",
        pronom_id="fmt/1949",
        description="""CDF 2.6-2.7""",
        version="2.6-2.7",
        uuid="d3a434d6-7e5f-4ee0-960c-76804c799f17",
    )
    IDRule.objects.filter(command_output=".cdf").delete()

    FormatVersion.objects.create(
        format_id="e778d72f-db63-431c-bfd7-b38191b30ba2",
        pronom_id="fmt/1950",
        description="""CDF 3.x""",
        version="3.x",
        uuid="2c671999-2daf-4912-a2d6-674d60c73e35",
    )
    IDRule.objects.create(
        format_id="2c671999-2daf-4912-a2d6-674d60c73e35",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".cdf",
    )

    FormatVersion.objects.create(
        format_id="7ba5971f-3bd6-4f1a-84ec-35fd3cced676",
        pronom_id="fmt/1951",
        description="""Pro Tools Session File 5-9""",
        version="5-9",
        uuid="56f60af3-7e47-4157-aa60-0d73b5de57ab",
    )
    IDRule.objects.create(
        format_id="56f60af3-7e47-4157-aa60-0d73b5de57ab",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".ptf",
    )

    Format.objects.create(
        description="""PechaMaker Format""",
        group_id="df5d5107-c803-48ba-844d-feba093a571c",
        uuid="44a6fd9a-6f43-4057-940d-e5b25f64834f",
    )
    FormatVersion.objects.create(
        format_id="44a6fd9a-6f43-4057-940d-e5b25f64834f",
        pronom_id="fmt/1952",
        description="""PechaMaker Format""",
        version="None",
        uuid="8aaa1412-9bdf-455b-b9ee-97afb324dc4e",
    )
    IDRule.objects.create(
        format_id="8aaa1412-9bdf-455b-b9ee-97afb324dc4e",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".pxp",
    )

    Format.objects.create(
        description="""Zoom Project Settings""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="0864df9c-8543-49f7-99fa-5d529157d9e3",
    )
    FormatVersion.objects.create(
        format_id="0864df9c-8543-49f7-99fa-5d529157d9e3",
        pronom_id="fmt/1953",
        description="""Zoom Project Settings H5""",
        version="H5",
        uuid="1a19f0c9-e520-4d93-8d61-e9624ce9d791",
    )
    IDRule.objects.create(
        format_id="1a19f0c9-e520-4d93-8d61-e9624ce9d791",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".hprj",
    )

    FormatVersion.objects.create(
        format_id="0864df9c-8543-49f7-99fa-5d529157d9e3",
        pronom_id="fmt/1954",
        description="""Zoom Project Settings H6""",
        version="H6",
        uuid="9be09e4e-a61e-4862-9f91-50651c0f3871",
    )
    IDRule.objects.filter(command_output=".hprj").delete()

    FormatVersion.objects.create(
        format_id="299a6aec-e095-4754-af86-f63ac7f5df93",
        pronom_id="fmt/1955",
        description="""Graphisoft Archicad Project versions 6-9 (Intel Mac, little-endian)""",
        version="6-9",
        uuid="6e91a64e-d81c-44d7-95df-8cfda2ad2d24",
    )
    IDRule.objects.create(
        format_id="6e91a64e-d81c-44d7-95df-8cfda2ad2d24",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".pla",
    )

    Format.objects.create(
        description="""Sandboxels Save File""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="960a7a3a-a77a-4ff8-9e25-cf2fb40ce0e7",
    )
    FormatVersion.objects.create(
        format_id="960a7a3a-a77a-4ff8-9e25-cf2fb40ce0e7",
        pronom_id="fmt/1956",
        description="""Sandboxels Save File""",
        version="None",
        uuid="58e7369d-e6ca-4e16-84e8-0a779177d3ca",
    )
    IDRule.objects.create(
        format_id="58e7369d-e6ca-4e16-84e8-0a779177d3ca",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sbxls",
    )

    Format.objects.create(
        description="""Program Embroidery Stitch (PES) File""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="ea93a548-6dac-46af-8d06-f218f186934e",
    )
    FormatVersion.objects.create(
        format_id="ea93a548-6dac-46af-8d06-f218f186934e",
        pronom_id="fmt/1957",
        description="""Program Embroidery Stitch (PES) File""",
        version="None",
        uuid="feca53f3-0eca-4079-a9e1-cbc3ed767a72",
    )
    IDRule.objects.create(
        format_id="feca53f3-0eca-4079-a9e1-cbc3ed767a72",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".pes",
    )

    Format.objects.create(
        description="""Melco OFM Project""",
        group_id="be86edbf-f62c-431f-b549-300d23c7cd0d",
        uuid="093f5f5e-1d49-4e79-971d-3aa8e6c2d7fd",
    )
    FormatVersion.objects.create(
        format_id="093f5f5e-1d49-4e79-971d-3aa8e6c2d7fd",
        pronom_id="fmt/1958",
        description="""Melco OFM Project v.11""",
        version="11",
        uuid="5dc10c9e-3923-40a9-af7a-3d91c8bdb424",
    )
    IDRule.objects.create(
        format_id="5dc10c9e-3923-40a9-af7a-3d91c8bdb424",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".ofm",
    )

    FormatVersion.objects.create(
        format_id="093f5f5e-1d49-4e79-971d-3aa8e6c2d7fd",
        pronom_id="fmt/1959",
        description="""Melco OFM Project""",
        version="pre v.11",
        uuid="59fda400-81df-4891-9525-9ea02687b886",
    )
    IDRule.objects.filter(command_output=".ofm").delete()

    Format.objects.create(
        description="""Disklavier E-Seq Music""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="14c43189-5a20-46cf-8f1d-d39fe8598369",
    )
    FormatVersion.objects.create(
        format_id="14c43189-5a20-46cf-8f1d-d39fe8598369",
        pronom_id="fmt/1960",
        description="""Disklavier E-Seq Music""",
        version="None",
        uuid="e649f4d1-cb8c-4f8c-99c0-194a1e8de016",
    )
    IDRule.objects.create(
        format_id="e649f4d1-cb8c-4f8c-99c0-194a1e8de016",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".fil",
    )

    Format.objects.create(
        description="""Shorten (codec)""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="1b61aebf-923b-4cae-9031-c1a8739bb668",
    )
    FormatVersion.objects.create(
        format_id="1b61aebf-923b-4cae-9031-c1a8739bb668",
        pronom_id="fmt/1961",
        description="""Shorten (codec)""",
        version="None",
        uuid="d619f2ed-9107-4338-ab64-3efd1906e539",
    )
    IDRule.objects.create(
        format_id="d619f2ed-9107-4338-ab64-3efd1906e539",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".shn",
    )

    Format.objects.create(
        description="""SolidWorks Material Database File""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="baf1ad97-6588-4a02-9ff4-11391d66061b",
    )
    FormatVersion.objects.create(
        format_id="baf1ad97-6588-4a02-9ff4-11391d66061b",
        pronom_id="fmt/1962",
        description="""SolidWorks Material Database File""",
        version="None",
        uuid="243a75a1-0cf8-4678-b6c1-192c7d8113a1",
    )
    IDRule.objects.create(
        format_id="243a75a1-0cf8-4678-b6c1-192c7d8113a1",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sldmat",
    )

    Format.objects.create(
        description="""NEC Thermo Tracer Image File""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="fe46d74b-f3bb-400b-a9a0-e33a750d883f",
    )
    FormatVersion.objects.create(
        format_id="fe46d74b-f3bb-400b-a9a0-e33a750d883f",
        pronom_id="fmt/1963",
        description="""NEC TH5100 Thermo Tracer Image File""",
        version="TH5100",
        uuid="c91858b5-6778-42a4-8038-8aac60af1875",
    )
    IDRule.objects.create(
        format_id="c91858b5-6778-42a4-8038-8aac60af1875",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".tmp",
    )

    Format.objects.create(
        description="""JPH (JPEG 2000 part 15)""",
        group_id="be86edbf-f62c-431f-b549-300d23c7cd0d",
        uuid="83d0c7da-8941-4988-a4da-4326effffc6a",
    )
    FormatVersion.objects.create(
        format_id="83d0c7da-8941-4988-a4da-4326effffc6a",
        pronom_id="fmt/1964",
        description="""JPEG2000 – JPH/HTJ2K""",
        version="None",
        uuid="f309e32f-1499-40f8-b8d4-9a278682ecc9",
    )
    IDRule.objects.create(
        format_id="f309e32f-1499-40f8-b8d4-9a278682ecc9",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".jph",
    )

    Format.objects.create(
        description="""Papyrus Document""",
        group_id="805d359a-32f0-4767-8a9c-cc14f13d8392",
        uuid="4035be98-61d2-4b07-9ebf-1365eef8224f",
    )
    FormatVersion.objects.create(
        format_id="4035be98-61d2-4b07-9ebf-1365eef8224f",
        pronom_id="fmt/1965",
        description="""Papyrus Document""",
        version="None",
        uuid="d30c0d9a-55ea-40b8-a5d6-0fa45a847b5e",
    )
    IDRule.objects.create(
        format_id="d30c0d9a-55ea-40b8-a5d6-0fa45a847b5e",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".pap",
    )

    Format.objects.create(
        description="""Final Writer Document""",
        group_id="805d359a-32f0-4767-8a9c-cc14f13d8392",
        uuid="7de7cf90-01fb-4a69-b2e7-abcba08eebab",
    )
    FormatVersion.objects.create(
        format_id="7de7cf90-01fb-4a69-b2e7-abcba08eebab",
        pronom_id="fmt/1966",
        description="""Final Writer Document""",
        version="None",
        uuid="8f3680f1-f294-4d00-a286-3f389fe86828",
    )
    IDRule.objects.filter(command_output=".fw").delete()

    Format.objects.create(
        description="""Solidworks Design Document Files""",
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf",
        uuid="00df1c6c-7e93-4259-b94d-945f03504d79",
    )
    FormatVersion.objects.create(
        format_id="00df1c6c-7e93-4259-b94d-945f03504d79",
        pronom_id="fmt/1967",
        description="""Solidworks Design Document Files 2015+""",
        version="2015+",
        uuid="07801de2-7a99-43ac-8e74-0e2d97d883ae",
    )
    IDRule.objects.create(
        format_id="07801de2-7a99-43ac-8e74-0e2d97d883ae",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sldprt",
    )

    Format.objects.create(
        description="""Atrac Codec File""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="b91ea2c5-f745-4ed3-9743-63b040b2b45c",
    )
    FormatVersion.objects.create(
        format_id="b91ea2c5-f745-4ed3-9743-63b040b2b45c",
        pronom_id="fmt/1968",
        description="""Atrac Codec File v.1""",
        version="v.1",
        uuid="7242bcbc-7dc0-41cc-864e-cfadb6694c40",
    )
    IDRule.objects.create(
        format_id="7242bcbc-7dc0-41cc-864e-cfadb6694c40",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".aea",
    )

    Format.objects.create(
        description="""ETC Express/Expression Show File""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="bb1677a1-3ece-4239-ada1-e17bb4dd5d08",
    )
    FormatVersion.objects.create(
        format_id="bb1677a1-3ece-4239-ada1-e17bb4dd5d08",
        pronom_id="fmt/1969",
        description="""ETC Express/Expression Show File""",
        version="None",
        uuid="875a8dd3-53ae-4dd1-884a-3fb1cc4901e0",
    )
    IDRule.objects.filter(command_output=".shw").delete()

    Format.objects.create(
        description="""MOXCEL""",
        group_id="fea8c626-4c6d-4d34-8747-b7df5c67c17c",
        uuid="59c4ab9c-1dd8-4b23-a91a-48f9f9c9d63b",
    )
    FormatVersion.objects.create(
        format_id="59c4ab9c-1dd8-4b23-a91a-48f9f9c9d63b",
        pronom_id="fmt/1970",
        description="""Moxcel Spreadsheet""",
        version="None",
        uuid="ce8af456-4561-4b38-bf73-8f84148496d3",
    )
    IDRule.objects.filter(command_output=".mxl").delete()

    FormatVersion.objects.create(
        format_id="c269901a-a61b-4790-99ce-af6d9dbe79f5",
        pronom_id="fmt/1971",
        description="""Enigma Binary File (Finale) v.1""",
        version="1",
        uuid="1586ee31-dc61-45d0-9677-d4964a183854",
    )
    IDRule.objects.filter(command_output=".mus").delete()

    FormatVersion.objects.create(
        format_id="c269901a-a61b-4790-99ce-af6d9dbe79f5",
        pronom_id="fmt/1972",
        description="""Enigma Binary File (Finale) v.2""",
        version="2",
        uuid="ad589321-3a03-4009-a8ed-c3d53de4a9fc",
    )
    IDRule.objects.create(
        format_id="ad589321-3a03-4009-a8ed-c3d53de4a9fc",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".mus",
    )

    Format.objects.create(
        description="""Finale Performance Assessment""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="8b8bf6ff-bd4c-40ea-ae72-7178b1063c18",
    )
    FormatVersion.objects.create(
        format_id="8b8bf6ff-bd4c-40ea-ae72-7178b1063c18",
        pronom_id="fmt/1973",
        description="""Finale Performance Assessment""",
        version="None",
        uuid="184513af-8194-4023-80d6-c0232d5ebf31",
    )
    IDRule.objects.create(
        format_id="184513af-8194-4023-80d6-c0232d5ebf31",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".fpa",
    )

    Format.objects.create(
        description="""Finale Notation File""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="f6a1e52e-9451-4828-963a-79bc10b8d032",
    )
    FormatVersion.objects.create(
        format_id="f6a1e52e-9451-4828-963a-79bc10b8d032",
        pronom_id="fmt/1974",
        description="""Finale Notation File""",
        version="2014+",
        uuid="f24f2ab1-f804-4c22-b9ff-949a44020f72",
    )
    IDRule.objects.filter(command_output=".musx").delete()

    Format.objects.create(
        description="""ICC Profile""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="2ea04202-e4fe-4e1b-a11a-1782469aedd1",
    )
    FormatVersion.objects.create(
        format_id="2ea04202-e4fe-4e1b-a11a-1782469aedd1",
        pronom_id="fmt/1975",
        description="""ICC Profie v2""",
        version="2",
        uuid="c627f600-9578-47c5-9283-baecd69d4b23",
    )
    IDRule.objects.create(
        format_id="c627f600-9578-47c5-9283-baecd69d4b23",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".icc",
    )

    FormatVersion.objects.create(
        format_id="2ea04202-e4fe-4e1b-a11a-1782469aedd1",
        pronom_id="fmt/1976",
        description="""ICC Profile v4""",
        version="4",
        uuid="d9ebb87b-f1fb-4186-a99f-06dc97560a9f",
    )
    IDRule.objects.filter(command_output=".icc").delete()

    FormatVersion.objects.create(
        format_id="2ea04202-e4fe-4e1b-a11a-1782469aedd1",
        pronom_id="fmt/1977",
        description="""ICC Profile v5""",
        version="iccMAX",
        uuid="ea63bd0d-6668-47e2-b7e7-a7c5d08f88d5",
    )
    IDRule.objects.create(
        format_id="ea63bd0d-6668-47e2-b7e7-a7c5d08f88d5",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".icc",
    )

    Format.objects.create(
        description="""Sibelius Score""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="17f42669-2d81-496d-b14f-cb3dd82ed801",
    )
    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1978",
        description="""Sibelius Score v.1.2""",
        version="1.2",
        uuid="9877789c-464d-43f0-97fb-4a2903fa9514",
    )
    IDRule.objects.filter(command_output=".sib").delete()

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1979",
        description="""Sibelius Score v.2""",
        version="2",
        uuid="95ae84bd-03a1-4e34-9a30-6b3f9f01f3d6",
    )
    IDRule.objects.create(
        format_id="95ae84bd-03a1-4e34-9a30-6b3f9f01f3d6",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sib",
    )

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1980",
        description="""Sibelius Score v.3""",
        version="3",
        uuid="3423b862-b6cd-4973-a0d1-16f950a0c680",
    )
    IDRule.objects.filter(command_output=".sib").delete()

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1981",
        description="""Sibelius Score v.4""",
        version="4",
        uuid="79955af3-ac70-424c-90e9-43276bffca63",
    )
    IDRule.objects.create(
        format_id="79955af3-ac70-424c-90e9-43276bffca63",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sib",
    )

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1982",
        description="""Sibelius Score v.5""",
        version="5",
        uuid="14ddd997-d3af-4c8a-b542-642d779bd57d",
    )
    IDRule.objects.filter(command_output=".sib").delete()

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1983",
        description="""Sibelius Score v.6""",
        version="6",
        uuid="66f6deef-ef9e-4e14-bc45-f4d24b742f3a",
    )
    IDRule.objects.create(
        format_id="66f6deef-ef9e-4e14-bc45-f4d24b742f3a",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sib",
    )

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1984",
        description="""Sibelius Score v.7""",
        version="7",
        uuid="953f41ab-e98a-4f0a-a0b4-fb84e625f312",
    )
    IDRule.objects.filter(command_output=".sib").delete()

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1985",
        description="""Sibelius Score v.7.5-8.0""",
        version="7.5-8.0",
        uuid="67819faf-bcca-425d-a56f-28fa279e23d1",
    )
    IDRule.objects.create(
        format_id="67819faf-bcca-425d-a56f-28fa279e23d1",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sib",
    )

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1986",
        description="""Sibelius Score v.8.1-8.5""",
        version="8.1-8.5",
        uuid="788e0a72-18b7-4d75-9797-7b91a94ccef4",
    )
    IDRule.objects.filter(command_output=".sib").delete()

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1987",
        description="""Sibelius Score v.8.6-2019.12""",
        version="",
        uuid="c86d7daa-420c-4068-8f0e-6437a3a424a2",
    )
    IDRule.objects.create(
        format_id="c86d7daa-420c-4068-8f0e-6437a3a424a2",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sib",
    )

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1988",
        description="""Sibelius Score v.2020.1""",
        version="2020.1",
        uuid="aabcfb8a-3a2f-41b9-a9e5-617e60fc2388",
    )
    IDRule.objects.filter(command_output=".sib").delete()

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1989",
        description="""Sibelius Score v.2020.3-2022.5""",
        version="",
        uuid="f503b129-1ebf-4866-a7e0-7cd46e0fa161",
    )
    IDRule.objects.create(
        format_id="f503b129-1ebf-4866-a7e0-7cd46e0fa161",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sib",
    )

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1990",
        description="""Sibelius Score v.2022.7-2022.11""",
        version="",
        uuid="5e251d3b-2e91-4150-89bd-da93931cf812",
    )
    IDRule.objects.filter(command_output=".sib").delete()

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1991",
        description="""Sibelius Score v.2022.12-2023.3""",
        version="",
        uuid="2c28819c-cc31-4fa6-a284-54eb0c505490",
    )
    IDRule.objects.create(
        format_id="2c28819c-cc31-4fa6-a284-54eb0c505490",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sib",
    )

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1992",
        description="""Sibelius Score v.2023.5-2023.8""",
        version="",
        uuid="4e09b394-0b04-4c3c-a0d1-e7656fdb83dc",
    )
    IDRule.objects.filter(command_output=".sib").delete()

    FormatVersion.objects.create(
        format_id="17f42669-2d81-496d-b14f-cb3dd82ed801",
        pronom_id="fmt/1993",
        description="""Sibelius Score v.2024""",
        version="2024",
        uuid="d9be4eb6-7695-4724-99d4-a904236c444e",
    )
    IDRule.objects.create(
        format_id="d9be4eb6-7695-4724-99d4-a904236c444e",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sib",
    )

    Format.objects.create(
        description="""Sibelius Scorch""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="9fd09e78-091c-4c82-9295-e805bfbde356",
    )
    FormatVersion.objects.create(
        format_id="9fd09e78-091c-4c82-9295-e805bfbde356",
        pronom_id="fmt/1994",
        description="""Sibelius Scorch""",
        version="None",
        uuid="0bfff967-a249-4c48-9412-9185e8838158",
    )
    IDRule.objects.create(
        format_id="0bfff967-a249-4c48-9412-9185e8838158",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".sco",
    )

    Format.objects.create(
        description="""WinFax Fax Image""",
        group_id="be86edbf-f62c-431f-b549-300d23c7cd0d",
        uuid="ae54ee29-5b7a-4cb0-b3b0-703516a1f3ec",
    )
    FormatVersion.objects.create(
        format_id="ae54ee29-5b7a-4cb0-b3b0-703516a1f3ec",
        pronom_id="fmt/1995",
        description="""WinFax Fax Image""",
        version="None",
        uuid="48e8e2f6-4767-4bf2-a9d2-53c3441dab6f",
    )
    IDRule.objects.create(
        format_id="48e8e2f6-4767-4bf2-a9d2-53c3441dab6f",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".fxr",
    )

    Format.objects.create(
        description="""SPIR-V""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="02937b41-c87c-45d9-9e24-0897c89892c2",
    )
    FormatVersion.objects.create(
        format_id="02937b41-c87c-45d9-9e24-0897c89892c2",
        pronom_id="fmt/1996",
        description="""SPIR-V""",
        version="None",
        uuid="eef17fa2-e12d-43bd-b9a6-6f52ecc3e37d",
    )
    IDRule.objects.create(
        format_id="eef17fa2-e12d-43bd-b9a6-6f52ecc3e37d",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".spirv",
    )

    Format.objects.create(
        description="""IMF Package Asset Map""",
        group_id="89961b53-4d5c-49e2-9910-8825d96c8640",
        uuid="ca7a58ac-3125-4f61-9bf8-e6719cb273f7",
    )
    FormatVersion.objects.create(
        format_id="ca7a58ac-3125-4f61-9bf8-e6719cb273f7",
        pronom_id="fmt/1997",
        description="""IMF Package Asset Map""",
        version="None",
        uuid="d5069141-6f1b-449f-a175-3a31b3f022f9",
    )
    IDRule.objects.filter(command_output=".xml").delete()

    Format.objects.create(
        description="""IMF Package Packing List""",
        group_id="89961b53-4d5c-49e2-9910-8825d96c8640",
        uuid="4dd81041-9644-4270-97a6-299aa675a64b",
    )
    FormatVersion.objects.create(
        format_id="4dd81041-9644-4270-97a6-299aa675a64b",
        pronom_id="fmt/1998",
        description="""IMF Package Packing List""",
        version="None",
        uuid="30be40eb-f7bd-4dff-bd24-d9c397c51534",
    )
    IDRule.objects.create(
        format_id="30be40eb-f7bd-4dff-bd24-d9c397c51534",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".xml",
    )

    Format.objects.create(
        description="""IMF Package Composition Playlist""",
        group_id="89961b53-4d5c-49e2-9910-8825d96c8640",
        uuid="e8394ae8-fb2c-49fc-bcbb-ee30fa06fd9c",
    )
    FormatVersion.objects.create(
        format_id="e8394ae8-fb2c-49fc-bcbb-ee30fa06fd9c",
        pronom_id="fmt/1999",
        description="""IMF Package Composition Playlist""",
        version="None",
        uuid="2f9c3586-08b1-42ca-aa4c-9395513368eb",
    )
    IDRule.objects.filter(command_output=".xml").delete()

    Format.objects.create(
        description="""Husqvarna Embroidery Stitch File""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="54ca3c25-f8a2-418c-b68d-050c344b7721",
    )
    FormatVersion.objects.create(
        format_id="54ca3c25-f8a2-418c-b68d-050c344b7721",
        pronom_id="fmt/2000",
        description="""Husqvarna Embroidery Stitch File""",
        version="None",
        uuid="a14634af-09e3-49e1-af5c-86107759638e",
    )
    IDRule.objects.create(
        format_id="a14634af-09e3-49e1-af5c-86107759638e",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".hus",
    )

    Format.objects.create(
        description="""Husqvarna / Pfaff Embroidery Stitch File""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="2d0203e5-9176-4412-ae81-dd0d5bc8704d",
    )
    FormatVersion.objects.create(
        format_id="2d0203e5-9176-4412-ae81-dd0d5bc8704d",
        pronom_id="fmt/2001",
        description="""Husqvarna / Pfaff Embroidery Stitch File""",
        version="None",
        uuid="aaabe296-406c-4573-9a39-69e03620b876",
    )
    IDRule.objects.create(
        format_id="aaabe296-406c-4573-9a39-69e03620b876",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".vip",
    )

    Format.objects.create(
        description="""Husqvarna / TruE Embroidery Stitch File""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="6b5fb194-fc87-49d7-a9e8-e0f3204a62ba",
    )
    FormatVersion.objects.create(
        format_id="6b5fb194-fc87-49d7-a9e8-e0f3204a62ba",
        pronom_id="fmt/2002",
        description="""Husqvarna / TruE Embroidery Stitch File""",
        version="None",
        uuid="64899ad4-d7c0-4052-b212-a9d8fae13945",
    )
    IDRule.objects.create(
        format_id="64899ad4-d7c0-4052-b212-a9d8fae13945",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".vp3",
    )

    Format.objects.create(
        description="""Husqvarna / Premier+ Embroidery Stitch File""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="c2aa12a6-d6ab-4632-bde6-61c2689db700",
    )
    FormatVersion.objects.create(
        format_id="c2aa12a6-d6ab-4632-bde6-61c2689db700",
        pronom_id="fmt/2003",
        description="""Husqvarna / Premier+ Stitch File""",
        version="None",
        uuid="59ecf79a-8ca9-4d65-8818-9ebfcbceec44",
    )
    IDRule.objects.create(
        format_id="59ecf79a-8ca9-4d65-8818-9ebfcbceec44",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".vp4",
    )

    Format.objects.create(
        description="""Husqvarna-Viking Designer 1 Stitch File""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="8254bb32-b22a-4115-bce5-d92701076fef",
    )
    FormatVersion.objects.create(
        format_id="8254bb32-b22a-4115-bce5-d92701076fef",
        pronom_id="fmt/2004",
        description="""Husqvarna-Viking Designer 1 Stitch File""",
        version="None",
        uuid="189e2172-9a64-4394-9484-58f533456ccd",
    )
    IDRule.objects.create(
        format_id="189e2172-9a64-4394-9484-58f533456ccd",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".shv",
    )

    Format.objects.create(
        description="""Compressed MusicXML""",
        group_id="00abbdd0-51b3-4162-b93a-45deb4ed8654",
        uuid="9defae19-8a2a-4886-81f0-26682466dea5",
    )
    FormatVersion.objects.create(
        format_id="9defae19-8a2a-4886-81f0-26682466dea5",
        pronom_id="fmt/2005",
        description="""Compressed MusicXML""",
        version="3.1+",
        uuid="a04f84bc-0879-4843-b33a-28d08602e4f5",
    )
    IDRule.objects.create(
        format_id="a04f84bc-0879-4843-b33a-28d08602e4f5",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".mxl",
    )

    FormatVersion.objects.create(
        format_id="896e3639-f500-4b6f-9d1d-9747519ed17f",
        pronom_id="fmt/2006",
        description="""QuarkXPress 18 (Motorola)""",
        version="18",
        uuid="ad619dad-2f34-4a2b-a3b7-7cf48ee5ba20",
    )
    IDRule.objects.filter(command_output=".qxp").delete()

    FormatVersion.objects.create(
        format_id="896e3639-f500-4b6f-9d1d-9747519ed17f",
        pronom_id="fmt/2007",
        description="""QuarkXPress 19 (Motorola)""",
        version="19",
        uuid="90ddeca1-dd2c-46b5-857f-1ee8d4a66365",
    )
    IDRule.objects.create(
        format_id="90ddeca1-dd2c-46b5-857f-1ee8d4a66365",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".qxp",
    )

    FormatVersion.objects.create(
        format_id="896e3639-f500-4b6f-9d1d-9747519ed17f",
        pronom_id="fmt/2008",
        description="""QuarkXPress 20 (Motorola)""",
        version="20",
        uuid="2c0de7f2-2e75-499e-ae39-26a82ccd3261",
    )
    IDRule.objects.filter(command_output=".qxp").delete()

    Format.objects.create(
        description="""Protein Data Bank File""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="07924713-c889-434e-8703-e04764600506",
    )
    FormatVersion.objects.create(
        format_id="07924713-c889-434e-8703-e04764600506",
        pronom_id="fmt/2009",
        description="""Protein Data Bank File v.3.3""",
        version="3.3",
        uuid="3e59d742-521f-431a-bfe9-77d35313c993",
    )
    IDRule.objects.filter(command_output=".pdb").delete()

    Format.objects.create(
        description="""Visualization Toolkit""",
        group_id="8d32bf98-b569-4469-8953-10416b53b920",
        uuid="02234cb1-2615-47d5-9ccd-ea1c60b9a877",
    )
    FormatVersion.objects.create(
        format_id="02234cb1-2615-47d5-9ccd-ea1c60b9a877",
        pronom_id="fmt/2010",
        description="""vtk v.1""",
        version="1.0",
        uuid="f64c9a9e-94db-4c12-adb1-a6508fb1b077",
    )
    IDRule.objects.create(
        format_id="f64c9a9e-94db-4c12-adb1-a6508fb1b077",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".vtk",
    )

    FormatVersion.objects.create(
        format_id="02234cb1-2615-47d5-9ccd-ea1c60b9a877",
        pronom_id="fmt/2011",
        description="""vtk v.2""",
        version="2.0",
        uuid="0420ebed-803a-4bac-b87e-9d64661bc4d6",
    )
    IDRule.objects.filter(command_output=".vtk").delete()

    FormatVersion.objects.create(
        format_id="02234cb1-2615-47d5-9ccd-ea1c60b9a877",
        pronom_id="fmt/2012",
        description="""vtk v.4.2""",
        version="4.2",
        uuid="fea63b8e-ef1b-4dc1-a2ac-9290f3feef58",
    )
    IDRule.objects.create(
        format_id="fea63b8e-ef1b-4dc1-a2ac-9290f3feef58",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".vtk",
    )

    Format.objects.create(
        description="""RawACF""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="0d7a0f03-9df5-481d-97fa-19187c697539",
    )
    FormatVersion.objects.create(
        format_id="0d7a0f03-9df5-481d-97fa-19187c697539",
        pronom_id="fmt/2013",
        description="""RawACF""",
        version="None",
        uuid="78935e71-625a-408c-a51a-9e212be15144",
    )
    IDRule.objects.create(
        format_id="78935e71-625a-408c-a51a-9e212be15144",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".rawacf",
    )

    Format.objects.create(
        description="""Axon Binary Format""",
        group_id="9c183a8f-89b7-47cc-a6ba-4ed038cf63d5",
        uuid="617e119d-b394-41fe-ba46-65a40f7c0859",
    )
    FormatVersion.objects.create(
        format_id="617e119d-b394-41fe-ba46-65a40f7c0859",
        pronom_id="fmt/2014",
        description="""Axon Binary Format""",
        version="None",
        uuid="3ec8b5d3-b6f1-4234-8da3-e4ab920677d5",
    )
    IDRule.objects.create(
        format_id="3ec8b5d3-b6f1-4234-8da3-e4ab920677d5",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".abf",
    )

    Format.objects.create(
        description="""KryoFlux Stream""",
        group_id="289ce9cf-7991-48e4-abbe-ca373ef632cf",
        uuid="8b4c1389-57e7-4cb6-b193-b4187d7fa070",
    )
    FormatVersion.objects.create(
        format_id="8b4c1389-57e7-4cb6-b193-b4187d7fa070",
        pronom_id="fmt/2015",
        description="""KryoFlux Stream v.3""",
        version="3",
        uuid="e133cc8c-3855-4014-8c28-6e75e8ebd52d",
    )
    IDRule.objects.filter(command_output=".raw").delete()

    Format.objects.create(
        description="""Binvox""",
        group_id="8d32bf98-b569-4469-8953-10416b53b920",
        uuid="47498ffa-f70c-4b40-b281-113fa83cc656",
    )
    FormatVersion.objects.create(
        format_id="47498ffa-f70c-4b40-b281-113fa83cc656",
        pronom_id="fmt/2016",
        description="""Binvox v.1""",
        version="1",
        uuid="93fb6830-358b-40fa-844f-00934a7ac455",
    )
    IDRule.objects.create(
        format_id="93fb6830-358b-40fa-844f-00934a7ac455",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".binvox",
    )

    FormatVersion.objects.create(
        format_id="39d89ff4-f419-455a-902e-895255b21261",
        pronom_id="fmt/2017",
        description="""GraphPad Prism 5-9""",
        version="5-9",
        uuid="55abc77f-264d-4f3a-b6b5-f264baf55686",
    )
    IDRule.objects.create(
        format_id="55abc77f-264d-4f3a-b6b5-f264baf55686",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".pzfx",
    )

    Format.objects.create(
        description="""Sony OpenMG Audio""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="3714eeb2-324c-46ca-9d66-c9b06004c8ff",
    )
    FormatVersion.objects.create(
        format_id="3714eeb2-324c-46ca-9d66-c9b06004c8ff",
        pronom_id="fmt/2018",
        description="""Sony Open MG Audio""",
        version="None",
        uuid="0127fa9c-5d19-424b-9f10-05fcbea34d78",
    )
    IDRule.objects.create(
        format_id="0127fa9c-5d19-424b-9f10-05fcbea34d78",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".oma",
    )

    Format.objects.create(
        description="""askSam Document for DOS""",
        group_id="7d161ac1-2879-445d-8e6d-cbc9eff5c225",
        uuid="a0dbdee2-6e38-4a6b-9acf-e1edc20f889f",
    )
    FormatVersion.objects.create(
        format_id="a0dbdee2-6e38-4a6b-9acf-e1edc20f889f",
        pronom_id="fmt/2019",
        description="""askSam for DOS""",
        version="None",
        uuid="9efdec30-d1bc-4abd-ab3f-54f596e00008",
    )
    IDRule.objects.create(
        format_id="9efdec30-d1bc-4abd-ab3f-54f596e00008",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".ask",
    )

    Format.objects.create(
        description="""askSam Document for Windows""",
        group_id="7d161ac1-2879-445d-8e6d-cbc9eff5c225",
        uuid="75bf6e5a-f40f-479d-843a-0670c5641856",
    )
    FormatVersion.objects.create(
        format_id="75bf6e5a-f40f-479d-843a-0670c5641856",
        pronom_id="fmt/2020",
        description="""askSam for Windows v.1""",
        version="1",
        uuid="ba903ffd-50ee-49bd-96d5-d337b34fdbf2",
    )
    IDRule.objects.filter(command_output=".ask").delete()

    FormatVersion.objects.create(
        format_id="75bf6e5a-f40f-479d-843a-0670c5641856",
        pronom_id="fmt/2021",
        description="""askSam for Windows v.2-3""",
        version="2-3",
        uuid="57223ceb-7047-452a-a800-f291c9ba9b7c",
    )
    IDRule.objects.create(
        format_id="57223ceb-7047-452a-a800-f291c9ba9b7c",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".ask",
    )

    FormatVersion.objects.create(
        format_id="75bf6e5a-f40f-479d-843a-0670c5641856",
        pronom_id="fmt/2022",
        description="""askSam for Windows v.4-7""",
        version="4-7",
        uuid="8cb1e911-2689-4ae4-a670-deaf302b8d45",
    )
    IDRule.objects.filter(command_output=".ask").delete()

    Format.objects.create(
        description="""Parquet File""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="d245bbe6-b461-4f3a-bd4d-f8bf7b9e151d",
    )
    FormatVersion.objects.create(
        format_id="d245bbe6-b461-4f3a-bd4d-f8bf7b9e151d",
        pronom_id="fmt/2023",
        description="""Parquet File""",
        version="None",
        uuid="9221caf5-5419-4efd-ab11-282925d2bb03",
    )
    IDRule.objects.create(
        format_id="9221caf5-5419-4efd-ab11-282925d2bb03",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".parquet",
    )

    Format.objects.create(
        description="""CD Architect Project File""",
        group_id="7d161ac1-2879-445d-8e6d-cbc9eff5c225",
        uuid="906669ab-969a-463d-b815-a7cb1e208e01",
    )
    FormatVersion.objects.create(
        format_id="906669ab-969a-463d-b815-a7cb1e208e01",
        pronom_id="fmt/2024",
        description="""CD Architect 4""",
        version="4",
        uuid="89d5ced6-c147-47ff-bdae-f527d2ef01da",
    )
    IDRule.objects.create(
        format_id="89d5ced6-c147-47ff-bdae-f527d2ef01da",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".cdp",
    )

    FormatVersion.objects.create(
        format_id="906669ab-969a-463d-b815-a7cb1e208e01",
        pronom_id="fmt/2025",
        description="""CD Architect 5""",
        version="5",
        uuid="dd584c1a-5c65-49e1-9e11-761b6defb6ca",
    )
    IDRule.objects.filter(command_output=".cdp").delete()

    Format.objects.create(
        description="""Codebook Exchange Format""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="d467c620-1ab7-43d2-b131-8399f02a6186",
    )
    FormatVersion.objects.create(
        format_id="d467c620-1ab7-43d2-b131-8399f02a6186",
        pronom_id="fmt/2026",
        description="""Codebook Exchange Format""",
        version="None",
        uuid="fe37498d-6549-45e0-b5c0-4ad4cde2b903",
    )
    IDRule.objects.create(
        format_id="fe37498d-6549-45e0-b5c0-4ad4cde2b903",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".qdc",
    )

    FormatVersion.objects.create(
        format_id="efe751be-6225-469f-96d8-4abb25ba0302",
        pronom_id="fmt/2027",
        description="""Microsoft Project v.1""",
        version="1",
        uuid="d05a45b7-53b2-4491-ba5c-84c509dcbc4b",
    )
    IDRule.objects.filter(command_output=".mpp").delete()

    FormatVersion.objects.create(
        format_id="efe751be-6225-469f-96d8-4abb25ba0302",
        pronom_id="fmt/2028",
        description="""Microsoft Project v.3""",
        version="3",
        uuid="d1f3a088-f472-4067-a6e9-22a66285945b",
    )
    IDRule.objects.create(
        format_id="d1f3a088-f472-4067-a6e9-22a66285945b",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".mpp",
    )

    Format.objects.create(
        description="""Apache Avro""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="29f6de66-8720-4d23-92f7-02e7d22c89a9",
    )
    FormatVersion.objects.create(
        format_id="29f6de66-8720-4d23-92f7-02e7d22c89a9",
        pronom_id="fmt/2029",
        description="""Apache Avro""",
        version="None",
        uuid="28dc979e-42eb-4fda-9f6d-4e0ca62e59c8",
    )
    IDRule.objects.create(
        format_id="28dc979e-42eb-4fda-9f6d-4e0ca62e59c8",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".avro",
    )

    Format.objects.create(
        description="""Apache ORC""",
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e",
        uuid="15c7eca5-c42a-4cf6-9094-7421f582bd4c",
    )
    FormatVersion.objects.create(
        format_id="15c7eca5-c42a-4cf6-9094-7421f582bd4c",
        pronom_id="fmt/2030",
        description="""Apache ORC""",
        version="V0 and V1",
        uuid="37278345-edb5-4073-9907-04f4e017ada8",
    )
    IDRule.objects.create(
        format_id="37278345-edb5-4073-9907-04f4e017ada8",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".orc",
    )

    Format.objects.create(
        description="""HxC Floppy Emulator Disk Image""",
        group_id="3616a69f-e9c4-4357-b366-57082cf75a3e",
        uuid="88c9c247-58ed-4865-94e1-4b5b84ff9a89",
    )
    FormatVersion.objects.create(
        format_id="88c9c247-58ed-4865-94e1-4b5b84ff9a89",
        pronom_id="fmt/2031",
        description="""HxC Floppy Emulator Disk Image""",
        version="None",
        uuid="600f1f17-3cc3-4c2c-9fa8-85759738a968",
    )
    IDRule.objects.create(
        format_id="600f1f17-3cc3-4c2c-9fa8-85759738a968",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".hfe",
    )

    Format.objects.create(
        description="""Open Packaging Format""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="13136e4b-a224-4097-b6b2-beb455110c82",
    )
    FormatVersion.objects.create(
        format_id="13136e4b-a224-4097-b6b2-beb455110c82",
        pronom_id="fmt/2032",
        description="""Open Packaging Format""",
        version="3",
        uuid="3e5ad5f8-3959-479c-8528-f6c42394f905",
    )
    IDRule.objects.filter(command_output=".opf").delete()

    Format.objects.create(
        description="""Daisy Talking Book Navigation Control File""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="1e82cd06-a79b-41f9-93e8-9e072faa3b61",
    )
    FormatVersion.objects.create(
        format_id="1e82cd06-a79b-41f9-93e8-9e072faa3b61",
        pronom_id="fmt/2033",
        description="""Daisy Talking Book Navigation Control File v.3""",
        version="3",
        uuid="d171a85f-ddda-4c22-887f-908b7c1b7056",
    )
    IDRule.objects.create(
        format_id="d171a85f-ddda-4c22-887f-908b7c1b7056",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".ncx",
    )

    Format.objects.create(
        description="""Daisy Talking Book Resource File""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="cd8b7550-5d70-437d-8361-474881c513fa",
    )
    FormatVersion.objects.create(
        format_id="cd8b7550-5d70-437d-8361-474881c513fa",
        pronom_id="fmt/2034",
        description="""Daisy Talking Book Resource file v.3""",
        version="3",
        uuid="2268e8ad-12f5-4103-a9af-be5f45da8c41",
    )
    IDRule.objects.create(
        format_id="2268e8ad-12f5-4103-a9af-be5f45da8c41",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".res",
    )

    Format.objects.create(
        description="""Plextalk Project File (imph)""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="253d9cd2-6da1-4280-86e6-42a96d631070",
    )
    FormatVersion.objects.create(
        format_id="253d9cd2-6da1-4280-86e6-42a96d631070",
        pronom_id="fmt/2035",
        description="""Plextalk Project File (imph)""",
        version="None",
        uuid="57791b95-220a-4715-812b-04f57d1916d4",
    )
    IDRule.objects.create(
        format_id="57791b95-220a-4715-812b-04f57d1916d4",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".imph",
    )

    Format.objects.create(
        description="""Plextalk Project File (imdn)""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="d3361ad2-a623-48de-9887-dc981471a78a",
    )
    FormatVersion.objects.create(
        format_id="d3361ad2-a623-48de-9887-dc981471a78a",
        pronom_id="fmt/2036",
        description="""Plextalk Project File (imdn)""",
        version="None",
        uuid="c762de68-f599-4350-bb5f-d1c9046162d3",
    )
    IDRule.objects.create(
        format_id="c762de68-f599-4350-bb5f-d1c9046162d3",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".imdn",
    )

    Format.objects.create(
        description="""Plextalk Project File (imtt)""",
        group_id="c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        uuid="b9a9b719-5188-4a7a-a59b-4aea7df12028",
    )
    FormatVersion.objects.create(
        format_id="b9a9b719-5188-4a7a-a59b-4aea7df12028",
        pronom_id="fmt/2037",
        description="""Plextalk Project File (imtt)""",
        version="None",
        uuid="c01732ec-9d92-4d0b-884b-e1aea95f46a6",
    )
    IDRule.objects.create(
        format_id="c01732ec-9d92-4d0b-884b-e1aea95f46a6",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".imtt",
    )

    FormatVersion.objects.create(
        format_id="88c9c247-58ed-4865-94e1-4b5b84ff9a89",
        pronom_id="fmt/2038",
        description="""HxC Floppy Emulator Disk Image v.3""",
        version="3",
        uuid="0a0ed164-a86c-44f0-94cb-3672ac11b0f6",
    )
    IDRule.objects.filter(command_output=".hfe").delete()

    Format.objects.create(
        description="""HxC Floppy Emulator Stream Image""",
        group_id="3616a69f-e9c4-4357-b366-57082cf75a3e",
        uuid="e5000f9a-0ec6-455d-b242-f739310294b3",
    )
    FormatVersion.objects.create(
        format_id="e5000f9a-0ec6-455d-b242-f739310294b3",
        pronom_id="fmt/2039",
        description="""HxC Floppy Emulator Stream Image""",
        version="None",
        uuid="1ed80e9c-3a01-4e3f-891b-d0acde9a02e1",
    )
    IDRule.objects.create(
        format_id="1ed80e9c-3a01-4e3f-891b-d0acde9a02e1",
        command_id="8546b624-7894-4201-8df6-f239d5e0d5ba",
        command_output=".hfe",
    )


class Migration(migrations.Migration):
    dependencies = [("fpr", "0047_update_format_groups")]
    operations = [migrations.RunPython(data_migration_up, migrations.RunPython.noop)]

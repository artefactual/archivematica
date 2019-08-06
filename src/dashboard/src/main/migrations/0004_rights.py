# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("main", "0003_archivesspacedipobjectresourcepairing_data")]

    operations = [
        migrations.AlterField(
            model_name="rightsstatement",
            name="metadataappliestoidentifier",
            field=models.CharField(
                max_length=36, db_column="metadataAppliesToidentifier", blank=True
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatement",
            name="rightsbasis",
            field=models.CharField(
                default="Copyright",
                max_length=64,
                verbose_name="Basis",
                db_column="rightsBasis",
                choices=[
                    ("Copyright", "Copyright"),
                    ("Statute", "Statute"),
                    ("License", "License"),
                    ("Donor", "Donor"),
                    ("Policy", "Policy"),
                    ("Other", "Other"),
                ],
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementcopyright",
            name="copyrightapplicableenddate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="Copyright end date",
                db_column="copyrightApplicableEndDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementcopyright",
            name="copyrightapplicablestartdate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="Copyright start date",
                db_column="copyrightApplicableStartDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementcopyright",
            name="copyrightjurisdiction",
            field=models.TextField(
                verbose_name="Copyright jurisdiction", db_column="copyrightJurisdiction"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementcopyright",
            name="copyrightstatus",
            field=models.TextField(
                verbose_name="Copyright status", db_column="copyrightStatus"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementcopyright",
            name="copyrightstatusdeterminationdate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="Copyright determination date",
                db_column="copyrightStatusDeterminationDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementcopyrightdocumentationidentifier",
            name="copyrightdocumentationidentifierrole",
            field=models.TextField(
                null=True,
                verbose_name="Copyright document identification role",
                db_column="copyrightDocumentationIdentifierRole",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementcopyrightdocumentationidentifier",
            name="copyrightdocumentationidentifiertype",
            field=models.TextField(
                verbose_name="Copyright document identification type",
                db_column="copyrightDocumentationIdentifierType",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementcopyrightdocumentationidentifier",
            name="copyrightdocumentationidentifiervalue",
            field=models.TextField(
                verbose_name="Copyright document identification value",
                db_column="copyrightDocumentationIdentifierValue",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementcopyrightnote",
            name="copyrightnote",
            field=models.TextField(
                verbose_name="Copyright note", db_column="copyrightNote"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementlicense",
            name="licenseapplicableenddate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="License end date",
                db_column="licenseApplicableEndDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementlicense",
            name="licenseapplicablestartdate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="License start date",
                db_column="licenseApplicableStartDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementlicense",
            name="licenseterms",
            field=models.TextField(
                null=True,
                verbose_name="License terms",
                db_column="licenseTerms",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementlicensedocumentationidentifier",
            name="licensedocumentationidentifierrole",
            field=models.TextField(
                null=True,
                verbose_name="License document identification role",
                db_column="licenseDocumentationIdentifierRole",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementlicensedocumentationidentifier",
            name="licensedocumentationidentifiertype",
            field=models.TextField(
                verbose_name="License documentation identification type",
                db_column="licenseDocumentationIdentifierType",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementlicensedocumentationidentifier",
            name="licensedocumentationidentifiervalue",
            field=models.TextField(
                verbose_name="License documentation identification value",
                db_column="licenseDocumentationIdentifierValue",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementlicensenote",
            name="licensenote",
            field=models.TextField(
                verbose_name="License note", db_column="licenseNote"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementotherrightsdocumentationidentifier",
            name="otherrightsdocumentationidentifierrole",
            field=models.TextField(
                null=True,
                verbose_name="Other rights document identification role",
                db_column="otherRightsDocumentationIdentifierRole",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementotherrightsdocumentationidentifier",
            name="otherrightsdocumentationidentifiertype",
            field=models.TextField(
                verbose_name="Other rights document identification type",
                db_column="otherRightsDocumentationIdentifierType",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementotherrightsdocumentationidentifier",
            name="otherrightsdocumentationidentifiervalue",
            field=models.TextField(
                verbose_name="Other right document identification value",
                db_column="otherRightsDocumentationIdentifierValue",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementotherrightsinformation",
            name="otherrightsapplicableenddate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="Other rights end date",
                db_column="otherRightsApplicableEndDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementotherrightsinformation",
            name="otherrightsapplicablestartdate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="Other rights start date",
                db_column="otherRightsApplicableStartDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementotherrightsinformation",
            name="otherrightsbasis",
            field=models.TextField(
                default="Other",
                verbose_name="Other rights basis",
                db_column="otherRightsBasis",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementotherrightsinformationnote",
            name="otherrightsnote",
            field=models.TextField(
                verbose_name="Other rights note", db_column="otherRightsNote"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementrightsgranted",
            name="act",
            field=models.TextField(db_column="act"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementrightsgranted",
            name="enddate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="End",
                db_column="endDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementrightsgranted",
            name="startdate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="Start",
                db_column="startDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementrightsgrantednote",
            name="rightsgrantednote",
            field=models.TextField(
                verbose_name="Rights note", db_column="rightsGrantedNote"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementrightsgrantedrestriction",
            name="restriction",
            field=models.TextField(db_column="restriction"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementstatutedocumentationidentifier",
            name="statutedocumentationidentifierrole",
            field=models.TextField(
                null=True,
                verbose_name="Statute document identification role",
                db_column="statuteDocumentationIdentifierRole",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementstatutedocumentationidentifier",
            name="statutedocumentationidentifiertype",
            field=models.TextField(
                verbose_name="Statute document identification type",
                db_column="statuteDocumentationIdentifierType",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementstatutedocumentationidentifier",
            name="statutedocumentationidentifiervalue",
            field=models.TextField(
                verbose_name="Statute document identification value",
                db_column="statuteDocumentationIdentifierValue",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementstatuteinformation",
            name="statuteapplicableenddate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="Statute end date",
                db_column="statuteApplicableEndDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementstatuteinformation",
            name="statuteapplicablestartdate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="Statute start date",
                db_column="statuteApplicableStartDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementstatuteinformation",
            name="statutecitation",
            field=models.TextField(
                verbose_name="Statute citation", db_column="statuteCitation"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementstatuteinformation",
            name="statutedeterminationdate",
            field=models.TextField(
                help_text="Use ISO 8061 (YYYY-MM-DD)",
                null=True,
                verbose_name="Statute determination date",
                db_column="statuteInformationDeterminationDate",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementstatuteinformation",
            name="statutejurisdiction",
            field=models.TextField(
                verbose_name="Statute jurisdiction", db_column="statuteJurisdiction"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="rightsstatementstatuteinformationnote",
            name="statutenote",
            field=models.TextField(
                verbose_name="Statute note", db_column="statuteNote"
            ),
            preserve_default=True,
        ),
    ]

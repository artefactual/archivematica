# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_archivesspacedipobjectresourcepairing_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rightsstatement',
            name='metadataappliestoidentifier',
            field=models.CharField(max_length=36, db_column=b'metadataAppliesToidentifier', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatement',
            name='rightsbasis',
            field=models.CharField(default=b'Copyright', max_length=64, verbose_name=b'Basis', db_column=b'rightsBasis', choices=[(b'Copyright', b'Copyright'), (b'Statute', b'Statute'), (b'License', b'License'), (b'Donor', b'Donor'), (b'Policy', b'Policy'), (b'Other', b'Other')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementcopyright',
            name='copyrightapplicableenddate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'Copyright end date', db_column=b'copyrightApplicableEndDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementcopyright',
            name='copyrightapplicablestartdate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'Copyright start date', db_column=b'copyrightApplicableStartDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementcopyright',
            name='copyrightjurisdiction',
            field=models.TextField(verbose_name=b'Copyright jurisdiction', db_column=b'copyrightJurisdiction'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementcopyright',
            name='copyrightstatus',
            field=models.TextField(verbose_name=b'Copyright status', db_column=b'copyrightStatus'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementcopyright',
            name='copyrightstatusdeterminationdate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'Copyright determination date', db_column=b'copyrightStatusDeterminationDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementcopyrightdocumentationidentifier',
            name='copyrightdocumentationidentifierrole',
            field=models.TextField(null=True, verbose_name=b'Copyright document identification role', db_column=b'copyrightDocumentationIdentifierRole', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementcopyrightdocumentationidentifier',
            name='copyrightdocumentationidentifiertype',
            field=models.TextField(verbose_name=b'Copyright document identification type', db_column=b'copyrightDocumentationIdentifierType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementcopyrightdocumentationidentifier',
            name='copyrightdocumentationidentifiervalue',
            field=models.TextField(verbose_name=b'Copyright document identification value', db_column=b'copyrightDocumentationIdentifierValue'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementcopyrightnote',
            name='copyrightnote',
            field=models.TextField(verbose_name=b'Copyright note', db_column=b'copyrightNote'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementlicense',
            name='licenseapplicableenddate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'License end date', db_column=b'licenseApplicableEndDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementlicense',
            name='licenseapplicablestartdate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'License start date', db_column=b'licenseApplicableStartDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementlicense',
            name='licenseterms',
            field=models.TextField(null=True, verbose_name=b'License terms', db_column=b'licenseTerms', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementlicensedocumentationidentifier',
            name='licensedocumentationidentifierrole',
            field=models.TextField(null=True, verbose_name=b'License document identification role', db_column=b'licenseDocumentationIdentifierRole', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementlicensedocumentationidentifier',
            name='licensedocumentationidentifiertype',
            field=models.TextField(verbose_name=b'License documentation identification type', db_column=b'licenseDocumentationIdentifierType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementlicensedocumentationidentifier',
            name='licensedocumentationidentifiervalue',
            field=models.TextField(verbose_name=b'License documentation identification value', db_column=b'licenseDocumentationIdentifierValue'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementlicensenote',
            name='licensenote',
            field=models.TextField(verbose_name=b'License note', db_column=b'licenseNote'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementotherrightsdocumentationidentifier',
            name='otherrightsdocumentationidentifierrole',
            field=models.TextField(null=True, verbose_name=b'Other rights document identification role', db_column=b'otherRightsDocumentationIdentifierRole', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementotherrightsdocumentationidentifier',
            name='otherrightsdocumentationidentifiertype',
            field=models.TextField(verbose_name=b'Other rights document identification type', db_column=b'otherRightsDocumentationIdentifierType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementotherrightsdocumentationidentifier',
            name='otherrightsdocumentationidentifiervalue',
            field=models.TextField(verbose_name=b'Other right document identification value', db_column=b'otherRightsDocumentationIdentifierValue'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementotherrightsinformation',
            name='otherrightsapplicableenddate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'Other rights end date', db_column=b'otherRightsApplicableEndDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementotherrightsinformation',
            name='otherrightsapplicablestartdate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'Other rights start date', db_column=b'otherRightsApplicableStartDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementotherrightsinformation',
            name='otherrightsbasis',
            field=models.TextField(default=b'Other', verbose_name=b'Other rights basis', db_column=b'otherRightsBasis'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementotherrightsinformationnote',
            name='otherrightsnote',
            field=models.TextField(verbose_name=b'Other rights note', db_column=b'otherRightsNote'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementrightsgranted',
            name='act',
            field=models.TextField(db_column=b'act'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementrightsgranted',
            name='enddate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'End', db_column=b'endDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementrightsgranted',
            name='startdate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'Start', db_column=b'startDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementrightsgrantednote',
            name='rightsgrantednote',
            field=models.TextField(verbose_name=b'Rights note', db_column=b'rightsGrantedNote'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementrightsgrantedrestriction',
            name='restriction',
            field=models.TextField(db_column=b'restriction'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementstatutedocumentationidentifier',
            name='statutedocumentationidentifierrole',
            field=models.TextField(null=True, verbose_name=b'Statute document identification role', db_column=b'statuteDocumentationIdentifierRole', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementstatutedocumentationidentifier',
            name='statutedocumentationidentifiertype',
            field=models.TextField(verbose_name=b'Statute document identification type', db_column=b'statuteDocumentationIdentifierType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementstatutedocumentationidentifier',
            name='statutedocumentationidentifiervalue',
            field=models.TextField(verbose_name=b'Statute document identification value', db_column=b'statuteDocumentationIdentifierValue'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementstatuteinformation',
            name='statuteapplicableenddate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'Statute end date', db_column=b'statuteApplicableEndDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementstatuteinformation',
            name='statuteapplicablestartdate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'Statute start date', db_column=b'statuteApplicableStartDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementstatuteinformation',
            name='statutecitation',
            field=models.TextField(verbose_name=b'Statute citation', db_column=b'statuteCitation'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementstatuteinformation',
            name='statutedeterminationdate',
            field=models.TextField(help_text=b'Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name=b'Statute determination date', db_column=b'statuteInformationDeterminationDate', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementstatuteinformation',
            name='statutejurisdiction',
            field=models.TextField(verbose_name=b'Statute jurisdiction', db_column=b'statuteJurisdiction'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rightsstatementstatuteinformationnote',
            name='statutenote',
            field=models.TextField(verbose_name=b'Statute note', db_column=b'statuteNote'),
            preserve_default=True,
        ),
    ]

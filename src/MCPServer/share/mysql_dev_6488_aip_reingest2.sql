
-- Update for mandatory/optional fields
ALTER TABLE RightsStatementCopyright
    MODIFY copyrightStatusDeterminationDate longtext NULL,
    MODIFY copyrightApplicableStartDate longtext NULL,
    MODIFY copyrightApplicableEndDate longtext NULL
    ;
ALTER TABLE RightsStatementCopyrightDocumentationIdentifier MODIFY copyrightDocumentationIdentifierRole longtext NULL;
ALTER TABLE RightsStatementLicense
    MODIFY licenseApplicableStartDate longtext NULL,
    MODIFY licenseApplicableEndDate longtext NULL
    ;
ALTER TABLE RightsStatementLicenseDocumentationIdentifier MODIFY licenseDocumentationIdentifierRole longtext NULL;
ALTER TABLE RightsStatementStatuteInformation
    MODIFY statuteInformationDeterminationDate longtext NULL,
    MODIFY statuteApplicableStartDate longtext NULL,
    MODIFY statuteApplicableEndDate longtext NULL
    ;
ALTER TABLE RightsStatementStatuteDocumentationIdentifier MODIFY statuteDocumentationIdentifierRole longtext NULL;
ALTER TABLE RightsStatementOtherRightsInformation
    MODIFY otherRightsApplicableStartDate longtext NULL,
    MODIFY otherRightsApplicableEndDate longtext NULL
    ;
ALTER TABLE RightsStatementOtherRightsDocumentationIdentifier MODIFY otherRightsDocumentationIdentifierRole longtext NULL;
ALTER TABLE RightsStatementRightsGranted
    MODIFY startDate longtext COLLATE utf8_unicode_ci NULL,
    MODIFY endDate longtext COLLATE utf8_unicode_ci NULL
    ;

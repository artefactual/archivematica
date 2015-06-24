
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

-- Only one exit code for determine version
DELETE FROM MicroServiceChainLinksExitCodes WHERE pk='7f2d5239-b464-4837-8e01-0fc43e31395d';
UPDATE MicroServiceChainLinksExitCodes SET exitCode=0 WHERE pk='6e06fd5e-3892-4e79-b64f-069876bd95a1';

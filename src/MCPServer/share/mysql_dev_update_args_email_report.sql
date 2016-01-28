-- Delete `date` and `server` arguments as they are not needed
UPDATE StandardTasksConfigs SET arguments = '--unitType "%unitType%" --unitIdentifier "%SIPUUID%" --unitName "%SIPName%"' WHERE execute = 'emailFailReport_v0.0';

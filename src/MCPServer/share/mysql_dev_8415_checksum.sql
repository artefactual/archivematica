-- Remove unused "checksumNoExtention" argument
UPDATE StandardTasksConfigs
    SET arguments='"%relativeLocation%" "%date%" "%taskUUID%" "%SIPUUID%"'
    WHERE execute='verifyMD5_v0.0';

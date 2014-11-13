-- Move Transfer/SIP name cleanup log into correct location
UPDATE StandardTasksConfigs
	SET standardErrorFile='%SIPLogsDirectory%SIPnameCleanup.log'
	WHERE standardErrorFile='%SIPDirectory%SIPnameCleanup.log';

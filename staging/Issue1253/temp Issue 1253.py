mysql> SELECT MicroServiceChainLinksPK FROM Jobs WHERE Jobs.jobType = 'Normalize' ORDER BY Jobs.createdTime;
+--------------------------------------+
| MicroServiceChainLinksPK             |
+--------------------------------------+
| 7509e7dc-1e1b-4dce-8d21-e130515fce73 |
| cb8e5706-e73f-472f-ad9b-d1236af8095f |
+--------------------------------------+
2 rows in set (0.00 sec)


mysql> SELECT MicroServiceChainLinksPK FROM Jobs WHERE Jobs.jobType = 'Approve normalization' ORDER BY Jobs.createdTime;
+--------------------------------------+
| MicroServiceChainLinksPK             |
+--------------------------------------+
| 150dcb45-46c3-4529-b35f-b0a8a5a553e9 |
| de909a42-c5b5-46e1-9985-c031b50e9d30 |
+--------------------------------------+
2 rows in set (0.00 sec)




DROP TABLE IF EXISTS UnitVariables;
CREATE TABLE UnitVariables (
    pk VARCHAR(50) PRIMARY KEY,
    unitType VARCHAR(50),    
    unitUUID VARCHAR(50),
    variable LONGTEXT,
    variableValue LONGTEXT,
    microServiceChainLink   VARCHAR(50),
    Foreign Key (microServiceChainLink) references MicroServiceChainLinks(pk),
    createdTime TIMESTAMP DEFAULT NOW(),
    updatedTime TIMESTAMP
) DEFAULT CHARSET=utf8;



DROP TABLE IF EXISTS TasksConfigsSetUnitVariable;
CREATE TABLE TasksConfigsSetUnitVariable (
    pk VARCHAR(50) PRIMARY KEY,
    variable LONGTEXT,
    variableValue LONGTEXT,
    microServiceChainLink   VARCHAR(50),
    Foreign Key (microServiceChainLink) references MicroServiceChainLinks(pk),
    createdTime TIMESTAMP DEFAULT NOW(),
    updatedTime TIMESTAMP
) DEFAULT CHARSET=utf8;



DROP TABLE IF EXISTS TasksConfigsUnitVariableLinkPull;
CREATE TABLE TasksConfigsUnitVariableLinkPull (
    pk VARCHAR(50) PRIMARY KEY,
    variable LONGTEXT,
    variableValue LONGTEXT,
    createdTime TIMESTAMP DEFAULT NOW(),
    updatedTime TIMESTAMP
) DEFAULT CHARSET=utf8;




SET Resume to selecting nomralization path

SELECT tool
4ca90c6d-e706-4c3d-9dcf-8fcddf9be9f1

    TasksConfigsSetUnitVariable
    

    TasksConfigsSetUnitVariable


    TasksConfigsSetUnitVariable



    TasksConfigsSetUnitVariable

GET Resume to processing Normalization path

SELECT normalization path
    TasksConfigsSetUnitVariable
    

    TasksConfigsSetUnitVariable


    TasksConfigsSetUnitVariable


    TasksConfigsSetUnitVariable


021d1e3a-f313-4f42-96c2-720ab821d566
86a0131c-ef4d-441c-9801-1748967b6da0
a72379af-5b19-4cd1-aca9-f814f7f01a11
9f835b12-31b6-4608-88da-e4c7dd3ca6ba
8dc6999f-40e0-4585-b466-2f56c2f6158e
7ea79b39-07f1-41d9-9b62-c9683d98c5ea
f6862483-9c7f-40b5-825f-634d764161d8
74526522-45e4-4276-8883-90624500c329
7c7d507c-7a10-445b-ac66-d307919625cf
b6a997aa-5f84-4959-8140-308f0f092e19
082de031-7756-4035-a9ce-8073e33b0f06
f6ef624d-7df0-497d-ab50-cc6165a0b4aa
848f8e7d-cbe5-4764-b80c-7a91c526ba53
2b7a7d4c-585d-4232-9529-cd4450e01516
2a49affd-1e91-4212-9f37-fe0cc900d35f
63b8133e-32cb-46ab-8564-0a1efe227565
adbf623c-5e81-4986-b388-874acff469e8
09cebd67-149f-487d-a77d-edcf7e6f8f8a
952602e8-4914-4049-bd72-d43659a1331b
96569caa-362b-4427-a676-ea6aba1b4ed5
6af530d4-9fb0-4cfc-8e25-82247f29b490
1b38057c-134d-442d-a324-7bb0c73e40ba
2a82367f-3588-4da9-a03e-ff5a1b28defb
b4e5da83-3371-4152-9007-d811f477e1aa



TasksConfigsSetUnitVariable (
    ->     pk VARCHAR(50) PRIMARY KEY,
    ->     variable LONGTEXT,
    ->     variableValue LONGTEXT,
    ->     microServiceChainLink   VARCHAR(50),
;
INSERT INTO TasksConfigs (taskType, taskTypePKReference, description)
    VALUES
    (7,       LAST_INSERT_ID(), 'Find thumbnail links to run.');
INSERT INTO MicroServiceChainLinks (microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@microserviceGroup, LAST_INSERT_ID(), @defaultNextChainLink);
SET @MicroServiceChainLink = LAST_INSERT_ID();
INSERT INTO MicroServiceChainLinksExitCodes (microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLink, 0, NULL);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;



TasksConfigsUnitVariableLinkPull (
    ->     pk VARCHAR(50) PRIMARY KEY,
    ->     variable LONGTEXT,
    ->     variableValue LONGTEXT,
    ->     createdTime TIMESTAMP DEFAULT NOW(),
    ->     updatedTime TIMESTAMP
    -> ) DEFAULT CHARSET=utf8;
Query OK, 0 rows affected (0.10 sec)





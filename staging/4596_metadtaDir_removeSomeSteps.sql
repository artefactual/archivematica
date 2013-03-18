SET foreign_key_checks = 0;

DELETE FROM MicroServiceChainLinks WHERE pk = '8d3ea3c8-26e2-4cc7-8237-5e2e2d1e3c9e';
DELETE FROM MicroServiceChainLinks WHERE pk = '2b1c8cca-ea96-4628-8e79-74e149f7a075';
DELETE FROM MicroServiceChainLinks WHERE pk = '7a5655a8-0750-4e20-8a0a-0935e04ebc52';
DELETE FROM MicroServiceChainLinks WHERE pk = 'eb14475a-a5a7-43a2-ac10-7132f1c758fa';


SELECT * FROM MicroServiceChainLinksExitCodes WHERE MicroServiceChainLinksExitCodes.microServiceChainLink NOT IN (SELECT pk FROM MicroServiceChainLinks);
DELETE   FROM MicroServiceChainLinksExitCodes WHERE MicroServiceChainLinksExitCodes.microServiceChainLink NOT IN (SELECT pk FROM MicroServiceChainLinks);

SELECT * FROM TasksConfigs WHERE TasksConfigs.pk NOT IN (SELECT MicroServiceChainLinks.currentTask FROM MicroServiceChainLinks);
DELETE   FROM TasksConfigs WHERE TasksConfigs.pk NOT IN (SELECT MicroServiceChainLinks.currentTask FROM MicroServiceChainLinks);



SELECT * FROM StandardTasksConfigs LEFT OUTER JOIN TasksConfigs ON StandardTasksConfigs.pk = TasksConfigs.taskTypePKReference WHERE TasksConfigs.pk IS NULL;
DELETE FROM StandardTasksConfigs WHERE pk IN (select * from (SELECT STC.pk FROM StandardTasksConfigs AS STC LEFT OUTER JOIN TasksConfigs AS TC ON STC.pk = TC.taskTypePKReference WHERE TC.pk IS NULL) AS t3);

SET foreign_key_checks = 1;

UPDATE  MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='f1e286f9-4ec7-4e19-820c-dae7b8ea7d09' WHERE microServiceChainLink = '8bc92801-4308-4e3b-885b-1a89fdcd3014';

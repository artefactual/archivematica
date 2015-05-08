-- Move select upload type to after content DM selection
-- Do not query server if upload type is project client

-- Remove direct upload vs project client from STC
UPDATE StandardTasksConfigs SET arguments='--uuid="%SIPUUID%" --dipDir "%SIPDirectory%"' WHERE pk='f9f7793c-5a70-4ffd-9727-159c1070e4f5';

-- Skip collections questions
SET @restructureMSCL='f12ece2c-fb7e-44de-ba87-7e3c5b6feb74' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChains SET startingLink=@restructureMSCL WHERE pk='526eded3-2280-4f10-ac86-eff6c464cc81';

-- Skip upload DIP
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='e3efab02-1860-42dd-a46c-25601251b930' WHERE microServiceChainLink=@restructureMSCL;
UPDATE MicroServiceChainLinks SET defaultNextChainLink='e3efab02-1860-42dd-a46c-25601251b930' WHERE pk=@restructureMSCL;

-- Delete collections based MSCLs
SET @d1='0745a713-c7dc-451d-87c1-ec3dc28568b8' COLLATE utf8_unicode_ci;
SET @d2='f7323418-9987-46ce-aac5-1fe0913c753a' COLLATE utf8_unicode_ci;
SET @d3='9304d028-8387-4ab5-9539-0aab9ac5bdb1' COLLATE utf8_unicode_ci;
SET @d4='45f01e11-47c7-45a3-a99b-48677eb321a5' COLLATE utf8_unicode_ci;
SET @d5='6fe4678a-b3fb-4144-a8a3-7386eb87247d' COLLATE utf8_unicode_ci;

DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@d1, @d2, @d3, @d4, @d5);
DELETE FROM MicroServiceChoiceReplacementDic WHERE choiceAvailableAtLink IN (@d1, @d2, @d3, @d4, @d5);
UPDATE MicroServiceChainLinks SET defaultNextChainLink=NULL WHERE pk IN (@d1, @d2, @d3, @d4, @d5);

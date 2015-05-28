-- these delete statements are optinal - they remove rows from the
-- MicroServiceChainLinks table that are no longer used by Archivematica
-- if your database has Jobs that reference any of these ChainLinks,
-- then you will not be able to delete those particular ChainLinks
-- which is fine.

SET @d1 = '1c7726a4-9165-4809-986a-bf4477c719ca' COLLATE utf8_unicode_ci;
SET @d2 = '26cf64e2-21b5-4935-a52b-71695870f1f2' COLLATE utf8_unicode_ci;
SET @d3 = '65916156-41a5-4ed2-9472-7dca11e6bc08' COLLATE utf8_unicode_ci;
SET @d4 = '14a0678f-9c2a-4995-a6bd-5acd141eeef1' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2, @d3, @d4);

SET @d0 = 'd05eaa5e-344b-4daa-b78b-c9f27c76499d' COLLATE utf8_unicode_ci;
SET @d1 = 'f4dea20e-f3fe-4a37-b20f-0e70a7bc960e' COLLATE utf8_unicode_ci;
SET @d2 = '5bddbb67-76b4-4bcb-9b85-a0d9337e7042' COLLATE utf8_unicode_ci;
SET @d3 = 'f3efc52e-22e1-4337-b8ed-b38dac0f9f77' COLLATE utf8_unicode_ci;
SET @d4 = 'd7681789-5f98-49bb-85d4-c01b34dac5b9' COLLATE utf8_unicode_ci;
SET @d5 = 'cf26b361-dd5f-4b62-a493-6ee02728bd5f' COLLATE utf8_unicode_ci;
SET @d6 = '01292b28-9588-4a85-953b-d92b29faf4d0' COLLATE utf8_unicode_ci;
SET @d7 = '2d751fc6-dc9d-4c52-b0d9-a4454cefb359' COLLATE utf8_unicode_ci;
SET @d8 = 'b063c4ce-ada1-4e72-a137-800f1c10905c' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE defaultNextChainLink in (@d0, @d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8);
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d0, @d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8);

SET @del = '58fcd2fd-bcdf-4e49-ad99-7e24cc8c3ba5' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk IN (@del);

SET @d1 = '2307b24a-a019-4b5b-a520-a6fff270a852' COLLATE utf8_unicode_ci;
SET @d2 = 'c4e109d6-38ee-4c92-b83d-bc4d360f6f2e' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2);

SET @d1 = '4df4cc06-3b03-4c6f-b5c4-bec12a97dc90' COLLATE utf8_unicode_ci;
SET @d2 = '5e4f7467-8637-49b2-a584-bae83dabf762' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2);

SET @d1 = '7d43afab-4d3e-4733-a3f2-84eb772e9e57' COLLATE utf8_unicode_ci;
SET @d2 = '48bfc7e1-75ed-44eb-a65c-0701c022d934' COLLATE utf8_unicode_ci;
SET @d3 = 'c73acd63-19c9-4ca8-912c-311107d0454e' COLLATE utf8_unicode_ci;
SET @d4 = 'f63970a2-dc63-4ab4-80a6-9bfd72e3cf5a' COLLATE utf8_unicode_ci;
SET @d5 = 'a58bd669-79af-4999-8654-951f638d4457' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE defaultNextChainLink IN (@d1, @d2, @d3, @d4, @d5);
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2, @d3, @d4, @d5);

SET @d1 = '25b5dc50-d42d-4ee2-91fc-5dcc3eef30a7' COLLATE utf8_unicode_ci;
SET @d2 = '1c0f5926-fd76-4571-a706-aa6564555199' COLLATE utf8_unicode_ci;
SET @d3 = '82c0eca0-d9b6-4004-9d77-ded9286a9ac7' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2, @d3);

SET @d1 = 'f2a6f2a5-2f92-47da-b63b-30326625f6ae' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk=@d1;

SET @d1 = '39ac9205-cb08-47b1-8bc3-d3375e37d9eb' COLLATE utf8_unicode_ci;
SET @d2 = 'bf6873f4-90b8-4393-9057-7f14f4687d72' COLLATE utf8_unicode_ci;
SET @d3 = '2f83c458-244f-47e5-a302-ce463163354e' COLLATE utf8_unicode_ci;
SET @d4 = '150dcb45-46c3-4529-b35f-b0a8a5a553e9' COLLATE utf8_unicode_ci;
SET @d5 = 'b443ba1a-a0b6-4f7c-aeb2-65bd83de5e8b' COLLATE utf8_unicode_ci;
SET @d6 = '0b5ad647-5092-41ce-9fe5-1cc376d0bc3f' COLLATE utf8_unicode_ci;
SET @d7 = 'f30b23d4-c8de-453d-9b92-50b86e21d3d5' COLLATE utf8_unicode_ci;
SET @d8 = 'ab0d3815-a9a3-43e1-9203-23a40c00c551' COLLATE utf8_unicode_ci;
SET @d9 = 'c168f1ee-5d56-4188-8521-09f0c5475133' COLLATE utf8_unicode_ci;
SET @d10 = 'f060d17f-2376-4c0b-a346-b486446e46ce' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8, @d9, @d10);

SET @d1 = '48199d23-afd0-4b9b-b8a3-cd80c7d45e7c' COLLATE utf8_unicode_ci;
SET @d2 = '1798e1d4-ec91-4299-a767-d10c32155d19' COLLATE utf8_unicode_ci;
SET @d3 = 'c425258a-cf54-44f9-b39f-cf14c7966a41' COLLATE utf8_unicode_ci;
SET @d4 = '8adb23cc-dee3-44da-8356-fa6ce849e4d6' COLLATE utf8_unicode_ci;
SET @d5 = 'd77ccaa0-3a3d-46ff-877f-4edf1a8179e2' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE defaultNextChainLink IN (@d1, @d2, @d3, @d4, @d5);
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2, @d3, @d4, @d5);

SET @d1='0745a713-c7dc-451d-87c1-ec3dc28568b8' COLLATE utf8_unicode_ci;
SET @d2='f7323418-9987-46ce-aac5-1fe0913c753a' COLLATE utf8_unicode_ci;
SET @d3='9304d028-8387-4ab5-9539-0aab9ac5bdb1' COLLATE utf8_unicode_ci;
SET @d4='45f01e11-47c7-45a3-a99b-48677eb321a5' COLLATE utf8_unicode_ci;
SET @d5='6fe4678a-b3fb-4144-a8a3-7386eb87247d' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2, @d3, @d4, @d5);

SET @removeIndexedAIPFiles='bfade79c-ab7b-11e2-bace-08002742f837' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk=@removeIndexedAIPFiles;

-- Delete unused MSCLs
SET @d1='663a11f6-91cb-4fef-9aa7-2594b3752e4c' COLLATE utf8_unicode_ci;
SET @d2='a132193a-2e79-4221-a092-c51839d566fb' COLLATE utf8_unicode_ci;
SET @d3='9e4e39be-0dad-41bc-bee0-35cb71e693df' COLLATE utf8_unicode_ci;
SET @d4='e888269d-460a-4cdf-9bc7-241c92734402' COLLATE utf8_unicode_ci;
-- Transfer backup
SET @d5='9fa0a0d1-25bb-4507-a5f7-f177d7fa920d' COLLATE utf8_unicode_ci;
SET @d6='c1339015-e15b-4303-8f37-a2516669ac4e' COLLATE utf8_unicode_ci;
SET @d7='a72afc44-fa28-4de7-b35f-c79b9f01aa5c' COLLATE utf8_unicode_ci;
SET @d8='478512a6-10e4-410a-847d-ce1e25d8d31c' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8);

SET @indexAIPfiles='3ba518ab-fc47-4cba-9b5c-79629adac10b' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinks WHERE pk=@indexAIPfiles;

-- Don't use weird normalization node, remove unitVars for that
SET @d1 = '29dece8e-55a4-4f2c-b4c2-365ab6376ceb' COLLATE utf8_unicode_ci;
SET @d2 = '635ba89d-0ad6-4fc9-acc3-e6069dffdcd5' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@d1, @d2);
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2);

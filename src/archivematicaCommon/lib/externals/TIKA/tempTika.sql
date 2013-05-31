INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('e898b49b-eb90-40b9-a48a-87566df7d2a6', 'image/tiff', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('06cd5b79-75fa-4356-a3d9-238a846f4665', 'e898b49b-eb90-40b9-a48a-87566df7d2a6', 'image/tiff', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('3b0291c4-666f-4114-b007-557565bf1db6', 'e898b49b-eb90-40b9-a48a-87566df7d2a6', '27c2969b-b6a0-441d-888d-85292b692064', '1628571b-c2cd-4822-afdb-53561400c7c4');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('7120c62d-0458-4f2f-a308-3416a3a21a13', 'e898b49b-eb90-40b9-a48a-87566df7d2a6', '3141bc6f-7f77-4809-9244-116b235e7330', 'a1921355-58c2-4d6f-9535-a6d227a0be16');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('2c0108de-95dd-4376-b9be-01b08c0d50c3', 'image/x-raw-sigma', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('7ad4500f-385a-4221-9323-95cac038a40e', '2c0108de-95dd-4376-b9be-01b08c0d50c3', 'image/x-raw-sigma', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('1907134e-8253-41f1-a2b1-c52022e8e0a2', '2c0108de-95dd-4376-b9be-01b08c0d50c3', '3141bc6f-7f77-4809-9244-116b235e7330', 'a1921355-58c2-4d6f-9535-a6d227a0be16');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('78de8d93-c3aa-4ba2-8789-861f31b936f4', '2c0108de-95dd-4376-b9be-01b08c0d50c3', '27c2969b-b6a0-441d-888d-85292b692064', '1628571b-c2cd-4822-afdb-53561400c7c4');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('dfa811c5-a43c-4301-810d-b21010d195b0', 'image/x-raw-minolta', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('56cd34fe-d16b-40eb-9865-ea1c1b66fa4b', 'dfa811c5-a43c-4301-810d-b21010d195b0', 'image/x-raw-minolta', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('2c638a4e-4a39-4770-8727-693a6381e17d', 'dfa811c5-a43c-4301-810d-b21010d195b0', '27c2969b-b6a0-441d-888d-85292b692064', '1628571b-c2cd-4822-afdb-53561400c7c4');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('5c0e49bd-a616-41cb-9a35-4efec011d0ef', 'dfa811c5-a43c-4301-810d-b21010d195b0', '3141bc6f-7f77-4809-9244-116b235e7330', 'a1921355-58c2-4d6f-9535-a6d227a0be16');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('e381d292-d3e4-41a7-80e9-4cd34a024b2e', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 1, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('b17ec158-2245-4132-9d6e-a121882e1efa', 'e381d292-d3e4-41a7-80e9-4cd34a024b2e', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('8d3f12d7-b1d8-423d-8366-de3be1bfdd9b', 'e381d292-d3e4-41a7-80e9-4cd34a024b2e', '3141bc6f-7f77-4809-9244-116b235e7330', '53d34372-8805-4adf-b940-6c05b835a94f');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('8e2cee0f-f252-4386-b21a-2bb8ed76a848', 'e381d292-d3e4-41a7-80e9-4cd34a024b2e', '3141bc6f-7f77-4809-9244-116b235e7330', '53d34372-8805-4adf-b940-6c05b835a94f');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('5c3f1092-0bb9-4974-b09b-4c82ee6966c5', 'video/x-ms-wmv', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('5a630c47-7768-4fdb-87b8-19823d923f87', '5c3f1092-0bb9-4974-b09b-4c82ee6966c5', 'video/x-ms-wmv', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('41b1bee1-0807-42b1-ae67-7cd4a8af2e9d', '5c3f1092-0bb9-4974-b09b-4c82ee6966c5', '3141bc6f-7f77-4809-9244-116b235e7330', 'bb5a6da2-4b89-4f8c-96e3-ca36c55d3337');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('3dead5d1-07c5-4f14-a963-b99fba986978', '5c3f1092-0bb9-4974-b09b-4c82ee6966c5', '3d1b570f-f500-4b3c-bbbc-4c58aad05c27', '76fd899e-cd5a-4da3-8752-45c43fc18656');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('a7d0039f-fe87-4fb9-9c2a-9442d3d26f2b', 'application/vnd.ms-excel', 1, 1, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('a2d0d1df-6406-4ac9-92ad-881abd660490', 'a7d0039f-fe87-4fb9-9c2a-9442d3d26f2b', 'application/vnd.ms-excel', 'Tika', '1.3');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('0c743b1b-4069-4090-b910-706939167554', 'application/x-123', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('3a8a6d90-3255-47a3-a213-81ad72b86935', '0c743b1b-4069-4090-b910-706939167554', 'application/x-123', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('0a290ab2-565f-47ec-ac80-5937357e26a9', '0c743b1b-4069-4090-b910-706939167554', '3141bc6f-7f77-4809-9244-116b235e7330', '6957fdac-a1ed-470f-89f7-fb00be42ea13');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('a65d705d-6a90-4b95-abfb-89ff3b22c1ba', '0c743b1b-4069-4090-b910-706939167554', '27c2969b-b6a0-441d-888d-85292b692064', '1628571b-c2cd-4822-afdb-53561400c7c4');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('cd3851e8-120c-41d4-a16c-2e363add98d4', '0c743b1b-4069-4090-b910-706939167554', '3d1b570f-f500-4b3c-bbbc-4c58aad05c27', 'a34ddc9b-c922-4bb6-8037-bbe713332175');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('97bf2b28-8d27-4ae0-b6da-0b3b58675a89', 'image/x-raw-canon', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('df06a2bb-e5b5-4a48-88f9-256f84941b27', '97bf2b28-8d27-4ae0-b6da-0b3b58675a89', 'image/x-raw-canon', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('f18aaebd-95b4-462d-a8df-c8bb0b4749b0', '97bf2b28-8d27-4ae0-b6da-0b3b58675a89', '3141bc6f-7f77-4809-9244-116b235e7330', 'a1921355-58c2-4d6f-9535-a6d227a0be16');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('71160681-bdf4-4eb9-a7a3-6422bfd0769f', '97bf2b28-8d27-4ae0-b6da-0b3b58675a89', '27c2969b-b6a0-441d-888d-85292b692064', '1628571b-c2cd-4822-afdb-53561400c7c4');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('2f31ecc3-830d-49e7-ad97-e2624e291f88', 'image/svg+xml', 1, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('0a0ba33a-49e8-402e-ba35-4b7e83f34680', '2f31ecc3-830d-49e7-ad97-e2624e291f88', 'image/svg+xml', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('19ee5056-82c0-480c-911a-d4a69a96c3f2', '2f31ecc3-830d-49e7-ad97-e2624e291f88', '3d1b570f-f500-4b3c-bbbc-4c58aad05c27', '64c450b4-135c-46d1-a9aa-3f9b15671677');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('d52b2524-e304-4964-a3cf-3b94e958357d', '2f31ecc3-830d-49e7-ad97-e2624e291f88', '3141bc6f-7f77-4809-9244-116b235e7330', 'd91f0637-b2f6-4492-ac1b-23c155102a3e');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('34a1798f-214a-4296-b383-ed9567a69efa', 'application/pdf', 0, 1, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('66a38c93-46c6-45d2-bd8f-902b6d07f0c5', '34a1798f-214a-4296-b383-ed9567a69efa', 'application/pdf', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('42b1b441-4f50-4c44-b9cd-d5c122592fac', '34a1798f-214a-4296-b383-ed9567a69efa', '3d1b570f-f500-4b3c-bbbc-4c58aad05c27', 'd6a33093-85d5-4088-83e1-b7a774a826bd');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('84160df2-1657-464a-946d-23325da63fca', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 1, 1, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('a3a1b0ae-1924-4ed5-ada4-e733df6d6092', '84160df2-1657-464a-946d-23325da63fca', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Tika', '1.3');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('793c1e30-5220-4dd9-bb0d-6f94c63222d6', 'audio/x-aiff', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('626eaea2-517c-48df-9caa-c0e366c8c23b', '793c1e30-5220-4dd9-bb0d-6f94c63222d6', 'audio/x-aiff', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('731a3c66-66ae-44a6-9e77-017f13018d57', '793c1e30-5220-4dd9-bb0d-6f94c63222d6', '3d1b570f-f500-4b3c-bbbc-4c58aad05c27', '9dc10fcb-5809-4c0b-917a-02517ef4d1c6');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('227593f2-0895-4291-a26e-450267e4838b', '793c1e30-5220-4dd9-bb0d-6f94c63222d6', '3141bc6f-7f77-4809-9244-116b235e7330', '520f976f-476d-4ec6-be1c-7c448c5c074d');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('81b378cc-0d0e-4894-8a9e-18424ac68487', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 1, 1, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('deabc04d-1f67-479d-ae80-7b1d920dfe37', '81b378cc-0d0e-4894-8a9e-18424ac68487', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Tika', '1.3');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('2437e13d-b620-4307-921a-51e539e6ca62', 'application/vnd.ms-powerpoint', 1, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('820cec83-702c-4033-bcf5-9579a44cf8bf', '2437e13d-b620-4307-921a-51e539e6ca62', 'application/vnd.ms-powerpoint', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('8f460cdd-f0f9-4d03-b454-71a5b5be4456', '2437e13d-b620-4307-921a-51e539e6ca62', '3141bc6f-7f77-4809-9244-116b235e7330', '53d34372-8805-4adf-b940-6c05b835a94f');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('5dac58e7-275d-447e-8409-10b5baefa868', 'video/mpeg', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('593810bc-f546-4e7e-ae06-d2810236537d', '5dac58e7-275d-447e-8409-10b5baefa868', 'video/mpeg', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('1072e9be-c91d-4670-82be-2d39a7cdb4c4', '5dac58e7-275d-447e-8409-10b5baefa868', '3141bc6f-7f77-4809-9244-116b235e7330', 'bb5a6da2-4b89-4f8c-96e3-ca36c55d3337');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('69751c5e-fbf5-4729-9fab-b588937d219c', '5dac58e7-275d-447e-8409-10b5baefa868', '3d1b570f-f500-4b3c-bbbc-4c58aad05c27', '76fd899e-cd5a-4da3-8752-45c43fc18656');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('9c2a7ca3-40ab-4ae3-98a2-990e8cb84107', 'application/msword', 1, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('375c4cab-7c24-41dd-814b-800b49466448', '9c2a7ca3-40ab-4ae3-98a2-990e8cb84107', 'application/msword', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('6ef02a97-81c1-4f2a-a841-6f88defcd7a8', '9c2a7ca3-40ab-4ae3-98a2-990e8cb84107', '3141bc6f-7f77-4809-9244-116b235e7330', '53d34372-8805-4adf-b940-6c05b835a94f');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('9e1194a9-8747-4218-93b6-c15a5da406cb', 'image/gif', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('076682f8-0946-4bf3-92d5-5ee34adc68bd', '9e1194a9-8747-4218-93b6-c15a5da406cb', 'image/gif', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('ea0f50df-c831-44d7-add4-8d2bfb3bec29', '9e1194a9-8747-4218-93b6-c15a5da406cb', '3d1b570f-f500-4b3c-bbbc-4c58aad05c27', 'a34ddc9b-c922-4bb6-8037-bbe713332175');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('a58629d6-9927-4473-9eb5-92523a09cb02', '9e1194a9-8747-4218-93b6-c15a5da406cb', '3141bc6f-7f77-4809-9244-116b235e7330', '6957fdac-a1ed-470f-89f7-fb00be42ea13');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('da7eb7ec-95cd-4436-8426-0669c47cb123', '9e1194a9-8747-4218-93b6-c15a5da406cb', '27c2969b-b6a0-441d-888d-85292b692064', '1628571b-c2cd-4822-afdb-53561400c7c4');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('99fb1250-7f9b-4f05-98e2-d5a5361ae4fa', 'audio/x-ms-wma', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('cb143a51-b713-4100-90a7-13bf4463f4ab', '99fb1250-7f9b-4f05-98e2-d5a5361ae4fa', 'audio/x-ms-wma', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('dfaa1643-dd2b-4828-bd23-c03ff5d7632c', '99fb1250-7f9b-4f05-98e2-d5a5361ae4fa', '3d1b570f-f500-4b3c-bbbc-4c58aad05c27', '9dc10fcb-5809-4c0b-917a-02517ef4d1c6');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('f9a5570d-64bc-46e5-9970-f99e2aa34bdd', '99fb1250-7f9b-4f05-98e2-d5a5361ae4fa', '3141bc6f-7f77-4809-9244-116b235e7330', '520f976f-476d-4ec6-be1c-7c448c5c074d');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('9020092a-5bb9-4bb8-93e9-841ffbf0523b', 'application/rtf', 1, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('55f41fff-cc25-462a-a435-6947d622b954', '9020092a-5bb9-4bb8-93e9-841ffbf0523b', 'application/rtf', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('6c43574b-12e9-4fb6-9ca3-ecd4329048c0', '9020092a-5bb9-4bb8-93e9-841ffbf0523b', '3141bc6f-7f77-4809-9244-116b235e7330', '53d34372-8805-4adf-b940-6c05b835a94f');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('190528c0-64f7-448b-971b-615483cca75e', 'image/png', 1, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('16583735-a362-47ef-ae50-b886856dd9b2', '190528c0-64f7-448b-971b-615483cca75e', 'image/png', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('7b197ea0-1e5d-45dd-9590-4a56f2e1bad8', '190528c0-64f7-448b-971b-615483cca75e', '27c2969b-b6a0-441d-888d-85292b692064', '1628571b-c2cd-4822-afdb-53561400c7c4');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('6f3419cd-e3d4-40b8-85df-89ad367e7426', '190528c0-64f7-448b-971b-615483cca75e', '3141bc6f-7f77-4809-9244-116b235e7330', '6957fdac-a1ed-470f-89f7-fb00be42ea13');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('eac7bb2f-8155-4f1a-adc8-ad939fe79e4e', 'video/quicktime', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('2bcccc30-6121-4d6a-8374-bfd675ba1d51', 'eac7bb2f-8155-4f1a-adc8-ad939fe79e4e', 'video/quicktime', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('78559ec7-c6c6-43ae-9813-9570bc86b4e1', 'eac7bb2f-8155-4f1a-adc8-ad939fe79e4e', '3d1b570f-f500-4b3c-bbbc-4c58aad05c27', '76fd899e-cd5a-4da3-8752-45c43fc18656');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('be5b635f-03a8-4327-908b-0bbb1160dd8d', 'eac7bb2f-8155-4f1a-adc8-ad939fe79e4e', '3141bc6f-7f77-4809-9244-116b235e7330', 'bb5a6da2-4b89-4f8c-96e3-ca36c55d3337');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('6c1e7dab-279a-427a-acc8-a0162c3b219e', 'audio/x-wav', 1, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('d0382db2-0566-4b6f-845a-fe3884c35fb8', '6c1e7dab-279a-427a-acc8-a0162c3b219e', 'audio/x-wav', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('b7623298-73f4-4cf8-8c12-f1e2cb908cd8', '6c1e7dab-279a-427a-acc8-a0162c3b219e', '3141bc6f-7f77-4809-9244-116b235e7330', '520f976f-476d-4ec6-be1c-7c448c5c074d');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('7b4f1fb8-7e8a-462f-b411-11888ee94427', 'image/x-raw-fuji', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('a2be06f8-564a-4311-ac3c-5f62faa32999', '7b4f1fb8-7e8a-462f-b411-11888ee94427', 'image/x-raw-fuji', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('7c8ac59a-29b5-4a07-a56a-5fbee7926822', '7b4f1fb8-7e8a-462f-b411-11888ee94427', '27c2969b-b6a0-441d-888d-85292b692064', '1628571b-c2cd-4822-afdb-53561400c7c4');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('5343eb45-87dd-4b26-96f7-cfc07b5b9fb9', '7b4f1fb8-7e8a-462f-b411-11888ee94427', '3141bc6f-7f77-4809-9244-116b235e7330', 'a1921355-58c2-4d6f-9535-a6d227a0be16');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('29bd84d4-304b-40a5-a0df-9316be7d5b27', 'application/postscript', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('5dbdede1-e5ea-4c61-b874-8a1397e7fe01', '29bd84d4-304b-40a5-a0df-9316be7d5b27', 'application/postscript', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('bb910a5a-28c4-45ca-bb7f-c483c0b29b6c', '29bd84d4-304b-40a5-a0df-9316be7d5b27', '3141bc6f-7f77-4809-9244-116b235e7330', 'e96b787d-57f6-41a4-9693-d0634bfacacb');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('c996d8d8-9ebe-4ff9-9bc7-ad9cacb549bf', '29bd84d4-304b-40a5-a0df-9316be7d5b27', '3d1b570f-f500-4b3c-bbbc-4c58aad05c27', '64c450b4-135c-46d1-a9aa-3f9b15671677');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('bbf3fa88-4b9f-42a8-91bb-434a3021df5e', 'image/x-raw-olympus', 0, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('2d9ba792-b41c-4a06-8093-c966b485f491', 'bbf3fa88-4b9f-42a8-91bb-434a3021df5e', 'image/x-raw-olympus', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('e7911098-24ed-4643-8181-5a56ab14e42d', 'bbf3fa88-4b9f-42a8-91bb-434a3021df5e', '3141bc6f-7f77-4809-9244-116b235e7330', 'a1921355-58c2-4d6f-9535-a6d227a0be16');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('7c366031-8909-436f-86cb-e31793478111', 'bbf3fa88-4b9f-42a8-91bb-434a3021df5e', '27c2969b-b6a0-441d-888d-85292b692064', '1628571b-c2cd-4822-afdb-53561400c7c4');

INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('bb7d4618-8dc1-4f9d-a3ac-3817b149ea1f', 'image/jp2', 1, 0, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');
INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('77ce31c5-5f17-468e-91a6-4d31f52a5983', 'bb7d4618-8dc1-4f9d-a3ac-3817b149ea1f', 'image/jp2', 'Tika', '1.3');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('ad8a76ab-265a-4c98-8dd0-0010bfe8659c', 'bb7d4618-8dc1-4f9d-a3ac-3817b149ea1f', '27c2969b-b6a0-441d-888d-85292b692064', '1628571b-c2cd-4822-afdb-53561400c7c4');
INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('f7979ddf-84e8-4219-a9ee-29156c84c3b7', 'bb7d4618-8dc1-4f9d-a3ac-3817b149ea1f', '3141bc6f-7f77-4809-9244-116b235e7330', '6957fdac-a1ed-470f-89f7-fb00be42ea13');


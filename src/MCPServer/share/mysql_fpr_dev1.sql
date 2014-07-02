-- Development changes to the FPR rules

-- Issue 6162

-- If script has a ; it should be a bashScript not a command, since command won't allow multiple commands in one
UPDATE fpr_fpcommand SET script_type='bashScript' WHERE command_usage ='event_detail' AND command LIKE '%;%';

-- End Issue 6162

-- Issue 5866 Characterization tools

-- New FITS command: runs FITS via the FPR instead of from archivematicaFITS.
-- This script is the default_characterization rule, so it gets called in the
-- case that no more specific rule is provided.
UPDATE `fpr_fpcommand` SET `replaces_id` = NULL, `enabled` = 0, `lastmodified` = '2013-11-15 01:18:36', `uuid` = '6537147f-4dd4-4950-8aff-5578db9a485d', `tool_id` = 'c5465b07-8dc7-475e-a5c9-ccb2ba2ed083', `description` = 'FITS', `command` = 'This is a placeholder command only, and should not be called.', `script_type` = 'as_is', `output_location` = '', `output_format_id` = 'd60e5243-692e-4af7-90cd-40c53cb8dc7d', `command_usage` = 'characterization', `verification_command_id` = NULL, `event_detail_command_id` = NULL WHERE `fpr_fpcommand`.`id` = 3;
INSERT INTO `fpr_fpcommand` (`replaces_id`, `enabled`, `lastmodified`, `uuid`, `tool_id`, `description`, `command`, `script_type`, `output_location`, `output_format_id`, `command_usage`, `verification_command_id`, `event_detail_command_id`) VALUES ('6537147f-4dd4-4950-8aff-5578db9a485d', 1, '2014-05-30 23:16:54', '183f6d5f-3a8e-4e5a-a6bc-948b9bfca176', 'c5465b07-8dc7-475e-a5c9-ccb2ba2ed083', 'FITS', 'fits.sh -i %relativeLocation%', 'command', NULL, 'd60e5243-692e-4af7-90cd-40c53cb8dc7d', 'characterization', NULL, NULL);
INSERT INTO `fpr_fprule` (`replaces_id`, `enabled`, `lastmodified`, `uuid`, `purpose`, `command_id`, `format_id`, `count_attempts`, `count_okay`, `count_not_okay`) VALUES (NULL, 1, '2014-05-30 23:53:13', '0eee2e2a-a31e-4b3e-a179-ef7211020c3b', 'default_characterization', '183f6d5f-3a8e-4e5a-a6bc-948b9bfca176', '0ab4cd40-90e7-4d75-b294-498177b3897d', 0, 0, 0);

-- /Issue 5866

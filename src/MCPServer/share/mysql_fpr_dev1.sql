-- Development changes to the FPR rules

-- Issue 6162

-- If script has a ; it should be a bashScript not a command, since command won't allow multiple commands in one
UPDATE fpr_fpcommand SET script_type='bashScript' WHERE command_usage ='event_detail' AND command LIKE '%;%';

-- End Issue 6162

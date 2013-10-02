BEGIN;
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE `fpr_idtool`;
TRUNCATE `fpr_idcommand`;
TRUNCATE `fpr_formatgroup`;
TRUNCATE `fpr_fpcommand`;
TRUNCATE `fpr_fptool`;
TRUNCATE `fpr_format`;
TRUNCATE `fpr_fprule`;
TRUNCATE `fpr_idrule`;
TRUNCATE `fpr_formatversion`;
SET FOREIGN_KEY_CHECKS = 1;

COMMIT;

-- These date fields used to use 0 as a "no date" value,
-- but Django is not able to represent that value.
-- Make them nullable and represent all non-dates as NULL instead.
ALTER TABLE Files
	MODIFY COLUMN removedTime timestamp NULL DEFAULT NULL;
UPDATE Files SET removedTime=NULL WHERE removedTime=0;

ALTER TABLE Tasks
	MODIFY COLUMN startTime timestamp NULL DEFAULT NULL,
	MODIFY COLUMN endTime timestamp NULL DEFAULT NULL;
UPDATE Tasks SET startTime=NULL WHERE startTime=0;
UPDATE Tasks SET endTime=NULL WHERE endTime=0;

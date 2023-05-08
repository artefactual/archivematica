-- name: CreateJob :exec
INSERT INTO Jobs (jobUUID, jobType) VALUES (?, ?);

-- name: CleanUpAwaitingJobs :exec
DELETE FROM Jobs WHERE currentStep = 1;

-- name: CleanUpActiveJobs :exec
UPDATE Jobs SET currentStep = 4 WHERE currentStep = 3;

-- name: CleanUpActiveTransfers :exec
UPDATE Transfers SET status = 4, completed_at = UTC_TIMESTAMP() WHERE status IN (0, 1);

-- name: CleanUpActiveSIPs :exec
UPDATE SIPs SET status = 4, completed_at = UTC_TIMESTAMP() WHERE status IN (0, 1);

-- name: CleanUpActiveTasks :exec
UPDATE Tasks SET exitCode = -1, stdError = "MCP shut down while processing." WHERE exitCode IS NULL;

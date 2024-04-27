package controller

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"time"

	"github.com/go-logr/logr"
	"github.com/google/uuid"

	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
)

type taskBackend struct {
	logger logr.Logger
	job    *job
	tasks  tasks

	// Present in all client chain links: files, directories, output.
	config *workflow.LinkStandardTaskConfig
}

func newTaskBackend(logger logr.Logger, job *job, config *workflow.LinkStandardTaskConfig) *taskBackend {
	return &taskBackend{
		logger: logger,
		job:    job,
		tasks:  tasks{map[uuid.UUID]*task{}},
		config: config,
	}
}

func (b *taskBackend) submit(pCtx *packageContext, args string, wantsOutput bool, stdoutFilePath, stderrFilePath string) uuid.UUID {
	t := &task{
		ID:             uuid.New(),
		CreatedAt:      mcpTime{time.Now().UTC()},
		Args:           args,
		stdoutFilePath: stdoutFilePath,
		stderrFilePath: stderrFilePath,
		pCtx:           pCtx,
	}

	if wantsOutput || stdoutFilePath != "" || stderrFilePath != "" {
		t.WantsOutput = true
	}

	b.tasks.Tasks[t.ID] = t

	return t.ID
}

func (b *taskBackend) wait(ctx context.Context) (*taskResults, error) {
	res, err := submitJob(ctx, b.logger, b.job.gearman, b.config.Execute, &b.tasks)
	b.logger.Info("Job executed.", "results", res, "err", err, "tasks", len(b.tasks.Tasks))
	if err != nil {
		return nil, err
	}

	return res, nil
}

type tasks struct {
	Tasks map[uuid.UUID]*task `json:"tasks"`
}

func (t tasks) MarshalJSON() ([]byte, error) {
	if len(t.Tasks) == 0 {
		return nil, errors.New("map is empty")
	}
	type alias tasks
	return json.Marshal(&struct{ *alias }{alias: (*alias)(&t)})
}

type task struct {
	ID          uuid.UUID `json:"task_uuid"`
	CreatedAt   time.Time `json:"createdDate"`
	Args        string    `json:"arguments"`
	WantsOutput bool      `json:"wants_output"`

	pCtx           *packageContext
	stdoutFilePath string
	stdout         string
	stderrFilePath string
	stderr         string
	exitCode       *int
	completedAt    time.Time
}

// writeOutput writes the stdout/stderr we got from MCPClient out to files if
// necessary.
func (t *task) writeOutput() (err error) {
	if t.stdoutFilePath != "" && t.stdout != "" {
		err = errors.Join(err, t.writeFile(t.stdoutFilePath, t.stdout))
	}
	if t.stderrFilePath != "" && t.stderr != "" {
		err = errors.Join(err, t.writeFile(t.stderrFilePath, t.stderr))
	}

	return err
}

func (t *task) writeFile(path, contents string) error {
	const mode = 0o750

	file, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, mode)
	if err != nil {
		return err
	}
	defer file.Close()

	if _, err := file.Write([]byte(contents)); err != nil {
		return err
	}

	if err := os.Chmod(path, mode); err != nil {
		return err
	}

	return nil
}

type taskResults struct {
	Results map[uuid.UUID]*taskResult `json:"task_results"`
}

func (tr taskResults) First() *taskResult {
	var r *taskResult
	for _, tr := range tr.Results {
		r = tr
		break
	}
	return r
}

func (tr taskResults) ExitCode() int {
	var code int
	for _, task := range tr.Results {
		if task.ExitCode > 0 {
			code = task.ExitCode
		}
	}
	return code
}

type taskResult struct {
	ExitCode   int       `json:"exitCode"`
	FinishedAt time.Time `json:"finishedTimestamp"`
	Stdout     string    `json:"stdout"`
	Stderr     string    `json:"stderr"`
}

package controller

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/google/uuid"
	"gotest.tools/v3/assert"
)

func TestTasksEncoding(t *testing.T) {
	t.Parallel()

	encoded := `{"tasks":{"5ef281c2-692f-49a2-b8dd-36ab4e2beca5":{"task_uuid":"5ef281c2-692f-49a2-b8dd-36ab4e2beca5","arguments":"\"%sharedPath%\"","wants_output":true,"createdDate":"2024-04-12T05:40:20.123456+00:00"}}}`
	tasks := tasks{
		Tasks: map[uuid.UUID]*task{
			uuid.MustParse("5ef281c2-692f-49a2-b8dd-36ab4e2beca5"): {
				ID:          uuid.MustParse("5ef281c2-692f-49a2-b8dd-36ab4e2beca5"),
				CreatedAt:   time.Date(2024, time.April, 12, 5, 40, 20, 123456000, time.UTC),
				Args:        "\"%sharedPath%\"",
				WantsOutput: true,
			},
		},
	}

	blob, err := json.Marshal(&tasks)

	assert.NilError(t, err)
	assert.Equal(t, string(blob), encoded)
}

func TestTaskResultsDecoding(t *testing.T) {
	t.Parallel()

	encoded := `{
		"task_results": {
			"89991b27-6276-4d83-bf8c-f62e6c2f9587": {
				"exitCode": 0,
				"finishedTimestamp": "2024-04-12T05:40:20.123456+00:00",
				"stdout": "data",
				"stderr": "data"
			}
		}
	}`

	ts := taskResults{}
	err := json.Unmarshal([]byte(encoded), &ts)

	assert.NilError(t, err)
	assert.DeepEqual(t, ts, taskResults{
		Results: map[uuid.UUID]*taskResult{
			uuid.MustParse("89991b27-6276-4d83-bf8c-f62e6c2f9587"): {
				ExitCode:   0,
				FinishedAt: time.Date(2024, time.April, 12, 5, 40, 20, 123456000, time.UTC),
				Stdout:     "data",
				Stderr:     "data",
			},
		},
	})
}

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

	encoded := `{"tasks":{"5ef281c2-692f-49a2-b8dd-36ab4e2beca5":{"task_uuid":"5ef281c2-692f-49a2-b8dd-36ab4e2beca5","createdDate":"2024-04-12 05:40:20+00:00","arguments":"\"%sharedPath%\"","wants_output":true}}}`
	decoded := tasks{
		Tasks: map[uuid.UUID]*task{
			uuid.MustParse("5ef281c2-692f-49a2-b8dd-36ab4e2beca5"): {
				ID:          uuid.MustParse("5ef281c2-692f-49a2-b8dd-36ab4e2beca5"),
				CreatedAt:   mcpTime{time.Date(2024, time.April, 12, 5, 40, 20, 0, time.UTC)},
				Args:        "\"%sharedPath%\"",
				WantsOutput: true,
			},
		},
	}

	t.Run("Encoding", func(t *testing.T) {
		t.Parallel()

		blob, err := json.Marshal(&decoded)

		assert.NilError(t, err)
		assert.DeepEqual(t, string(blob), encoded)
	})

	t.Run("Decoding", func(t *testing.T) {
		t.Parallel()

		ts := tasks{}
		err := json.Unmarshal([]byte(encoded), &ts)

		assert.NilError(t, err)
		assert.DeepEqual(t, ts, decoded)
	})
}

func TestTaskResultsDecoding(t *testing.T) {
	t.Parallel()

	encoded := `{
		"task_results": {
			"89991b27-6276-4d83-bf8c-f62e6c2f9587": {
				"exitCode": 0,
				"finishedTimestamp": {
					"__type__": "datetime",
					"year": 2019,
					"month": 6,
					"day": 18,
					"hour": 1,
					"minute": 1,
					"second": 1,
					"microsecond": 123
				},
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
				ExitCode: 0,
				FinishedAt: pickleTime{
					time.Date(2019, 6, 18, 1, 1, 1, 123, time.UTC),
				},
				Stdout: "data",
				Stderr: "data",
			},
		},
	})
}

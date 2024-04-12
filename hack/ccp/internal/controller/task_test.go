package controller

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/google/uuid"
	"gotest.tools/v3/assert"
)

func TestEncoding(t *testing.T) {
	t.Parallel()

	encoded := `{"tasks":[{"task_uuid":"5ef281c2-692f-49a2-b8dd-36ab4e2beca5","createdDate":"2024-04-12 05:40:20+00:00","arguments":"\"%sharedPath%\"","wants_output":true}]}`
	decoded := tasks{
		Tasks: []*task{
			{
				ID:          uuid.MustParse("5ef281c2-692f-49a2-b8dd-36ab4e2beca5"),
				CreatedAt:   mcpTime{time.Date(2024, time.April, 12, 5, 40, 20, 0, time.UTC)},
				Args:        "\"%sharedPath%\"",
				WantsOutput: true,
			},
		},
	}

	t.Run("Encoding", func(t *testing.T) {
		blob, err := json.Marshal(&decoded)

		assert.NilError(t, err)
		assert.DeepEqual(t, string(blob), encoded)
	})

	t.Run("Decoding", func(t *testing.T) {
		ts := tasks{}
		err := json.Unmarshal([]byte(encoded), &ts)

		assert.NilError(t, err)
		assert.DeepEqual(t, ts, decoded)
	})
}

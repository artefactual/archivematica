package controller

import (
	"encoding/json"
	"time"

	"github.com/google/uuid"
)

type tasks struct {
	Tasks []*task `json:"tasks"`
}

type task struct {
	ID          uuid.UUID `json:"task_uuid"`
	CreatedAt   mcpTime   `json:"createdDate"`
	Args        string    `json:"arguments"`
	WantsOutput bool      `json:"wants_output"`
}

type mcpTime struct {
	time.Time
}

// Custom time layout used by MCP.
//
// Using the reference Go time: 1136239445 (tz=MST):
//
//	>>> from datetime import datetime, timezone, timedelta
//	>>> datetime.fromtimestamp(1136239445, tz=timezone(timedelta(hours=-7))).isoformat(" ")
//	'2006-01-02 15:04:05-07:00'
const timeLayout = "2006-01-02 15:04:05-07:00"

func (t mcpTime) MarshalJSON() ([]byte, error) {
	return json.Marshal(t.Format(timeLayout))
}

func (t *mcpTime) UnmarshalJSON(data []byte) error {
	var str string
	if err := json.Unmarshal(data, &str); err != nil {
		return err
	}
	pt, err := time.Parse(timeLayout, str)
	if err != nil {
		return err
	}
	t.Time = pt
	return nil
}

package controller

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/sevein/gearmin"
)

func submitJob(ctx context.Context, gearman *gearmin.Server, funcName string, tasks *tasks) (ret []byte, err error) {
	defer func() {
		err = fmt.Errorf("submitJob: %v", err)
	}()

	if tasks == nil {
		return nil, fmt.Errorf("tasks is nil")
	}
	data, err := json.Marshal(tasks)
	if err != nil {
		return nil, fmt.Errorf("marshal tasks: %v", err)
	}

	done := make(chan struct{})

	gearman.Submit(
		&gearmin.JobRequest{
			// MCPClient lowercases the function name.
			FuncName:   strings.ToLower(funcName),
			Data:       data,
			Background: false,
			Callback: func(update gearmin.JobUpdate) {
				switch update.Type {
				case gearmin.JobUpdateTypeComplete:
					ret = update.Data
					done <- struct{}{}
				case gearmin.JobUpdateTypeException:
					ret = update.Data
					err = errors.New("failed: JobUpdateTypeException")
					done <- struct{}{}
				case gearmin.JobUpdateTypeFail:
					err = errors.New("failed: JobUpdateTypeFail")
					done <- struct{}{}
				}
			},
		},
	)

	select {
	case <-done:
		return ret, err
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

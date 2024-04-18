package controller

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/go-logr/logr"
	"github.com/sevein/gearmin"
)

func submitJob(ctx context.Context, logger logr.Logger, gearman *gearmin.Server, funcName string, tasks *tasks) (_ *taskResults, err error) {
	defer func() {
		if err != nil {
			err = fmt.Errorf("submitJob: %v", err)
		}
	}()

	if tasks == nil {
		return nil, fmt.Errorf("tasks is nil")
	}
	data, err := json.Marshal(tasks)
	if err != nil {
		return nil, fmt.Errorf("marshal tasks: %v", err)
	}

	logger.V(2).Info("Submitting job to the server.", "data", string(data))

	done := make(chan struct{})
	res := &taskResults{}

	gearman.Submit(
		&gearmin.JobRequest{
			// MCPClient lowercases the function name.
			FuncName:   strings.ToLower(funcName),
			Data:       data,
			Background: false,
			Callback: func(update gearmin.JobUpdate) {
				switch update.Type {
				case gearmin.JobUpdateTypeComplete:
					err = json.Unmarshal(update.Data, res)
					done <- struct{}{}
				case gearmin.JobUpdateTypeException:
					// TODO: encode update.Data into the error.
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
		return res, err
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

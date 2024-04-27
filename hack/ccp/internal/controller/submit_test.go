package controller

import (
	"context"
	"testing"
	"time"

	"github.com/go-logr/logr"
	"github.com/google/uuid"
	"github.com/sevein/gearmin"
	"gotest.tools/v3/assert"
)

func TestSubmitJob(t *testing.T) {
	t.Parallel()

	t.Run("Rejects nil tasks", func(t *testing.T) {
		t.Parallel()

		ret, err := submitJob(context.Background(), logr.Discard(), &gearmin.Server{}, "fn", nil)

		assert.Assert(t, ret == nil)
		assert.Error(t, err, "submitJob: tasks is nil")
	})

	t.Run("Rejects empty tasks", func(t *testing.T) {
		t.Parallel()

		ret, err := submitJob(context.Background(), logr.Discard(), &gearmin.Server{}, "fn", &tasks{})

		assert.Assert(t, ret == nil)
		assert.Error(t, err, "submitJob: marshal tasks: json: error calling MarshalJSON for type *controller.tasks: map is empty")
	})

	t.Run("Returns of context is canceled", func(t *testing.T) {
		t.Parallel()

		gearmin := fakeGearman(t)

		ctx, cancel := context.WithCancel(context.Background())
		cancel()

		ret, err := submitJob(
			ctx,
			logr.Discard(),
			gearmin,
			"fn",
			&tasks{
				Tasks: map[uuid.UUID]*task{
					uuid.MustParse("5ef281c2-692f-49a2-b8dd-36ab4e2beca5"): {
						ID:          uuid.MustParse("5ef281c2-692f-49a2-b8dd-36ab4e2beca5"),
						CreatedAt:   time.Date(2024, time.April, 12, 5, 40, 20, 0, time.UTC),
						Args:        "\"%sharedPath%\"",
						WantsOutput: true,
					},
				},
			},
		)

		assert.Assert(t, ret == nil)
		assert.Error(t, err, "submitJob: context canceled")
	})

	t.Run("Blocks until resolution", func(t *testing.T) {
		t.Skip("Needs gearmintest with workers that can do the work.")
	})
}

func fakeGearman(t *testing.T) *gearmin.Server {
	t.Helper()

	srv := gearmin.NewServer(gearmin.Config{ListenAddr: "127.0.0.1:0"})
	t.Cleanup(func() {
		srv.Stop()
	})

	return srv
}

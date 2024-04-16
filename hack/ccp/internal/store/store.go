package store

import (
	"context"
	"fmt"
	"strings"

	"github.com/go-logr/logr"
	"github.com/google/uuid"

	sqlc "github.com/artefactual/archivematica/hack/ccp/internal/store/sqlcmysql"
)

type Store interface {
	RemoveTransientData(ctx context.Context) error
	CreateJob(ctx context.Context, params *sqlc.CreateJobParams) error
	UpdateJobStatus(ctx context.Context, id uuid.UUID, status string) error

	// UpsertTransfer checks for a Transfer using the specified UUID. It updates
	// the current location if the Transfer exists, or it creates a new Transfer
	// with the provided UUID and location if it does not exist.
	UpsertTransfer(ctx context.Context, id uuid.UUID, path string) (created bool, err error)

	// EnsureTransfer checks if a Transfer exists at the given location; creates
	// a new Transfer with a new UUID otherwise.
	EnsureTransfer(ctx context.Context, path string) (id uuid.UUID, created bool, err error)

	Running() bool
	Close() error
}

func New(logger logr.Logger, driver, dsn string) (Store, error) {
	var store *mysqlStoreImpl

	switch strings.ToLower(driver) {
	case "mysql":
		{
			logger = logger.WithName("mysql")
			pool, err := connectToMySQL(logger, dsn)
			if err != nil {
				return nil, fmt.Errorf("connect to MySQL: %v", err)
			}
			store, err = newMySQLStore(logger, pool)
			if err != nil {
				return nil, fmt.Errorf("new MySQL store: %v", err)
			}
		}
	default:
		return nil, fmt.Errorf("unsupported db driver: %q", driver)
	}

	return store, nil
}

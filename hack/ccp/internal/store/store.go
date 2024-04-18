package store

import (
	"context"
	"errors"
	"fmt"
	"strings"

	"github.com/go-logr/logr"
	"github.com/google/uuid"

	sqlc "github.com/artefactual/archivematica/hack/ccp/internal/store/sqlcmysql"
)

var ErrNotFound error = errors.New("object not found")

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

	// ReadUnitVars retrieves a list of package variables associated with a
	// specific package identified by its type and UUID. It filters the
	// variables based on the provided name. If name is an empty string, it
	// returns all variables for the specified package. If name is provided,
	// only variables matching this name are returned.
	ReadUnitVars(ctx context.Context, id uuid.UUID, packageType, name string) ([]UnitVar, error)

	// ReadUnitVar reads a string value stored as a package variable.
	ReadUnitVar(ctx context.Context, id uuid.UUID, packageType, name string) (string, error)

	// ReadUnitLinkID reads a workflow link ID stored as a package variable.
	ReadUnitLinkID(ctx context.Context, id uuid.UUID, packageType, name string) (uuid.UUID, error)

	// CreateUnitVar creates a new variable.
	CreateUnitVar(ctx context.Context, id uuid.UUID, packageType, name, value string, linkID uuid.UUID, update bool) error

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

type UnitVar struct {
	Name   string
	Value  *string
	LinkID *uuid.UUID
}
